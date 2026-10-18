// Create functions at code starts Ghidra missed: after int3/nop padding, and at call targets.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.reloc.*;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.cmd.function.CreateFunctionCmd;
import java.util.*;

public class AddMissingFunctions extends GhidraScript {
    @Override
    public void run() throws Exception {
        Memory mem = currentProgram.getMemory();
        MemoryBlock text = mem.getBlock(".text");
        Listing lst = currentProgram.getListing();
        FunctionManager fm = currentProgram.getFunctionManager();
        Set<Long> relocSites = new HashSet<>();
        Iterator<Relocation> ri = currentProgram.getRelocationTable().getRelocations();
        while (ri.hasNext()) relocSites.add(ri.next().getAddress().getOffset());
        long start = text.getStart().getOffset(), end = text.getEnd().getOffset();
        byte[] b = new byte[(int)(end - start + 1)];
        text.getBytes(text.getStart(), b);
        int created = 0, pass = 0;
        boolean again = true;
        while (again && pass < 4) {
            again = false; pass++;
            for (int i = 1; i < b.length - 1; i++) {
                if (b[i] == (byte)0xCC || b[i - 1] != (byte)0xCC) continue;
                long va = start + i;
                if ((va & 3) != 0) continue;
                Address a = toAddr(va);
                if (fm.getFunctionContaining(a) != null) continue;
                Data d = lst.getDefinedDataContaining(a);
                if (d != null) continue;
                if (relocSites.contains(va)) continue;
                if (lst.getInstructionAt(a) == null) {
                    DisassembleCommand dc = new DisassembleCommand(a, null, true);
                    if (!dc.applyTo(currentProgram, monitor)) continue;
                    if (lst.getInstructionAt(a) == null) continue;
                }
                CreateFunctionCmd cf = new CreateFunctionCmd(a);
                if (cf.applyTo(currentProgram, monitor)) { created++; again = true; }
            }
            println("pass " + pass + ": total created " + created);
        }
        println("created " + created + " functions; now " + fm.getFunctionCount());
    }
}
