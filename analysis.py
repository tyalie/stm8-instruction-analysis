#!/usr/bin/env python3
from collections import defaultdict
import json

DATA_FILE = "./out.json"

def util_print_rows(statement: str, values: list):
    print(f"{statement}:", end="")
    for i, m in enumerate(values):
        if i % 9 == 0:
            print("\n    ", end="")
        print(f"{m}, ", end="")
    print()

with open(DATA_FILE, "r") as fp:
  opcodes = json.load(fp)

for opcode in opcodes:
    opcode["operands"] = [op.removeprefix('ST8_') for op in opcode["operands"]]

# put data into multiset as asm name doesn't change over similar opcodes
mset_asm = defaultdict(list)
opcode_set = dict()

for opcode in opcodes:
    _o = {
        "mod": opcode["opcode"] >> 8,
        "code": opcode["opcode"] & 0xFF,
        "operands": opcode["operands"]
    }

    mset_asm[opcode["name"]].append(_o)
    opcode_set[opcode["opcode"]] = opcode

# Distribution of amount of 'sub'-opcodes per mnemonic
dist_sub_amount = defaultdict(list)
for k in mset_asm:
    dist_sub_amount[len(mset_asm[k])].append(k)

dist_sub_amount = {k:dist_sub_amount[k] for k in sorted(dist_sub_amount)}

def print_distribution_opcodes_per_mnemonic():
    print("================")
    print("Distribution of how many different opcodes a single asm mnemonic has")
    print()
    for k,vs in dist_sub_amount.items():
        util_print_rows(f"{k}", vs)
    print()

print_distribution_opcodes_per_mnemonic()


# multiset by operands type
mset_by_operands = defaultdict(list)
mset_by_arguments = defaultdict(list)

# these are the operands that are used to specify a qualification of
# the opcode, but that do not represent any arguments of it.
# e.g. and opcode with operand REG_A will act upon REG_A, but does not
# have it as an argument, but this property is encoded in the opcode
arg_operands_ignore_list = [
    "END","BIT_0","BIT_1","BIT_2","BIT_3", "BIT_4",
    "BIT_5","BIT_6","BIT_7","REG_CC","REG_A","REG_X",
    "REG_Y","REG_SP","REG_XL","REG_XH","REG_YL",
    "REG_YH","INDX","INDY"
]

for opcode in opcodes:
    k = ",".join(opcode["operands"])
    ik = ",".join(op for op in opcode["operands"] if op not in arg_operands_ignore_list)
    mset_by_operands[k].append(opcode)
    mset_by_arguments[ik].append(opcode)

def print_argument_tuples():
    print("================")
    print(f"There are {len(mset_by_arguments)} different opcode argument tuples")

    for tup in mset_by_arguments:
        print("   -", ", ".join(tup.split(",")))

    print()
print_argument_tuples()

# multiset by modifier
mset_by_modifier = defaultdict(list)
for name, vs in mset_asm.items():
    for v in vs:
        mset_by_modifier[v["mod"]].append({"name": name, **v})

mset_by_modifier = {k: mset_by_modifier[k] for k in sorted(mset_by_modifier)}


# check whether modifiers are actually consistent
op_map_mod_90 = {
    "INDY": "INDX",
    "REG_Y": "REG_X",
    "REG_YL": "REG_XL",
    "REG_YH": "REG_XH",
    "SHORTOFF_Y": "SHORTOFF_X",
    "LONGOFF_Y": "LONGOFF_X",
    "EXTOFF_Y": "EXTOFF_X",
    "SHORTPTRW_Y": "SHORTPTRW_X",
    "LONGPTRW_Y": "LONGPTRW_X",
    "LONGPTRE_Y": "LONGPTRE_X"
}
for k, v in dict(**op_map_mod_90).items():  # add inversions too
    op_map_mod_90[v] = k

def check_0x90_mod():
    def replace_operands_Y_to_X(operands: list[str]):
        return [(op_map_mod_90[op] if op in op_map_mod_90 else op) for op in operands]

    print("================")
    print("Checking whether opcodes with modifier 0x90 just replace X access with access to Y and v.v.")
    print("Note that warning with BCCM and BCPL are expected as these are two bit handling instructions\n")
    count = 0
    for opcodeY in mset_by_modifier[0x90]:
        opcodeX = opcode_set[opcodeY["code"]]

        operands_Y = opcodeY["operands"]
        operands_X = opcodeX["operands"]
        
        if opcodeY["name"] != opcodeX["name"]:
            print(f"WARN: mnemonic mismatch. Expected {opcodeY['name']} / Got {opcodeX['name']} [code: 0x{opcodeY['code']:X}]")
            continue

        _operands_X = replace_operands_Y_to_X(operands_Y)
        if _operands_X != operands_X:
            print(f"WARN: Difference between opcode 0x{opcodeY['code']:02X} using modifier 0x90 - (mnemonic: {opcodeY['name']})")
            print(f"   X: {operands_X}")
            print(f"   Y: {operands_Y}")
        else:
            count += 1

    print(f"\nFinished with {count}/{len(mset_by_modifier[0x90])} fitting the rule")


# Get a list of opcode offset between two mnemonic
# This can finding instructions that have a very similar set of opcodes
# where just the opcode has a static offset between two instructions
def compare_mnemonic_opcode_offsets(inst_a: str, inst_b: str) -> list[int]:
    def calc_code(opcode):
        return (opcode["mod"] << 8) + opcode["code"]

    if (v := len(mset_asm[inst_a]) - len(mset_asm[inst_b])) != 0:
        print(f"WARN: {inst_a} has {'more' if v > 0 else 'less'} opcodes than {inst_b}")

    l = list()
    for ia, ib in zip(mset_asm[inst_a], mset_asm[inst_b]):
        if ia["operands"] != ib["operands"]:
            print(f"WARN: {calc_code(ia):X} and {calc_code(ib):X} have different operands - skipping")
            continue
        l.append(calc_code(ia) - calc_code(ib))
    return l


# find similar mnemonics by their opcode offset and arguments
def comp(mnemonic: str, doprint: bool = False) -> list:
    global print
    assert mnemonic in mset_asm
    required = len(mset_asm[mnemonic])
    found = list()

    o_print = print
    def print(*args, **kwargs):
        ...
    
    if doprint is False:
        mprint = print
    else:
        mprint = o_print

    for m in mset_asm:
        if len((v := compare_mnemonic_opcode_offsets(mnemonic, m))) == required:
            if len(mset_asm[m]) != required or len(set(v)) != 1:
                mprint("X ", end="")
            else:
                mprint("  ", end="")
                found.append(m)
            mprint(f"{m} vs. {mnemonic}: {len(v)} {v}")
    print = o_print
    return found

def find_instr_groups() -> list[list[str]]:
    groups = []
    unprocessed = set(mset_asm)

    while len(unprocessed) > 0:
        mem = unprocessed.pop()
        groups.append(comp(mem))
        unprocessed -= set(groups[-1])

    return groups

def print_instr_groups():
    print("================")
    print("The following mnemonic groups exist. The criterias have been:")
    print("  - same amount of opcodes / argument types per mnemonic")
    print("  - for each opcode & argument from a mnemonic there is a matching pair\n"
          "    in the other mnemonic where the opcode just has a constant offset")
    print()

    unique = []

    i = 0
    for group in find_instr_groups():
        if len(group) == 1:
            unique.append(group[0])
            continue
        i += 1
        util_print_rows(f"Group {i}", group)
    print()
    util_print_rows("unique", unique)

print_instr_groups()
