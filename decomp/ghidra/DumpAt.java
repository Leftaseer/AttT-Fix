// debug: the lines of the decompiled C holding ops of the given machine addresses (FUNC:ADDR,...), with the ops
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.app.decompiler.component.DecompilerUtils;
import ghidra.program.model.listing.*;
import ghidra.program.model.pcode.*;
import java.util.*;

public class DumpAt extends GhidraScript {
    @Override
    public void run() throws Exception {
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        for (String fa : getScriptArgs()[0].split(",")) {
            String[] q = fa.split(":");
            Function f = getFunctionAt(toAddr(Long.parseLong(q[0], 16)));
            long at = Long.parseLong(q[1], 16);
            DecompileResults r = di.decompileFunction(f, 120, monitor);
            for (ClangLine line : DecompilerUtils.toLines(r.getCCodeMarkup())) {
                boolean hit = false;
                StringBuilder sb = new StringBuilder();
                for (ClangToken t : line.getAllTokens()) {
                    PcodeOp op = t.getPcodeOp();
                    if (op != null && op.getSeqnum().getTarget().getOffset() == at) hit = true;
                    sb.append(t.getText());
                    if (op != null && op.getSeqnum().getTarget().getOffset() == at) {
                        sb.append("{").append(op.getMnemonic());
                        for (Varnode v : op.getInputs()) sb.append(" ").append(v.getHigh() == null ? v.toString() : v.getHigh().getDataType().getName());
                        sb.append("}");
                    }
                }
                if (hit) println(q[0] + ":" + q[1] + " " + sb.toString().trim());
            }
        }
    }
}
