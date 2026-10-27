// Functions that leave ECX or EDX as they found them (column 5 of symbols/GAME_functions.tsv, tools/regclobber.py:
// the volatile registers a function changes, through its callees too).  Their callers built with /LTCG use the
// register again after the call: the decompiler, taking the convention's word that a call kills ECX and EDX, made
// that value an 'extraout_ECX' (0x459C30 keeps this in ECX across 0x459810), and the function could not be
// translated.  Gives each such function a copy of its calling convention with those registers unaffected
// (__thiscall_keepECX, ...: prototype models added to the program's compiler spec), keeping its storage.
// tools/autodecomp.py and AutoExport.java print the plain convention name.
// Args: symbols/GAME_functions.tsv
import ghidra.app.script.GhidraScript;
import ghidra.framework.Application;
import ghidra.program.database.SpecExtension;
import ghidra.program.model.lang.PrototypeModel;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.SourceType;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;

public class KeepRegisters extends GhidraScript {
    @Override
    public void run() throws Exception {
        String cspec = new String(Files.readAllBytes(Paths.get(Application.getInstallationDirectory().getAbsolutePath(),
            "Ghidra", "Processors", "x86", "data", "languages", "x86win.cspec")));
        Map<String, String> base = new HashMap<>();
        Matcher m = Pattern.compile("<prototype name=\"(__\\w+)\".*?</prototype>", Pattern.DOTALL).matcher(cspec);
        while (m.find()) base.put(m.group(1), m.group());
        SpecExtension ext = new SpecExtension(currentProgram);
        Set<String> made = new HashSet<>();
        int done = 0, skipped = 0;
        for (String l : Files.readAllLines(Paths.get(getScriptArgs()[0]))) {
            if (l.startsWith("#")) continue;
            String[] q = l.split("\t", -1);
            if (q.length < 5) continue;
            Set<String> changed = new HashSet<>(Arrays.asList(q[4].split(",")));
            List<String> keep = new ArrayList<>();
            for (String r : new String[] { "ECX", "EDX" }) if (!changed.contains(r)) keep.add(r);
            if (keep.isEmpty()) continue;
            Function f = getFunctionAt(toAddr(Long.parseLong(q[0], 16)));
            if (f == null || f.isThunk()) continue;
            String cc = f.getCallingConventionName();
            String plain = cc.replaceAll("_keep[A-Z]+$", "");
            // (the decompiler gives only a convention named __thiscall its implicit this: a copy of it would lose the
            // parameter, unless the storage is the function's own)
            if (plain.equals("__thiscall") && !f.hasCustomVariableStorage()) { skipped++; continue; }
            String xml = base.get(plain);
            if (xml == null) { skipped++; continue; }
            String name = plain + "_keep" + String.join("", keep);
            if (!made.contains(name)) {
                String x = xml.replaceFirst("name=\"" + plain + "\"", "name=\"" + name + "\"");
                for (String r : keep) {
                    // out of killedbycall and likelytrash, into unaffected
                    x = x.replaceAll("(?s)(<killedbycall>.*?)\\s*<register name=\"" + r + "\"/>(.*?</killedbycall>)", "$1$2");
                    x = x.replaceAll("(?s)(<likelytrash>.*?)\\s*<register name=\"" + r + "\"/>(.*?</likelytrash>)", "$1$2");
                    x = x.replaceFirst("<unaffected>", "<unaffected>\n      <register name=\"" + r + "\"/>");
                }
                x = x.replaceAll("<(likelytrash|killedbycall)>\\s*</\\1>", "");     // (no empty lists)
                ext.addReplaceCompilerSpecExtension(x, monitor);
                made.add(name);
            }
            if (name.equals(cc)) continue;
            boolean custom = f.hasCustomVariableStorage();
            f.setCallingConvention(name);
            if (custom && !f.hasCustomVariableStorage()) f.setCustomVariableStorage(true);
            done++;
        }
        println("functions keeping ECX/EDX given conventions that say so: " + done + ", conventions " + made +
                ", without a base convention or a __thiscall without its own storage " + skipped);
    }
}
