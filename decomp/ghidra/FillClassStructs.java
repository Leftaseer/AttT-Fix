// Build class structures: size from operator new sites, primary base class embedded at offset 0, vftable pointer,
// then fields discovered from 'this' accesses in every method (Ghidra's FillOutStructureHelper).
// Args: sizes.json rtti.json
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.app.decompiler.util.FillOutStructureHelper;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.data.*;
import ghidra.program.model.pcode.*;
import ghidra.app.util.NamespaceUtils;
import com.google.gson.*;
import java.io.*;
import java.util.*;

public class FillClassStructs extends GhidraScript {
    @Override
    public void run() throws Exception {
        JsonObject sizes = JsonParser.parseReader(new FileReader(getScriptArgs()[0])).getAsJsonObject();
        JsonArray rtti = JsonParser.parseReader(new FileReader(getScriptArgs()[1])).getAsJsonArray();
        DataTypeManager dtm = currentProgram.getDataTypeManager();
        SymbolTable st = currentProgram.getSymbolTable();
        Map<String, GhidraClass> classes = new HashMap<>();
        Iterator<GhidraClass> ci = st.getClassNamespaces();
        while (ci.hasNext()) { GhidraClass c = ci.next(); classes.put(c.getName(true), c); }
        // order: fewer bases first
        Map<String, List<String>> bases = new HashMap<>();
        Map<String, Integer> primaryBaseOff = new HashMap<>();
        for (JsonElement e : rtti) {
            JsonObject o = e.getAsJsonObject();
            List<String> b = new ArrayList<>();
            for (JsonElement x : o.getAsJsonArray("bases")) b.add(x.getAsJsonObject().get("name").getAsString());
            bases.put(o.get("name").getAsString(), b);
        }
        List<String> order = new ArrayList<>(classes.keySet());
        order.sort(Comparator.comparingInt(n -> bases.getOrDefault(n, List.of()).size()));
        int structs = 0;
        int tx = currentProgram.startTransaction("class structs");
        Map<String, Structure> sts = new HashMap<>();
        for (String n : order) {
            GhidraClass c = classes.get(n);
            Structure s0 = VariableUtilities.findOrCreateClassStruct(c, dtm);
            if (s0 == null) continue;
            Structure s = (Structure) dtm.resolve(s0, DataTypeConflictHandler.KEEP_HANDLER);
            sts.put(n, s);
            int size = sizes.has(n) ? sizes.get(n).getAsInt() : 0;
            List<String> b = bases.getOrDefault(n, List.of());
            // primary base = first base after the class itself (MSVC lists the class first, then bases depth-first)
            Structure base = null;
            if (b.size() > 1 && sts.containsKey(b.get(1))) base = sts.get(b.get(1));
            try {
                if (base != null && base.getLength() > 1 && s.isZeroLength()) {
                    s.insertAtOffset(0, base, base.getLength(), "base_" + base.getName().replaceAll("[^A-Za-z0-9_]", "_"), null);
                } else if (s.isZeroLength() && !st.getSymbols("vftable", c).isEmpty()) {
                    s.insertAtOffset(0, new PointerDataType(), 4, "vftable", null);
                }
                if (size > s.getLength()) s.growStructure(size - s.getLength());
            } catch (Exception ex) { println("struct " + n + ": " + ex.getMessage()); }
            structs++;
        }
        currentProgram.endTransaction(tx, true);
        println("structures prepared: " + structs);
        // fill fields from methods
        FillOutStructureHelper helper = new FillOutStructureHelper(currentProgram, monitor);
        DecompInterface d = helper.setUpDecompiler(new DecompileOptions());
        d.openProgram(currentProgram);
        int done = 0, failed = 0;
        for (String n : order) {
            GhidraClass c = classes.get(n);
            Structure s = sts.get(n);
            if (s == null) continue;
            for (Symbol sym : st.getSymbols(c)) {
                if (sym.getSymbolType() != SymbolType.FUNCTION) continue;
                Function f = getFunctionAt(sym.getAddress());
                if (f == null || f.getParameterCount() == 0) continue;
                Parameter p0 = f.getParameter(0);
                if (!"this".equals(p0.getName())) continue;
                int t = currentProgram.startTransaction("fill " + n);
                boolean ok = false;
                try {
                    if (!(p0.getDataType() instanceof Pointer) || !(((Pointer)p0.getDataType()).getDataType() instanceof Structure)) {
                        if (!p0.isAutoParameter()) p0.setDataType(new PointerDataType(s), SourceType.ANALYSIS);
                    }
                    DecompileResults r = d.decompileFunction(f, 60, monitor);
                    HighFunction hf = r.getHighFunction();
                    if (hf != null) {
                        HighSymbol hs = hf.getLocalSymbolMap().getParamSymbol(0);
                        if (hs != null && hs.getHighVariable() != null) {
                            Structure res = helper.processStructure(hs.getHighVariable(), f, false, false, d);
                            if (res != null) {
                                dtm.addDataType(res, DataTypeConflictHandler.REPLACE_HANDLER);
                                ok = true;
                            }
                        }
                    }
                } catch (Exception ex) { failed++; }
                currentProgram.endTransaction(t, true);
                if (ok) done++;
            }
        }
        d.dispose();
        println("methods processed: " + done + ", failed: " + failed);
    }
}
