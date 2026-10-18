// Write all data types of the program (structures, unions, enums, typedefs, function definitions) as a C header.
// Arg: output .h path
import ghidra.app.script.GhidraScript;
import ghidra.program.model.data.*;
import java.io.*;

public class ExportTypes extends GhidraScript {
    @Override
    public void run() throws Exception {
        DataTypeManager dtm = currentProgram.getDataTypeManager();
        try (FileWriter fw = new FileWriter(getScriptArgs()[0])) {
            DataTypeWriter w = new DataTypeWriter(dtm, fw, false);
            w.write(dtm, monitor);
        }
        println("types written");
    }
}
