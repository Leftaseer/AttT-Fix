// Apply names from a symbol file: "ADDRESS KIND NAME [# comment]", KIND f = function, d = data label.
// Qualified names (A::B::name, templates allowed) create class namespaces; methods of classes become __thiscall
// unless they already have custom storage.  Later lines win over earlier ones for the same address.
import ghidra.app.script.GhidraScript;
import ghidra.app.util.NamespaceUtils;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.address.*;
import ghidra.app.cmd.function.CreateFunctionCmd;
import java.io.*;
import java.util.*;

public class ApplySymbols extends GhidraScript {
    static List<String> split(String q) {
        List<String> parts = new ArrayList<>(); int depth = 0; StringBuilder cur = new StringBuilder();
        for (int i = 0; i < q.length(); i++) {
            char c = q.charAt(i);
            if (c == '<') depth++; else if (c == '>') depth--;
            if (depth == 0 && c == ':' && i + 1 < q.length() && q.charAt(i + 1) == ':') { parts.add(cur.toString()); cur.setLength(0); i++; continue; }
            cur.append(c);
        }
        parts.add(cur.toString()); return parts;
    }
    @Override
    public void run() throws Exception {
        int fn = 0, dn = 0, bad = 0;
        boolean setThis = getScriptArgs().length > 1 && getScriptArgs()[1].equals("thiscall");
        for (String file : getScriptArgs()[0].split(",")) {
            try (BufferedReader r = new BufferedReader(new FileReader(file))) {
                String line;
                while ((line = r.readLine()) != null) {
                    int h = line.indexOf('#'); if (h >= 0) line = line.substring(0, h);
                    line = line.trim(); if (line.isEmpty()) continue;
                    String[] p = line.split("\\s+", 3); if (p.length < 3) continue;
                    Address a = toAddr(Long.parseLong(p[0], 16));
                    String full = p[2].trim().replace(' ', '_');
                    List<String> parts = split(full);
                    String name = parts.remove(parts.size() - 1);
                    try {
                        Namespace ns = currentProgram.getGlobalNamespace();
                        if (!parts.isEmpty()) {
                            ns = NamespaceUtils.createNamespaceHierarchy(String.join("::", parts), null, currentProgram, SourceType.IMPORTED);
                            if (!(ns instanceof GhidraClass) && p[1].equals("f")) {
                                try { ns = NamespaceUtils.convertNamespaceToClass(ns); } catch (Exception e) { }
                            }
                        }
                        if (p[1].equals("f")) {
                            Function f = getFunctionAt(a);
                            if (f == null) {
                                new CreateFunctionCmd(a).applyTo(currentProgram, monitor);
                                f = getFunctionAt(a);
                            }
                            if (f == null) { bad++; continue; }
                            f.setName(name, SourceType.IMPORTED);
                            f.setParentNamespace(ns);
                            fn++;
                        } else {
                            Symbol s = createLabel(a, name, ns, true, SourceType.IMPORTED);
                            dn++;
                        }
                    } catch (Exception e) { bad++; println("failed " + p[0] + " " + full + ": " + e.getMessage()); }
                }
            }
        }
        println("applied " + fn + " function names, " + dn + " labels, " + bad + " failures");
    }
}
