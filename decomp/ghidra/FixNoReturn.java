// Clear wrong "no return" flags (Ghidra marked e.g. operator delete as non-returning, which cut the code after
// every call to it) and repair the flow after the affected calls.  Genuinely non-returning: functions without a
// reachable RET (and import thunks of exit/abort/_CxxThrowException/...).
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.cmd.function.CreateFunctionCmd;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class FixNoReturn extends GhidraScript {
    static final Set<String> NORETURN = Set.of("_CxxThrowException", "exit", "_exit", "abort", "ExitProcess",
        "_amsg_exit", "__report_gsfailure", "longjmp", "_invoke_watson", "_invalid_parameter", "terminate",
        "TerminateProcess", "RaiseException", "ExitThread", "_endthread", "_endthreadex", "FatalAppExitA");
    boolean hasRet(Function f) {
        InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
        while (it.hasNext()) {
            Instruction i = it.next();
            if (i.getMnemonicString().startsWith("RET")) return true;
        }
        return false;
    }
    @Override
    public void run() throws Exception {
        FunctionManager fm = currentProgram.getFunctionManager();
        List<Function> cleared = new ArrayList<>();
        for (Function f : fm.getFunctions(true)) {
            if (!f.hasNoReturn()) continue;
            boolean genuine;
            Function t = f.isThunk() ? f.getThunkedFunction(true) : f;
            if (t != null && t.isExternal()) genuine = NORETURN.contains(t.getName());
            else if (f.isExternal()) genuine = NORETURN.contains(f.getName());
            else genuine = !hasRet(f) && !NORETURN.contains("x");
            if (!genuine) { f.setNoReturn(false); cleared.add(f); }
        }
        println("cleared no-return on " + cleared.size() + " functions");
        // repair the flow after the calls
        Set<Function> touched = new HashSet<>();
        int dis = 0;
        for (Function f : cleared) {
            for (Reference r : getReferencesTo(f.getEntryPoint())) {
                if (!r.getReferenceType().isCall()) continue;
                Instruction call = getInstructionAt(r.getFromAddress());
                if (call == null) continue;
                Address next = call.getFallThrough();
                if (next == null) {
                    call.setFlowOverride(ghidra.program.model.listing.FlowOverride.NONE);
                    next = call.getMaxAddress().add(1);
                }
                if (getInstructionAt(next) == null && getDataAt(next) == null) {
                    DisassembleCommand dc = new DisassembleCommand(next, null, true);
                    if (dc.applyTo(currentProgram, monitor)) dis++;
                }
                Function c = getFunctionContaining(call.getAddress());
                if (c != null) touched.add(c);
            }
        }
        int fixed = 0;
        for (Function c : touched) {
            if (CreateFunctionCmd.fixupFunctionBody(currentProgram, c, monitor)) fixed++;
        }
        println("disassembled after " + dis + " calls, fixed bodies of " + fixed + " / " + touched.size() + " functions");
    }
}
