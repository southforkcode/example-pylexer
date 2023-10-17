#
# Simple driver to illustrate an example lexer written in python
# 

from lexer import Lexer

def lex_file(file_name: str):
    with open(file_name, 'rb') as f:
        lexer = Lexer(f)
        while (token := lexer.next()) is not None:
            print(token)

if __name__ == '__main__':
    import argparse
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("FILES", nargs='*', help="input files")
    
    args = arg_parser.parse_args()

    for file_name in args.FILES:
        lex_file(file_name)