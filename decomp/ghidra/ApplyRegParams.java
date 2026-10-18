// Apply register inputs found by regparams.py (machine-code liveness): plain ECX -> __thiscall, ECX+EDX ->
// __fastcall, anything else -> custom storage (ECX first, then EAX, EDX, EBX, ESI, EDI, then stack params).
// Arg: regparams.tsv
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.data.*;
import ghidra.program.model.lang.Register;
import ghidra.program.model.symbol.SourceType;
import java.io.*;
import java.util.*;

public class ApplyRegParams extends GhidraScript {
    static final String[] ORDER = {"ECX", "EAX", "EDX", "EBX", "ESI", "EDI"};
    @Override
    public void run() throws Exception {
        int thisc = 0, fast = 0, custom = 0, fail = 0;
        try (BufferedReader r = new BufferedReader(new FileReader(getScriptArgs()[0]))) {
            String line;
            while ((line = r.readLine()) != null) {
                String[] p = line.split("\t", -1);
                Function f = getFunctionAt(toAddr(Long.parseLong(p[0], 16)));
                if (f == null || f.isThunk()) continue;
                String n = f.getName();
                if (n.startsWith("Unwind@") || n.startsWith("Catch@")) continue;
                Set<String> regs = new HashSet<>();
                for (String x : p[1].split(",")) if (!x.isEmpty() && !x.equals("EBP")) regs.add(x);
                if (regs.isEmpty()) continue;
                String cc = f.getCallingConventionName();
                try {
                    if (regs.equals(Set.of("ECX"))) {
                        if (!cc.equals("__thiscall") && !cc.equals("__fastcall")) { f.setCallingConvention("__thiscall"); thisc++; }
                        else if (cc.equals("__fastcall") && f.getParameterCount() >= 2 && f.getParameter(1).isRegisterVariable()) {
                            f.setCallingConvention("__thiscall"); thisc++;
                        }
                        continue;
                    }
                    if (regs.equals(Set.of("ECX", "EDX")) || regs.equals(Set.of("EDX"))) {
                        if (!cc.equals("__fastcall")) { f.setCallingConvention("__fastcall"); fast++; }
                        continue;
                    }
                    List<Variable> params = new ArrayList<>();
                    for (String o : ORDER) {
                        if (!regs.contains(o)) continue;
                        Register reg = currentProgram.getRegister(o);
                        String pn = o.equals("ECX") ? "this" : "in_" + o.toLowerCase();
                        params.add(new ParameterImpl(pn, Undefined4DataType.dataType, reg, currentProgram));
                    }
                    for (Parameter q : f.getParameters()) {
                        if (q.isStackVariable())
                            params.add(new ParameterImpl(q.getName(), q.getDataType(), q.getVariableStorage(), currentProgram));
                    }
                    f.updateFunction(cc.equals("unknown") ? "__stdcall" : cc, f.getReturn(), params,
                        Function.FunctionUpdateType.CUSTOM_STORAGE, true, SourceType.ANALYSIS);
                    custom++;
                } catch (Exception e) { fail++; }
            }
        }
        println("thiscall " + thisc + ", fastcall " + fast + ", custom " + custom + ", failed " + fail);
    }
}
