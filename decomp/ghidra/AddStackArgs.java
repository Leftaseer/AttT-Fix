// Functions whose decompiled body reads an incoming stack slot above the prototype's parameters
// ('in_stack_000000xx', no 'ff'): the prototype lacks stack arguments the machine code has.  The slots come from
// the ret pop (symbols/<game>_functions.tsv) and the stack slots the machine code uses
// (symbols/<game>_stackparams.tsv, exact counts): parameters are added up to max(pop, 4*slots), at their own
// offsets for custom storage (ApplyRegParams), appended for the decompiler's own.  Only functions whose current
// decompilation really shows such a slot are touched, so the popped slots the decompiler never reads (fit_convention
// gives those to build.py's shims) stay filler.  A body that tests the caller's flags (in_OF, a funclet that is no
// function start) or reads slots past what the tables give (a lost stack depth) is left alone.
// Args: functions.tsv stackparams.tsv [addresses of hand-written replacements to leave alone (DECOMP(...))]
import ghidra.app.decompiler.*;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.data.*;
import ghidra.program.model.symbol.SourceType;
import java.io.*;
import java.util.*;
import java.util.regex.*;

public class AddStackArgs extends GhidraScript {
    static int roundup(int n) { return (n + 3) & ~3; }

    @Override
    public void run() throws Exception {
        Map<Long, Integer> pops = new HashMap<>();
        for (String l : readLines(getScriptArgs()[0])) {
            if (l.startsWith("#")) continue;
            String[] p = l.split("\t", -1);
            if (p.length < 4 || p[3].equals("?")) continue;
            pops.put(Long.parseLong(p[0], 16), p[3].isEmpty() ? 0 : Integer.parseInt(p[3]));
        }
        Map<Long, Integer> slots = new HashMap<>();
        Set<Long> exact = new HashSet<>();
        for (String l : readLines(getScriptArgs()[1])) {
            if (l.startsWith("#")) continue;
            String[] p = l.split("\t", -1);
            if (p.length < 3) continue;
            long a = Long.parseLong(p[0], 16);
            slots.put(a, Integer.parseInt(p[1]));
            if (p[2].equals("exact")) exact.add(a);
        }
        Set<Long> hand = new HashSet<>();
        if (getScriptArgs().length > 2)
            for (String l : readLines(getScriptArgs()[2]))
                if (!l.isEmpty() && !l.startsWith("#")) hand.add(Long.parseLong(l.trim(), 16));
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        int added = 0, skipped = 0, failed = 0;
        for (long a : new TreeSet<>(pops.keySet())) {
            if (hand.contains(a)) continue;
            int pop = pops.get(a);
            int nslots = exact.contains(a) ? slots.getOrDefault(a, 0) : 0;
            int target = Math.max(pop, 4 * nslots);
            if (target == 0) continue;
            if (nslots > 32) { skipped++; continue; }         // a lost stack depth, not a parameter list
            Function f = getFunctionAt(toAddr(a));
            if (f == null || f.isThunk() || f.isExternal()) continue;
            List<Parameter> stack = new ArrayList<>();
            boolean[] covered = new boolean[target / 4 + 1];
            int have = 0;
            for (Parameter q : f.getParameters()) {
                if (q.isAutoParameter() || !q.isStackVariable()) continue;
                stack.add(q);
                int off = q.getStackOffset(), n = roundup(q.getLength());
                have = Math.max(have, off - 4 + n);
                for (int k = (off - 4) / 4; k < (off - 4 + n) / 4 && k < covered.length; k++) covered[k] = true;
            }
            if (have >= target) continue;
            DecompileResults r = di.decompileFunction(f, 60, monitor);
            if (!r.decompileCompleted()) { failed++; continue; }
            String c = r.getDecompiledFunction().getC();
            if (Pattern.compile("\\bin_(?:OF|SF|ZF|CF|PF)\\b").matcher(c).find()) { skipped++; continue; }  // a funclet
            Matcher m = Pattern.compile("\\bin_stack_([0-9a-f]{8})\\b").matcher(c);
            boolean reads = false, beyond = false;
            while (m.find()) {
                int off = (int) Long.parseLong(m.group(1), 16);
                if (off < 0) continue;                    // below the frame (ffffffxx): outgoing arguments, not parameters
                if (off > target) { beyond = true; break; }   // (a slot at offset 4 is inside a 4-byte target)
                reads = true;
            }
            if (!reads || beyond) { skipped++; continue; }
            boolean custom = f.hasCustomVariableStorage();
            List<Variable> all = new ArrayList<>();
            Set<String> names = new HashSet<>();
            for (Parameter q : f.getParameters()) {
                if (q.isAutoParameter()) continue;
                names.add(q.getName());
                all.add(custom ? new ParameterImpl(q.getName(), q.getDataType(), q.getVariableStorage(), currentProgram)
                               : new ParameterImpl(q.getName(), q.getDataType(), currentProgram));
            }
            int idx = all.size() + 1;
            for (int k = 0; 4 * k < target; k++) {
                if (k < covered.length && covered[k]) continue;
                String n = "param_" + idx++;
                while (names.contains(n)) n = "param_" + idx++;
                names.add(n);
                all.add(custom ? new ParameterImpl(n, Undefined4DataType.dataType,
                                     new VariableStorage(currentProgram, 4 + 4 * k, 4), currentProgram)
                               : new ParameterImpl(n, Undefined4DataType.dataType, currentProgram));
            }
            try {
                f.updateFunction(f.getCallingConventionName(), f.getReturn(), all,
                    custom ? Function.FunctionUpdateType.CUSTOM_STORAGE : Function.FunctionUpdateType.DYNAMIC_STORAGE_FORMAL_PARAMS,
                    true, SourceType.ANALYSIS);
                added++;
                println(String.format("%08X %s pop=%d slots=%d stack %d->%d", a, f.getName(), pop, nslots, have, target));
            } catch (Exception e) { failed++; }
        }
        di.dispose();
        println("stack arguments added to " + added + " functions, skipped " + skipped + ", failed " + failed);
    }

    static List<String> readLines(String path) throws IOException {
        List<String> out = new ArrayList<>();
        try (BufferedReader r = new BufferedReader(new FileReader(path))) {
            String l;
            while ((l = r.readLine()) != null) out.add(l);
        }
        return out;
    }
}
