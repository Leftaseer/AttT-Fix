// Prototypes set by hand (symbols/GAME_protos.tsv: address, convention, ret pop, the prototype in C, why): where
// the analysis of the machine code cannot find them (the runtime's helpers that set up their frame with
// __SEH_prolog4, whose parameters are read through the EBP the helper sets).  The function gets the prototype, its
// name, and the storage of its convention.
// Args: symbols/GAME_protos.tsv
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.function.ApplyFunctionSignatureCmd;
import ghidra.app.util.parser.FunctionSignatureParser;
import ghidra.program.model.data.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.SourceType;
import java.nio.file.*;

public class ManualProtos extends GhidraScript {
    @Override
    public void run() throws Exception {
        FunctionSignatureParser parser = new FunctionSignatureParser(currentProgram.getDataTypeManager(), null);
        int done = 0, failed = 0;
        if (!Files.exists(Paths.get(getScriptArgs()[0]))) { println("no " + getScriptArgs()[0]); return; }
        for (String l : Files.readAllLines(Paths.get(getScriptArgs()[0]))) {
            if (l.startsWith("#") || l.trim().isEmpty()) continue;
            String[] q = l.split("\t");
            Function f = getFunctionAt(toAddr(Long.parseLong(q[0], 16)));
            if (f == null) { println("no function at " + q[0]); failed++; continue; }
            try {
                // (the convention goes separately: the parser takes none in the text)
                FunctionDefinitionDataType def = parser.parse(null, q[3].replaceAll("\\b__(cdecl|stdcall|thiscall|fastcall)\\b", ""));
                f.setCustomVariableStorage(false);
                ApplyFunctionSignatureCmd cmd = new ApplyFunctionSignatureCmd(f.getEntryPoint(), def, SourceType.USER_DEFINED);
                if (!cmd.applyTo(currentProgram)) throw new Exception(cmd.getStatusMsg());
                f.setCallingConvention("__" + q[1]);
                f.setStackPurgeSize(Integer.parseInt(q[2]));
                done++;
            } catch (Exception e) {
                println("failed " + q[0] + ": " + e.getMessage());
                failed++;
            }
        }
        println("prototypes set by hand: " + done + ", failed " + failed);
    }
}
