// Make the stack parameters of callee-pop functions agree with their ret: symbols/<game>_functions.tsv has the
// bytes each function pops (ret N).  The decompiler often finds fewer parameters (one is only addressed, not
// read) or more; then every caller is decompiled with arguments missing or invented.  Functions with ret N and
// a caller-pop convention become __stdcall.  Custom storage (ApplyRegParams) is left alone.
// Caller-pop functions (no ret N) get the stack parameters their machine code uses (stackparams.py), when the
// decompiler found fewer: a parameter that is only passed on to a call is easily missed; or as many as their
// callers push, when that is more (an HRESULT check given __FILE__ and __LINE__ it ignores).
// Byte and word parameters whose slot the machine code reads as a dword (stackparams.py) become undefined4;
// untyped or integer ones whose slot only float instructions use become float (or double).
// Args: functions.tsv [stackparams.tsv]
import ghidra.program.model.listing.VariableStorage;
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
                if (p[3].equals("?")) continue;
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
        if (getScriptArgs().length > 1) {
            Map<Long, Integer> pops = new HashMap<>();
            try (BufferedReader r = new BufferedReader(new FileReader(getScriptArgs()[0]))) {
                String line;
                while ((line = r.readLine()) != null) {
                    if (line.startsWith("#")) continue;
                    String[] p = line.split("\t", -1);
                    pops.put(Long.parseLong(p[0], 16), p[3].isEmpty() ? 0 : p[3].equals("?") ? -1 : Integer.parseInt(p[3]));
                }
            }
            int grown = 0, gfail = 0, shrunk = 0;
            try (BufferedReader r = new BufferedReader(new FileReader(getScriptArgs()[1]))) {
                String line;
                while ((line = r.readLine()) != null) {
                    if (line.startsWith("#")) continue;
                    String[] p = line.split("\t", -1);
                    long a = Long.parseLong(p[0], 16);
                    // the slots the machine code uses (when ESP could be followed everywhere), or the arguments its
                    // callers push if more (a function may ignore some: then the decompiler gives the extra pushes to
                    // a call nearby)
                    int slots = p[2].equals("exact") ? Integer.parseInt(p[1]) : 0;
                    if (p.length > 4 && !p[4].isEmpty()) slots = Math.max(slots, Integer.parseInt(p[4]));
                    if (pops.getOrDefault(a, 0) != 0 || (slots == 0 && !p[2].equals("exact"))) continue;
                    Function f = getFunctionAt(toAddr(a));
                    if (f == null || f.isThunk() || f.isExternal()) continue;
                    int have = 0;
                    for (Parameter q : f.getParameters())
                        if (q.isStackVariable()) have = Math.max(have, (q.getStackOffset() - 4 + q.getLength() + 3) / 4);
                    if (have > slots && p[2].equals("exact")) {
                        // more than the machine code reads and the callers push: parameters an earlier, wrong
                        // count gave it (a local taken for a parameter); its callers' saved registers then
                        // looked like arguments (unaff_ESI)
                        try {
                            boolean custom = f.hasCustomVariableStorage();
                            List<Variable> keep = new ArrayList<>();
                            for (Parameter q : f.getParameters()) {
                                if (q.isAutoParameter()) continue;
                                if (q.isStackVariable() && (q.getStackOffset() - 4) / 4 >= slots) continue;
                                keep.add(custom ? new ParameterImpl(q.getName(), q.getDataType(), q.getVariableStorage(), currentProgram)
                                                : new ParameterImpl(q.getName(), q.getDataType(), currentProgram));
                            }
                            f.updateFunction(f.getCallingConventionName(), f.getReturn(), keep,
                                custom ? Function.FunctionUpdateType.CUSTOM_STORAGE : Function.FunctionUpdateType.DYNAMIC_STORAGE_FORMAL_PARAMS,
                                true, SourceType.ANALYSIS);
                            shrunk++;
                        } catch (Exception e) { gfail++; }
                        continue;
                    }
                    if (have >= slots) continue;
                    try {
                        boolean custom = f.hasCustomVariableStorage();
                        List<Variable> all = new ArrayList<>();
                        for (Parameter q : f.getParameters()) {
                            if (q.isAutoParameter()) continue;
                            all.add(custom ? new ParameterImpl(q.getName(), q.getDataType(), q.getVariableStorage(), currentProgram)
                                           : new ParameterImpl(q.getName(), q.getDataType(), currentProgram));
                        }
                        for (int k = have; k < slots; k++) {
                            String n = "param_" + (all.size() + 1);
                            all.add(custom ? new ParameterImpl(n, Undefined4DataType.dataType,
                                                 new VariableStorage(currentProgram, 4 + 4 * k, 4), currentProgram)
                                           : new ParameterImpl(n, Undefined4DataType.dataType, currentProgram));
                        }
                        f.updateFunction(f.getCallingConventionName(), f.getReturn(), all,
                            custom ? Function.FunctionUpdateType.CUSTOM_STORAGE : Function.FunctionUpdateType.DYNAMIC_STORAGE_FORMAL_PARAMS,
                            true, SourceType.ANALYSIS);
                        grown++;
                    } catch (Exception e) { gfail++; }
                }
            }
            println("caller-pop functions given the stack parameters they use: " + grown + ", fewer: " + shrunk + ", failed " + gfail);
            // parameters typed narrower than 4 bytes whose slot the machine code reads as a whole dword (and never
            // writes): the callers would cut a pointer down to a byte
            int widened = 0, wfail = 0;
            try (BufferedReader r = new BufferedReader(new FileReader(getScriptArgs()[1]))) {
                String line;
                while ((line = r.readLine()) != null) {
                    if (line.startsWith("#")) continue;
                    String[] p = line.split("\t", -1);
                    if (p.length < 4 || p[3].isEmpty()) continue;
                    Set<Integer> dw = new HashSet<>();
                    for (String k : p[3].split(",")) dw.add(Integer.parseInt(k));
                    Function f = getFunctionAt(toAddr(Long.parseLong(p[0], 16)));
                    if (f == null || f.isThunk() || f.isExternal()) continue;
                    boolean change = false;
                    for (Parameter q : f.getParameters())
                        if (q.isStackVariable() && q.getLength() < 4 && (q.getStackOffset() - 4) % 4 == 0 &&
                            dw.contains((q.getStackOffset() - 4) / 4)) change = true;
                    if (!change) continue;
                    try {
                        boolean custom = f.hasCustomVariableStorage();
                        List<Variable> all = new ArrayList<>();
                        for (Parameter q : f.getParameters()) {
                            if (q.isAutoParameter()) continue;
                            DataType t = q.getDataType();
                            boolean wide = q.isStackVariable() && q.getLength() < 4 && (q.getStackOffset() - 4) % 4 == 0 &&
                                           dw.contains((q.getStackOffset() - 4) / 4);
                            if (wide) t = Undefined4DataType.dataType;
                            all.add(custom ? new ParameterImpl(q.getName(), t, wide ? new VariableStorage(currentProgram,
                                                 q.getStackOffset(), 4) : q.getVariableStorage(), currentProgram)
                                           : new ParameterImpl(q.getName(), t, currentProgram));
                        }
                        f.updateFunction(f.getCallingConventionName(), f.getReturn(), all,
                            custom ? Function.FunctionUpdateType.CUSTOM_STORAGE : Function.FunctionUpdateType.DYNAMIC_STORAGE_FORMAL_PARAMS,
                            true, SourceType.ANALYSIS);
                        widened++;
                    } catch (Exception e) { wfail++; }
                }
            }
            println("byte/word parameters read as dwords, widened: " + widened + ", failed " + wfail);
            // untyped or integer parameters whose slot only float instructions use (stackparams.py): float, or
            // double for an 8-byte one; sqrt(x) had x undefined4, and callers passed float bits as an integer
            int floated = 0, ffail = 0;
            try (BufferedReader r = new BufferedReader(new FileReader(getScriptArgs()[1]))) {
                String line;
                while ((line = r.readLine()) != null) {
                    if (line.startsWith("#")) continue;
                    String[] p = line.split("\t", -1);
                    if (p.length < 6 || p[5].isEmpty()) continue;
                    Map<Integer, String> fl = new HashMap<>();
                    for (String e : p[5].split(",")) fl.put(Integer.parseInt(e.split(":")[0]), e.split(":")[1]);
                    Function f = getFunctionAt(toAddr(Long.parseLong(p[0], 16)));
                    if (f == null || f.isThunk() || f.isExternal()) continue;
                    boolean custom = f.hasCustomVariableStorage(), change = false;
                    List<Variable> all = new ArrayList<>();
                    for (Parameter q : f.getParameters()) {
                        if (q.isAutoParameter()) continue;
                        DataType t = q.getDataType();
                        if (q.isStackVariable() && (q.getStackOffset() - 4) % 4 == 0 && fl.containsKey((q.getStackOffset() - 4) / 4)) {
                            String w = fl.get((q.getStackOffset() - 4) / 4);
                            DataType b = t instanceof TypeDef ? ((TypeDef) t).getBaseDataType() : t;
                            boolean integral = b instanceof Undefined || b instanceof AbstractIntegerDataType || b instanceof DefaultDataType;
                            if (integral && w.equals("f") && t.getLength() == 4) { t = FloatDataType.dataType; change = true; }
                            if (integral && w.equals("d") && t.getLength() == 8) { t = DoubleDataType.dataType; change = true; }
                        }
                        all.add(custom ? new ParameterImpl(q.getName(), t, q.getVariableStorage(), currentProgram)
                                       : new ParameterImpl(q.getName(), t, currentProgram));
                    }
                    if (!change) continue;
                    try {
                        f.updateFunction(f.getCallingConventionName(), f.getReturn(), all,
                            custom ? Function.FunctionUpdateType.CUSTOM_STORAGE : Function.FunctionUpdateType.DYNAMIC_STORAGE_FORMAL_PARAMS,
                            true, SourceType.ANALYSIS);
                        floated++;
                    } catch (Exception e) { ffail++; }
                }
            }
            println("parameters only used as floats typed float/double in " + floated + " functions, failed " + ffail);
        }
        println("parameters added to " + added + ", removed from " + removed + ", made __stdcall " + conv + ", failed " + fail);
    }
}
