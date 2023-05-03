import re
import subprocess
import sys

while_count = 0

def replace_while_code(allcode):
    global while_count

    # Find the first occurrence of the while loop
    while_start_index = allcode.find("while(")
    while_condition_index = allcode.find("(", while_start_index)
    while_condition_end = allcode.find(")", while_condition_index)
    if while_start_index == -1:
        # If the while loop isn't found, return the original string
        return allcode

    # Find the end of the while loop block
    block_start_index = allcode.find("{", while_start_index)
    block_end_index = find_matching_bracket(allcode, block_start_index)

    # Build the replacement string
    # replacement = "pushmask\nandmask " + allcode[while_start_index + 6:block_start_index - 1] + "\nwhile_start:\n"
    replacement = "pushmask\nandmask " + allcode[while_condition_index + 1:while_condition_end] + "\njmpnotmask while_end" + str(while_count) + "\nwhile_start" + str(while_count) + ":\n"
    replacement += allcode[block_start_index + 1:block_end_index] + "\n"
    replacement += "andmask " + allcode[while_start_index + 6:block_start_index - 1] + "\njmpmask while_start" + str(while_count) + "\nwhile_end" + str(while_count) + ":\npopmask"

    while_count += 1

    # Replace the while loop block with the replacement string
    return allcode[:while_start_index] + replacement + allcode[block_end_index + 1:]

if_count = 0

def replace_if_code(allcode):
    global if_count

    # Find the first occurrence of the if statement
    if_start_index = allcode.find("if(")
    if_condition_index = allcode.find("(", if_start_index)
    if_condition_end = allcode.find(")", if_condition_index)
    if if_start_index == -1:
        # If the if statement isn't found, return the original string
        return allcode

    # Find the end of the if statement block
    block_start_index = allcode.find("{", if_start_index)
    block_end_index = find_matching_bracket(allcode, block_start_index)

    # Build the replacement string
    replacement = "pushmask\nandmask " + allcode[if_condition_index + 1:if_condition_end] + "\njmpnotmask if_end" + str(if_count) + "\n"
    replacement += allcode[block_start_index + 1:block_end_index] + "\nif_end" + str(if_count) + ":\n"

    # try to find else statement immediately after if statement
    # like if (condition) { ... } else { ... }, there must be exactly one space between the } and else
    # has_else = allcode[block_end_index-1:block_end_index + 7] == "} else {"
    has_else = allcode.find("} else {", block_end_index - 3, block_end_index + 10) != -1
    if has_else:
        # Find the end of the else statement block
        else_block_start_index = allcode.find("{", block_end_index)
        else_block_end_index = find_matching_bracket(allcode, else_block_start_index)

        # invert the mask
        replacement += "peekmask r4\n invertmask \n andmask r4\njmpmask else_end" + str(if_count) + "\n"

        replacement += allcode[else_block_start_index + 1:else_block_end_index] + "\nelse_end" + str(if_count) + ":\n"
        block_end_index = else_block_end_index

    # pop the mask
    replacement += "popmask\n"

    if_count += 1

    
    
    #"popmask"

    # Replace the if statement block with the replacement string
    return allcode[:if_start_index] + replacement + allcode[block_end_index + 1:]

def find_matching_bracket(string, start_index):
    # Helper function to find the matching closing bracket
    stack = ["{"]
    i = start_index + 1
    while i < len(string) and stack:
        if string[i] == "{":
            stack.append("{")
        elif string[i] == "}":
            stack.pop()
        i += 1
    return i - 1



