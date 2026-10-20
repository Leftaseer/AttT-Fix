// The MSVC runtime's x87 intrinsics (_CIsin, _CIcos, _CIsqrt, _CIpow, _CIatan2, ...) take their arguments on the
// FPU stack and return in ST0; the game calls them through 'jmp [import]' thunks.  Without that the decompiler
// sees no arguments ('fVar = (float10)sub_005E405E();' for sin(angle)), and every function that calls one is
// decompiled without the value.  Gives each thunk (and the import) a custom-storage prototype: one argument in
// ST0, or two in ST1 and ST0 (pow(x, y): x in ST1), the result in ST0.  tools/autodecomp.py calls them through
// helpers that put the arguments there (rebuild/rt_support.c).
// Args: none.  Prints the thunk addresses as 'FPU <address> <name> <arguments>'.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.data.*;
import ghidra.program.model.lang.Register;
import ghidra.program.model.symbol.*;
import java.util.*;

public class FpuIntrinsics extends GhidraScript {
    static final Map<String, Integer> ARGS = new HashMap<>();
    static {
        for (String n : new String[] { "_CIsin", "_CIcos", "_CItan", "_CIsqrt", "_CIatan", "_CIasin", "_CIacos",
                                       "_CIexp", "_CIlog", "_CIlog10", "_CIsinh", "_CIcosh", "_CItanh" })
            ARGS.put(n, 1);
        for (String n : new String[] { "_CIpow", "_CIatan2", "_CIfmod" })
            ARGS.put(n, 2);
    }

    void apply(Function f, int n) throws Exception {
        DataType t = Float10DataType.dataType;
        Register st0 = currentProgram.getRegister("ST0"), st1 = currentProgram.getRegister("ST1");
        List<Variable> ps = new ArrayList<>();
        if (n == 2) ps.add(new ParameterImpl("x", t, new VariableStorage(currentProgram, st1), currentProgram));
        ps.add(new ParameterImpl(n == 2 ? "y" : "x", t, new VariableStorage(currentProgram, st0), currentProgram));
        ReturnParameterImpl ret = new ReturnParameterImpl(t, new VariableStorage(currentProgram, st0), currentProgram);
        f.updateFunction("__cdecl", ret, ps, Function.FunctionUpdateType.CUSTOM_STORAGE, true, SourceType.USER_DEFINED);
    }

    @Override
    public void run() throws Exception {
        int done = 0;
        for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
            Function target = f.isThunk() ? f.getThunkedFunction(true) : null;
            if (target == null) {
                // 'jmp [IAT]' thunks the analysis did not mark: the reference of the first instruction
                Instruction i = getInstructionAt(f.getEntryPoint());
                if (i == null || !i.getMnemonicString().equals("JMP")) continue;
                for (Reference r : i.getReferencesFrom()) {
                    Symbol s = getSymbolAt(r.getToAddress());
                    if (s != null && ARGS.containsKey(s.getName())) {
                        apply(f, ARGS.get(s.getName()));
                        println(String.format("FPU %08X %s %d", f.getEntryPoint().getOffset(), s.getName(), ARGS.get(s.getName())));
                        done++;
                    }
                }
                continue;
            }
            if (!ARGS.containsKey(target.getName())) continue;
            apply(f, ARGS.get(target.getName()));
            if (target.isExternal()) apply(target, ARGS.get(target.getName()));
            println(String.format("FPU %08X %s %d", f.getEntryPoint().getOffset(), target.getName(), ARGS.get(target.getName())));
            done++;
        }
        println("x87 intrinsic thunks given their FPU arguments: " + done);
    }
}
