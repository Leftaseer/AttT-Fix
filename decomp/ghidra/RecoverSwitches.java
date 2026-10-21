// Switches the decompiler could not recover ('Could not recover jumptable', 'Treating indirect jump as call': it
// then calls into the middle of its own function): 'jmp [reg*4 + table]' gets the table's entries as its targets,
// read as tools/stackfx.py switch_targets does (the dwords that point into the function, up to the first that does
// not), each case disassembled and added to the function, and a jump table override for the decompiler.
// Args: functions.tsv (the function sizes from the machine code)
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.function.CreateFunctionCmd;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.pcode.JumpTable;
import ghidra.program.model.symbol.*;
import ghidra.program.model.scalar.Scalar;
import java.io.*;
import java.util.*;

public class RecoverSwitches extends GhidraScript {
    @Override
    public void run() throws Exception {
        Map<Long, Long> sizes = new HashMap<>();
        try (BufferedReader r = new BufferedReader(new FileReader(getScriptArgs()[0]))) {
            for (String l; (l = r.readLine()) != null; ) {
                if (l.startsWith("#")) continue;
                String[] q = l.split("\t");
                sizes.put(Long.parseLong(q[0], 16), Long.parseLong(q[1]));
            }
        }
        int tables = 0, funcs = 0, fail = 0;
        for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
            if (f.isThunk() || f.isExternal()) continue;
            long lo = f.getEntryPoint().getOffset();
            Long size = sizes.get(lo);
            if (size == null) continue;
            long hi = lo + size;
            boolean any = false;
            List<Instruction> jumps = new ArrayList<>();      // first collect: the body changes below
            for (Instruction i : currentProgram.getListing().getInstructions(f.getBody(), true))
                if (i.getMnemonicString().equals("JMP") && i.getNumOperands() == 1) jumps.add(i);
            for (Instruction i : jumps) {
                // jmp dword ptr [reg*4 + table]
                Object[] o = i.getOpObjects(0);
                Long table = null;
                int scale = 0;
                boolean reg = false;
                for (Object x : o) {
                    if (x instanceof Scalar) {
                        long v = ((Scalar) x).getUnsignedValue();
                        if (v == 4 && scale == 0) scale = 4;
                        else if (v > 0x1000) table = v;
                    } else if (x instanceof ghidra.program.model.lang.Register) reg = true;
                }
                if (table == null || scale != 4 || !reg || !i.toString().contains("*0x4")) continue;
                // already a recovered switch: the decompiler has its targets
                if (i.getFlowType().isComputed() && i.getFlows().length > 1) continue;
                ArrayList<Address> dests = new ArrayList<>();
                for (int k = 0; k < 512; k++) {
                    long v;
                    try { v = currentProgram.getMemory().getInt(toAddr(table + 4L * k)) & 0xffffffffL; }
                    catch (Exception e) { break; }
                    if (v < lo || v >= hi) break;
                    dests.add(toAddr(v));
                }
                if (dests.isEmpty()) continue;
                try {
                    for (Address d : dests) {
                        i.addMnemonicReference(d, RefType.COMPUTED_JUMP, SourceType.USER_DEFINED);
                        if (getInstructionAt(d) == null) disassemble(d);
                    }
                    i.setFlowOverride(FlowOverride.NONE);
                    CreateFunctionCmd.fixupFunctionBody(currentProgram, f, monitor);
                    new JumpTable(i.getAddress(), dests, true).writeOverride(f);
                    tables++;
                    any = true;
                } catch (Exception e) {
                    println(String.format("failed %s: %s", i.getAddress(), e.getMessage()));
                    fail++;
                }
            }
            if (any) funcs++;
        }
        println("switch tables given to the decompiler: " + tables + " in " + funcs + " functions, failed " + fail);
    }
}
