// Re-run auto analysis with the Decompiler Parameter ID analyzer enabled (calling conventions, params).
import ghidra.app.script.GhidraScript;
import java.util.*;
public class ParamId extends GhidraScript {
    @Override
    public void run() throws Exception {
        Map<String, String> o = new HashMap<>();
        o.put("Decompiler Parameter ID", "true");
        setAnalysisOptions(currentProgram, o);
        analyzeAll(currentProgram);
    }
}
