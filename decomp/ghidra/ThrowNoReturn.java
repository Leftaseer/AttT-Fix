// Functions that only throw: no ret, no jump out of their body, and the last instruction a call of a function that
// does not return (in the end _CxxThrowException, through its import thunk) - std::_Xran-like helpers such as
// 0x457840, which builds an out_of_range and throws it.  Unmarked, the decompiler continued their callers' code
// after the call with whatever the call left in registers (extraout_ECX in 0x4578C0, a vector's at()).
// Iterates: a function that ends in a call of one found here is one too.
// Args: none.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class ThrowNoReturn extends GhidraScript {
    boolean noReturn(Function f) {
        if (f == null) return false;
        if (f.hasNoReturn()) return true;
        Function t = f.isThunk() ? f.getThunkedFunction(true) : null;
        if (t != null && (t.hasNoReturn() || t.getName().equals("_CxxThrowException"))) return true;
        return f.getName().equals("_CxxThrowException");
    }

    @Override
    public void run() throws Exception {
        Listing l = currentProgram.getListing();
        int marked = 0;
        for (int round = 0; round < 6; round++) {
            int now = 0;
            for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
                if (f.isThunk() || f.isExternal() || f.hasNoReturn()) continue;
                AddressSetView body = f.getBody();
                Instruction last = null;
                boolean ok = true;
                for (Instruction i : l.getInstructions(body, true)) {
                    String m = i.getMnemonicString();
                    if (m.startsWith("RET")) { ok = false; break; }
                    if (m.equals("JMP")) {
                        Address[] fl = i.getFlows();
                        if (fl.length == 0) { ok = false; break; }            // a switch or a jump through a pointer
                        for (Address a : fl) if (!body.contains(a)) { ok = false; break; }   // a tail call
                        if (!ok) break;
                    }
                    last = i;
                }
                if (!ok || last == null || !last.getMnemonicString().equals("CALL")) continue;
                // the callee: a direct call's target, or the import a 'call [IAT]' reads
                Function callee = null;
                Address[] fl = last.getFlows();
                if (fl.length == 1) callee = getFunctionAt(fl[0]);
                if (callee == null)
                    for (Reference r : last.getReferencesFrom()) {
                        Symbol s = getSymbolAt(r.getToAddress());
                        if (s != null && s.getObject() instanceof Function) callee = (Function) s.getObject();
                        else if (s != null && s.getSymbolType() == SymbolType.LABEL) {
                            for (Reference r2 : getReferencesFrom(r.getToAddress())) {
                                Symbol s2 = getSymbolAt(r2.getToAddress());
                                if (s2 != null && s2.getObject() instanceof Function) callee = (Function) s2.getObject();
                            }
                        }
                    }
                if (!noReturn(callee)) continue;
                f.setNoReturn(true);
                println(String.format("NORETURN %08X %s (ends in %s)", f.getEntryPoint().getOffset(), f.getName(),
                                      callee.getName()));
                now++;
            }
            marked += now;
            if (now == 0) break;
        }
        println("functions that only throw marked noreturn: " + marked);
    }
}
