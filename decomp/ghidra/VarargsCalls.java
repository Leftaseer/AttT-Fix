// Calls of C functions with variable arguments (sprintf and the like, imports of the C runtime among them): the
// decompiler passes only the fixed parameters and drops the rest ('sprintf(buf, "%s 1. %s")' at 0x5111E0, whose two
// strings were lost and the game faulted).  The caller removes all it pushed ('add esp, N' after the call): each such
// call gets a call-site override with the callee's fixed parameters and undefined4 for the other N/4 dwords.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.data.*;
import ghidra.program.model.lang.OperandType;
import ghidra.program.model.pcode.HighFunctionDBUtil;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.symbol.*;
import java.util.*;

public class VarargsCalls extends GhidraScript {
    Function callee(Instruction call) {
        for (Reference r : call.getReferencesFrom()) {
            if (!r.getReferenceType().isCall() && r.getReferenceType() != RefType.INDIRECTION &&
                    !r.getReferenceType().isData()) continue;
            Address to = r.getToAddress();
            Function t = getFunctionAt(to);
            if (t == null) {
                // 'call [slot]': the import the slot names
                for (Reference x : getReferencesFrom(to))
                    if (x.isExternalReference() && ((ExternalReference) x).getExternalLocation() != null)
                        t = ((ExternalReference) x).getExternalLocation().getFunction();
            }
            if (t != null && t.isThunk()) t = t.getThunkedFunction(true);
            if (t != null) return t;
        }
        return null;
    }

    // N of the 'add esp, N' among the few instructions after the call that leave ESP alone, -1 if none
    int cleanup(Instruction call) {
        Instruction i = call.getNext();
        for (int k = 0; i != null && k < 4; k++, i = i.getNext()) {
            String m = i.getMnemonicString();
            if (m.equals("ADD") && i.getRegister(0) != null && i.getRegister(0).getName().equals("ESP")) {
                Scalar s = i.getScalar(1);
                return s == null ? -1 : (int) s.getValue();
            }
            if (m.equals("CALL") || m.startsWith("J") || m.equals("RET") || m.startsWith("PUSH") || m.startsWith("POP"))
                return -1;
            for (Object o : i.getResultObjects())
                if (o instanceof ghidra.program.model.lang.Register && ((ghidra.program.model.lang.Register) o).getName().equals("ESP"))
                    return -1;
        }
        return -1;
    }

    // the instruction pushing argument k of the call (arguments are pushed last to first: argument 0 is the
    // last push before the call), null where the pushes are not plain
    Instruction pushOf(Instruction call, int k) {
        Instruction i = call.getPrevious();
        int seen = 0;
        for (int j = 0; i != null && j < 24; j++, i = i.getPrevious()) {
            String m = i.getMnemonicString();
            if (m.equals("CALL") || m.startsWith("J") || m.equals("RET")) return null;
            if (m.equals("PUSH")) {
                if (seen == k) return i;
                seen++;
            }
            if (m.equals("SUB") && i.getRegister(0) != null && i.getRegister(0).getName().equals("ESP")) return null;
        }
        return null;
    }

    // the sizes of the variable arguments a constant format string asks for (4 or 8 each, 'd' for a double), null
    // where it is not one or not understood
    List<String> formatArgs(Address a) {
        StringBuilder sb = new StringBuilder();
        try {
            for (int k = 0; k < 512; k++) {
                byte b = getByte(a.add(k));
                if (b == 0) break;
                sb.append((char) (b & 0xff));
            }
        } catch (Exception e) { return null; }
        String f = sb.toString();
        List<String> out = new ArrayList<>();
        for (int i = 0; i < f.length(); i++) {
            if (f.charAt(i) != '%') continue;
            i++;
            if (i < f.length() && f.charAt(i) == '%') continue;
            String mod = "";
            while (i < f.length() && "-+ #0123456789.*hlLI64".indexOf(f.charAt(i)) >= 0) {
                if (f.charAt(i) == '*') out.add("4");
                mod += f.charAt(i);
                i++;
            }
            if (i >= f.length()) return null;
            char c = f.charAt(i);
            boolean wide = mod.contains("I64") || mod.contains("ll");
            if ("diouxXc".indexOf(c) >= 0) out.add(wide ? "8" : "4");
            else if ("sSpn".indexOf(c) >= 0) out.add("4");
            else if ("feEgGaA".indexOf(c) >= 0) out.add("d");
            else return null;
        }
        return out;
    }

    @Override
    public void run() throws Exception {
        DataTypeManager dtm = currentProgram.getDataTypeManager();
        int written = 0, skipped = 0;
        for (Instruction ins : currentProgram.getListing().getInstructions(true)) {
            if (!ins.getMnemonicString().equals("CALL")) continue;
            Function t = callee(ins);
            if (t == null || !t.hasVarArgs()) continue;
            Function fn = getFunctionContaining(ins.getAddress());
            int n = cleanup(ins);
            if (fn == null || n <= 0 || !t.getCallingConventionName().equals("__cdecl")) { skipped++; continue; }
            List<ParameterDefinition> ps = new ArrayList<>();
            int bytes = 0;
            for (Parameter p : t.getParameters()) {
                int len = (p.getLength() + 3) / 4 * 4;
                if (bytes + len > n) break;
                ps.add(new ParameterDefinitionImpl(p.getName(), p.getDataType(), null));
                bytes += len;
            }
            // the types the format asks for, where it is a constant pushed as the last fixed parameter and they fill
            // the bytes removed (a double for %f: 0x45D460)
            List<String> fa = null;
            if (!ps.isEmpty()) {
                Instruction pu = pushOf(ins, ps.size() - 1);
                Scalar sc = pu != null ? pu.getScalar(0) : null;
                if (sc != null) {
                    fa = formatArgs(toAddr(sc.getUnsignedValue()));
                    int sum = 0;
                    if (fa != null) for (String x : fa) sum += x.equals("4") ? 4 : 8;
                    if (fa != null && sum != n - bytes) fa = null;
                }
            }
            int k = 0;
            if (fa != null)
                for (String x : fa) {
                    ps.add(new ParameterDefinitionImpl("va" + k++, x.equals("d") ? DoubleDataType.dataType :
                        x.equals("8") ? LongLongDataType.dataType : Undefined4DataType.dataType, null));
                    bytes += x.equals("4") ? 4 : 8;
                }
            for (; bytes < n; k++, bytes += 4)
                ps.add(new ParameterDefinitionImpl("va" + k, Undefined4DataType.dataType, null));
            FunctionDefinitionDataType def = new FunctionDefinitionDataType(String.format("vacall_%08X",
                ins.getAddress().getOffset()), dtm);
            def.setArguments(ps.toArray(new ParameterDefinition[0]));
            def.setReturnType(t.getReturnType());
            def.setCallingConvention("__cdecl");
            try {
                HighFunctionDBUtil.writeOverride(fn, ins.getAddress(), def);
                written++;
            } catch (Exception e) { skipped++; }
        }
        println("varargs call overrides: " + written + " written, " + skipped + " skipped");
    }
}
