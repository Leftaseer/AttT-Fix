// Dump functions, symbols and vtables to TSV files in the directory given as script argument.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.address.*;
import java.io.*;

public class DumpInfo extends GhidraScript {
    @Override
    public void run() throws Exception {
        String dir = getScriptArgs()[0];
        new File(dir).mkdirs();
        try (PrintWriter w = new PrintWriter(new FileWriter(dir + "/functions.tsv"))) {
            FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
            while (it.hasNext()) {
                Function f = it.next();
                AddressSetView b = f.getBody();
                w.printf("%s\t%s\t%d\t%s\t%d\t%s\t%s%n", f.getEntryPoint(), f.getName(true), b.getNumAddresses(),
                    f.getCallingConventionName(), f.getParameterCount(), f.isThunk() ? "thunk" : "",
                    f.getSignature().getPrototypeString());
            }
        }
        try (PrintWriter w = new PrintWriter(new FileWriter(dir + "/symbols.tsv"))) {
            SymbolIterator it = currentProgram.getSymbolTable().getAllSymbols(true);
            while (it.hasNext()) {
                Symbol s = it.next();
                if (s.getSource() == SourceType.DEFAULT) continue;
                if (!s.getAddress().isMemoryAddress()) continue;
                w.printf("%s\t%s\t%s\t%s%n", s.getAddress(), s.getName(true), s.getSymbolType(), s.getSource());
            }
        }
    }
}
