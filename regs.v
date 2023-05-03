`timescale 1ps/1ps
`define RANGE16(i) (511 - 16 * (i)) -: 16

module regs(input clk, input [31:0] mask,
	input [3:0] vAddr0, output [511:0] vVal0,
	input [3:0] vAddr1, output [511:0] vVal1,
	input [3:0] vAddr2, output [511:0] vVal2,
	input [3:0] vAddr3, output [511:0] vVal3,
	input [3:0] sAddr0, output [15:0] sVal0,
	input [3:0] sAddr1, output [15:0] sVal1,
	input vEn, input [3:0] vAddrW, input [511:0] vDataW,
	input sEn, input [3:0] sAddrW, input [15:0] sDataW);

	reg [511:0] vData[0:15];
	reg [15:0] sData[0:15];

	// 4 vector read ports (don't worry about resource hazards for simplicity)
	assign vVal0 = vData[vAddr0];
	assign vVal1 = vData[vAddr1];
	assign vVal2 = vData[vAddr2];
	assign vVal3 = vData[vAddr3];

	// 2 shared read ports
	assign sVal0 = sData[sAddr0];
	assign sVal1 = sData[sAddr1];

	integer count, count2;

	// generate value to write to register depending on the mask
	wire [511:0]overWriteMask;
	generate
		genvar i;
		for(i = 0; i < 32; i = i + 1) begin
			assign overWriteMask[`RANGE16(i)] = mask[i] ? vDataW[`RANGE16(i)] : vData[vAddrW][`RANGE16(i)];
		end
	endgenerate

	always @(posedge clk) begin
		if (vEn) begin
			vData[vAddrW] <= overWriteMask;
		end
		if (sEn) begin
			sData[sAddrW] <= sDataW;
		end
	end

endmodule
