`timescale 1ps/1ps
`define START(i) (511 - 16 * (i))
`define RANGE16(i) `START(i) -: 16

module main(input clk);

	reg [15:1] pc = 0;

	always @ (posedge clk) begin
		pc <= jumpTime ? imm16[14:0] : pc + 1;
	end

	wire [511:0] ins_in;

	wire [4:0] ins_first_idx = {pc[4:1], 1'b0};

	wire [31:0] ins = ins_in[`START(ins_first_idx) -: 32];

	wire [5:0] opcode = ins[31:26];
	wire [1:0] suffix = ins[25:24];
	wire [3:0] rt = ins[23:20];
	wire [3:0] ra = ins[19:16];
	wire [3:0] rb = ins[15:12];
	wire [3:0] s_rt = rt;
	wire [3:0] s_ra = is_ld_tex ? ins[11:8] : ra;
	wire [3:0] s_rb = rb;
	wire [15:0] imm16 = ins[19:4];

	// [add/sub/mul/div] rt, ra, rb --> rt = ra <op> rb
	wire is_vector_arithmetic = (opcode == 6'b000001);
	wire is_vector_add = is_vector_arithmetic & (suffix == 2'b00);
	wire is_vector_sub = is_vector_arithmetic & (suffix == 2'b01);
	wire is_vector_mul = is_vector_arithmetic & (suffix == 2'b10);
	wire is_vector_div = is_vector_arithmetic & (suffix == 2'b11);

	// [add/sub/mul/div] s_rt, s_ra, s_rb --> s_rt = s_ra <op> s_rb
	wire is_shared_arithmetic = (opcode == 6'b000000);
	wire is_shared_add = is_shared_arithmetic & (suffix == 2'b00);
	wire is_shared_sub = is_shared_arithmetic & (suffix == 2'b01);
	wire is_shared_mul = is_shared_arithmetic & (suffix == 2'b10);
	wire is_shared_div = is_shared_arithmetic & (suffix == 2'b11);

	wire is_vector_mov = (opcode == 6'b000010);
	wire is_vector_mov_imm = is_vector_mov & (suffix == 2'b00);		// mov rt, imm16 --> fill all threads of rt with imm16
	wire is_movl = is_vector_mov & (suffix == 2'b01);				// mov rt, s_ra --> fill all threads of rt with s_ra % 2048 converted to float16
	wire is_mov_idx = is_vector_mov & (suffix == 2'b10);            // movidx rt --> fill each thread of rt with thread index as float16
	wire is_mov_raw = is_vector_mov & (suffix == 2'b11);			// movraw rt, s_ra --> fill all threads of rt with raw bits of s_ra
	
	wire is_shared_mov = (opcode == 6'b000011);
	wire is_shared_mov_imm = is_shared_mov & (suffix == 2'b00);		// movs s_rt, imm16 --> s_rt = imm16
	wire is_shared_mov_vector = is_shared_mov & (suffix == 2'b01);	// movpart s_rt, ra --> s_rt = round(ra[0])

	wire is_vector_ld = (opcode == 6'b000100);
	wire is_ld = is_vector_ld & (suffix == 2'b00);					// ld rt, s_ra --> load next 16*32 bits from address s_ra into r_t
	wire is_ld_all = is_vector_ld & (suffix == 2'b01);				// ldall rt, s_ra --> load next 16 bits from address s_ra into all threads of s_ra

	wire is_vector_st = (opcode == 6'b000101);						// st s_rt, ra --> store 16*32 bits from ra to address s_rt
	wire is_shared_st = (opcode == 6'b000110);						// st, s_rt, s_ra --> store 16 bits from s_ra to address s_rt
	wire is_wrscreen = (opcode == 6'b000111);						// output to screen

	wire is_mask_stack_op = (opcode == 6'b001000);
	wire is_push_mask = is_mask_stack_op & (suffix == 2'b00);		// pushmask --> push current predicated mask to mask stack
	wire is_pop_mask = is_mask_stack_op & (suffix == 2'b01);		// popmask --> pop from stack mask into current predicated mask
	wire is_peek_mask = is_mask_stack_op & (suffix == 2'b10);		// peekmask rt --> elementwise copies a bool based on each bit of the mask to each thread of rt

	wire is_mask_editor = (opcode == 6'b001001);
	wire is_invert_mask = is_mask_editor & (suffix == 2'b00);		// invertmask --> inverts the current mask
	wire is_vector_and_mask = is_mask_editor & (suffix == 2'b01);	// andmask ra --> elementwise ands each bit of the current mask with a bool from each thread of rt
	wire is_shared_and_mask = is_mask_editor & (suffix == 2'b10);	// andmask s_ra --> bitwise ands the current mask with s_ra

	wire is_jmp = (opcode == 6'b001010);
	wire is_jmp_mask = is_jmp & (suffix == 2'b00);					// jmpmask imm16 --> jumps PC to imm16 if any of the bits in the mask are 1
	wire is_jmp_not_mask = is_jmp & (suffix == 2'b01);				// jmpnotmask imm16 --> jumps PC to imm16 if none of the bits in the mask are 1

	wire is_vector_bitwise = (opcode == 6'b010000);
	wire is_vector_and = is_vector_bitwise & (suffix == 2'b00);		// and rt, ra, rb --> bitwise ands each thread of ra and rb into rt
	wire is_vector_or = is_vector_bitwise & (suffix == 2'b01);		// or rt, ra, rb --> bitwise ors each thread of ra and rb into rt
	wire is_vector_not = is_vector_bitwise & (suffix == 2'b10);		// not rt, ra --> bitwise nots each thread of ra into rt

	wire is_vector_bool = (opcode == 6'b010001);
	wire is_vector_gt = is_vector_bool & (suffix == 2'b00);			// gt rt, ra, rb --> rt = ra > rb (boolean)
	wire is_vector_lt = is_vector_bool & (suffix == 2'b01);			// lt rt, ra, rb --> rt = ra < rb (boolean)
	wire is_vector_gte = is_vector_bool & (suffix == 2'b10);		// gte rt, ra, rb --> rt = ra >= rb (boolean)
	wire is_vector_lte = is_vector_bool & (suffix == 2'b11);		// lte rt, ra, rb --> rt = ra <= rb (boolean)

	wire is_shared_bitwise = (opcode == 6'b010010);
	wire is_shared_and = is_shared_bitwise & (suffix == 2'b00);		// ands s_rt, s_ra, s_rb --> s_rt = s_ra & s_rb (bitwise)
	wire is_shared_or = is_shared_bitwise & (suffix == 2'b01);		// ors s_rt, s_ra, s_rb --> s_rt = s_ra | s_rb (bitwise)
	wire is_shared_not = is_shared_bitwise & (suffix == 2'b10);		// nots s_rt, s_ra --> s_rt = ~s_ra (bitwise)

	wire is_shared_bool = (opcode == 6'b010011);
	wire is_shared_gt = is_shared_bool & (suffix == 2'b00);			// gts s_rt, s_ra, s_rb --> s_rt = s_ra > s_rb (boolean)
	wire is_shared_lt = is_shared_bool & (suffix == 2'b01);			// lts s_rt, s_ra, s_rb --> s_rt = s_ra < s_rb (boolean)
	wire is_shared_gte = is_shared_bool & (suffix == 2'b10);		// gtes s_rt, s_ra, s_rb --> s_rt = s_ra >= s_rb (boolean)
	wire is_shared_lte = is_shared_bool & (suffix == 2'b11);		// ltes s_rt, s_ra, s_rb --> s_rt = s_ra <= s_rb (boolean)

	wire is_ld_tex = (opcode == 6'b010100);							// ldtex32 rt, ra, rb, s_ra --> rt[i] = mem[s_ra + round(ra[i]) + 32 * round(rb[i])]

	wire is_publish = (opcode == 6'b010101);						// marker to publish an image to the display

	wire is_halt = (opcode == 6'b111111);

	always @ (posedge clk) begin
		if (is_halt)
			$finish();
		if (is_publish)
			$write("publish");
	end

	wire [511:0] va;
	wire [511:0] vb;
	wire [15:0] s_va;
	wire [15:0] s_vb;

	wire [511:0] red = va;
	wire [511:0] green = vb;
	wire [511:0] blue;
	wire [511:0] depth;
	wire [15:0] x_val = s_va;
	wire [15:0] y_val = s_vb;

	always @ (posedge clk) begin
		// output to be read by the display
		if (is_wrscreen) begin
			$write("%512b", red);
			$write("%512b", green);
			$write("%512b", blue);
			$write("%512b", depth);
			$write("%32b", mask);
			$write("%16b", x_val);
			$write("%16b", y_val);
		end
	end

	wire [15:0] shared_mov_vector_result;
	round_float rounder(va, shared_mov_vector_result);

	// treat shared registers as integer values
	wire [15:0] shared_arithmetic_result =  is_shared_div ? s_va / s_vb :
											is_shared_mul ? s_va * s_vb :
											is_shared_sub ? s_va - s_vb :
											s_va + s_vb;

	wire [15:0] shared_bitwise_result =  	is_shared_not ? ~s_va :
											is_shared_or ? s_va | s_vb :
											s_va & s_vb;

	wire [15:0] shared_bool_result =  	is_shared_lte ? s_va <= s_vb :
										is_shared_gte ? s_va >= s_vb :
										is_shared_lt ? s_va < s_vb :
										s_va > s_vb;

	wire enable_rt_write = is_vector_arithmetic | is_vector_mov | is_vector_ld | is_vector_bitwise | is_vector_bool | is_ld_tex;
	wire [511:0] rt_target;
	wire enable_s_rt_write = is_shared_arithmetic | is_shared_mov | is_shared_bitwise | is_shared_bool;
	wire [15:0] s_rt_target;

	// initialize mask to 111...111 (all threads enabled)
	reg [31:0] mask = -1;
	wire jumpTime = (is_jmp_mask & mask != 0) | (is_jmp_not_mask & mask == 0);

	wire [3:0] vec_reg_addr0 = is_wrscreen ? 4'b0000 : ra;
	wire [3:0] vec_reg_addr1 = is_wrscreen ? 4'b0001 : rb;
	wire [3:0] shared_reg_addr0 = is_wrscreen ? 4'b0000 : s_ra;
	wire [3:0] shared_reg_addr1 = is_wrscreen ? 4'b0001 : s_rb;
	regs regs(clk, mask, vec_reg_addr0, va, vec_reg_addr1, vb, 4'b0010, blue, 4'b0011, depth,
				shared_reg_addr0, s_va, shared_reg_addr1, s_vb,
				enable_rt_write, rt, rt_target, enable_s_rt_write, s_rt, s_rt_target);

	wire [511:0] memVal64;
	wire [511:0] ld_tex_val;

	mem mem(clk, pc[15:5], ins_in, s_va[15:5], memVal64,
			va, vb, s_va, ld_tex_val,
			is_vector_st, s_va[15:5], vb, mask, is_shared_st, s_va, s_vb);

	wire [31:0] outMask;
	wire pushEn;
	wire popEn;
	
	wire [15:0] ldAllValue = memVal64[`RANGE16(s_va[4:0])];

	assign pushEn = is_push_mask;
	assign popEn = is_pop_mask;
	
	stacc stacc(clk, pushEn, popEn, mask, outMask);

	wire [21:0] movl_input_int = {6'd0, s_va};
	wire [15:0] movl_val;
	int_to_float16 movl_converter(movl_input_int, movl_val);

	wire [511:0] vector_add_result;
	wire [511:0] vector_sub_result;
	wire [511:0] vector_mul_result;
	wire [511:0] vector_div_result;

	wire [511:0] vector_arithmetic_result = is_vector_add ? vector_add_result :
											is_vector_sub ? vector_sub_result :
											is_vector_mul ? vector_mul_result :
											vector_div_result;

	float16_add adds [0:31] (va, vb, vector_add_result);
	float16_sub subs [0:31] (va, vb, vector_sub_result);
	float16_mult muls [0:31] (va, vb, vector_mul_result);
	float16_div divs [0:31] (va, vb, vector_div_result);

	// get int indexes and store in large register
	wire [703:0] int_idx;
	generate
		genvar idx;
		for (idx = 0; idx < 32; idx = idx + 1) begin
			assign int_idx[703 - 22 * idx -: 22] = 31 - idx;
		end
	endgenerate

	// convert all the int indexes to float indexes for movidx isntruction
	wire [511:0] mov_idx_val;
	int_to_float16 idx_converters [0:31] (int_idx, mov_idx_val);

	wire gt_value[31:0];
	wire gte_value[31:0];

	wire [15:0] va_bytes[0:31];
	wire [15:0] vb_bytes[0:31];

	generate 
		genvar mI;
		for(mI = 0; mI < 32; mI = mI + 1) begin
			// turn the large register into an array of 2-byte values
			assign va_bytes[mI] = va[`RANGE16(mI)];
			assign vb_bytes[mI] = vb[`RANGE16(mI)];

			// float comparison
			assign gt_value[mI] = (va_bytes[mI][15] != vb_bytes[mI][15]) ? 	~va_bytes[mI][15] :
																			~va_bytes[mI][15] ?	va_bytes[mI] > vb_bytes[mI] :
																								va_bytes[mI] < vb_bytes[mI];
			assign gte_value[mI] = (va_bytes[mI][15] != vb_bytes[mI][15]) ? ~va_bytes[mI][15] :
																			~va_bytes[mI][15] ?	va_bytes[mI] >= vb_bytes[mI] :
																								va_bytes[mI] <= vb_bytes[mI];
			
			assign rt_target[`RANGE16(mI)] = 	(is_vector_arithmetic) ? vector_arithmetic_result[`RANGE16(mI)] :
												(is_peek_mask) ? outMask[mI] : 
												(is_vector_and) ? va_bytes[mI] & vb_bytes[mI] : 
												(is_vector_or) ? va_bytes[mI] | vb_bytes[mI] : 
												(is_vector_not) ? ~va_bytes[mI] : 
												(is_vector_gt) ? {15'd0, gt_value[mI]} : 
												(is_vector_lt) ? {15'd0, ~gte_value[mI]} : 
												(is_vector_gte) ? {15'd0, gte_value[mI]} : 
												(is_vector_lte) ? {15'd0, ~gt_value[mI]} : 
												(is_ld) ? memVal64[`RANGE16(mI)] :
												(is_ld_all) ? ldAllValue :
												(is_mov_idx) ? mov_idx_val[`RANGE16(mI)] : 
												(is_vector_mov_imm) ? imm16 : 
												(is_movl) ? movl_val :
												(is_mov_raw) ? s_va :
												(is_ld_tex) ? ld_tex_val[`RANGE16(mI)] : 0;
		end
	endgenerate

	assign s_rt_target = 	(is_shared_arithmetic) ? shared_arithmetic_result :
							(is_shared_bitwise) ? shared_bitwise_result : 
							(is_shared_bool) ? shared_bool_result : 
							(is_shared_mov_imm) ? imm16 :
							(is_shared_mov_vector) ? shared_mov_vector_result :
							0;
	
	// update the mask based on the mask editing instructions
	integer mII;
	always @(posedge clk) begin
		for (mII = 0; mII < 32; mII = mII + 1) begin
			mask[mII] <=    is_invert_mask ? ~mask[mII] : 
							is_vector_and_mask ? mask[mII] & (va[`RANGE16(mII)] != 0) : 
							is_shared_and_mask ? mask[mII] & (s_va != 0) : 
							is_pop_mask ? outMask[mII] : 
							mask[mII];
		end
	end

endmodule

/*

OUR FLOATING POINT FORMAT:

- 16 bit (half-precision)
- 1 sign bit, 5 exponent bits, 10 mantissa bits
- Exponent bias is 16 (real exponent = exponent - 16)
- There is always an implied leading 1 in front of the mantissa
- Only representation for 0 is all 0s
- Overflow, underflow, and divide by 0 undefined (no NaN of infinity)

*/

module float16_add(input [15:0] a, input [15:0] b, output [15:0] out);

	wire a_sign = a[15];
	wire [4:0] a_exponent = a[14:10];
	wire a_zero = (a_exponent == 0) & (a[9:0] == 0);
	wire [15:0] a_mantissa = {5'b00000, a_zero ? 1'b0 : 1'b1, a[9:0]}; // convert to 16 bit value with explicit leading 1

	wire b_sign = b[15];
	wire [4:0] b_exponent = b[14:10];
	wire b_zero = (b_exponent == 0) & (b[9:0] == 0);
	wire [15:0] b_mantissa = {5'b00000, b_zero ? 1'b0 : 1'b1, b[9:0]}; // convert to 16 bit value with explicit leading 1

	wire is_diff_signs = (a_sign != b_sign);
	wire a_higher_magnitude = a[14:0] > b[14:0];
	wire a_is_higher_exp = a_exponent > b_exponent;

	wire [4:0] exponent_diff = a_is_higher_exp ? a_exponent - b_exponent : b_exponent - a_exponent;

	// shift the smaller value's mantissa so locations of the binary point match
	wire [15:0] a_fraction = a_is_higher_exp ? a_mantissa : (a_mantissa >> exponent_diff);
	wire [15:0] b_fraction = !a_is_higher_exp ? b_mantissa : (b_mantissa >> exponent_diff);

	// add the numbers as integers and convert back to float
	wire [21:0] res_fraction = 	is_diff_signs ? (a_higher_magnitude ? a_fraction - b_fraction : b_fraction - a_fraction) :
								a_fraction + b_fraction;
	wire [15:0] float_before_exp;
	int_to_float16 converter(res_fraction, float_before_exp);

	// add 6 at the end (equivalent to -(10 + 16) mod 32, 10 because of 10 bit
	// mantissa, and 16 because of the bias since it has been included twice)
	wire [4:0] actual_exp = float_before_exp[14:10] + (a_is_higher_exp ? a_exponent : b_exponent) + 6;

	// handle special zero cases
	assign out =	(res_fraction == 0) ? 0 :
					a_zero ? b :
					b_zero ? a :
					{is_diff_signs ? (a_higher_magnitude ? a[15] : b[15]) : a[15], actual_exp, float_before_exp[9:0]};

endmodule

// adder already handles both negatives and positives, just reuse it
module float16_sub(input [15:0] a, input [15:0] b, output [15:0] out);

	wire [15:0] negative_b = {~b[15], b[14:0]};
	float16_add adder(a, negative_b, out);

endmodule

module float16_mult(input [15:0] a, input [15:0] b, output [15:0] out);

	wire a_zero = (a[14:10] == 0) & (a[9:0] == 0);
	wire b_zero = (b[14:10] == 0) & (b[9:0] == 0);

	wire a_sign = a[15];
	wire [4:0] a_exponent = a[14:10];
	wire [21:0] a_mantissa = {11'd0, 1'b1, a[9:0]}; // convert to 22 bit value with explicit leading 1
	
	wire b_sign = b[15];
	wire [4:0] b_exponent = b[14:10];
	wire [21:0] b_mantissa = {11'd0, 1'b1, b[9:0]}; // convert to 22 bit value with explicit leading 1

	wire sign = a_sign ^ b_sign;
	wire [21:0] mantissa_intermediate = (a_mantissa * b_mantissa) >> 10; // shift to only use 10 mantissa bits

	// Fractional parts of a and b are between 1 and 2, so maximum resulting fractional
	// part is between 2 and 4, so shift resulting mantissa if it became greater than 2
	wire [9:0] mantissa_shifted = mantissa_intermediate[11] ? mantissa_intermediate[10:1] : mantissa_intermediate[9:0];

	// add 16 at the end because the bias was counted twice in a_exponent and b_exponent (increment the exponent for overflow)
	wire [4:0] exponent = (mantissa_intermediate[11] ? 1 : 0) + a_exponent + b_exponent + 16'b10000;

	assign out = (a_zero | b_zero) ? 0 : {sign, exponent, mantissa_shifted};

endmodule


module float16_div(input [15:0] a, input [15:0] b, output [15:0] out);

	wire a_zero = (a[14:10] == 0) & (a[9:0] == 0);
	wire b_zero = (b[14:10] == 0) & (b[9:0] == 0);

	wire a_sign = a[15];
	wire [4:0] a_exponent = a[14:10];
	wire [21:0] a_mantissa = {1'b1, a[9:0], 11'd0}; // convert to shifted 22 bit value (include 0s at the end for precision)
	
	wire b_sign = b[15];
	wire [4:0] b_exponent = b[14:10];
	wire [15:0] b_mantissa = {11'd0, 1'b1, b[9:0]}; // convert to 22 bit value (not shifted)

	wire sign = a_sign ^ b_sign;
	wire [21:0] mantissa = a_mantissa / b_mantissa;

	wire [15:0] float_before_exp;
	int_to_float16 converter(mantissa, float_before_exp);
	
	// subtract 11 for the initial shifting on a_mantissa (no need to shift due to
	// bias since it has been included 3 times, equivalent to including it 1 time)
	wire [4:0] actual_exp = float_before_exp[14:10] + (a_exponent - b_exponent) - 11;

	assign out = (a_zero | b_zero) ? 0 : {sign, actual_exp, float_before_exp[9:0]};	

endmodule

module int_to_float16(input [21:0] in, output [15:0] out);

	// really bad way of counting the number of leading zeros
	// (if you know of a better way please let me know)
	wire [4:0] num_leading_zeros = 	in[21] ? 0 :
									in[20] ? 1 :
									in[19] ? 2 :
									in[18] ? 3 :
									in[17] ? 4 :
									in[16] ? 5 :
									in[15] ? 6 :
									in[14] ? 7 :
									in[13] ? 8 :
									in[12] ? 9 :
									in[11] ? 10 :
									in[10] ? 11 :
									in[9] ? 12 :
									in[8] ? 13 :
									in[7] ? 14 :
									in[6] ? 15 :
									in[5] ? 16 :
									in[4] ? 17 :
									in[3] ? 18 :
									in[2] ? 19 :
									in[1] ? 20 :
									in[0] ? 21 :
									22;
	
	// count exponent needed to get past leading 1 (there is always an implied leading 1)
	wire [4:0] exponent = 22 - (num_leading_zeros + 1);
	wire [4:0] real_exponent = exponent + 16; // include the bias
	wire [21:0] in_shifted = in << (num_leading_zeros + 1); // shift integer left past leading 1 to get mantissa
	assign out = (in == 0) ? 0 : {1'b0, real_exponent, in_shifted[21:12]};

endmodule

module round_float(input [15:0] in, output [15:0] out);
	wire [4:0] exponent = in[14:10];
	wire [31:0] mantissa_shifted = {21'd0, 1'b1, in[9:0]} << (exponent - 16);

	// if the exponent with bias is < 0, then round up to 1 only if the value is >= 0.5
	// (similar rounding for all values based on first bit after the binary point)
	assign out = (exponent[4] == 0) ? (exponent == 5'b01111 & in[9]) : (mantissa_shifted[25:10] + mantissa_shifted[9]);
endmodule
