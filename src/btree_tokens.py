from enum import Enum, auto
try:
    from sys import intern
except ImportError:
    pass

# Tokens

class TokenType(Enum):
    # character tokens
    OPAREN = auto()
    CPAREN = auto()
    COLON = auto()
    INDENT = auto()
    DEDENT = auto()

    # Literals
    IDENTIFIER = auto()
    STRING = auto()

    # Keywords
    IMPORT = auto()
    INCLUDE = auto()
    ROOT = auto()

    # built-in composites
    SELECTOR = auto()
    RANDOMSELECTOR = auto()
    SEQUENCE = auto()
    RANDOMSEQUENCE = auto()
    PARALLEL = auto()
    DYNAMICGUARDSELECTOR = auto()

    # built-in decorators

    ALWAYSFAIL = auto()
    ALWAYSSUCCEED = auto()
    INVERT = auto()
    REPEAT = auto()
    SEMAPHOREGUARD = auto()
    UNTILFAIL = auto()
    UNTILSUCCESS = auto()

    EOF = auto()
    

class Token():
    def __init__(self, tokenType: TokenType, lexeme: str,
                 literal, line: int, column: int):
        self.tokenType = tokenType
        self.lexeme = lexeme
        self.literal = literal
        self.line = line
        self.column = column

    def __str__(self):
        return ("Token" +
                " " +
                str(self.tokenType) +
                " " + 
                self.lexeme +
                " " + 
                (self.literal if self.literal else ""))
