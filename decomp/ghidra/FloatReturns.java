// Functions that leave their result in ST0 (tools/x87ret.py follows the x87 stack to their rets) get a float or
// double result.  The decompiler typed many of them 'float10' and, as 10 bytes do not fit its ST0 return entry,
// gave them a hidden pointer to the result as a first stack parameter (sqrt(x) became
// 'float10 *f(float10 *__return_storage_ptr__)' and its x the pointer); others it typed int or void.  Their
// callers then mix float and integer bits (extraout_ST0) and tools/autodecomp.py leaves them out.
// The stack slot the hidden pointer took is a parameter (x of sqrt): it stays, as undefined4.
// Runs before FixStackParams.java, which then counts the stack parameters again.
// Args: x87ret.tsv
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.data.*;
import ghidra.program.model.symbol.SourceType;
import java.io.*;
import java.util.*;

public class FloatReturns extends GhidraScript {
    @Override
    public void run() throws Exception {
        int set = 0, hidden = 0, custom = 0, fail = 0;
        List<Function> customs = new ArrayList<>();
        Map<Function, DataType> types = new HashMap<>();
        VariableStorage floatSt0 = null, doubleSt0 = null;
        try (BufferedReader r = new BufferedReader(new FileReader(getScriptArgs()[0]))) {
            for (String l; (l = r.readLine()) != null; ) {
                if (l.startsWith("#") || l.isBlank()) continue;
                String[] q = l.split("\t");
                Function f = getFunctionAt(toAddr(Long.parseLong(q[0], 16)));
                if (f == null || f.isThunk() || f.isExternal()) continue;
                DataType t = q[1].equals("float") ? FloatDataType.dataType : DoubleDataType.dataType;
                if (f.hasCustomVariableStorage()) {
                    customs.add(f);
                    types.put(f, t);
                    continue;
                }
                try {
                    // the formal parameters only: 'this' and the hidden result pointer are the convention's
                    // (the stack slot of the hidden pointer is a real parameter: it stays, untyped)
                    List<Variable> ps = new ArrayList<>();
                    for (Parameter p : f.getParameters()) {
                        if (p.isAutoParameter()) {
                            if (p.getAutoParameterType() == AutoParameterType.RETURN_STORAGE_PTR) {
                                ps.add(new ParameterImpl("param_0", Undefined4DataType.dataType, currentProgram, SourceType.USER_DEFINED));
                                hidden++;
                            }
                            continue;
                        }
                        ps.add(new ParameterImpl(p.getName(), p.getDataType(), currentProgram, p.getSource()));
                    }
                    String cc = f.getCallingConventionName();
                    if ("__stdcall".equals(cc) && f.getStackPurgeSize() == 0) cc = "__cdecl";
                    f.updateFunction(cc, new ReturnParameterImpl(t, currentProgram), ps,
                                     Function.FunctionUpdateType.DYNAMIC_STORAGE_FORMAL_PARAMS, true, SourceType.USER_DEFINED);
                    VariableStorage s = f.getReturn().getVariableStorage();
                    if (t == FloatDataType.dataType && floatSt0 == null) floatSt0 = s;
                    if (t == DoubleDataType.dataType && doubleSt0 == null) doubleSt0 = s;
                    set++;
                } catch (Exception e) {
                    println(String.format("failed %s: %s", f.getEntryPoint(), e.getMessage()));
                    fail++;
                }
            }
        }
        // register parameters (custom storage): the result goes where the convention puts a float of that size
        for (Function f : customs) {
            DataType t = types.get(f);
            VariableStorage s = t == FloatDataType.dataType ? floatSt0 : doubleSt0;
            if (s == null) { fail++; continue; }
            try {
                f.setReturn(t, s, SourceType.USER_DEFINED);
                f.setSignatureSource(SourceType.USER_DEFINED);
                custom++;
            } catch (Exception e) {
                println(String.format("failed %s: %s", f.getEntryPoint(), e.getMessage()));
                fail++;
            }
        }
        println(String.format("float results in ST0: %d set (%d had a hidden result pointer), %d with register parameters, failed %d; storage %s / %s",
                              set, hidden, custom, fail, floatSt0, doubleSt0));
    }
}
