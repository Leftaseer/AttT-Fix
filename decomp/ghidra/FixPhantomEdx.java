// Functions whose machine code reads only ECX but whose prototype is still __fastcall with an EDX parameter
// (regparams.tsv vs the Ghidra prototype): every caller then passes an undefined EDX (extraout_EDX).  Drops
// the phantom register parameters, makes the function __thiscall and gives it the stack parameters its ret
// pops (functions.tsv), preserving the existing stack parameters' slots and types.  Runs after ApplyRegParams
// so the machine-code register inputs always win over the convention left on the function.
// Args: regparams.tsv functions.tsv
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.data.*;
import ghidra.program.model.symbol.SourceType;
import java.io.*;
import java.util.*;

public class FixPhantomEdx extends GhidraScript {
    @Override
    public void run() throws Exception {
        Map<Long, Integer> pops = new HashMap<>();
        try (BufferedReader r = new BufferedReader(new FileReader(getScriptArgs()[1]))) {
            String l;
            while ((l = r.readLine()) != null) {
                if (l.startsWith("#")) continue;
                String[] p = l.split("\t", -1);
                if (p.length < 4 || p[3].isEmpty() || p[3].equals("?")) continue;
                pops.put(Long.parseLong(p[0], 16), Integer.parseInt(p[3]));
            }
        }
        int fixed = 0, failed = 0, skipped = 0;
        try (BufferedReader r = new BufferedReader(new FileReader(getScriptArgs()[0]))) {
            String l;
            while ((l = r.readLine()) != null) {
                String[] p = l.split("\t", -1);
                // (EBP is a live value the caller leaves, not an argument: ApplyRegParams drops it too)
                List<String> rr = new ArrayList<>(Arrays.asList(p[1].split(",")));
                rr.remove("EBP");
                if (!rr.equals(List.of("ECX"))) continue;
                long ea = Long.parseLong(p[0], 16);
                Function f = getFunctionAt(toAddr(ea));
                if (f == null || f.isThunk() || f.isExternal()) continue;
                if (!f.getCallingConventionName().equals("__fastcall")) continue;
                boolean edx = false;
                List<Parameter> stack = new ArrayList<>();
                List<Variable> all = new ArrayList<>();
                int bytes = 0;
                for (Parameter q : f.getParameters()) {
                    if (q.isAutoParameter()) continue;
                    if (q.isRegisterVariable() && q.getRegister().getName().equals("EDX")) { edx = true; continue; }
                    if (q.isRegisterVariable()) continue;          // ECX: becomes the implicit this
                    if (!q.isStackVariable()) { edx = true; continue; }
                    stack.add(q);
                }
                if (!edx) continue;
                if (f.hasCustomVariableStorage()) { skipped++; continue; }
                int pop = pops.getOrDefault(ea, 0);
                stack.sort(Comparator.comparingInt(Parameter::getStackOffset));
                // contiguous from +4; keep the existing parameters' names/types in place, fill the gaps
                int off = 4;
                for (Parameter q : stack) {
                    while (off < q.getStackOffset()) {
                        all.add(new ParameterImpl("param_" + (off / 4), Undefined4DataType.dataType, currentProgram));
                        off += 4;
                    }
                    all.add(new ParameterImpl(q.getName(), q.getDataType(), currentProgram));
                    off = q.getStackOffset() + ((q.getLength() + 3) & ~3);
                }
                // (pop 0 is caller-pop: the ret says nothing about the count, the callers' pushes do)
                while (pop > 0 && off - 4 < pop) {
                    all.add(new ParameterImpl("param_" + (off / 4), Undefined4DataType.dataType, currentProgram));
                    off += 4;
                }
                if (pop > 0 && off - 4 > pop) { skipped++; continue; }     // a wide parameter overruns the ret
                try {
                    f.setCallingConvention("__thiscall");
                    f.updateFunction("__thiscall", f.getReturn(), all,
                            Function.FunctionUpdateType.DYNAMIC_STORAGE_FORMAL_PARAMS, true, SourceType.ANALYSIS);
                    fixed++;
                    println(String.format("%08X %s pop=%d stack=%d", ea, f.getName(), pop, all.size()));
                } catch (Exception e) { failed++; println("failed " + f.getEntryPoint() + ": " + e.getMessage()); }
            }
        }
        println("phantom EDX fixed " + fixed + ", skipped " + skipped + ", failed " + failed);
    }
}
