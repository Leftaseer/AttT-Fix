// Export decompiled functions in a form that can be compiled again (for tools/autodecomp.py):
// the C text is rebuilt from the decompiler's token tree, with every call written as sub_XXXXXXXX, every global
// as G_XXXXXXXX and every string literal as a pointer to the original string, so nothing depends on names.
// Also writes the C definitions of all structures/unions/enums/typedefs the functions use (types.h).
// Args: out.jsonl types.h [maxFunctionSize]
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.app.decompiler.parallel.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.data.*;
import ghidra.program.model.pcode.*;
import ghidra.program.model.symbol.*;
import ghidra.util.task.TaskMonitor;
import java.io.*;
import java.util.*;

public class AutoExport extends GhidraScript {
    static String js(String s) {
        StringBuilder b = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            switch (c) {
                case '"': b.append("\\\""); break;
                case '\\': b.append("\\\\"); break;
                case '\n': b.append("\\n"); break;
                case '\r': break;
                case '\t': b.append("\\t"); break;
                default: if (c < 32 || c > 126) b.append(String.format("\\u%04x", (int)c)); else b.append(c);
            }
        }
        return b.append('"').toString();
    }
    static String san(String n) {
        StringBuilder b = new StringBuilder();
        for (char c : n.toCharArray()) b.append(Character.isLetterOrDigit(c) || c == '_' ? c : '_');
        String s = b.toString();
        if (s.isEmpty() || Character.isDigit(s.charAt(0))) s = "t_" + s;
        return s;
    }
    static String tname(DataType d) { return san(d.getPathName()); }
    // C type text of a data type: name of the type with pointers, arrays folded into pointers here
    String ctype(DataType dt, Set<DataType> used) {
        if (dt == null) return "undefined4";
        if (dt instanceof Pointer) {
            DataType t = ((Pointer) dt).getDataType();
            if (t == null || t instanceof FunctionDefinition) return "void *";
            return ctype(t, used) + " *";
        }
        if (dt instanceof TypeDef && ((TypeDef) dt).isAutoNamed()) return ctype(((TypeDef) dt).getDataType(), used);
        if (dt instanceof Array) return ctype(((Array) dt).getDataType(), used) + " *";
        if (dt instanceof FunctionDefinition) return "void";
        if (dt instanceof Structure || dt instanceof Union || dt instanceof ghidra.program.model.data.Enum || dt instanceof TypeDef) {
            used.add(dt);
            return tname(dt);
        }
        if (dt instanceof VoidDataType) return "void";
        if (dt instanceof Undefined || dt instanceof DefaultDataType) {
            int l = dt.getLength();
            return l == 1 ? "undefined1" : l == 2 ? "undefined2" : l == 8 ? "undefined8" : "undefined4";
        }
        String n = dt.getName();
        switch (n) {
            case "float10": return "float10";
            case "bool": return "bool";
            case "char": case "uchar": case "byte": case "short": case "ushort": case "int": case "uint": case "long":
            case "ulong": case "longlong": case "ulonglong": case "float": case "double": case "word": case "dword":
            case "undefined1": case "undefined2": case "undefined4": case "undefined8": case "wchar_t": case "wchar16":
            case "sbyte": case "qword": case "string": case "TerminatedCString":
                return n.equals("string") || n.equals("TerminatedCString") ? "char" : n;
        }
        int l = dt.getLength();
        return l == 1 ? "undefined1" : l == 2 ? "undefined2" : l == 8 ? "undefined8" : l == 4 ? "undefined4" : "undefined4";
    }

    // A value that moves between a float type and an integer type without a conversion op (COPY, CAST, a load or
    // store through a pointer of the other kind, a call argument, the result): the decompiler means the same bits,
    // C converts the number.  Such functions cannot be compiled faithfully as printed.
    static DataType base(DataType d) {
        while (d instanceof TypeDef) d = ((TypeDef) d).getBaseDataType();
        return d;
    }
    static boolean isFloat(DataType d) { return base(d) instanceof AbstractFloatDataType; }
    static DataType htype(Varnode v) {
        if (v == null) return null;
        HighVariable h = v.getHigh();
        return h == null ? null : h.getDataType();
    }
    static DataType pointee(DataType d) {
        d = base(d);
        return d instanceof Pointer ? ((Pointer) d).getDataType() : null;
    }
    static boolean mix(DataType a, DataType b) {
        if (a == null || b == null) return false;
        if (base(a) instanceof Undefined || base(b) instanceof Undefined) {
            // undefinedN prints as an unsigned integer type
        }
        return isFloat(a) != isFloat(b) && base(a).getLength() == base(b).getLength() && !(base(a) instanceof Pointer && false);
    }
    String floatMix(HighFunction hf, Function f, Set<SequenceNumber> bits) {
        Iterator<PcodeOpAST> it = hf.getPcodeOps();
        while (it.hasNext()) {
            PcodeOpAST op = it.next();
            int c = op.getOpcode();
            Varnode out = op.getOutput();
            if (c == PcodeOp.CAST && bits.contains(op.getSeqnum())) continue;     // printed as BITCAST
            // part of a value (or two put together) of the other kind: 0x525070 stored the low half of the int64 of
            // a fistp in a float variable and passed it on as '(float)x', a conversion in C (a particle count read as
            // a float's bits: bad_alloc)
            if (c == PcodeOp.SUBPIECE || c == PcodeOp.PIECE) {
                DataType ot = htype(out);
                for (int k = 0; k < (c == PcodeOp.PIECE ? 2 : 1); k++) {
                    DataType pt = htype(op.getInput(k));
                    if (ot != null && pt != null && isFloat(ot) != isFloat(pt)) return "piece at " + op.getSeqnum().getTarget();
                }
            }
            if (c == PcodeOp.COPY || c == PcodeOp.CAST || c == PcodeOp.MULTIEQUAL || c == PcodeOp.INDIRECT) {
                if (mix(htype(out), htype(op.getInput(0)))) return "copy at " + op.getSeqnum().getTarget();
            } else if (c == PcodeOp.STORE) {
                if (mix(pointee(htype(op.getInput(1))), htype(op.getInput(2)))) return "store at " + op.getSeqnum().getTarget();
            } else if (c == PcodeOp.LOAD) {
                if (mix(pointee(htype(op.getInput(1))), htype(out))) return "load at " + op.getSeqnum().getTarget();
            } else if (c == PcodeOp.CALL) {
                Function t = getFunctionAt(op.getInput(0).getAddress());
                if (t == null) continue;
                Parameter[] ps = t.getParameters();
                for (int k = 1; k < op.getNumInputs() && k - 1 < ps.length; k++)
                    if (mix(ps[k - 1].getDataType(), htype(op.getInput(k)))) return "argument at " + op.getSeqnum().getTarget();
            } else if (c == PcodeOp.CALLIND) {
                // the call-site prototypes of ICallOverride.java take undefined4: a float argument would be converted
                for (int k = 1; k < op.getNumInputs(); k++)
                    if (isFloat(htype(op.getInput(k)))) return "indirect argument at " + op.getSeqnum().getTarget();
            } else if (c == PcodeOp.RETURN && op.getNumInputs() > 1) {
                if (mix(f.getReturnType(), htype(op.getInput(1)))) return "result at " + op.getSeqnum().getTarget();
            }
        }
        return null;
    }

    // the x87 rounding mode at a fistp is truncation: 'fldcw' of a word with 0xC00 or-ed in, within the few
    // instructions before it (MSVC's inline float to integer conversion)
    boolean truncatingCW(Address at) {
        Instruction i = getInstructionAt(at);
        boolean cw = false;
        for (int k = 0; i != null && k < 24; k++, i = i.getPrevious()) {
            String m = i.getMnemonicString();
            if (m.equals("CALL") || m.equals("RET") || m.startsWith("J")) return false;
            if (m.equals("FLDCW")) {
                if (cw) return false;            // the one before restored a mode: not this conversion's
                cw = true;
            }
            if (cw && m.equals("OR") && i.toString().toLowerCase().contains("0xc00")) return true;
        }
        return false;
    }

    // ---- casts that keep the bits: '(float)x' of a CAST between a float and an integer type of one size means
    // the same bits to the decompiler and a conversion to C; written BITCAST(float, x) (ghidra_prelude.h).
    // The cast's own tokens carry no p-code op: the operand is the unary expression after '(type)', and its op is
    // found from the ops of its tokens.
    static boolean blank(ClangToken t) { return t instanceof ClangBreak || t.getText().trim().isEmpty(); }
    static int next(List<ClangNode> toks, int i) {
        while (i < toks.size() && blank((ClangToken) toks.get(i))) i++;
        return i;
    }
    static String txt(List<ClangNode> toks, int i) { return i < toks.size() ? ((ClangToken) toks.get(i)).getText() : ""; }
    // index of the ')' closing a cast '(' TYPE '*'... ')' that starts at i, or -1
    static int castEnd(List<ClangNode> toks, int i) {
        if (!txt(toks, i).equals("(") || !(toks.get(i) instanceof ClangSyntaxToken)) return -1;
        int k = next(toks, i + 1);
        if (k >= toks.size() || !(toks.get(k) instanceof ClangTypeToken)) return -1;
        k = next(toks, k + 1);
        while (txt(toks, k).equals("*")) k = next(toks, k + 1);
        return txt(toks, k).equals(")") ? k : -1;
    }
    static int matching(List<ClangNode> toks, int i, String open, String close) {
        int d = 0;
        for (int k = i; k < toks.size(); k++) {
            String x = txt(toks, k);
            if (x.equals(open)) d++;
            else if (x.equals(close) && --d == 0) return k;
        }
        return -1;
    }
    // last token index of the unary expression starting at i (C grammar: prefix operators and casts, then a
    // primary expression with its postfix operators), or -1
    static int unaryEnd(List<ClangNode> toks, int i) {
        i = next(toks, i);
        if (i >= toks.size()) return -1;
        String x = txt(toks, i);
        int c = castEnd(toks, i);
        if (c >= 0) return unaryEnd(toks, c + 1);
        if (toks.get(i) instanceof ClangOpToken && (x.equals("*") || x.equals("-") || x.equals("!") || x.equals("~") || x.equals("&")))
            return unaryEnd(toks, i + 1);
        int e;
        if (x.equals("(")) e = matching(toks, i, "(", ")");
        else if (x.equals(")") || x.equals(",") || x.equals(";")) return -1;
        else e = i;
        while (e >= 0) {
            int k = next(toks, e + 1);
            String y = txt(toks, k);
            if (y.equals("[")) e = matching(toks, k, "[", "]");
            else if (y.equals("(") && castEnd(toks, k) < 0) e = matching(toks, k, "(", ")");
            else if (y.equals(".") || y.equals("->")) e = next(toks, k + 1);
            else break;
        }
        return e;
    }
    // CAST ops printed as '(T)operand' that change between float and integer bits: open-paren index -> its op
    Map<Integer, PcodeOp> bitCasts(List<ClangNode> toks) {
        Map<Integer, PcodeOp> res = new HashMap<>();
        for (int i = 0; i < toks.size(); i++) {
            int c = castEnd(toks, i);
            if (c < 0) continue;
            int e = unaryEnd(toks, c + 1);
            if (e < 0) continue;
            Set<PcodeOp> span = new HashSet<>();
            for (int k = c + 1; k <= e; k++) {
                PcodeOp op = ((ClangToken) toks.get(k)).getPcodeOp();
                if (op != null) span.add(op);
            }
            DataType printed = ((ClangTypeToken) toks.get(next(toks, i + 1))).getDataType();
            PcodeOp found = null;
            int n = 0;
            // the CAST: an op of the operand's tokens (a lone variable carries the op reading it), or the op that
            // reads the result of one of them
            Set<PcodeOp> cand = new LinkedHashSet<>(span);
            for (PcodeOp op : span) {
                Varnode o = op.getOutput();
                if (o == null) continue;
                for (Iterator<PcodeOp> d = o.getDescendants(); d.hasNext(); ) cand.add(d.next());
            }
            for (PcodeOp op : cand) {
                if (op.getOpcode() != PcodeOp.CAST) continue;
                Varnode in = op.getInput(0), out = op.getOutput();
                boolean inside = span.contains(op) || (in.getDef() != null && span.contains(in.getDef()));
                if (!inside || out == null) continue;
                // the root of the operand: nothing else in it reads the cast's result (an outer '(int *)' of
                // '(int)f + 0x10' is not the CAST of f)
                boolean root = true;
                for (PcodeOp o2 : span)
                    if (o2 != op) for (Varnode v : o2.getInputs()) if (v == out) root = false;
                if (!root) continue;
                if (!mix(htype(out), htype(in))) continue;
                if (printed == null || base(printed).getLength() != base(htype(out)).getLength() ||
                    isFloat(printed) != isFloat(htype(out))) continue;
                found = op;
                n++;
            }
            if (n == 1) res.put(i, found);
        }
        return res;
    }

    String render(DecompileResults r, Function f, Map<Long, String> globals, Map<Long, String> callees,
                  Set<DataType> used, Map<Long, String> strings, Map<String, String> sized, Set<SequenceNumber> bits) {
        ClangTokenGroup g = r.getCCodeMarkup();
        List<ClangNode> toks = new ArrayList<>();
        g.flatten(toks);
        StringBuilder sb = new StringBuilder();
        Map<Integer, PcodeOp> bc = bitCasts(toks);
        Map<Integer, String> before = new HashMap<>(), after = new HashMap<>();
        for (Map.Entry<Integer, PcodeOp> e : bc.entrySet()) {
            int i = e.getKey(), c = castEnd(toks, i), end = unaryEnd(toks, c + 1);
            before.put(i, "BITCAST(");
            before.put(c, ", (");
            after.put(end, after.getOrDefault(end, "") + "))");
            bits.add(e.getValue().getSeqnum());
        }
        for (int ti = 0; ti < toks.size(); ti++) {
            if (after.containsKey(ti - 1)) sb.append(after.get(ti - 1));   // the end of a BITCAST operand
            ClangToken t = (ClangToken) toks.get(ti);
            String text = t.getText();
            if (before.containsKey(ti)) {
                sb.append(before.get(ti));
                continue;
            }
            if (t instanceof ClangBreak) {
                sb.append('\n');
                for (int i = 0; i < ((ClangBreak) t).getIndent(); i++) sb.append(' ');
                continue;
            }
            // '(*E)(args)' of an indirect call: the '*' is the CALLIND's own token; tools/autodecomp.py gives the call
            // the prototype ICallOverride.java wrote for this address
            if (t instanceof ClangOpToken && text.equals("*") && t.getPcodeOp() != null &&
                    t.getPcodeOp().getOpcode() == PcodeOp.CALLIND) {
                sb.append(String.format("ICALL_%08X*", t.getPcodeOp().getSeqnum().getTarget().getOffset()));
                continue;
            }
            // '*p' of a void pointer ('Load size is inaccurate'): the load's own size and the type its value is used
            // as are known, written as '*(T *)p' (tools/autodecomp.py rejects a bare void dereference)
            if (t instanceof ClangOpToken && text.equals("*") && t.getPcodeOp() != null &&
                    (t.getPcodeOp().getOpcode() == PcodeOp.LOAD || t.getPcodeOp().getOpcode() == PcodeOp.STORE)) {
                PcodeOp op = t.getPcodeOp();
                DataType pt = base(htype(op.getInput(1)));
                DataType pointee = pt instanceof Pointer ? base(((Pointer) pt).getDataType()) : null;
                if (pt instanceof Pointer && (pointee == null || pointee instanceof VoidDataType)) {
                    // the value loaded, or the one stored
                    Varnode o = op.getOpcode() == PcodeOp.LOAD ? op.getOutput() : op.getInput(2);
                    DataType ot = htype(o);
                    String c = ot != null && ot.getLength() == o.getSize() && !(base(ot) instanceof VoidDataType)
                        ? ctype(ot, used) : ctype(Undefined.getUndefinedDataType(o.getSize()), used);
                    sb.append("*(").append(c).append(" *)");
                    continue;
                }
            }
            // fistp after MSVC's '(int)x' sequence (fnstcw; or 0xC00; fldcw): the decompiler's ROUND is in the
            // rounding mode set just before, truncation
            if (text.equals("ROUND") && t.getPcodeOp() != null && truncatingCW(t.getPcodeOp().getSeqnum().getTarget())) {
                sb.append("TRUNC");
                continue;
            }
            if (t instanceof ClangFuncNameToken) {
                PcodeOp op = t.getPcodeOp();
                if (op != null && (op.getOpcode() == PcodeOp.CALL) && op.getInput(0) != null) {
                    long a = op.getInput(0).getAddress().getOffset();
                    callees.put(a, "");
                    sb.append(String.format("sub_%08X", a));
                    continue;
                }
                if (text.equals(f.getName()) || text.endsWith("::" + f.getName()) || op == null) {
                    // the definition (or a call through a pointer) - definitions are renamed by the converter
                    Function c = getFunction(text);
                    sb.append(text.equals(f.getName()) ? String.format("f_%08X", f.getEntryPoint().getOffset()) : "UNRESOLVED_" + san(text));
                    continue;
                }
                sb.append("UNRESOLVED_").append(san(text));
                continue;
            }
            if (t instanceof ClangVariableToken) {
                HighVariable hv = t.getHighVariable();
                Varnode vn = t.getVarnode();
                if (hv instanceof HighGlobal || (hv != null && hv.getSymbol() != null && hv.getSymbol().isGlobal())) {
                    HighSymbol hs = hv.getSymbol();
                    if (hs != null && hs.getStorage() != null && hs.getStorage().getMinAddress() != null &&
                        hs.getStorage().getMinAddress().isMemoryAddress()) {
                        long a = hs.getStorage().getMinAddress().getOffset();
                        DataType dt = hs.getDataType();
                        int vs = vn != null ? vn.getSize() : 0;
                        if (vs > 0 && !(dt instanceof Array) && vs != dt.getLength() && (vs == 1 || vs == 2 || vs == 4 || vs == 8)) {
                            // the symbol's type (often undefined1 where nothing was defined) is not the size of this
                            // access: an access of its own size
                            String key = String.format("%08X_%d", a, vs);
                            String t2 = vs == 1 ? "unsigned char" : vs == 2 ? "unsigned short" : vs == 4 ? "unsigned int" : "unsigned long long";
                            DataType vt = hv != null ? hv.getDataType() : null;
                            if (vt != null && vt.getLength() == vs && isFloat(vt))
                                t2 = vs == 4 ? "float" : "double";      // a float stored there (the access says so)
                            sized.put(key, t2);
                            sb.append("GV_").append(key);
                            continue;
                        }
                        if (dt instanceof Array)
                            globals.put(a, "ARRAY|" + ctype(((Array) dt).getDataType(), used) + "|" + dt.getLength());
                        else
                            globals.put(a, ctype(dt, used) + "|" + dt.getLength());
                        sb.append(String.format("G_%08X", a));
                        continue;
                    }
                }
                if ((text.startsWith("\"") || text.startsWith("L\"") || text.startsWith("u\"")) && vn != null && vn.isConstant()) {
                    long a = vn.getOffset();
                    strings.put(a, "");
                    sb.append(String.format("((%s)S_%08X)", text.startsWith("\"") ? "char *" : "wchar16 *", a));
                    continue;
                }
                if (text.startsWith("\"") || text.startsWith("L\"") || text.startsWith("u\"")) {
                    sb.append("UNRESOLVED_STRING");
                    continue;
                }
                // a symbol name whose address is an input of the token's p-code op (vftable of a constructor): the
                // name alone is ambiguous (a class has a vftable for each base), the address is not
                if (vn == null && t.getPcodeOp() != null && text.matches("&?[A-Za-z_][\\w:<>,`' ]*") &&
                        !text.matches("(true|false|NULL)")) {
                    String bare = text.replace("&", "");
                    bare = bare.contains("::") ? bare.substring(bare.lastIndexOf("::") + 2) : bare;
                    Long found = null;
                    for (Varnode in : t.getPcodeOp().getInputs()) {
                        if (in == null || !(in.isConstant() || in.isAddress())) continue;
                        Address ad = toAddr(in.getOffset());
                        for (Symbol sy : currentProgram.getSymbolTable().getSymbols(ad))
                            if (sy.getName().equals(bare)) found = in.getOffset();
                    }
                    if (found != null) {
                        globals.put(found, "code|0");
                        sb.append(String.format("((void *)G_%08X)", found));
                        continue;
                    }
                }
                // addresses printed with a symbol name (vftable, LAB_, FUN_, PTR_...)
                if (vn != null && vn.isConstant() && text.matches("&?[A-Za-z_][\\w:<>,`' ]*") && !text.matches("(true|false|NULL)")) {
                    long a = vn.getOffset();
                    globals.put(a, "code|0");
                    sb.append(String.format("((void *)G_%08X)", a));
                    continue;
                }
            }
            if (t instanceof ClangTypeToken) {
                DataType dt = ((ClangTypeToken) t).getDataType();
                if (dt != null) {
                    String c = ctype(dt, used);
                    // the token is the base type name; pointer stars are separate tokens
                    if (dt instanceof Pointer) c = ctype(((Pointer) dt).getDataType(), used);
                    sb.append(c.replace(" *", ""));
                    continue;
                }
            }
            if (t instanceof ClangFieldToken) {
                sb.append(san(text));
                continue;
            }
            sb.append(text);
        }
        if (after.containsKey(toks.size() - 1)) sb.append(after.get(toks.size() - 1));
        return sb.toString();
    }

    @Override
    public void run() throws Exception {
        String out = getScriptArgs()[0], typesOut = getScriptArgs()[1];
        int maxSize = getScriptArgs().length > 2 ? Integer.parseInt(getScriptArgs()[2]) : 4096;
        List<Function> funcs = new ArrayList<>();
        for (Function f : currentProgram.getFunctionManager().getFunctions(true))
            if (!f.isExternal() && !f.isThunk() && f.getBody().getNumAddresses() <= maxSize &&
                !f.getName().startsWith("Unwind@") && !f.getName().startsWith("Catch")) funcs.add(f);
        Set<DataType> usedAll = Collections.synchronizedSet(new HashSet<>());
        DecompilerCallback<String> cb = new DecompilerCallback<>(currentProgram, new DecompileConfigurer() {
            public void configure(DecompInterface d) {
                d.toggleCCode(true); d.toggleSyntaxTree(true); d.setSimplificationStyle("decompile");
            }
        }) {
            public String process(DecompileResults r, TaskMonitor m) {
                Function f = r.getFunction();
                if (r.getDecompiledFunction() == null) return null;
                Map<Long, String> globals = new TreeMap<>(), callees = new TreeMap<>(), strings = new TreeMap<>();
                Map<String, String> sized = new TreeMap<>();
                Set<DataType> used = new HashSet<>();
                String code;
                Set<SequenceNumber> bits = new HashSet<>();
                try { code = render(r, f, globals, callees, used, strings, sized, bits); }
                catch (Exception e) { return null; }
                usedAll.addAll(used);
                StringBuilder sb = new StringBuilder();
                sb.append("{\"a\":\"").append(String.format("%08X", f.getEntryPoint().getOffset())).append("\"");
                sb.append(",\"size\":").append(f.getBody().getNumAddresses());
                sb.append(",\"cc\":").append(js(f.getCallingConventionName()));
                sb.append(",\"custom\":").append(f.hasCustomVariableStorage());
                String fm = null;
                try { fm = floatMix(r.getHighFunction(), f, bits); } catch (Exception e) { fm = "check failed"; }
                if (fm != null) sb.append(",\"floatmix\":").append(js(fm));
                sb.append(",\"code\":").append(js(code));
                sb.append(",\"globals\":{");
                boolean first = true;
                for (Map.Entry<Long, String> e : globals.entrySet()) {
                    if (!first) sb.append(','); first = false;
                    sb.append(String.format("\"%08X\":", e.getKey())).append(js(e.getValue()));
                }
                sb.append("},\"sized\":{");
                first = true;
                for (Map.Entry<String, String> e : sized.entrySet()) {
                    if (!first) sb.append(','); first = false;
                    sb.append(js(e.getKey())).append(':').append(js(e.getValue()));
                }
                sb.append("},\"callees\":[");
                first = true;
                for (Long a : callees.keySet()) { if (!first) sb.append(','); first = false; sb.append(String.format("\"%08X\"", a)); }
                sb.append("],\"strings\":[");
                first = true;
                for (Long a : strings.keySet()) { if (!first) sb.append(','); first = false; sb.append(String.format("\"%08X\"", a)); }
                sb.append("]}");
                return sb.toString();
            }
        };
        cb.setTimeout(60);
        List<String> res = ParallelDecompiler.decompileFunctions(cb, funcs, monitor);
        cb.dispose();
        try (PrintWriter w = new PrintWriter(new OutputStreamWriter(new FileOutputStream(out), "UTF-8"))) {
            for (String s : res) if (s != null) w.println(s);
        }
        // prototypes of every function (for the callees)
        try (PrintWriter w = new PrintWriter(new OutputStreamWriter(new FileOutputStream(out + ".protos"), "UTF-8"))) {
            Set<DataType> used = new HashSet<>();
            for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
                if (f.isExternal()) continue;
                StringBuilder sb = new StringBuilder();
                sb.append(String.format("%08X\t", f.getEntryPoint().getOffset()));
                sb.append(f.getCallingConventionName()).append('\t').append(f.hasCustomVariableStorage()).append('\t');
                sb.append(ctype(f.getReturnType(), used)).append('\t');
                Parameter[] ps = f.getParameters();
                for (int i = 0; i < ps.length; i++) {
                    if (i > 0) sb.append(',');
                    sb.append(ctype(ps[i].getDataType(), used)).append(' ').append(ps[i].isAutoParameter() ? "this" : san(ps[i].getName()));
                }
                sb.append('\t').append(f.hasVarArgs()).append("\tfunc\t");
                for (int i = 0; i < ps.length; i++) {
                    if (i > 0) sb.append(',');
                    sb.append(ps[i].isRegisterVariable() ? ps[i].getRegister().getName() : "stack");
                }
                w.println(sb);
            }
            for (Function ef : currentProgram.getFunctionManager().getExternalFunctions()) {
                for (ghidra.program.model.symbol.Reference r : getReferencesTo(ef.getEntryPoint())) {
                    if (!r.getFromAddress().isMemoryAddress() || getInstructionAt(r.getFromAddress()) != null) continue;
                    StringBuilder sb = new StringBuilder();
                    sb.append(String.format("%08X\t", r.getFromAddress().getOffset()));
                    sb.append(ef.getCallingConventionName()).append("\tfalse\t").append(ctype(ef.getReturnType(), used)).append('\t');
                    Parameter[] ps = ef.getParameters();
                    for (int i = 0; i < ps.length; i++) {
                        if (i > 0) sb.append(',');
                        sb.append(ctype(ps[i].getDataType(), used)).append(' ').append(ps[i].isAutoParameter() ? "this" : san(ps[i].getName()));
                    }
                    sb.append('\t').append(ef.hasVarArgs()).append("\timport");
                    w.println(sb);
                }
            }
            usedAll.addAll(used);
        }
        try (PrintWriter w = new PrintWriter(new OutputStreamWriter(new FileOutputStream(typesOut + ".list"), "UTF-8"))) {
            for (DataType d : usedAll) w.println(d.getPathName());
        }
        new TypesC(this).write(typesOut, usedAll);
        println("exported " + res.size() + " functions, " + usedAll.size() + " types used");
    }

}
