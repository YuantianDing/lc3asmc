"""
Usage:
    lc3asmc <inputfile> [-o <output>]
"""

import re
from docopt import docopt
from inspect import isfunction

def assign(str):
    return str == '=' or str == '<-'
def assignp(str):
    return str == '+=' or str == '<+'

def is_int(z):
    try:
        z = int(z)
        return isinstance(z, int)
    except ValueError:
        return False


def is_not0(z):
    return is_int(z) and int(z) != 0


def is_reg(str):
    return len(str) == 2 and str[0] == "R" and '0' <= str[1] <= '7'


def is_hex(str):
    if not str[0] == 'x':
        return False
    for i in str[1:]:
        if not ('0' <= i <= '9' or 'a' <= i <= 'f'or 'A' <= i <= 'F'):
            return False
    return True

def tablen(str):
    return len(str.expandtabs(tabsize=4))


class pattern:
    def __init__(self, p, gen, labelgen=None):
        self.expr = p
        self.gen = gen

        self.labelgen = labelgen

    def __contains__(self, line):
        if len(self.expr) != len(line):
            return False
        for e, l in zip(self.expr, line):
            if isfunction(e):
                if not e(l):
                    return False
            elif type(e) == str:
                if e != l:
                    return False
            elif e == None:
                if is_reg(l) or is_int(l):
                    return False
        return True

    def __call__(self, line):
        return self.gen(line)

stack = []
nzp = {
    ">": "p",
    ">=": "zp",
    "<": "n",
    "<=": "nz",
    "==": "z",
    "!-": "np",
}

def DoWhile(line):
    global stack
    stack += [line[1]]
    return ""
def EndDoWhile(line):
    global stack, nzp
    l = stack[-1]
    stack.pop()
    return "BR%s\t\t%s" %(nzp[line[3]],l)



