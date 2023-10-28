import io

#
# some utility functions
#

def ISEOL(c: str): return c == '\r' or c== '\n'
def ISWS(c: str): return c == ' ' or c == '\t' or ISEOL(c)
def ISDIGIT(c: str): return c >= '0' and c <= '9'
def ISLOWER(c: str): return c >= 'a' and c <= 'z'
def ISUPPER(c: str): return c >= 'A' and c <= 'Z'
def ISALPHA(c: str): return ISLOWER(c) or ISUPPER(c)
def ISALNUM(c: str): return ISALPHA(c) or ISDIGIT(c)

# this is a little helper function which takes a function
# and returns the boolean inverse, i.e. "not" of the input
# function. can be used to implement "read_until" from a "read_while"
# condition.
def ISNOT(fn: callable):
    def not_fn(*args):
        return not fn(*args)
    return not_fn

class Token(object):

    #
    # T_* constants are integer values uniquely identified the type of token.
    # You add more, each with a unique integer, as needed for new kinds of tokens.
    #
    T_ID = 1
    T_INT = 2
    T_PUNCT = 3

    @classmethod
    def Punct(cls, text: str): return Token(Token.T_PUNCT, text)

    def __init__(self, token_id: int, text: str, raw_text=None, value=None):
        self.token_id = token_id
        self.text = text
        self.raw_text = raw_text or text
        self.value = value

    def __repr__(self):
        return f"<T ({self.token_id}) value={self.value} text={self.text}>"


class LexerReader(object):    
    def __init__(self, input: io.TextIOWrapper):
        if type(input) is io.TextIOWrapper:
            self._s = input
        else:
            raise ValueError(f"input must be of type io.TextIOWrapper, not {type(input).__name__}")
        
    def is_eos(self):
        return self.peek() == None
        
    def tell(self):
        return self._s.tell()
    
    def peek(self, offset=0, count=1):
        """Reads a character without changing stream position"""
        pos = self._s.tell()
        self._s.seek(pos+offset, io.SEEK_SET)
        c = self._s.read(count)
        self._s.seek(pos, io.SEEK_SET)
        return c
    
    def skip(self, count=1):
        self._s.read(count)

    def read(self, cnt=1):
        """Reads up to cnt characters"""
        return self._s.read(cnt)
    
    def read_while(self, check_fn:callable):
        s = ""
        while True:
            pos = self._s.tell()
            c = self._s.read(1)
            if c is None or not check_fn(c):
                self._s.seek(pos)
                break
            s += c
        return s
        
class Lexer(object):

    def __init__(self, input: str | io.BufferedReader, line_comment='//'):
        """Intiialize the lexer with an input string or stream. Can specify some behaviors such
        as line comment sequence, and whether to return a comment as a token.
        """
        self._ls = LexerReader(input)
        self._line_comment = line_comment

    def next(self):

        # skip initial whitespace and comments
        
        while True:

            start_pos = self._ls.tell()
        
            # skip while ISWS returns True for subsequent
            self._ls.read_while(ISWS)
        
            # check for line comment, does the next characters match the line comment sequence?
            if self._line_comment and self._ls.peek(0, len(self._line_comment)) == self._line_comment:
                self._ls.read_while(ISNOT(ISEOL))
        
            if start_pos == self._ls.tell():
                break # we didn't read any whitespace or comments

        # done skipping inconsequential text
        if self._ls.is_eos():
            return None # we are done

        # now start matching token types

        # let's peek the next two characters - the second character
        # helps us detect different token types that happen to begin
        # with the same first character, e.g., 0x vs. 0b
        c0 = self._ls.peek(0)
        c1 = self._ls.peek(1)

        # identifier? [_azAZ][_azAZ09]*
        if ISALPHA(c0) or c0 == '_':
            id_text = self._ls.read_while(ISALNUM)
            return Token(Token.T_ID, id_text)
        
        if c0 in ['@','(', ')', '[', ']', '{', '}']: return Token.Punct(self._ls.read(1))

        
        return None


                


