// std::string parameters passed by value (tools/byvalue.py: the function destroys a string in its own parameter
// area): the caller copy-constructs the string in the outgoing arguments and the callee owns it.  The decompiler
// took the 7 dwords for separate parameters (or for none) and lost the depth of the stack in the callers
// (0x42AF50 passed the return addresses of earlier calls on to 0x42A010).  Those slots become one 28-byte
// parameter of the type StrByValue; tools/autodecomp.py passes it as a C struct.
// Args: byvalue.tsv (address, parameter offsets from the return address, ret pop)
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.data.*;
import ghidra.program.model.symbol.SourceType;
import java.io.*;
import java.util.*;

public class ByValueParams extends GhidraScript {
    static String unique(String n, Set<String> names) {
        String m = n;
        for (int k = 2; names.contains(m); k++) m = n + "_" + k;
        names.add(m);
        return m;
    }
    @Override
    public void run() throws Exception {
        DataTypeManager dtm = currentProgram.getDataTypeManager();
        StructureDataType sd = new StructureDataType(new CategoryPath("/decomp"), "StrByValue", 0, dtm);
        for (int k = 0; k < 7; k++) sd.add(Undefined4DataType.dataType, 4, "d" + k, null);
        DataType str = dtm.addDataType(sd, DataTypeConflictHandler.REPLACE_HANDLER);
        int done = 0, fail = 0;
        try (BufferedReader r = new BufferedReader(new FileReader(getScriptArgs()[0]))) {
            for (String line; (line = r.readLine()) != null; ) {
                if (line.startsWith("#") || line.isBlank()) continue;
                String[] p = line.split("\t", -1);
                Function f = getFunctionAt(toAddr(Long.parseLong(p[0], 16)));
                if (f == null || f.isThunk() || f.isExternal()) continue;
                Set<Integer> offs = new TreeSet<>();
                for (String o : p[1].split(",")) offs.add(Integer.parseInt(o));
                int pop = p[2].isEmpty() || p[2].equals("?") ? 0 : Integer.parseInt(p[2]);
                boolean custom = f.hasCustomVariableStorage();
                List<Variable> regs = new ArrayList<>();
                Map<Integer, Parameter> stack = new TreeMap<>();
                int end = 4;
                for (Parameter q : f.getParameters()) {
                    if (q.isAutoParameter()) continue;
                    if (q.isStackVariable()) {
                        stack.put(q.getStackOffset(), q);
                        end = Math.max(end, q.getStackOffset() + ((q.getLength() + 3) & ~3));
                    } else regs.add(custom ? new ParameterImpl(q.getName(), q.getDataType(), q.getVariableStorage(), currentProgram)
                                           : new ParameterImpl(q.getName(), q.getDataType(), currentProgram));
                }
                for (int o : offs) end = Math.max(end, o + 28);
                if (pop > 0) end = Math.max(end, 4 + pop);
                List<Variable> all = new ArrayList<>(regs);
                boolean ok = true;
                Set<String> names = new HashSet<>();
                for (Variable v : regs) names.add(v.getName());
                for (int o = 4; o < end; ) {
                    if (offs.contains(o)) {
                        String n = unique("str_" + (o - 4) / 4, names);
                        all.add(custom ? new ParameterImpl(n, str, new VariableStorage(currentProgram, o, 28), currentProgram)
                                       : new ParameterImpl(n, str, currentProgram));
                        o += 28;
                        continue;
                    }
                    Parameter q = stack.get(o);
                    DataType t = q != null && q.getLength() <= 4 ? q.getDataType() : Undefined4DataType.dataType;
                    if (q != null && q.getLength() > 4) {
                        // a wide parameter (a double) not overlapping a string keeps its place
                        boolean clash = false;
                        for (int s : offs) if (s < o + q.getLength() && o < s + 28) clash = true;
                        if (!clash) {
                            names.add(q.getName());
                            all.add(custom ? new ParameterImpl(q.getName(), q.getDataType(), q.getVariableStorage(), currentProgram)
                                           : new ParameterImpl(q.getName(), q.getDataType(), currentProgram));
                            o += (q.getLength() + 3) & ~3;
                            continue;
                        }
                    }
                    String n = unique(q != null && q.getLength() <= 4 ? q.getName() : "param_" + (o - 4) / 4, names);
                    all.add(custom ? new ParameterImpl(n, t.getLength() == 4 ? t : Undefined4DataType.dataType,
                                                       new VariableStorage(currentProgram, o, 4), currentProgram)
                                   : new ParameterImpl(n, t.getLength() == 4 ? t : Undefined4DataType.dataType, currentProgram));
                    o += 4;
                }
                if (!ok) { fail++; continue; }
                try {
                    f.updateFunction(f.getCallingConventionName(), f.getReturn(), all,
                        custom ? Function.FunctionUpdateType.CUSTOM_STORAGE : Function.FunctionUpdateType.DYNAMIC_STORAGE_FORMAL_PARAMS,
                        true, SourceType.USER_DEFINED);
                    done++;
                } catch (Exception e) { println("failed " + f.getName() + ": " + e.getMessage()); fail++; }
            }
        }
        println("functions given std::string parameters by value: " + done + ", failed " + fail);
    }
}