patterns = [
    # 计算指令
    pattern([is_reg, assign, is_reg, '+', is_reg],
            lambda l: "ADD\t\t%s,\t\t%s,\t\t%s" % (l[0], l[2], l[4])),
    pattern([is_reg, assign, is_reg, '&', is_reg],
            lambda l: "AND\t\t%s,\t\t%s,\t\t%s" % (l[0], l[2], l[4])),

    pattern([is_reg, assign, is_reg, '+', is_int],
            lambda l: "ADD\t\t%s,\t\t%s,\t\t#%s" % (l[0], l[2], l[4])),
    pattern([is_reg, assign, is_reg, '-', is_int],
            lambda l: "ADD\t\t%s,\t\t%s,\t\t#-%s" % (l[0], l[2], l[4])),
    pattern([is_reg, assign, is_reg, '&', is_int],
            lambda l: "AND\t\t%s,\t\t%s,\t\t#%s" % (l[0], l[2], l[4])),
    pattern([is_reg, assign, is_reg, '&','-', is_int],
            lambda l: "AND\t\t%s,\t\t%s,\t\t#-%s" % (l[0], l[2], l[5])),

    pattern([is_reg, assign, '~', is_reg],
            lambda l: "NOT\t\t%s,\t\t%s" % (l[0], l[3])),

    pattern([is_reg, assignp, is_int],
            lambda l: "ADD\t\t%s,\t\t%s,\t\t#%s" % (l[0], l[0], l[2])),
    pattern([is_reg, assignp,'-', is_int],
            lambda l: "ADD\t\t%s,\t\t%s,\t\t#-%s" % (l[0], l[0], l[3])),
    pattern([is_reg, '-=', is_int],
            lambda l: "ADD\t\t%s,\t\t%s,\t\t#-%s" % (l[0], l[0], l[2])),
    pattern([is_reg, assignp, is_reg],
            lambda l: "ADD\t\t%s,\t\t%s,\t\t%s" % (l[0], l[0], l[2])),

    pattern([is_reg, assign, '0'],
            lambda l: "AND\t\t%s,\t\t%s,\t\t#0" % (l[0], l[0])),
    pattern([is_reg, assign, is_reg],
            lambda l: "ADD\t\t%s,\t\t%s,\t\t#0" % (l[0], l[2])),
    pattern([is_reg, assign, is_not0],
            lambda l: [
                "AND\t\t%s,\t\t%s,\t\t#0" % (l[0], l[0]),
                "ADD\t\t%s,\t\t%s,\t\t#%s" % (l[0],l[0],l[2]),
                ]
            ),
    pattern([is_reg, assign,'-', is_not0],
            lambda l: [
                "AND\t\t%s,\t\t%s,\t\t#0" % (l[0], l[0]),
                "ADD\t\t%s,\t\t%s,\t\t#-%s" % (l[0],l[0],l[3]),
                ]
            ),
    pattern([is_reg, assign,'-', is_reg],
            lambda l: [
                "NOT\t\t%s,\t\t%s,\t\t" % (l[0], l[3]),
                "ADD\t\t%s,\t\t%s,\t\t#1" % (l[0],l[0]),
                ]
            ),

    # 数据转移
    pattern(['Mem', '[', None, ']', assign, is_reg],
            lambda l: "ST\t\t%s,\t\t%s" % (l[5], l[2])),
    pattern(['Mem', '[', 'Mem', '[', None, ']]', assign, is_reg],
            lambda l: "STI\t\t%s,\t\t%s" % (l[7], l[4])),

    pattern(['Mem', '[', is_reg, '+', is_int, ']', assign, is_reg],
            lambda l: "STR\t\t%s,\t\t%s,\t\t#%s" % (l[7], l[2], l[4])),
    pattern(['Mem', '[', is_reg, '-', is_int, ']', assign, is_reg],
            lambda l: "STR\t\t%s,\t\t%s,\t\t#-%s" % (l[7], l[2], l[4])),
    pattern(['Mem', '[', is_reg, ']', assign, is_reg],
            lambda l: "STR\t\t%s,\t\t%s,\t\t#0" % (l[5], l[2])),

    pattern([is_reg, assign, 'Mem', '[', None, ']'],
            lambda l: "LD\t\t%s,\t\t%s" % (l[0], l[4])),
    pattern([is_reg, assign, 'Mem', '[', 'Mem', '[', None, ']]'],
            lambda l: "LDI\t\t%s,\t\t%s" % (l[0], l[6])),

    pattern([is_reg, assign, 'Mem', '[', is_reg, '+', is_int, ']'],
            lambda l: "LDR\t\t%s,\t\t%s,\t\t#%s" % (l[0], l[4], l[6])),
    pattern([is_reg, assign, 'Mem', '[', is_reg, '-', is_int, ']'],
            lambda l: "LDR\t\t%s,\t\t%s,\t\t#-%s" % (l[0], l[4], l[6])),
    pattern([is_reg, assign, 'Mem', '[', is_reg, ']'],
            lambda l: "LDR\t\t%s,\t\t%s,\t\t#0" % (l[0], l[4])),
    # 跳转
    pattern(['goto', None],
            lambda l: "BR\t\t%s" % (l[1])),
    pattern(['if', '(', '%', '>', '0', ')', 'goto', None],
            lambda l: "BRp\t\t%s" % (l[7])),
    pattern(['if', '(', '%', '<', '0', ')', 'goto', None],
            lambda l: "BRn\t\t%s" % (l[7])),
    pattern(['if', '(', '%', '>=', '0', ')', 'goto', None],
            lambda l: "BRzp\t%s" % (l[7])),
    pattern(['if', '(', '%', '<=', '0', ')', 'goto', None],
            lambda l: "BRnz\t%s" % (l[7])),
    pattern(['if', '(', '%', '==', '0', ')', 'goto', None],
            lambda l: "BRz\t\t%s" % (l[7])),
    pattern(['if', '(', '%', '!=', '0', ')', 'goto', None],
            lambda l: "BRnp\t%s" % (l[7])),
    pattern(['call', None],
            lambda l: "JSR\t\t%s" % (l[1])),
    pattern(['call', is_reg],
            lambda l: "JSRR\t%s" % (l[1])),
    pattern([None,'()'],
            lambda l: "JSR\t\t%s" % (l[0])),
    pattern([is_reg,'()'],
            lambda l: "JSRR\t%s" % (l[0])),
    pattern(['trap', is_hex],
            lambda l: "TRAP\t%s" % (l[1])),
    pattern(['HALT'],
            lambda l: "TRAP\tx25"),
    pattern(['GETC'],
            lambda l: "TRAP\tx20"),
    pattern(['OUT'],
            lambda l: "TRAP\tx21"),
    pattern(['IN'],
            lambda l: "TRAP\tx23"),
    pattern(['PUTS'],
            lambda l: "TRAP\tx22"),
    pattern(['PUTSP'],
            lambda l: "TRAP\tx24"),
    pattern(['do',None],DoWhile,
            lambda l: l[1]),
    pattern(['while','(','%','>','0',')'],EndDoWhile),
    pattern(['while','(','%','>=','0',')'],EndDoWhile),
    pattern(['while','(','%','<','0',')'],EndDoWhile),
    pattern(['while','(','%','<=','0',')'],EndDoWhile),
    pattern(['while','(','%','==','0',')'],EndDoWhile),
    pattern(['while','(','%','!=','0',')'],EndDoWhile),
    pattern([is_hex],
            lambda l : ".FILL\t"+l[0]),
    pattern([is_int],
            lambda l : ".FILL\t#"+l[0]),
    pattern(['-',is_int],
            lambda l : ".FILL\t#-"+l[0]),
    pattern(['at',is_hex,'{'],
            lambda l : ".ORIG\t"+l[1]),
    pattern(['}'],
            lambda l : ".END"),
    pattern(['return'],
            lambda l : "RET"),


]


