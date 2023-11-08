#
# Simple driver to illustrate an example lexer written in python
# 

import sys
import io
from lexer import Lexer

def lex_file(file_name: str):
    with open(file_name, 'r') as f:
        lexer = Lexer(f)
        while (token := lexer.next()) is not None:
            print(token)

if __name__ == '__main__':
    import argparse
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-I", "--interactive", action="store_true", help="Force interactive mode.")
    arg_parser.add_argument("FILES", nargs='*', help="input files")
    args = arg_parser.parse_args()

    for file_name in args.FILES:
        lex_file(file_name)

    if len(args.FILES) > 0 and not args.interactive:
        sys.exit(0)

    print("Entering REPL. Ctrl-D to exit.")
    while(True):
        try:
            line = input("user> ")
            line_ss = io.StringIO(line)
            lex_file(line_ss)
        except EOFError:
            break
    print("Good-bye.")