class Compiler:
    
    def preprocess(self, lines) -> list[str]:
        instructions = []
        labels = {
            "red": "r0",
            "green": "r1",
            "blue": "r2",
            "depth": "r3",
            "x": "s_r0",
            "y": "s_r1",
        }
        
        for line in lines:
            line = line.strip()

            # remove comments
            if not line:
                continue
            if "//" in line:
                line = line[:line.index("//")].strip()
            if "#" in line:
                line = line[:line.index("#")].strip()
            # if ";" in line:
            #     line = line[:line.index(";")].strip()

            # replace labels if they are surrounded by whitespace/parentheses/commas
            for label in labels:
                # surround with regex
                temp_label = r"(?<!\w)" + re.escape(label) + r"(?!\w)"
                matches = re.search(temp_label, line)
                if matches:
                    # replace with regex
                    line = re.sub(temp_label, labels[label], line)
                
                # if temp_label in line:
                #     # replace with regex
                #     line = re.sub(temp_label, labels[label], line)

            # # if it's in the form r1 = imm, replace with mov r1, imm
            # match_mov = re.search(r"^r(1[0-5]|[0-9])\s*=\s*(\d+)", line)
            # if(match_mov):
            #     # line = re.sub(r"r(1[0-5]|[0-9])\s*=\s**\d+", "mov " + match_mov.group(1) + ", imm", line)
            #     line = "mov r" + match_mov.group(1) + ", " + match_mov.group(2)
            # match_movs = re.search(r"^s_r(1[0-5]|[0-9])\s*=\s*(\d+)", line)
            # if(match_movs):
            #     line = "movs s_r" + match_movs.group(1) + ", " + match_movs.group(2)
            # #movl rt, s_ra // fills all threads of rt with value s_ra mod 2048 converted to float16
            # match_movl = re.search(r"^r(1[0-5]|[0-9])\s*=\s*s_r(1[0-5]|[0-9])", line)
            # if(match_movl):
            #     line = "movl r" + match_movl.group(1) + ", s_r" + match_movl.group(2)
            




            # output non-empty lines
            if len(line) > 0:
                instructions.append(line)
        
        # combine all lines into one string
        allcode = "\n".join(instructions)

        # allow "int32 xxx = yyy;" variable declarations
        free_s_regs = [True] * 16
        free_v_regs = [True] * 16

        # mark s registers that are used in the code
        for i in range(len(allcode)):
            if allcode[i:i+3] == "s_r":
                # can be 0-15
                # reg = int(allcode[i+4:i+6])
                reg_str = allcode[i+3:i+5]
                reg_match = re.search(r"\b(1[0-5]|[0-9])\b", reg_str)
                reg = int(reg_match.group(1))
                free_s_regs[reg] = False
            if allcode[i:i+2] == "r_":
                # can be 0-15
                # reg = int(allcode[i+3:i+5])
                reg_str = allcode[i+2:i+4]
                reg_match = re.search(r"\b(1[0-5]|[0-9])\b", reg_str)
                reg = int(reg_match.group(1))
                free_v_regs[reg] = False

        # if s register is in the labels map's values, mark it as used
        for label in labels.values():
            # if starts with s_r and ends with an int [0, 15]
            if re.match(r"^s_r(1[0-5]|[0-9])$", label):
                reg = int(label[3:])
                free_s_regs[reg] = False
        # if v register is in the labels map's values, mark it as used
        for label in labels.values():
            # if starts with r and ends with an int [0, 15]
            if re.match(r"^r(1[0-5]|[0-9])$", label):
                reg = int(label[1:])
                free_v_regs[reg] = False

        var_s_regs_map = {}
        var_v_regs_map = {}
        i = 0
        while i < len(allcode):
            # continue if looking back there is a // before the newline
            slash_index = allcode.rfind("//", 0, i+1)
            newline_index = allcode.rfind("\n", 0, i+1)
            if slash_index > newline_index:
                i += 1
                continue

            if allcode[i:i+4] == "int ":
                # find the end of the variable name
                var_name_end = allcode.find("=", i + 4)
                var_name = allcode[i + 4:var_name_end].strip()
                # find the end of the variable value
                var_val_end = allcode.find("\n", var_name_end)
                if var_val_end == -1:
                    var_val_end = len(allcode)
                var_val = allcode[var_name_end + 1:var_val_end].strip()
                # find the next free s register
                found = False
                for j in range(len(free_s_regs)):
                    if free_s_regs[j]:
                        free_s_regs[j] = False
                        found = True
                        break
                if not found:
                    raise Exception("No free s registers")
                # replace the declaration with a movs instruction
                allcode = allcode[:i] + allcode[i + 4:] # + "movs s_r" + str(j) + ", " + var_val + "\n" + allcode[var_val_end + 1:]
                # register in map
                var_s_regs_map[var_name] = j
                i -= 1
                # # replace all instances of the variable name with the s register
                # allcode = allcode.replace(var_name, "s_r" + str(j))
                # print(allcode)
            if allcode[i:i+4] == "vec ":
                # find the end of the variable name
                var_name_end = allcode.find("=", i + 4)
                var_name = allcode[i + 4:var_name_end].strip()
                # find the end of the variable value
                var_val_end = allcode.find("\n", var_name_end)
                if var_val_end == -1:
                    var_val_end = len(allcode)
                var_val = allcode[var_name_end + 1:var_val_end].strip()
                # find the next free v register
                found = False
                for j in range(len(free_v_regs)):
                    if free_v_regs[j]:
                        free_v_regs[j] = False
                        found = True
                        break
                if not found:
                    raise Exception("No free v registers")
                # replace the declaration with a movs instruction
                allcode = allcode[:i] + allcode[i + 4:] # + "mov r" + str(j) + ", " + var_val + "\n" + allcode[var_val_end + 1:]
                # register in map
                var_v_regs_map[var_name] = j
                i -= 1
                # # replace all instances of the variable name with the s register
                # allcode = allcode.replace(var_name, "s_r" + str(j))
                # print(allcode)
            # handle variable del (delete the variable from the map)
            if allcode[i:i+5] == "deli ":
                # find the end of the variable name
                var_name_end = allcode.find("\n", i + 5)
                var_name = allcode[i + 5:var_name_end].strip()
                # find the s register associated with the variable
                s_reg = var_s_regs_map[var_name]
                # mark the s register as free
                free_s_regs[s_reg] = True
                # remove the variable from the map
                del var_s_regs_map[var_name]
                # remove the del instruction
                allcode = allcode[:i] + "\n" + allcode[var_name_end + 1:]
            if allcode[i:i+5] == "delv ":
                # find the end of the variable name
                var_name_end = allcode.find("\n", i + 5)
                var_name = allcode[i + 5:var_name_end].strip()
                # find the v register associated with the variable
                v_reg = var_v_regs_map[var_name]
                # mark the v register as free
                free_v_regs[v_reg] = True
                # remove the variable from the map
                del var_v_regs_map[var_name]
                # remove the del instruction
                allcode = allcode[:i] + "\n" + allcode[var_name_end + 1:]
            # handle variable occurrences
            for var_name in var_s_regs_map:
                # surround with regex
                temp_var_name = r"(\n|[^\w])" + re.escape(var_name) + r"($|[^\w])"
                var_match = re.match(temp_var_name, allcode[i:])
                if var_match: # and var_match.pos > 0:
                    # replace with regex
                    allcode = allcode[:i+1] + "s_r" + str(var_s_regs_map[var_name]) + allcode[i + 1 + len(var_name):]
                    # add comment with original variable name right before newline
                    newlinepos = allcode.find("\n", i + 1)
                    allcode = allcode[:newlinepos] + " // " + var_name + allcode[newlinepos:]


            for var_name in var_v_regs_map:
                # surround with regex
                temp_var_name = r"(\n|[^\w])" + re.escape(var_name) + r"($|[^\w])"
                var_match = re.match(temp_var_name, allcode[i:])
                if var_match: # and var_match.pos > 0:
                    # replace with regex
                    allcode = allcode[:i+1] + "r" + str(var_v_regs_map[var_name]) + allcode[i + 1 + len(var_name):]
                    # add comment with original variable name right before newline
                    newlinepos = allcode.find("\n", i + 1)
                    allcode = allcode[:newlinepos] + " // " + var_name + allcode[newlinepos:]
            i += 1

        # find while loops
        # while allcode.find("while") != -1:
        #     # find the while loop
        #     while_start = allcode.find("while")
        while allcode.find("while(") != -1:
            allcode = replace_while_code(allcode)

        # find if statements
        while allcode.find("if(") != -1:
            allcode = replace_if_code(allcode)



        # split by newlines
        instructions = allcode.split("\n")

            
        
        
        # # print instructions with line numbers starting from 0
        # for i in range(len(instructions)):
        #     print(str(i) + ": " + instructions[i])

        return instructions
    

    def compile(self, lines) -> list[str]:
        instructions = []
        labels = dict()
        
        for line in lines:
            line = line.strip()

            # if it's in the form r1 = imm, replace with mov r1, imm
            match_mov = re.search(r"^r(1[0-5]|[0-9])\s*=\s*(-?\d+(\.\d+)?)", line)
            if(match_mov):
                # line = re.sub(r"r(1[0-5]|[0-9])\s*=\s*(-?\d+(\.\d+)?", "mov " + match_mov.group(1) + ", imm", line)
                line = "mov r" + match_mov.group(1) + ", " + match_mov.group(2)
            match_movs = re.search(r"^s_r(1[0-5]|[0-9])\s*=\s*(\d+)", line)
            if(match_movs):
                line = "movs s_r" + match_movs.group(1) + ", " + match_movs.group(2)
            #movl rt, s_ra // fills all threads of rt with value s_ra mod 2048 converted to float16
            match_movl = re.search(r"^r(1[0-5]|[0-9])\s*=\s*s_r(1[0-5]|[0-9])", line)
            if(match_movl):
                line = "movl r" + match_movl.group(1) + ", s_r" + match_movl.group(2)

            if len(line) > 0:
                instructions.append(line)

        # # print instructions with line numbers starting from 0
        # for i in range(len(instructions)):
        #     print(str(i) + ": " + instructions[i])

        return instructions
    

