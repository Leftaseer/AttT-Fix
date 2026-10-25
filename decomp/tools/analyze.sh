#!/usr/bin/env bash
# Full analysis of both games from the user's own executables:
#   Ghidra project with names, register conventions and class structures, symbol tables in decomp/symbols,
#   raw decompilation split into units (one .cpp per class / source file) in $WORK/decomp.
#
# usage: GHIDRA=/path/to/ghidra_11.x WORK=/path/to/workdir decomp/tools/analyze.sh ATThrone_AttT.exe ATThrone_Valkyrie.exe
# needs: Ghidra 11.x (+ JDK 21), python3 with pefile and capstone, llvm (llvm-undname).
# Takes about an hour on 4 cores.  Nothing here is written into the repository except decomp/symbols.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SYMS="$HERE/../symbols"
GH="$HERE/../ghidra"
: "${GHIDRA:?set GHIDRA to the Ghidra install directory}"
: "${WORK:?set WORK to a work directory}"
HL="$GHIDRA/support/analyzeHeadless"
mkdir -p "$WORK"/{bin,proj,out,logs,decomp}
cp "$1" "$WORK/bin/attt.exe"
cp "$2" "$WORK/bin/valk.exe"
O="$WORK/out"
py() { python3 -I "$HERE/$1" "${@:2}"; }

# 1. import, auto analysis, functions Ghidra misses (after int3 padding), parameter ID
for g in attt valk; do
  "$HL" "$WORK/proj" $g -import "$WORK/bin/$g.exe" -max-cpu 4 > "$WORK/logs/import_$g.log" 2>&1
  "$HL" "$WORK/proj" $g -process $g.exe -scriptPath "$GH" -preScript AddMissingFunctions.java \
        -postScript ParamId.java > "$WORK/logs/pass2_$g.log" 2>&1
  "$HL" "$WORK/proj" $g -process $g.exe -noanalysis -readOnly -scriptPath "$GH" \
        -postScript DumpInfo.java "$O/${g}_g1" > "$WORK/logs/dump_$g.log" 2>&1
  cut -f1 "$O/${g}_g1/functions.tsv" | grep -v EXTERNAL > "$O/${g}_starts.tsv"
  py binfeat.py "$WORK/bin/$g.exe" "$O/${g}_starts.tsv" "$O/${g}_binfeat.json"
  py rtti.py "$WORK/bin/$g.exe" "$O/${g}_rtti.json"
  py vnames.py "$WORK/bin/$g.exe" "$O/${g}_rtti.json" "$O/${g}_rtti.sym"
  py staticinit.py "$WORK/bin/$g.exe" "$O/${g}_lunar.json"
  py regparams.py "$WORK/bin/$g.exe" "$O/${g}_binfeat.json" "$O/${g}_regparams.tsv"
  py regclobber.py "$WORK/bin/$g.exe" "$O/${g}_binfeat.json" "$O/${g}_clobber.tsv"
done
py luaglobals.py "$WORK/bin/attt.exe" 4031F0 4034F0 "$O/attt_luaglobals.tsv"
py luaglobals.py "$WORK/bin/valk.exe" 403010 403320 "$O/valk_luaglobals.tsv"

