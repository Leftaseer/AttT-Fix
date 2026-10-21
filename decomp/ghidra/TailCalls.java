// Indirect jumps that are tail calls, not switches: 'add ecx, 4; jmp [eax+8]' (the this-adjusting thunks of
// multiple inheritance), 'jmp eax' after loading a vftable slot, 'jmp [import]' at the end of a function.  The
// decompiler took them for switches it could not recover ('Could not recover jumptable', 314 of them, none a real
// switch) and left the functions out.  Every indirect JMP without an index register (a table) gets the CALL_RETURN
// flow override: the decompiler then writes 'return (*p)(...)', a call that tools/icalls.py describes as well.
// Args: none.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.lang.Register;
import ghidra.program.model.scalar.Scalar;

public class TailCalls extends GhidraScript {
    @Override
    public void run() throws Exception {
        int set = 0;
        for (Instruction i : currentProgram.getListing().getInstructions(true)) {
            if (!i.getMnemonicString().equals("JMP") || i.getNumOperands() != 1) continue;
            if (!i.getFlowType().isComputed()) continue;           // a direct jump
            if (i.getFlows().length > 0) continue;                 // a switch the analysis recovered
            String op = i.getDefaultOperandRepresentation(0);
            if (op.contains("*")) continue;                        // [reg*4 + table]: a switch
            if (i.getFlowOverride() == FlowOverride.CALL_RETURN) continue;
            i.setFlowOverride(FlowOverride.CALL_RETURN);
            set++;
        }
        println("indirect jumps made tail calls: " + set);
    }
}
