// Prototypes of indirect calls (virtual calls, function pointers) from the machine code (tools/icalls.py): the
// decompiler gives such a call its default prototype, which has no register inputs, and the object passed in ECX
// is lost ('(**(code **)*p)(1)' for 'mov ecx, esi; call [eax+4]').  For every call whose stack arguments the
// decompiler found consistently with the machine code (the 'add esp' after a caller-pop call, or the pushes right
// before a callee-pop one), writes a call-site override:
//   caller-pop                 __cdecl    (stack arguments)
//   callee-pop, ECX set        __thiscall (ECX, stack arguments)   - harmless for a __stdcall callee: it ignores ECX
//   callee-pop, ECX not set    __stdcall  (stack arguments)
// returning undefined4 when the decompiler found a result in EAX, void when it found none; calls with a float or
// 8-byte result are left alone.  Writes OUT.tsv: call address, convention, stack arguments, result.
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
    static class Fact { int ecx, cleanup, pushes; }
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
                    if (f == null) why = "no machine-code facts";
                    else if (!s.regs.isEmpty() && !(s.regs.equals(Collections.singleton("ECX")) && f.ecx == 1 && f.cleanup < 0))
                        why = "register input " + s.regs;     // ECX alone with a callee-pop call is a __thiscall
                    else if (s.out.equals("other")) why = "float or wide result";
                    if (why == null) {
                        if (f.cleanup >= 0) {
                            cc = "__cdecl";
                            if (f.cleanup != 4 * s.nstack) why = "add esp " + f.cleanup + ", decompiler " + s.nstack + " arguments";
                        } else {
                            cc = f.ecx == 1 ? "__thiscall" : "__stdcall";
                            if (f.pushes != s.nstack) why = "pushes " + f.pushes + ", decompiler " + s.nstack + " arguments";
                        }
                        if (why == null) {
                            Address ca = toAddr(s.call);
                            Function fn = getFunctionContaining(ca);
                            FunctionDefinitionDataType def = new FunctionDefinitionDataType(String.format("icall_%08X", s.call), dtm);
                            List<ParameterDefinition> ps = new ArrayList<>();
                            if (cc.equals("__thiscall")) ps.add(new ParameterDefinitionImpl("this", new PointerDataType(VoidDataType.dataType, dtm), null));
                            for (int k = 0; k < s.nstack; k++) ps.add(new ParameterDefinitionImpl("a" + k, Undefined4DataType.dataType, null));
                            def.setArguments(ps.toArray(new ParameterDefinition[0]));
                            def.setReturnType(s.out.equals("void") ? VoidDataType.dataType : Undefined4DataType.dataType);
                            def.setCallingConvention(cc);
                            try {
                                HighFunctionDBUtil.writeOverride(fn, ca, def);
                                w.printf("%08X\t%s\t%d\t%s%n", s.call, cc, s.nstack, s.out);
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
