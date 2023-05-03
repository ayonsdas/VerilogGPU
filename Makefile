%.compiled: %.gpufun compiler.py
	@python3 compiler.py $@
	@echo "Compiled" $<

%.gpuasm: %.compiled assembly_preprocessor.py
	@python3 assembly_preprocessor.py $<
	@echo "Pre-processed" $<

%.run: %.gpuasm emulator.py display.py
	@rm -f output.png
	@python3 emulator.py $< | python3 display.py
	@echo "Emulation complete"

build: sim_main.cpp $(wildcard *.v)
	@verilator -Wno-fatal --cc --exe -O3 --build -j 4 sim_main.cpp gpu.v >/dev/null 2>&1
	@echo "Simulation compiled"

%.img: %.gpuasm build assembler.py
	@rm -f output.png
	@python3 assembler.py $<
	@obj_dir/Vgpu | awk '{{sub(/-.*/, ""); printf "%s", $$0}}' | python3 display.py
	@echo "Simulation complete"

clean:
	@rm -f mem.hex
	@rm -f *.vcd
	@rm -rf obj_dir
	@rm -f output.png
	@rm -f output.mp4
	@rm -rf __pycache__