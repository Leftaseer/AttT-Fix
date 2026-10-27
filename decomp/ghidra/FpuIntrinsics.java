// The MSVC runtime's x87 intrinsics (_CIsin, _CIcos, _CIsqrt, _CIpow, _CIatan2, ...) take their arguments on the
// FPU stack and return in ST0; the game calls them through 'jmp [import]' thunks.  Without that the decompiler
// sees no arguments ('fVar = (float10)sub_005E405E();' for sin(angle)), and every function that calls one is
// decompiled without the value.  Gives each thunk (and the import) a custom-storage prototype: one argument in
// ST0, or two in ST1 and ST0 (pow(x, y): x in ST1), the result in ST0.  tools/autodecomp.py calls them through
// helpers that put the arguments there (rebuild/rt_support.c).
// Also the runtime's _ftol2_sse / _ftol2 (float to integer of ST0, found by their code): x in ST0, the result in
// EAX or EDX:EAX, and calls of them replaced by that p-code (a call fixup) which pops the FPU stack as they do.
// Args: none.  Prints the thunk addresses as 'FPU <address> <name> <arguments>', the conversions as 'FTOL'.
import ghidra.app.script.GhidraScript;
import ghidra.program.database.SpecExtension;
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

    static boolean at(byte[] b, int k, int... v) {
        for (int i = 0; i < v.length; i++) if (v[i] >= 0 && (b[k + i] & 0xff) != v[i]) return false;
        return true;
    }
    // _ftol2_sse: cmp dword [x], 0; je y; push ebp; mov ebp, esp; sub esp, 8; and esp, -8; fstp qword [esp];
    // cvttsd2si eax, [esp].  _ftol2: push ebp; mov ebp, esp; sub esp, 0x20; and esp, -16; fld st0; fst [esp+0x18];
    // fistp qword [esp+0x10]; fild qword [esp+0x10]
    static String ftolKind(byte[] b) {
        if (at(b, 0, 0x83, 0x3d, -1, -1, -1, -1, 0x00, 0x74, -1, 0x55, 0x8b, 0xec, 0x83, 0xec, 0x08, 0x83, 0xe4, 0xf8,
               0xdd, 0x1c, 0x24, 0xf2, 0x0f, 0x2c, 0x04, 0x24)) return "int";
        if (at(b, 0, 0x55, 0x8b, 0xec, 0x83, 0xec, 0x20, 0x83, 0xe4, 0xf0, 0xd9, 0xc0, 0xd9, 0x54, 0x24, 0x18, 0xdf, 0x7c,
               0x24, 0x10, 0xdf, 0x6c, 0x24, 0x10)) return "long long";
        return null;
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
        // the runtime's float to integer conversions of ST0 (as tools/crtfuncs.py finds them): _ftol2_sse returns
        // EAX, _ftol2 EDX:EAX.  The decompiler had made _ftol2_sse a __fastcall of ECX and EDX, and its 221 callers
        // passed registers they had not set.
        int ftol = 0;
        SpecExtension fixups = null;
        Register st0 = currentProgram.getRegister("ST0"), eax = currentProgram.getRegister("EAX"),
                 edx = currentProgram.getRegister("EDX");
        for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
            byte[] b = new byte[32];
            try { currentProgram.getMemory().getBytes(f.getEntryPoint(), b); } catch (Exception e) { continue; }
            String kind = ftolKind(b);
            if (kind == null) continue;
            List<Variable> ps = new ArrayList<>();
            ps.add(new ParameterImpl("x", Float10DataType.dataType, new VariableStorage(currentProgram, st0), currentProgram));
            ReturnParameterImpl ret = kind.equals("int")
                ? new ReturnParameterImpl(IntegerDataType.dataType, new VariableStorage(currentProgram, eax), currentProgram)
                : new ReturnParameterImpl(LongLongDataType.dataType, new VariableStorage(currentProgram, edx, eax), currentProgram);
            f.updateFunction("__cdecl", ret, ps, Function.FunctionUpdateType.CUSTOM_STORAGE, true, SourceType.USER_DEFINED);
            // and a call fixup: the conversion pops ST0, so what the caller keeps below it moves up.  A call keeps
            // nothing on the FPU stack for the decompiler: 0x43D440 divides two values by one constant loaded once,
            // and the second division became '/ extraout_ST0'
            if (fixups == null) {
                SpecExtension ext = new SpecExtension(currentProgram);
                for (String[] k : new String[][] { { "int", "EAX = trunc(ST0);" },
                                                   { "long long", "tmp:8 = trunc(ST0); EAX = tmp:4; EDX = tmp(4);" } })
                    ext.addReplaceCompilerSpecExtension("<callfixup name=\"decomp_ftol_" + k[0].replace(' ', '_') +
                        "\"><pcode><body><![CDATA[\n" + k[1] +
                        "\nST0 = ST1; ST1 = ST2; ST2 = ST3; ST3 = ST4; ST4 = ST5; ST5 = ST6; ST6 = ST7;" +
                        // (the fixup replaces the call, not the push of its return address: the ret's pop is ours,
                        // else ESP stays 4 lower and 0x495300's frame variables move)
                        "\nESP = ESP + 4;\n]]></body></pcode></callfixup>",
                        monitor);
                fixups = ext;
            }
            f.setCallFixup("decomp_ftol_" + kind.replace(' ', '_'));
            println(String.format("FTOL %08X %s", f.getEntryPoint().getOffset(), kind));
            ftol++;
        }
        println("float to integer conversions of ST0: " + ftol);
    }
}
