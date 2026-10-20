// Imports named the __stdcall way, '_name@N' (Miles Sound System's mss32.dll, Bink's binkw32.dll: no type library
// describes them), get a prototype from the name: __stdcall with N/4 dword parameters and a dword result.
// Without one the decompiler takes the call for one that leaves its arguments on the stack, and everything the
// caller addresses through ESP after it is off by N (0x4C1760 stored its saved ESI where it meant a local after
// _AIL_set_sample_volume_pan@12).  Imports that already have parameters are left alone.
// Args: none.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.data.*;
import ghidra.program.model.symbol.SourceType;
import java.util.*;
import java.util.regex.*;

public class DecoratedImports extends GhidraScript {
    @Override
    public void run() throws Exception {
        Pattern p = Pattern.compile("_?[A-Za-z_]\\w*@(\\d+)");
        int set = 0, kept = 0, fail = 0;
        List<Function> todo = new ArrayList<>();
        for (Function f : currentProgram.getFunctionManager().getExternalFunctions()) todo.add(f);
        for (Function f : currentProgram.getFunctionManager().getFunctions(true))
            if (f.isThunk() && f.getThunkedFunction(true) != null && f.getThunkedFunction(true).isExternal()) todo.add(f);
        for (Function f : todo) {
            Function target = f.isThunk() ? f.getThunkedFunction(true) : f;
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
        println("decorated imports given __stdcall prototypes: " + set + ", already typed " + kept + ", failed " + fail);
    }
}
