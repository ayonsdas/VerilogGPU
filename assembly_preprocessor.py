import sys

class AssemblyPreprocessor:
    def preprocess(self, lines) -> list:
        instructions = []
        labels = dict()
        final_asm_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if "//" in line:
                line = line[:line.index("//")].strip()
            if "#" in line:
                line = line[:line.index("#")].strip()
            if ";" in line:
                line = line[:line.index(";")].strip()
            if ":" in line:
                label = line[:line.index(":")].strip()
                labels[label] = len(final_asm_lines)
                line = '' # line[line.index(":") + 1:].strip()
            if len(line) > 0:
                final_asm_lines.append(line)
        for line in final_asm_lines:
            line = line.strip()
            if not line:
                continue
            for label in labels:
                if label in line:
                    line = line.replace(label, str(labels[label]))


            if len(line) > 0:
                instructions.append(line)
        # print instructions with line numbers starting from 0
        # for i in range(len(instructions)):
        #     print(str(i) + ": " + instructions[i])
        assert len(instructions) == len(final_asm_lines)
        return instructions
    
def main():
    # if has argv[1]
    if len(sys.argv) > 1:
        myFile = open(sys.argv[1]).readlines()
        f = open(sys.argv[1].split(".")[0] + ".gpuasm", "w")
    else:
        myFile = open("yeehaw.gpuasm").readlines()
        f = open("intermediate.gpuasm", "w")
    pre = AssemblyPreprocessor()
    out = pre.preprocess(myFile)
    for line in out:
        f.write(line)
        f.write("\n")


if __name__ == "__main__":
    main()


