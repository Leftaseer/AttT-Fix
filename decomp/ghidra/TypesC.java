// C definitions of Ghidra data types with exactly the original layout (#pragma pack(1), explicit padding,
// fields of unusual sizes as byte arrays), in dependency order.  Used by AutoExport.java and ExportTypesC.java.
import ghidra.program.model.data.*;
import java.io.*;
import java.util.*;

public class TypesC {
    final Object owner;
    public TypesC(Object owner) { this.owner = owner; }
    static String san(String n) {
        StringBuilder b = new StringBuilder();
        for (char c : n.toCharArray()) b.append(Character.isLetterOrDigit(c) || c == '_' ? c : '_');
        String s = b.toString();
        if (s.isEmpty() || Character.isDigit(s.charAt(0))) s = "t_" + s;
        return s;
    }
    static String tname(DataType d) { return san(d.getPathName()); }
    static boolean named(DataType d) {
        return d instanceof Structure || d instanceof Union || d instanceof ghidra.program.model.data.Enum ||
               (d instanceof TypeDef && !((TypeDef) d).isAutoNamed());
    }
    static String scalar(DataType dt) {
        if (dt instanceof VoidDataType) return "void";
        String n = dt.getName();
        switch (n) {
            case "float": case "double": case "char": case "uchar": case "byte": case "short": case "ushort":
            case "int": case "uint": case "long": case "ulong": case "longlong": case "ulonglong": case "word":
            case "dword": case "bool": case "wchar_t": case "wchar16": case "sbyte": case "qword":
                if (dt.getLength() > 0 && dt.getLength() != sizeOf(n)) break;
                return n;
        }
        int l = dt.getLength();
        return l == 1 ? "undefined1" : l == 2 ? "undefined2" : l == 4 ? "undefined4" : l == 8 ? "undefined8" : null;
    }
    static int sizeOf(String n) {
        switch (n) {
            case "char": case "uchar": case "byte": case "bool": case "sbyte": return 1;
            case "short": case "ushort": case "word": case "wchar_t": case "wchar16": return 2;
            case "double": case "longlong": case "ulonglong": case "qword": return 8;
            default: return 4;
        }
    }
    // a declarator for a field/typedef: handles pointers, arrays, odd sizes
    static String decl(DataType t, String name) {
        if (t == null) return "undefined4 " + name;
        if (t instanceof TypeDef && ((TypeDef) t).isAutoNamed()) return decl(((TypeDef) t).getDataType(), name);
        if (t instanceof Array) {
            Array a = (Array) t;
            return decl(a.getDataType(), name + "[" + Math.max(1, a.getNumElements()) + "]");
        }
        if (t instanceof Pointer) {
            DataType p = ((Pointer) t).getDataType();
            if (p == null || p instanceof FunctionDefinition || (p instanceof TypeDef && ((TypeDef) p).getBaseDataType() instanceof FunctionDefinition))
                return "void *" + name;
            String inner = name.startsWith("[") ? "(*" + name + ")" : "*" + name;
            if (name.contains("[")) inner = "*" + name;
            return decl(p, inner);
        }
        if (named(t)) return tname(t) + " " + name;
        if (t instanceof FunctionDefinition) return "undefined4 " + name;
        String s = scalar(t);
        if (s != null) return s + " " + name;
        return "unsigned char " + name + "[" + Math.max(1, t.getLength()) + "]";
    }
    // the named type a declarator needs fully defined (null: none, or only a pointer to it)
    static DataType needs(DataType t) {
        while (true) {
            if (t instanceof TypeDef && ((TypeDef) t).isAutoNamed()) { t = ((TypeDef) t).getDataType(); continue; }
            if (t instanceof Array) { t = ((Array) t).getDataType(); continue; }
            return named(t) ? t : null;
        }
    }
    static DataType pointee(DataType t) {
        while (true) {
            if (t instanceof TypeDef && ((TypeDef) t).isAutoNamed()) { t = ((TypeDef) t).getDataType(); continue; }
            if (t instanceof Array) { t = ((Array) t).getDataType(); continue; }
            if (t instanceof Pointer) { t = ((Pointer) t).getDataType(); if (t == null) return null; continue; }
            return named(t) ? t : null;
        }
    }
    LinkedHashSet<DataType> order = new LinkedHashSet<>();
    Set<DataType> visiting = new HashSet<>();
    LinkedHashSet<DataType> fwd = new LinkedHashSet<>();
    void visit(DataType d) {
        if (d == null || order.contains(d) || visiting.contains(d) || !named(d)) return;
        visiting.add(d);
        List<DataType> parts = new ArrayList<>();
        if (d instanceof Composite) for (DataTypeComponent c : ((Composite) d).getComponents()) parts.add(c.getDataType());
        else if (d instanceof TypeDef) parts.add(((TypeDef) d).getDataType());
        for (DataType p : parts) {
            DataType full = needs(p);
            if (full != null) visit(full);
            else {
                DataType pt = pointee(p);
                if (pt instanceof Structure || pt instanceof Union) fwd.add(pt);
                else if (pt != null) visit(pt);        // typedef/enum behind a pointer must be defined first
                if (pt instanceof Structure || pt instanceof Union) pendingVisit.add(pt);
            }
        }
        visiting.remove(d);
        order.add(d);
    }
    List<DataType> pendingVisit = new ArrayList<>();
    public void write(String path, Collection<DataType> roots) throws Exception {
        for (DataType d : roots) visit(d);
        while (!pendingVisit.isEmpty()) {
            List<DataType> p = new ArrayList<>(pendingVisit); pendingVisit.clear();
            for (DataType d : p) visit(d);
        }
        try (PrintWriter w = new PrintWriter(new OutputStreamWriter(new FileOutputStream(path), "UTF-8"))) {
            w.println("/* generated from the Ghidra project: types of the auto-decompiled functions */");
            w.println("#pragma pack(push, 1)");
            for (DataType d : order) {
                if (d instanceof Structure) w.println("typedef struct " + tname(d) + " " + tname(d) + ";");
                else if (d instanceof Union) w.println("typedef union " + tname(d) + " " + tname(d) + ";");
            }
            for (DataType d : fwd) {
                if (order.contains(d)) continue;
                if (d instanceof Structure) w.println("typedef struct " + tname(d) + " " + tname(d) + ";");
                else if (d instanceof Union) w.println("typedef union " + tname(d) + " " + tname(d) + ";");
            }
            for (DataType d : order) w.println(def(d));
            w.println("#pragma pack(pop)");
        }
    }
    // undefined bytes of a structure: the decompiler names them field_0xNN (offset in this structure)
    static void gap(StringBuilder b, int from, int to) {
        int named = Math.min(to, from + 0x1000);
        for (int o = from; o < named; o++) b.append(String.format("    unsigned char field_0x%x;\n", o));
        if (to > named) b.append("    unsigned char pad_").append(named).append("[").append(to - named).append("];\n");
    }
    String def(DataType d) {
        String n = tname(d);
        if (d instanceof ghidra.program.model.data.Enum)
            return "typedef " + (d.getLength() == 1 ? "unsigned char" : d.getLength() == 2 ? "unsigned short" : "unsigned int") + " " + n + ";";
        if (d instanceof TypeDef) return "typedef " + decl(((TypeDef) d).getDataType(), n) + ";";
        StringBuilder b = new StringBuilder();
        b.append(d instanceof Union ? "union " : "struct ").append(n).append(" {\n");
        int off = 0, pad = 0;
        if (d instanceof Structure) {
            for (DataTypeComponent c : ((Structure) d).getDefinedComponents()) {
                if (c.isBitFieldComponent() || c.getLength() == 0) continue;
                if (c.getOffset() < off) continue;
                if (c.getOffset() > off) { gap(b, off, c.getOffset()); off = c.getOffset(); }
                String fn = c.getFieldName() != null ? san(c.getFieldName()) : c.getDefaultFieldName();
                DataType ct = c.getDataType();
                String dl = (ct == null || (ct.getLength() > 0 && ct.getLength() != c.getLength()))
                    ? "unsigned char " + fn + "[" + c.getLength() + "]" : decl(ct, fn);
                // a component whose C size is not its Ghidra size becomes bytes
                b.append("    ").append(dl).append(";\n");
                off = c.getOffset() + c.getLength();
            }
            if (d.getLength() > off) gap(b, off, d.getLength());
        } else {
            for (DataTypeComponent c : ((Composite) d).getComponents()) {
                String fn = c.getFieldName() != null ? san(c.getFieldName()) : "u" + c.getOrdinal();
                b.append("    ").append(decl(c.getDataType(), fn)).append(";\n");
            }
        }
        if (d.getLength() <= 0 || ((Composite) d).getNumDefinedComponents() == 0 && d instanceof Union) b.append("    unsigned char empty_;\n");
        b.append("};\n");
        b.append(String.format("_Static_assert(sizeof(%s) == %d, \"%s\");", n, Math.max(1, d.getLength()), n));
        return b.toString();
    }
}