class code:
    def __init__(self, line, label="",comment=[]):
        self.label = label
        self.line = line
        self.comment = comment

    def __call__(self, indent, cm_pos):
        cm = ""
        if self.comment != [] :
            cm = "\t; "
            for s in self.comment:
                cm += " " + s

        if(tablen(self.label) < indent):
            self.label += ' ' * (indent - tablen(self.label))
        instr_len = tablen(self.label) + tablen(self.line)
        if instr_len < cm_pos:
            cm = " "*(cm_pos - instr_len) + cm
        return self.label + self.line + cm


def lexer(file):
    tokens = []
    for l in file:
        sp0 = re.split("//", l)[0]  # 去注释
        sp1 = re.split("[ \t\n]", sp0)
        sp2 = []
        for s in sp1:
            sp2 += re.split("([!:=\+\-\*/\(\)\[\]#@~&\|;.><\?{}]+)", s)
        sp2 = list(filter(('').__ne__, sp2))
        tokens.append(sp2)
    return tokens


def parser(tokens):
    asm = []
    indent = 8
    max_instr_len = 10
    last_label = None

    for i, line in enumerate(tokens):
        label = ''
        if len(line) >= 2 and line[1] == ":":
            if last_label:
                asm += [code("", last_label)]
                last_label = None
            while(len(line[0]) > indent):
                indent += 4
            label = line[0]
            line = line[2:]
        c = None
        for p in patterns:
            if line in p:
                if p.labelgen and label == "":
                    label = p.labelgen(line)
                elif p.labelgen and label != "":
                    print("invalid label at", i)
                if last_label:
                    label = last_label
                    last_label = None
                instr = p(line)
                if type(instr) is list:
                    c = [code(instr[0], label)]
                    for i in instr[1:-1]:
                        c += [code(i)]
                    c += [code(instr[-1],"",line)]
                    max_instr_len = max([tablen(i) for i in instr] + [max_instr_len])
                else:
                    c = [code(instr, label, line)]
                    max_instr_len = max(max_instr_len, tablen(instr))
                break
        if c:
            asm += c
        elif line == []:
            if label:
                last_label = label
        else:
            print("parttern not found at ", i)
    return asm, indent, max_instr_len


if __name__ == "__main__":
    arguments = docopt(__doc__)
    arg_file = arguments['<inputfile>']
    arg_output = arguments['<output>']
    if arg_file:
        file = open(arg_file)
        asm, indent, max_instr_len = parser(lexer(file))
        if not arg_output:
            arg_output = "a.out.asm"
        out = open(arg_output, "w")
        for c in asm:
            out.write(c(indent,max_instr_len + indent + 1) + '\n')
