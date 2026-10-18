// Make the stack parameters of callee-pop functions agree with their ret: symbols/<game>_functions.tsv has the
// bytes each function pops (ret N).  The decompiler often finds fewer parameters (one is only addressed, not
// read) or more; then every caller is decompiled with arguments missing or invented.  Functions with ret N and
// a caller-pop convention become __stdcall.  Custom storage (ApplyRegParams) is left alone.
// Arg: functions.tsv
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.data.*;
import ghidra.program.model.symbol.SourceType;
import java.io.*;
import java.util.*;

public class FixStackParams extends GhidraScript {
    @Override
    public void run() throws Exception {
        int added = 0, removed = 0, conv = 0, fail = 0;
        try (BufferedReader r = new BufferedReader(new FileReader(getScriptArgs()[0]))) {
            String line;
            while ((line = r.readLine()) != null) {
                if (line.startsWith("#")) continue;
                String[] p = line.split("\t", -1);
                Function f = getFunctionAt(toAddr(Long.parseLong(p[0], 16)));
                if (f == null || f.isThunk() || f.hasCustomVariableStorage() || f.isExternal()) continue;
                int pop = p[3].isEmpty() ? 0 : Integer.parseInt(p[3]);
                String cc = f.getCallingConventionName();
                if (pop == 0) continue;                   // caller-pop: the ret says nothing about the count
                if (cc.equals("__cdecl") || cc.equals("unknown") || cc.equals("default")) cc = "__stdcall";
                List<Variable> regs = new ArrayList<>(), stack = new ArrayList<>();
                int bytes = 0;
                for (Parameter q : f.getParameters()) {
                    if (q.isAutoParameter()) continue;     // this of __thiscall: the convention adds it again
                    if (q.isStackVariable()) {
                        stack.add(new ParameterImpl(q.getName(), q.getDataType(), currentProgram));
                        bytes += (q.getLength() + 3) & ~3;
                    } else regs.add(new ParameterImpl(q.getName(), q.getDataType(), currentProgram));
                }
                if (bytes == pop && cc.equals(f.getCallingConventionName())) continue;
                int a0 = 0, r0 = 0;
                while (bytes > pop && !stack.isEmpty()) {
                    Variable last = stack.get(stack.size() - 1);
                    int n = (last.getLength() + 3) & ~3;
                    if (bytes - n < pop) break;
                    stack.remove(stack.size() - 1); bytes -= n; r0++;
                }
                if (bytes > pop) { fail++; continue; }        // a wide parameter straddles the ret size
                int idx = regs.size() + stack.size() + 1;
                Set<String> names = new HashSet<>();
                for (Variable v : regs) names.add(v.getName());
                for (Variable v : stack) names.add(v.getName());
                while (bytes < pop) {
                    String n = "param_" + idx++;
                    while (names.contains(n)) n = "param_" + idx++;
                    stack.add(new ParameterImpl(n, Undefined4DataType.dataType, currentProgram));
                    bytes += 4; a0++;
                }
                List<Variable> all = new ArrayList<>();
                // the convention's own register parameters (this of __thiscall, ECX/EDX of __fastcall) come first
                all.addAll(regs);
                all.addAll(stack);
                try {
                    boolean changedConv = !cc.equals(f.getCallingConventionName());
                    f.updateFunction(cc, f.getReturn(), all, Function.FunctionUpdateType.DYNAMIC_STORAGE_FORMAL_PARAMS,
                        true, SourceType.ANALYSIS);
                    if (changedConv) conv++;
                    if (a0 > 0) added++;
                    if (r0 > 0) removed++;
                } catch (Exception e) { fail++; }
            }
        }
        println("parameters added to " + added + ", removed from " + removed + ", made __stdcall " + conv + ", failed " + fail);
    }
}
