// Seed Cortex-M vector entry points before auto analysis.
// @category JetRover
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.lang.Register;
import ghidra.program.model.symbol.SourceType;
import ghidra.program.model.listing.Function;
import java.math.BigInteger;

public class SeedVectors extends GhidraScript {
    public void run() throws Exception {
        long base = 0x08000000L;
        long end = 0x080140dfL;
        Register tmode = currentProgram.getRegister("TMode");
        if (tmode != null) currentProgram.getProgramContext().setValue(tmode, toAddr(base), toAddr(end), BigInteger.ONE);
        String[] core = new String[16];
        core[1] = "Reset_Handler"; core[2] = "NMI_Handler"; core[3] = "HardFault_Handler";
        core[4] = "MemManage_Handler"; core[5] = "BusFault_Handler"; core[6] = "UsageFault_Handler";
        core[11] = "SVC_Handler"; core[12] = "DebugMon_Handler";
        core[14] = "PendSV_Handler"; core[15] = "SysTick_Handler";
        java.util.Set<Long> seen = new java.util.HashSet<>();
        int created = 0;
        for (int i = 1; i < 98; i++) {
            long pointer = currentProgram.getMemory().getInt(toAddr(base + 4L * i)) & 0xffffffffL;
            long target = pointer & ~1L;
            if ((pointer & 1) == 0 || target < base || target > end || !seen.add(target)) continue;
            Address address = toAddr(target);
            String name = i < 16 && core[i] != null ? core[i] : "IRQ_" + (i - 16) + "_Handler";
            if (!disassemble(address)) continue;
            Function function = getFunctionAt(address);
            if (function == null) function = createFunction(address, name);
            if (function != null) { function.setName(name, SourceType.USER_DEFINED); created++; }
        }
        println("Seeded " + created + " unique vector functions");
    }
}