# main
def main():
    c = Compiler()
    # filename should be argv[1]
    filename = sys.argv[1] if len(sys.argv) > 1 else "yeehaw.gpuasm"
    # open yeehaw.gpufun
    with open(filename.split(".")[0] + ".gpufun", "r") as f:
        lines = f.readlines()
    lines = c.preprocess(lines)
    lines = c.compile(lines)
    # write to yeehaw1.gpuasm
    with open(filename, "w") as f:
        for line in lines:
            f.write(line + "\n")


    # # run emulator.py with yeehaw1.gpuasm as first argv
    # print("Running emulator.py with yeehaw1.gpuasm as first argv")
    # subprocess.run(['python3', 'emulator.py', 'yeehaw1.gpuasm'])

    # run emulator.py and pipe output to display.py
    # print("Running emulator.py and piping output to display.py")
    # p1 = subprocess.Popen(['python3', 'emulator.py', 'yeehaw1.gpuasm'], stdout=subprocess.PIPE)
    # p2 = subprocess.Popen(['python3', 'display.py'], stdin=p1.stdout, stdout=subprocess.PIPE)
    # p2 should write to our console
    # p2 = subprocess.Popen(['python3', 'display.py'], stdin=p1.stdout, stdout=sys.stdout)
    # p1.stdout.close()
    # output = p2.communicate()[0]
    # print(output)


if __name__ == "__main__":
    main()