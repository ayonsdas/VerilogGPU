#include "Vgpu.h"
#include <verilated.h>
#include "verilated_vcd_c.h"

#define MAX_SIM_TIME 10000000000000000000
vluint64_t sim_time = 0;

int main(int argc, char** argv) {
	Verilated::commandArgs(argc, argv);
	Vgpu* top = new Vgpu;
	// Verilated::traceEverOn(true);
    // VerilatedVcdC* tfp = new VerilatedVcdC;
    // top->trace(tfp, 99);
    // tfp->open("waveform.vcd");
	while (sim_time < MAX_SIM_TIME && !Verilated::gotFinish()) {
		top->clk ^= 1;
		top->eval();
		sim_time++;
		// tfp->dump(sim_time);
	}
	// tfp->close();
	top->eval();
	delete top;
	return 0;
}
