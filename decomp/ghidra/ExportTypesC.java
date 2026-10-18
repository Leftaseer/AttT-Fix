// Write the C header for a list of data type paths (written by AutoExport.java next to its types.h).
// Args: types.h.list types.h
import ghidra.app.script.GhidraScript;
import ghidra.program.model.data.*;
import java.io.*;
import java.util.*;

public class ExportTypesC extends GhidraScript {
    @Override
    public void run() throws Exception {
        DataTypeManager dtm = currentProgram.getDataTypeManager();
        List<DataType> roots = new ArrayList<>();
        try (BufferedReader r = new BufferedReader(new FileReader(getScriptArgs()[0]))) {
            String l;
            while ((l = r.readLine()) != null) {
                DataType d = dtm.getDataType(l.trim());
                if (d != null) roots.add(d);
            }
        }
        new TypesC(this).write(getScriptArgs()[1], roots);
        println("types: " + roots.size());
    }
}
