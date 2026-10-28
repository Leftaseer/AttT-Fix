// Prototypes of indirect calls (virtual calls, function pointers) from the machine code (tools/icalls.py): the
// decompiler gives such a call its default prototype, which has no register inputs, and the object passed in ECX
// is lost ('(**(code **)*p)(1)' for 'mov ecx, esi; call [eax+4]').  For every call whose stack arguments the
// machine code tells (the 'add esp' after a caller-pop call, the ESP balance around a callee-pop one: icalls.py),
// writes a call-site override:
//   caller-pop                 __cdecl    (stack arguments)
//   callee-pop, ECX set        __thiscall (ECX, stack arguments)   - harmless for a __stdcall callee: it ignores ECX
//   callee-pop, ECX not set    __stdcall  (stack arguments)
// returning undefined4 when the decompiler found a result in EAX, void when it found none, float/double for one in
// ST0, undefined8 for 8 bytes in EDX:EAX.  Writes OUT.tsv: call address, convention, stack arguments, result.
// Args: icalls.tsv out.tsv
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.app.decompiler.parallel.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.data.*;
import ghidra.program.model.pcode.*;
import ghidra.util.task.TaskMonitor;
import java.io.*;
import java.util.*;

public class ICallOverride extends GhidraScript {
    static class Fact { int ecx, cleanup, pushes, pop, args = -1, espsafe = 0; }
    static class Site { long call; int nstack; Set<String> regs = new TreeSet<>(); String out; }

