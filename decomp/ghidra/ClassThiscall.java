// Methods of classes that Ghidra typed __fastcall/__stdcall although they only take ECX as a register (MSVC
// member functions): make them __thiscall so 'this' gets the class type.  Arg: regparams.tsv
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.util.*;

public class ClassThiscall extends GhidraScript {
    @Override
    public void run() throws Exception {
        Map<Long, String> regs = new HashMap<>();
        try (BufferedReader r = new BufferedReader(new FileReader(getScriptArgs()[0]))) {
            String l;
            while ((l = r.readLine()) != null) { String[] p = l.split("\t", -1); regs.put(Long.parseLong(p[0], 16), p[1]); }
        }
        int n = 0;
        for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
            if (!(f.getParentNamespace() instanceof GhidraClass)) continue;
            String cc = f.getCallingConventionName();
            if (cc.equals("__thiscall")) continue;
            if (f.hasCustomVariableStorage()) continue;
            String rr = regs.getOrDefault(f.getEntryPoint().getOffset(), "");
            Set<String> s = new HashSet<>(Arrays.asList(rr.split(",")));
            s.remove(""); s.remove("EBP");
            if (!s.equals(Set.of("ECX"))) continue;
            try {
                if (cc.equals("__fastcall") && f.getParameterCount() >= 1 && f.getParameter(0).isRegisterVariable())
                    f.removeParameter(0);
                f.setCallingConvention("__thiscall");
                n++;
            } catch (Exception e) { println("failed " + f.getEntryPoint() + ": " + e.getMessage()); }
        }
        println("switched to __thiscall: " + n);
    }
}
