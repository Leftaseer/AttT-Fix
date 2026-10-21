// Imports named the __stdcall way, '_name@N' (Miles Sound System's mss32.dll, Bink's binkw32.dll: no type library
// describes them), get a prototype from the name: __stdcall with N/4 dword parameters and a dword result.
// Without one the decompiler takes the call for one that leaves its arguments on the stack, and everything the
// caller addresses through ESP after it is off by N (0x4C1760 stored its saved ESI where it meant a local after
// _AIL_set_sample_volume_pan@12).  Imports that already have parameters are left alone.
// Undecorated __stdcall imports no type library covers (D3DX9), and MSVCP80 functions whose prototypes miss a hidden
// parameter (the result's address of those returning a class, the most-derived flag of constructors of classes
// with a virtual base), take their prototypes from a table instead (by name or decorated name), which replaces
// whatever the import had.
// Args: [symbols/import_protos.tsv: name, result, parameter types].
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.data.*;
import ghidra.program.model.symbol.SourceType;
import java.util.*;
import java.util.regex.*;
import java.nio.file.*;

public class DecoratedImports extends GhidraScript {
    @Override
    public void run() throws Exception {
        Pattern p = Pattern.compile("_?[A-Za-z_]\\w*@(\\d+)");
        Map<String, String[]> table = new HashMap<>();
        String[] args = getScriptArgs();
        if (args.length > 0)
            for (String l : Files.readAllLines(Paths.get(args[0]))) {
                String[] q = l.split("\t");
                if (!l.startsWith("#") && q.length > 2) table.put(q[0], q);
            }
        int set = 0, kept = 0, fail = 0, tabled = 0;
        List<Function> todo = new ArrayList<>();
        for (Function f : currentProgram.getFunctionManager().getExternalFunctions()) todo.add(f);
        for (Function f : currentProgram.getFunctionManager().getFunctions(true))
            if (f.isThunk() && f.getThunkedFunction(true) != null && f.getThunkedFunction(true).isExternal()) todo.add(f);
        for (Function f : todo) {
            Function target = f.isThunk() ? f.getThunkedFunction(true) : f;
            String[] row = table.get(target.getName());
            if (row == null && target.getExternalLocation() != null && target.getExternalLocation().getOriginalImportedName() != null)
                row = table.get(target.getExternalLocation().getOriginalImportedName());
            if (row != null) {
                List<Variable> ps = new ArrayList<>();
                int k = 0;
                for (String t : row[2].split(","))
                    ps.add(new ParameterImpl("param_" + (++k), type(t.trim()), currentProgram));
                try {
                    String cc = row.length > 3 ? row[3].trim() : "__stdcall";
                    f.updateFunction(cc, new ReturnParameterImpl(type(row[1].trim()), currentProgram), ps,
                        Function.FunctionUpdateType.DYNAMIC_STORAGE_FORMAL_PARAMS, true, SourceType.USER_DEFINED);
                    tabled++;
                } catch (Exception e) {
                    println("failed " + target.getName() + ": " + e.getMessage());
                    fail++;
                }
                continue;
            }
            Matcher m = p.matcher(target.getName());
            if (!m.matches()) continue;
            int n = Integer.parseInt(m.group(1));
            if (n % 4 != 0 || n > 64) continue;
            if (f.getParameterCount() > 0) { kept++; continue; }
            List<Variable> ps = new ArrayList<>();
            for (int k = 0; k < n / 4; k++)
                ps.add(new ParameterImpl("param_" + (k + 1), Undefined4DataType.dataType, currentProgram));
            try {
                f.updateFunction("__stdcall", new ReturnParameterImpl(Undefined4DataType.dataType, currentProgram), ps,
                    Function.FunctionUpdateType.DYNAMIC_STORAGE_FORMAL_PARAMS, true, SourceType.USER_DEFINED);
                set++;
            } catch (Exception e) {
                println("failed " + target.getName() + ": " + e.getMessage());
                fail++;
            }
        }
        println("decorated imports given __stdcall prototypes: " + set + ", from the table " + tabled + ", already typed " +
                kept + ", failed " + fail);
    }

    DataType type(String t) {
        switch (t) {
            case "void *": return new PointerDataType(VoidDataType.dataType);
            case "char *": return new PointerDataType(CharDataType.dataType);
            case "float": return FloatDataType.dataType;
            case "uint": return UnsignedIntegerDataType.dataType;
            case "int": return IntegerDataType.dataType;
        }
        throw new IllegalArgumentException("type " + t);
    }
}
