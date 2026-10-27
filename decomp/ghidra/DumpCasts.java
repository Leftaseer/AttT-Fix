// debug: the casts of the decompiled C of the functions given, with the p-code ops of their operands
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.pcode.*;
import java.util.*;

public class DumpCasts extends GhidraScript {
    @Override
    public void run() throws Exception {
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        for (String a : getScriptArgs()[0].split(",")) {
            Function f = getFunctionAt(toAddr(Long.parseLong(a, 16)));
            DecompileResults r = di.decompileFunction(f, 120, monitor);
            List<ClangNode> toks = new ArrayList<>();
            r.getCCodeMarkup().flatten(toks);
            String want = getScriptArgs()[1];
            for (int i = 0; i < toks.size(); i++) {
                ClangToken t = (ClangToken) toks.get(i);
                if (!(t instanceof ClangTypeToken) || !t.getText().equals(want)) continue;
                StringBuilder sb = new StringBuilder();
                for (int k = Math.max(0, i - 2); k < Math.min(toks.size(), i + 12); k++) {
                    ClangToken x = (ClangToken) toks.get(k);
                    PcodeOp op = x.getPcodeOp();
                    sb.append("[").append(x.getText()).append(op == null ? "" : "|" + op.getMnemonic() + "@" + op.getSeqnum().getTarget() + "#" + op.getSeqnum().getTime()).append("]");
                }
                println(a + ": " + sb);
            }
            Iterator<PcodeOpAST> it = r.getHighFunction().getPcodeOps();
            while (it.hasNext()) {
                PcodeOpAST op = it.next();
                if (op.getOpcode() == PcodeOp.CAST) {
                    Varnode in = op.getInput(0);
                    println("  CAST " + op.getSeqnum().getTarget() + "#" + op.getSeqnum().getTime() + " out " +
                        (op.getOutput().getHigh() == null ? "?" : op.getOutput().getHigh().getDataType().getName()) + " in " +
                        (in.getHigh() == null ? "?" : in.getHigh().getDataType().getName()) + " def " + (in.getDef() == null ? "-" : in.getDef().getMnemonic() + "#" + in.getDef().getSeqnum().getTime()));
                }
            }
        }
    }
}
