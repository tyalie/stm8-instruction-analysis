#!/usr/bin/env python3

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional
from tree_sitter import Language, Node, Parser
import logging
import argparse

logger = logging.basicConfig(level=logging.DEBUG)

PARSER_LIB = Path("build/c-parser.so")

STRUCT_QUERY = """
(declaration
    declarator: (_
        declarator: (array_declarator 
            declarator: (identifier) @s
        )
    ) 
    (#eq? @s "{struct_name}")
) @declaration
"""

ELEMENT_QUERY = """
(initializer_list 
    (string_literal)
    (initializer_list (identifier)*) 
    (number_literal)
) @element
"""

@dataclass
class OpCode:
    name: str
    opcode: int
    operands: list[str]

    def __str__(self) -> str:
        return f" {self.opcode: 4X}    {self.name} {', '.join(self.operands)}"

def get_args():
    args = argparse.ArgumentParser(description="Parse a C struct into a further usable more easily accessible data format")
    args.add_argument("-s", "--source", help="Source C file to parse", required=True)
    args.add_argument("-n", "--name", help="Name of struct to extract", required=True)
    args.add_argument("-o", "--output", help="Output file name [json]", required=False)
    args.add_argument("--library", help="TreeSitter library for C", default=PARSER_LIB)
    return args.parse_args()

def load_language_library(lib_location: Path | str) -> Language:
    lib_location = str(lib_location)

    logging.info(f"Loading parser library ({PARSER_LIB})")
    try:
        lang = Language(lib_location, "c")
        logging.debug(f"Successfully loaded parser library")
        return lang
    except OSError:
        logging.warning(f"library not found - building")
        try:
            Language.build_library(lib_location, ["tree-sitter-c"])
            logging.info("Finished building the library")
            return load_language_library(lib_location)
        except FileNotFoundError:
            logging.error(
                "Could not find tree-sitter definitions for C. Please download them with\n"
                "    git clone --depth=1 https://github.com/tree-sitter/tree-sitter-c tree-sitter-c\n"
            )
            exit(1)

def save_to_pickle(opcodes: list[OpCode], output: str | Path):
    logging.info("Saving opcodes as pickle file")
    import pickle
    with open(output, "wb") as fp:
        pickle.dump(opcodes, fp)

def save_to_json(opcodes: list[OpCode], output: str | Path):
    logging.info("Saving opcodes as json file")
    import json
    def _custom_ser(o):
        if isinstance(o, OpCode):
            return o.__dict__
        else:
            return o

    with open(output, "w") as fp:
        json.dump(opcodes, fp, default=_custom_ser, indent=2)

def print_to_stdout(opcodes: list[OpCode]):
    logging.info("Printing opcodes to stdout")
    for opcode in opcodes:
        print(opcode)

def main(C_LANG: Language, source: Path | str, name: str, output: Optional[str | Path]):
    source = Path(source)

    assert source.is_file(), "Please specify correct C file as source"

    logging.info(f"Parsing C file ({source})")

    parser = Parser()
    parser.set_language(C_LANG)

    with source.open("rb") as fp:
        tree = parser.parse(fp.read())

    # find the struct that we wanna extract
    query = C_LANG.query(STRUCT_QUERY.format(struct_name=name))
    captured = [a[0] for a in query.captures(tree.root_node) if a[1] == "declaration"]

    logging.debug(f"structs: Found matches: {captured}")

    assert len(captured) == 1, f"There have been multiple (or none) occurences of '{name}' been found (#captured = {len(captured)})"

    struct_node = captured[0]

    # find all elements in it
    query = C_LANG.query(ELEMENT_QUERY)
    captured = list(map(lambda v: v[0], query.captures(struct_node)))

    logging.debug(f"struct elements: Found #{len(captured)} matches")
    assert len(captured) > 0, "Found no matching elements inside the struct."

    opcodes: list[OpCode] = []

    def operands_parser(operands_list: Node) -> Iterator[str]:
        for id in operands_list.named_children:
            yield id.text.decode("ascii")

    for element in captured:
        opcodes.append(OpCode(
            name=element.named_children[0].named_children[0].text.decode("ascii"),
            operands=list(operands_parser(element.named_children[1])),
            opcode=int(element.named_children[2].text, 0),
        ))

    logging.debug("Parsing complete")

    if output is not None:
        save_to_json(opcodes, output)
    else:
        print_to_stdout(opcodes)

if __name__ == "__main__":
    args = get_args()
    C_LANG = load_language_library(args.library)
    main(C_LANG, args.source, args.name, args.output)
