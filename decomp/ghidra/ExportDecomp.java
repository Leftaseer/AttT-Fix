// Decompile every function (in parallel) and write JSON lines {a, name, ns, sig, cc, size, c} to the given file.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.app.decompiler.parallel.*;
import ghidra.program.model.listing.*;
import ghidra.util.task.TaskMonitor;
import java.io.*;
import java.util.*;

public class ExportDecomp extends GhidraScript {
    static String js(String s) {
        StringBuilder b = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            switch (c) {
                case '"': b.append("\\\""); break;
                case '\\': b.append("\\\\"); break;
                case '\n': b.append("\\n"); break;
                case '\r': break;
                case '\t': b.append("\\t"); break;
                default: if (c < 32) b.append(String.format("\\u%04x", (int)c)); else b.append(c);
            }
        }
        return b.append('"').toString();
    }
    @Override
    public void run() throws Exception {
        String out = getScriptArgs()[0];
        List<Function> funcs = new ArrayList<>();
        for (Function f : currentProgram.getFunctionManager().getFunctions(true))
            if (!f.isExternal()) funcs.add(f);
        DecompilerCallback<String> cb = new DecompilerCallback<>(currentProgram, new DecompileConfigurer() {
            public void configure(DecompInterface d) {
                DecompileOptions o = new DecompileOptions();
                o.setMaxPayloadMBytes(200);
                d.setOptions(o);
                d.toggleCCode(true); d.setSimplificationStyle("decompile");
            }
        }) {
            public String process(DecompileResults r, TaskMonitor m) {
                Function f = r.getFunction();
                String c = r.getDecompiledFunction() != null ? r.getDecompiledFunction().getC() : ("/* decompilation failed: " + r.getErrorMessage() + " */");
                return "{\"a\":\"" + f.getEntryPoint() + "\",\"name\":" + js(f.getName()) + ",\"ns\":" + js(f.getParentNamespace().getName(true)) +
                    ",\"sig\":" + js(f.getSignature().getPrototypeString()) + ",\"cc\":" + js(f.getCallingConventionName()) +
                    ",\"size\":" + f.getBody().getNumAddresses() + ",\"c\":" + js(c) + "}";
            }
        };
        cb.setTimeout(120);
        List<String> res = ParallelDecompiler.decompileFunctions(cb, funcs, monitor);
        cb.dispose();
        try (PrintWriter w = new PrintWriter(new OutputStreamWriter(new FileOutputStream(out), "UTF-8"))) {
            for (String s : res) if (s != null) w.println(s);
        }
        println("exported " + res.size() + " functions");
    }
}
