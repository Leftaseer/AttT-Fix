// Functions whose callers use EAX after the call (tools/retlive.py, also through virtual calls) but that the
// decompiler typed void or left undefined (then it decides there is no result): their result becomes undefined4, so the decompiler writes out what the machine code
// leaves in EAX (CRenderObject::vf7 leaves 'this' there and a virtual call of that slot uses it).  Where that
// value is something the decompiler cannot express, its output says so (extraout_EAX) and the function is left
// out by tools/autodecomp.py as before.
// A float result the decompiler gave a function on its own (not one of tools/x87ret.py's, which the machine code
// shows leaving ST0) goes the same way when callers use EAX: the constructor 0x431C60 returns this, and its
// callers (0x5119A0, a factory, and 0x516880 after it) had an extraout_EAX.
// Args: retlive.tsv [x87ret.tsv]
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.data.*;
import ghidra.program.model.symbol.SourceType;
import java.io.*;

public class SetReturns extends GhidraScript {
    @Override
    public void run() throws Exception {
        int set = 0, fail = 0;
        java.util.Set<Long> x87 = null;
        if (getScriptArgs().length > 1) {
            x87 = new java.util.HashSet<>();
            for (String l : java.nio.file.Files.readAllLines(java.nio.file.Paths.get(getScriptArgs()[1])))
                if (!l.startsWith("#") && !l.isBlank()) x87.add(Long.parseLong(l.split("\t")[0], 16));
        }
        try (BufferedReader r = new BufferedReader(new FileReader(getScriptArgs()[0]))) {
            for (String l; (l = r.readLine()) != null; ) {
                if (l.startsWith("#") || l.isBlank()) continue;
                Function f = getFunctionAt(toAddr(Long.parseLong(l.trim(), 16)));
                if (f == null || f.isThunk() || f.isExternal()) continue;
                DataType rt = f.getReturnType();
                boolean guessedFloat = x87 != null && (rt instanceof FloatDataType || rt instanceof DoubleDataType ||
                    rt instanceof Float10DataType) && !x87.contains(f.getEntryPoint().getOffset());
                if (!(rt instanceof VoidDataType) && !(rt instanceof Undefined) && !(rt instanceof DefaultDataType) &&
                        !guessedFloat) continue;
                try {
                    // a locked undefined4: the decompiler must express the result instead of deciding there is none
                    // (with custom storage, the one of register parameters, the result needs its register
                    // named: setReturnType leaves it without storage and the decompiler shows void, 0x4254A0)
                    if (f.hasCustomVariableStorage())
                        f.setReturn(Undefined4DataType.dataType, new VariableStorage(currentProgram,
                            currentProgram.getRegister("EAX")), SourceType.USER_DEFINED);
                    else
                        f.setReturnType(Undefined4DataType.dataType, SourceType.USER_DEFINED);
                    f.setSignatureSource(SourceType.USER_DEFINED);
                    set++;
                } catch (Exception e) { fail++; }
            }
        }
        println("void functions whose callers use EAX given an undefined4 result: " + set + ", failed " + fail);
    }
}