# 2. Lua 5.1 library functions (optional: needs the Lua 5.1.2 sources and i686-w64-mingw32-gcc)
LUALIB=/dev/null
if [ -n "${LUA_SRC:-}" ]; then
  mkdir -p "$WORK/lua_o2"
  for f in "$LUA_SRC"/*.c; do
    i686-w64-mingw32-gcc -O2 -fno-toplevel-reorder -fno-optimize-sibling-calls -fno-reorder-functions -c "$f" \
      -o "$WORK/lua_o2/$(basename "${f%.c}").o"
  done
  py srcfeat.py "$O/lua_feat.json" $(ls "$WORK"/lua_o2/*.o | grep -v -E '/(lua|luac|print)\.o$')
  py libmatch.py "$O/lua_feat.json" "$LUA_SRC" "$O/attt_binfeat.json" "$WORK/bin/attt.exe" "$O/attt_lua.tsv" \
     seed=4031F0:lua_pushcclosure seed=4034F0:lua_setfield range=401000:430000
  LUALIB="$O/attt_lua.tsv"
fi

# 3. symbol tables: AttT, then the function/data maps to Valkyrie and the Valkyrie table
py buildsyms.py --exe "$WORK/bin/attt.exe" --rtti "$O/attt_rtti.json" --rttisym "$O/attt_rtti.sym" \
   --lunar "$O/attt_lunar.json" --luaglobals "$O/attt_luaglobals.tsv" --lualib "$LUALIB" \
   --manual "$SYMS/attt_manual.sym" --out "$SYMS/attt.sym"
XMATCH_EXTRA="$O/attt_lunar.json,$O/valk_lunar.json,$O/attt_luaglobals.tsv,$O/valk_luaglobals.tsv" \
  py crossmatch.py "$WORK/bin/attt.exe" "$O/attt_binfeat.json" "$O/attt_rtti.json" \
                   "$WORK/bin/valk.exe" "$O/valk_binfeat.json" "$O/valk_rtti.json" "$SYMS/attt2valk.tsv"
py datamap.py "$WORK/bin/attt.exe" "$O/attt_binfeat.json" "$WORK/bin/valk.exe" "$O/valk_binfeat.json" \
   "$SYMS/attt2valk.tsv" "$SYMS/attt2valk_data.tsv"
py portsyms.py "$SYMS/attt.sym" "$SYMS/attt2valk.tsv" "$HERE/../../src/exeaddr.h" "$O/valk_from_attt.sym"
py portsyms.py "$SYMS/attt_manual.sym" "$SYMS/attt2valk.tsv" "$HERE/../../src/exeaddr.h" "$O/valk_manual.sym"
py buildsyms.py --exe "$WORK/bin/valk.exe" --rtti "$O/valk_rtti.json" --rttisym "$O/valk_rtti.sym" \
   --lunar "$O/valk_lunar.json" --luaglobals "$O/valk_luaglobals.tsv" --ported "$O/valk_from_attt.sym" \
   --manual "$O/valk_manual.sym" --out "$SYMS/valk.sym"
for g in attt valk; do
  py ctors.py "$WORK/bin/$g.exe" "$O/${g}_rtti.json" "$O/${g}_binfeat.json" "$SYMS/$g.sym" "$SYMS/${g}_ctors.sym" "$O/${g}_sizes.json"
  # twice: the second regparams pass knows the stack parameters of the callees (which pushes are arguments)
  for pass in 1 2; do
    [ $pass = 2 ] && py regparams.py "$WORK/bin/$g.exe" "$O/${g}_binfeat.json" "$O/${g}_regparams.tsv" \
                        "$SYMS/${g}_stackparams.tsv" "$SYMS/${g}_functions.tsv"
    python3 -I - "$O" "$SYMS" $g <<'EOF'
import json, sys
o, s, g = sys.argv[1:4]
bf = json.load(open('%s/%s_binfeat.json' % (o, g)))
rp = {l.split('\t')[0]: l.rstrip('\n').split('\t') for l in open('%s/%s_regparams.tsv' % (o, g))}
cl = {l.split('\t')[0]: l.rstrip('\n').split('\t')[1] for l in open('%s/%s_clobber.tsv' % (o, g))}
with open('%s/%s_functions.tsv' % (s, g), 'w') as f:
    f.write('# address\tsize\tregister inputs\tret pop bytes\tvolatile registers changed (transitively)\n')
    for a in sorted(bf):
        r = rp.get(a, [a, '', ''])
        f.write('%s\t%d\t%s\t%s\t%s\n' % (a, bf[a]['size'], r[1], r[2] if r[2] and ',' not in r[2] else '?', cl.get(a, 'EAX,ECX,EDX')))
EOF
    py tailpop.py "$WORK/bin/$g.exe" "$O/${g}_regparams.tsv" "$SYMS/${g}_functions.tsv"
    py retlive.py "$WORK/bin/$g.exe" "$SYMS/${g}_functions.tsv" "$SYMS/${g}_retlive.tsv" "$SYMS/$g.sym"   # + virtual calls
    py x87ret.py "$WORK/bin/$g.exe" "$SYMS/${g}_functions.tsv" "$SYMS/${g}_x87ret.tsv"   # float results in ST0
    py icalls.py "$WORK/bin/$g.exe" "$SYMS/${g}_functions.tsv" "$O/${g}_icalls0.tsv"   # pops of indirect callees
    py stackparams.py "$WORK/bin/$g.exe" "$SYMS/${g}_functions.tsv" "$SYMS/${g}_stackparams.tsv" - "$O/${g}_icalls0.tsv"
    py importargs.py "$WORK/bin/$g.exe" "$SYMS/${g}_importargs.tsv"
    py cxximports.py "$WORK/bin/$g.exe" "$SYMS/${g}_cxximports.tsv"
    py byvalue.py "$WORK/bin/$g.exe" "$SYMS/${g}_functions.tsv" "$O/${g}_icalls0.tsv" "$SYMS/${g}_byvalue.tsv"   # strings by value
  done
  # functions that hand on their caller's EAX (found by earlier exports: tools/eaxin.py update)
  [ -f "$SYMS/${g}_eaxin.tsv" ] && py eaxin.py apply "$SYMS/${g}_eaxin.tsv" "$O/${g}_regparams.tsv" "$SYMS/${g}_functions.tsv"
done

# 4. back into Ghidra: register conventions, names, thiscall methods, class structures; export
for g in attt valk; do
  "$HL" "$WORK/proj" $g -process $g.exe -noanalysis -scriptPath "$GH" \
     -postScript FixNoReturn.java \
     -postScript RecoverSwitches.java "$SYMS/${g}_functions.tsv" \
     -postScript ApplyRegParams.java "$O/${g}_regparams.tsv" \
     -postScript ApplySymbols.java "$SYMS/$g.sym,$SYMS/${g}_ctors.sym" \
     -postScript ClassThiscall.java "$O/${g}_regparams.tsv" \
     -postScript FloatReturns.java "$SYMS/${g}_x87ret.tsv" \
     -postScript FixStackParams.java "$SYMS/${g}_functions.tsv" "$SYMS/${g}_stackparams.tsv" \
     -postScript SetReturns.java "$SYMS/${g}_retlive.tsv" \
     -postScript ByValueParams.java "$SYMS/${g}_byvalue.tsv" \
     -postScript FpuIntrinsics.java \
     -postScript DecoratedImports.java "$SYMS/import_protos.tsv" "$SYMS/${g}_cxximports.tsv" \
     -postScript ThrowNoReturn.java \
     -postScript TailCalls.java \
     -postScript FillClassStructs.java "$O/${g}_sizes.json" "$O/${g}_rtti.json" \
     -postScript ExportDecomp.java "$WORK/decomp/$g.jsonl" > "$WORK/logs/annotate_$g.log" 2>&1
  py organize.py "$WORK/decomp/$g.jsonl" "$SYMS/$g.sym" "$O/${g}_binfeat.json" "$WORK/decomp/$g" --game $g
done

# 5. compilable C of every function the decompiler handled cleanly (AttT), for rebuild/build.py --auto;
#    indirect calls get call-site prototypes from the machine code first
#    (a first export gives the conventions of the imports that icalls.py follows the stack through)
"$HL" "$WORK/proj" attt -process attt.exe -noanalysis -readOnly -scriptPath "$GH" \
   -postScript AutoExport.java "$WORK/decomp/attt_auto0.jsonl" "$WORK/decomp/attt_auto0_types.h" > "$WORK/logs/auto0_attt.log" 2>&1
py icalls.py "$WORK/bin/attt.exe" "$SYMS/attt_functions.tsv" "$O/attt_icalls.tsv" "$WORK/decomp/attt_auto0.jsonl.protos" "$SYMS/attt.sym" "$SYMS/attt_icall_pops.tsv" "$O/attt_rtti.json"
"$HL" "$WORK/proj" attt -process attt.exe -noanalysis -scriptPath "$GH" \
   -postScript ICallOverride.java "$O/attt_icalls.tsv" "$O/attt_icall_overrides.tsv" > "$WORK/logs/icall_attt.log" 2>&1
"$HL" "$WORK/proj" attt -process attt.exe -noanalysis -readOnly -scriptPath "$GH" \
   -postScript AutoExport.java "$WORK/decomp/attt_auto.jsonl" "$WORK/decomp/attt_auto_types.h" > "$WORK/logs/auto_attt.log" 2>&1
py autodecomp.py "$WORK/decomp/attt_auto.jsonl" "$WORK/decomp/attt_auto_types.h" "$WORK/auto/attt" \
   --exe "$WORK/bin/attt.exe" --functions "$SYMS/attt_functions.tsv" \
   --syms "$O/attt_g1/symbols.tsv" --syms "$SYMS/attt.sym" --syms "$SYMS/attt_manual.sym" --icalls "$O/attt_icall_overrides.tsv" \
   --exclude-range 401000-420600   # Lua 5.1.2: from its sources
echo "done: Ghidra projects in $WORK/proj, decompilation in $WORK/decomp, compilable C in $WORK/auto/attt"
