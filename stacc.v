`timescale 1ps/1ps

module stacc(input clk, input pushEn, input popEn, input [31:0] inMask, output [31:0] outMask);

	reg [6:0] staccPointer = 0; // start at the bottom of the stack (subtracting will cause overflow to bottom)
	reg [31:0] staccy[0:63]; // store up to 64 32-bit masks (enforce max depth of 64)

	assign outMask = staccy[staccPointer];

	// pushing and popping on mask stack
	always @(posedge clk) begin
		if (popEn) begin
			staccy[staccPointer] <= -1;
			staccPointer <= staccPointer + 1;
		end
		if (pushEn) begin
			staccy[staccPointer - 1] <= inMask;
			staccPointer <= staccPointer - 1;
		end
	end

endmodule