// Export every Ghidra-discovered function as C-like pseudocode.
// @category JetRover
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import java.io.BufferedWriter;
import java.io.FileWriter;

public class ExportDecomp extends GhidraScript {
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) throw new IllegalArgumentException("Pass output directory");
        String directory = args[0];
        DecompInterface decompiler = new DecompInterface();
        decompiler.toggleCCode(true);
        decompiler.toggleSyntaxTree(true);
        if (!decompiler.openProgram(currentProgram)) throw new IllegalStateException("Decompiler open failed");
        int count = 0;
        int failed = 0;
        try (BufferedWriter code = new BufferedWriter(new FileWriter(directory + "/decompiled.c"));
             BufferedWriter index = new BufferedWriter(new FileWriter(directory + "/functions.tsv"))) {
            index.write("address\tname\tstatus\n");
            code.write("/* Ghidra C-like pseudocode. Not original or directly buildable source.\n");
            code.write(" * Input: RosRobotControllerM4.hex, Cortex-M Thumb, flash 0x08000000.\n");
            code.write(" */\n\n");
            FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
            while (functions.hasNext() && !monitor.isCancelled()) {
                Function function = functions.next();
                DecompileResults result = decompiler.decompileFunction(function, 120, monitor);
                String address = function.getEntryPoint().toString();
                String name = function.getName();
                if (result.decompileCompleted() && result.getDecompiledFunction() != null) {
                    code.write("/* " + address + " */\n" + result.getDecompiledFunction().getC() + "\n\n");
                    index.write(address + "\t" + name + "\tok\n");
                    count++;
                } else {
                    String message = result.getErrorMessage().replace('\t', ' ').replace('\n', ' ');
                    code.write("/* " + address + " " + name + ": decompilation failed: " + message + " */\n\n");
                    index.write(address + "\t" + name + "\tfailed: " + message + "\n");
                    failed++;
                }
            }
        } finally { decompiler.dispose(); }
        println("Exported " + count + " functions; " + failed + " failed");
    }
}