    @Override
    public void run() throws Exception {
        String in = getScriptArgs()[0], outPath = getScriptArgs()[1];
        Map<Long, Fact> facts = new HashMap<>();
        Set<Function> funcs = new HashSet<>();
        try (BufferedReader r = new BufferedReader(new FileReader(in))) {
            for (String l; (l = r.readLine()) != null; ) {
                if (l.startsWith("#")) continue;
                String[] q = l.split("\t");
                Fact f = new Fact();
                f.ecx = Integer.parseInt(q[2]); f.cleanup = Integer.parseInt(q[3]); f.pushes = Integer.parseInt(q[4]);
                f.pop = q.length > 5 ? Integer.parseInt(q[5]) : -1;
                if (q.length > 7) { f.args = Integer.parseInt(q[6]); f.espsafe = Integer.parseInt(q[7]); }
                long a = Long.parseLong(q[0], 16);
                facts.put(a, f);
                Function fn = getFunctionContaining(toAddr(a));
                if (fn != null) funcs.add(fn);
            }
        }
        DecompilerCallback<List<Site>> cb = new DecompilerCallback<>(currentProgram, new DecompileConfigurer() {
            public void configure(DecompInterface d) { d.toggleSyntaxTree(true); d.setSimplificationStyle("decompile"); }
        }) {
            public List<Site> process(DecompileResults r, TaskMonitor m) {
                List<Site> sites = new ArrayList<>();
                HighFunction hf = r.getHighFunction();
                if (hf == null) return sites;
                Iterator<PcodeOpAST> it = hf.getPcodeOps();
                while (it.hasNext()) {
                    PcodeOpAST op = it.next();
                    if (op.getOpcode() != PcodeOp.CALLIND) continue;
                    Site s = new Site();
                    s.call = op.getSeqnum().getTarget().getOffset();
                    // the inputs are the values passed: a raw register is a register argument (the decompiler's
                    // guess for an unknown prototype), anything else a stack argument of the default convention
                    for (int k = 1; k < op.getNumInputs(); k++) {
                        Varnode v = op.getInput(k);
                        if (v.isRegister()) {
                            ghidra.program.model.lang.Register rg = currentProgram.getRegister(v.getAddress(), v.getSize());
                            s.regs.add(rg == null ? v.getAddress().toString() : rg.getName());
                        } else s.nstack++;
                    }
                    Varnode o = op.getOutput();
                    if (o == null) s.out = "void";
                    else if (o.isRegister() && o.getSize() == 4 &&
                             "EAX".equals(currentProgram.getRegister(o.getAddress(), 4) == null ? null :
                                          currentProgram.getRegister(o.getAddress(), 4).getName())) s.out = "undefined4";
                    // after simplification the result is often a temporary (it went straight into a variable,
                    // 'this = (*vf)(...)' in 0x442890): 4 bytes that are no float are EAX all the same
                    else if (o.getSize() == 4 && !o.isRegister() &&
                             !(o.getHigh() != null && o.getHigh().getDataType() instanceof AbstractFloatDataType)) s.out = "undefined4";
                    // a float result: ST0 after the call, as the machine code goes on with it ('fstp' right after
                    // 0x4E0750's 'call edx'); 8 other bytes: EDX:EAX
                    else if ((o.isRegister() && currentProgram.getRegister(o.getAddress(), o.getSize()) != null &&
                              currentProgram.getRegister(o.getAddress(), o.getSize()).getName().startsWith("ST")) ||
                             (o.getHigh() != null && o.getHigh().getDataType() instanceof AbstractFloatDataType) ||
                             o.getSize() == 10)     // (an x87 value, ST0: the 'undefined1[10]' of 0x4B8746 'call eax; fadd')
                        s.out = o.getSize() == 4 ? "float" : "double";
                    else if (o.getSize() == 8) s.out = "undefined8";
                    else s.out = "other";
                    sites.add(s);
                }
                return sites;
            }
        };
        cb.setTimeout(60);
        List<List<Site>> res = ParallelDecompiler.decompileFunctions(cb, new ArrayList<>(funcs), monitor);
        cb.dispose();
        DataTypeManager dtm = currentProgram.getDataTypeManager();
        int written = 0, skipped = 0;
        try (PrintWriter w = new PrintWriter(new FileWriter(outPath))) {
            w.println("# call address\tconvention\tstack arguments\tresult\t(or: skipped, reason)");
            for (List<Site> sites : res) {
                if (sites == null) continue;
                for (Site s : sites) {
                    Fact f = facts.get(s.call);
                    String why = null, cc;
                    int nstack = 0;
                    boolean any = false;
                    if (f == null) why = "no machine-code facts";
                    else if (s.out.equals("other")) why = "float or wide result";
                    // the stack arguments come from the machine code: the decompiler's count for a call it has no
                    // prototype of is a guess (it takes the pushes of a later call's arguments as well)
                    else if (f.cleanup >= 0) nstack = f.cleanup / 4;
                    else if (f.pop >= 0) nstack = f.pop / 4;
                    // the pop unknown, but nothing after the call depends on ESP and the arguments are the dwords
                    // pushed since the call before: called through gh_call_any, which restores ESP ('any')
                    else if (f.espsafe == 1 && f.args >= 0) { nstack = f.args; any = true; }
                    else why = "stack arguments unknown";
                    cc = f == null || f.cleanup >= 0 ? "__cdecl" : f.ecx == 1 ? "__thiscall" : "__stdcall";
                    if (any) cc = f.ecx == 1 ? "__thiscall" : "__stdcall";
                    s.nstack = nstack;
                    if (why == null) {
                        if (why == null) {
                            Address ca = toAddr(s.call);
                            Function fn = getFunctionContaining(ca);
                            FunctionDefinitionDataType def = new FunctionDefinitionDataType(String.format("icall_%08X", s.call), dtm);
                            List<ParameterDefinition> ps = new ArrayList<>();
                            if (cc.equals("__thiscall")) ps.add(new ParameterDefinitionImpl("this", new PointerDataType(VoidDataType.dataType, dtm), null));
                            for (int k = 0; k < s.nstack; k++) ps.add(new ParameterDefinitionImpl("a" + k, Undefined4DataType.dataType, null));
                            def.setArguments(ps.toArray(new ParameterDefinition[0]));
                            def.setReturnType(s.out.equals("void") ? VoidDataType.dataType :
                                              s.out.equals("float") ? FloatDataType.dataType :
                                              s.out.equals("double") ? DoubleDataType.dataType :
                                              s.out.equals("undefined8") ? Undefined8DataType.dataType :
                                              Undefined4DataType.dataType);
                            def.setCallingConvention(cc);
                            try {
                                HighFunctionDBUtil.writeOverride(fn, ca, def);
                                w.printf("%08X\t%s\t%d\t%s%s%n", s.call, cc, s.nstack, s.out, any ? "\tany" : "");
                                written++;
                                continue;
                            } catch (Exception e) { why = "override failed: " + e.getMessage(); }
                        }
                    }
                    w.printf("%08X\tskipped\t%s%n", s.call, why);
                    skipped++;
                }
            }
        }
        println("indirect call overrides: " + written + " written, " + skipped + " skipped");
    }
}
