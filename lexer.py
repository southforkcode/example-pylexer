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
def ISBIN(c: str): return c == '0' or c == '1'
def ISHEX(c: str): return ISDIGIT(c) or (c >= 'a' and c <= 'f') or (c >= 'A' and c <= 'F')
def ISOCT(c: str): return c >= '0' and c <= '7'

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
    T_FLOAT = 3
    T_PUNCT = 10

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
    
    def rewind(self, count=1):
        self.move(-count)

    def move(self, count=1):
        self._s.seek(self._s.tell()+count, io.SEEK_SET)
    
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

        # now start matching token types

        # let's peek the next two characters - the second character
        # helps us detect different token types that happen to begin
        # with the same first character, e.g., 0x vs. 0b
        c0 = self._ls.peek(0)
        if c0 == '': return None # done

        c1 = self._ls.peek(1)

        # identifier? [_azAZ][_azAZ09]*
        if ISALPHA(c0) or c0 == '_':
            id_text = self._ls.read_while(ISALNUM)
            return Token(Token.T_ID, id_text)
        
        # numbers are fun... and messy
        # use helpers to make things clean, e.g., "read_hex"
        if c0 == '0' and (c1 == 'x' or c1 == 'X'): return self.read_hex(self._ls.read(2))
        if c0 == '0' and (c1 == 'b' or c1 == 'B'): return self.read_bin(self._ls.read(2))
        # if initial zero and a decimal point does not follow,
        # then it MUST be octal, e.g., 07
        if c0 == '0' and c1 != '.': return self.read_oct(self._ls.read(1))

        # now decimal integers and floats, again we use helpers
        # because an integer value can escalate to a float
        if ISDIGIT(c0): return self.read_num()

        # check multi-char symbols
        if c0 == '=' and c1 == '=': return Token.Punct(self._ls.read(2))
        if c0 == '!' and c1 == '=': return Token.Punct(self._ls.read(2))
        if c0 == '>' and c1 == '=': return Token.Punct(self._ls.read(2))
        if c0 == '<' and c1 == '=': return Token.Punct(self._ls.read(2))

        # check single char symboles
        if c0 in ['(', ')', '[', ']', '{', '}']: return Token.Punct(self._ls.read(1))
        if c0 in ['^', '%', '-', '+', '/', '*']: return Token.Punct(self._ls.read(1))
        if c0 in ['&', '|', '!', '<', '>']: return Token.Punct(self._ls.read(1))
        if c0 in ['@', ':', '=']: return Token.Punct(self._ls.read(1))

        # we reached a character that doesn't make sense to start any token
        if str.isprintable(c0):
            raise ValueError(f"unexpected character: '{c0}' ({ord(c0)})")
        else:
            raise ValueError(f"unexpected character: ({ord(c0)})")
            
    def read_hex(self, prefix: str) -> Token:
        hval = self._ls.read_while(ISHEX)
        if len(hval) == 0: raise ValueError("hex literal invalid")
        return Token(Token.T_INT, hval, prefix+hval, int(hval, 16))
    
    def read_bin(self, prefix: str) -> Token:
        bval = self._ls.read_while(ISBIN)
        if len(bval) == 0: raise ValueError("binary literal invalid")
        return Token(Token.T_INT, bval, prefix+bval, int(bval, 2))
    
    def read_oct(self, prefix: str) -> Token:
        oval = self._ls.read_while(ISOCT)
        # we don't check length, because 0, the prefix, is valid by itself!
        return Token(Token.T_INT, prefix+oval, prefix+oval, int(prefix+oval, 8))
    
    def read_num(self) -> Token:
        ival = self._ls.read_while(ISDIGIT)
        # we are guaranteed to pass the following check, so commented out
        # but left in code so that you can convince yourself of this fact.
        #if len(ival) == 0: raise ValueError("integer literal invalid")
        
        # check if we are a float... this can happen a couple of ways
        c = self._ls.peek(0)
        if c == '.': return self.read_float(ival + self._ls.read(1))
        if c == 'e' or c == 'E': return self.read_exp(ival + self._ls.read(1))

        # otherwise we must just be an integer
        return Token(Token.T_INT, ival, ival, int(ival, 10))
    
    def read_float(self, prefix:str) -> Token:
        dval = self._ls.read_while(ISDIGIT)
        # actually don't care if there isn't a digit after the decimal point
        # but if you did care, you could assert that here by uncommenting the
        # following line:
        # if len(dval) == 0: raise ValueError("float literal invalid - nothing after the decimal")
        
        # check for exponent
        c = self._ls.peek(0)
        if c == 'e' or c== 'E': return self.read_exp(prefix + dval + self._ls.read(1))

        # otherwise we are a float without an exponent clause
        return Token(Token.T_FLOAT, prefix+dval, prefix+dval, float(prefix+dval))
    
    def read_exp(self, prefix:str) -> Token:
        # first check for - or + following the "e"
        c = self._ls.peek(0)
        if c == '-' or c == '+': exp = self._ls.read(1)
        else: exp = ""
        # now read the exponent
        eval = self._ls.read_while(ISDIGIT)
        # we do require digits here
        if len(eval) == 0: raise ValueError("invalid exponent in float literal")
        # otherwise, we are good, and... done!
        return Token(Token.T_FLOAT, prefix+exp+eval, prefix+exp+eval, float(prefix+exp+eval))
        


                


