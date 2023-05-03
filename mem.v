`timescale 1ps/1ps
`define RANGE(i, start, len) (511 - 16 * (i) - 15 + start) -: len
`define RANGE16(i) (511 - 16 * (i)) -: 16

module mem(input clk, input [15:5] raddr0, output [511:0] rdata0,
			input [15:5] raddr1, output [511:0] rdata1,
			input [511:0] base, input [511:0] index, input [15:0] disp, output [511:0] ld_tex_val,
			input wen64, input [15:5] waddr64, input [511:0] wdata64, input [31:0] mask,
			input wen2, input [15:0] waddr2, input [15:0] wdata2);
	
	// 2^11 * 64 bytes of memory (use 16 bit read addresses to address every 2 bytes of memory)
	reg [511:0] data[0:11'h7ff];

	assign rdata0 = data[raddr0];
	assign rdata1 = data[raddr1];

	/* Simulation -- read initial content from file */
	initial begin
		$readmemh("mem.hex", data);
	end

	wire [511:0] overWriteMask;
	wire [511:0] overWriteShared;

	// generate rounded base and index based on
	// float base and index for ldtex32 instruction
	wire [511:0] rounded_base;
	wire [511:0] rounded_index;
	round_float base_rounder [0:31] (base, rounded_base);
	round_float index_rounder [0:31] (index, rounded_index);
	wire [511:0] ld_tex_addr;

	// generate the value for ldtex (integrate the regular memory with texture memory for simplicity)
	generate
		genvar j;
		for (j = 0; j < 32; j = j + 1) begin
			assign ld_tex_addr[`RANGE16(j)] = disp + rounded_base[`RANGE16(j)] + 32 * rounded_index[`RANGE16(j)];
			assign ld_tex_val[`RANGE16(j)] = data[ld_tex_addr[`RANGE(j, 15, 11)]][`RANGE16(ld_tex_addr[`RANGE(j, 4, 5)])];
		end
	endgenerate

	// generate value to write based on shared and vector registers depending on the mask
	generate
		genvar i;
		for(i = 0; i < 32; i = i + 1) begin
			assign overWriteShared[`RANGE16(i)] = (i == waddr2[4:0]) ? wdata2 : data[waddr2[15:5]][`RANGE16(i)];
			assign overWriteMask[`RANGE16(i)] = mask[i] ? wdata64[`RANGE16(i)] : data[waddr64][`RANGE16(i)];
		end
	endgenerate
	
	integer count;
	always @(posedge clk) begin
		if (wen64) begin
			data[waddr64] <= overWriteMask;
		end
		if (wen2) begin			
			data[waddr2[15:5]] <= overWriteShared;
		end
	end

endmodule