import os
import re
import sys

from btree_tokens import TokenType, Token
from btree_analyser import Analyser

# line = [[indent] [guardableTask] [comment]]
# guardableTask = [guard [...]] task
# guard = '(' task ')'
# task = name [attr:value [...]] | subtreeRef

source = '''import setCurrentBehaviorState:"com.rager.behavior.blah"
import hooplah:"com.rager.behavior.atomic"
import setBehaviorStates:"com.rager.behavior.blahblah"

root
\trandomSelector
\t\tsetBehaviorState behavior:"IDLING"
\t\tsetBehaviorState behavior:"DANCING"
\t\tsetBehaviorState behavior:"SOCIALIZING"
\t# run the currently selected behavior
\tdynamicGuardSelector
\t\t(isCurrentBehavior? behavior:"IDLING") sequence
\t\t\tinclude subtree:"behavior/idle.btree"
'''

err_source = '''import setCurrentBehaviorState:"com.rager.behavior.blah"
import hooplah:"com.rager.behavior.atomic"

root
\trandomSelector
\t\tsetBehaviorState behavior:"IDLING" crump:
\t\tsetBehaviorState behavior:"DANCING"
\t\tsetBehaviorState behavior:"SOCIALIZING" # err
\t# run the currently selected behavior
\tdynamicGuardSelector
\t\t(isCurrentBehavior? :foo behavior:"IDLING") sequence
\t\t\tinclude subtree:"behavior/idle.btree"
'''

class Tokenizer():

    keywords = {
        "import": TokenType.IMPORT,
    }

    identifier_pattern = re.compile(r"[a-zA-Z_][a-zA-Z\d_$\?]*")
    
    def __init__(self, source: str, filename:str="source.btree"):
        self.source = source
        self.filename = filename
        self.start = 0
        self.current = 0
        self.line_num = 0
        self.tokens = []
        self.indent_stack = [0]
        self.line = None
        self.lines = None
        self.load_token_handler()

    def error(self, msg: str):
        print(self.filename, ":",
              self.line_num, ":",
              self.start, ":",
              " error: ",
              msg,
              sep='')

    def load_token_handler(self):
        "Initialize dictionary of characters to token_handlers."
        self.token_handler = {
            ':' : lambda: self.add_token(TokenType.COLON),
            '(' : lambda: self.add_token(TokenType.OPAREN),
            ')' : lambda: self.add_token(TokenType.CPAREN),
            '#' : self.scan_comment,
            '"' : self.scan_string,
            ' ' : self.scan_whitespace,
            '\t': self.scan_whitespace
        }
        ident_start = "abcdefghijklmnopqrstuvwxyz"
        ident_start += ident_start.upper() + "_"
        for char in ident_start:
            self.token_handler[char] = self.scan_ident_or_keyword
        num_start = "-0123456789"
        for char in num_start:
            pass # TODO add number scanner

    def add_token(self, token_type: TokenType, literal=None):
        "Add a token to the list of tokens."
        token = Token(token_type,
                      self.line[self.start:self.current],
                      literal,
                      self.line_num,
                      self.start)
        self.tokens.append(token)
        
    def scan_comment(self):
        "Ignore comment lines."
        self.next_line()

    def scan_whitespace(self):
        "Ignore whitespace."
        pass

    def get_indent(line: str) -> int:
        "Return the number of indentations at the beginning of a line."
        m = re.match("\t*", line)
        return len(m.group(0))

    def scan_string(self):
        "Consume a string and produce a string token."
        while self.peek() != '"' and self.has_next():
            self.advance();
        if not self.has_next():
            self.error("unterminated string.")
            return
        self.advance()
        string = self.line[self.start+1:self.current-1]
        self.add_token(TokenType.STRING, string)

    def scan_ident_or_keyword(self):
        "Consume an identifier/keyword and produce appropriate token."
        pat = Tokenizer.identifier_pattern
        m = pat.match(self.line[self.start:])
        if not m:
            return # TODO handle identifer error
        ident = m.group(0)
        self.current += len(ident) - 1
        if ident in Tokenizer.keywords:
            self.add_token(Tokenizer.keywords[ident])
        else:
            self.add_token(TokenType.IDENTIFIER, ident)

    def scan_indent(self):
        "Scan beginning of current line for indent level."
        indent = Tokenizer.get_indent(self.line)
        self.current += indent
        if indent > self.indent_stack[-1]:
            self.add_token(TokenType.INDENT)
            self.indent_stack.append(indent)
        elif indent < self.indent_stack[-1]:
            while indent < self.indent_stack[-1]:
                self.add_token(TokenType.DEDENT)
                self.indent_stack.pop()
            if indent != self.indent_stack[-1]:
                self.error("unexpected indentation level % (expected %)." % (indent, self.indent_stack[-1]))
            
            
    def advance(self) -> str:
        "Consume and return the next character in current line."
        char = self.line[self.current]
        self.current += 1
        return char

    def peek(self) -> str:
        "Returns the next character without consuming it."
        if not self.has_next():
            return '\0'
        return self.line[self.current]

    def next_line(self) -> bool:
        "Advance to next line. return False if there are no more lines."
        line_num, line = next(self.lines, (None, None))
        #self.line_num, self.line = next(self.lines, (None, None))
        if line_num is None:
            self.at_end = True
            return False
        self.line_num = line_num
        self.line = line
        self.current = 0
        self.scan_indent()
        return True

    def has_next(self) -> bool:
        "Returns true if there are still characters to parse on line."
        return self.current < len(self.line)

    def tokenize(self) -> list:
        "Tokenize a provided btree source and returns list of tokens."
        indent_stack = [0]
        tokens = []
        self.lines = enumerate(self.source.split("\n"), 1)
        self.next_line()
        self.at_end = False
        while not self.at_end:
            if self.has_next():
                self.start = self.current
                char = self.advance()
                if char in self.token_handler:
                    self.token_handler[char]()
                else:
                    self.error(f"invalid character {char} encountered.")
            else:
                self.next_line()
        self.add_token(TokenType.EOF)
        return self.tokens


class BTreeParseException(Exception):
    pass


class Parser():

    def __init__(self, filename:str=None):
        self.filename = filename

    def match(self, *types: Token) -> bool:
        "Return True if current token matches one of provided types."
        for t in types:
            if t == self.peek().tokenType:
                return True
        return False

    def match2(self, *types: Token) -> bool:
        "Return True if next token matches one of provided types."
        for t in types:
            if t == self.peek2().tokenType:
                return True
        return False

    def advance(self) -> Token:
        "Consume current token and advance to the next one."
        if not self.at_end():
            self.current += 1
        return self.previous()

    def peek(self) -> Token:
        "Return the next token without consuming it."
        return self.tokens[self.current]

    def peek2(self) -> Token:
        "Return the second next token without consuming it."
        if self.current + 1 >= len(self.tokens):
            return self.tokens[self.current]
        return self.tokens[self.current + 1]

    def previous(self) -> Token:
        "Return the previous token."
        return self.tokens[self.current - 1]

    def at_end(self) -> bool:
        "Return True if we have reached the end of file token."
        return self.peek().tokenType == TokenType.EOF

    def error(self, msg: str, token=None):
        "Format and print error message, then throw a parse exception."
        token = self.peek() if token is None else token
        print(self.filename, ":",
              token.line, ":",
              token.column, ":",
              " error: ",
              msg,
              sep='')
        raise BTreeParseException()

    def next_line_token(self) -> Token:
        "Advance until a token is reached from the next line."
        token = self.peek()
        line = token.line
        while line == token.line:
            token = self.advance()
            if token.tokenType == TokenType.EOF:
                break
        return token

    def parse_import(self) -> tuple:
        "Parse and return an (import-name, class-path) token tuple."
        if not self.match(TokenType.IMPORT):
            self.error("expected import statement not found!")
        import_tok = self.advance()
        if not self.match(TokenType.IDENTIFIER):
            self.error("expected identifier not found!")
        ident_tok = self.advance()
        if not self.match(TokenType.COLON):
            self.error('expected separator ":" not found!')
        self.advance()
        if not self.match(TokenType.STRING):
            self.error('expected string not found!')
        str_tok = self.advance()
        return (ident_tok, str_tok)

    def add_import(self, name:Token, class_path:Token):
        "Add an import name and class path to list of imports."
        if name.literal in self.imports:
            self.error(f"redefinition of {name.literal}", name)
        self.imports[name.literal] = class_path.literal

    def parse_indent_level(self) -> bool:
        "Return True if indentation level was increased."
        if self.match(TokenType.DEDENT):
            while self.match(TokenType.DEDENT):
                self.indent_level -= 1
                self.advance()
                if self.parent and self.parent["parent"]:
                    self.parent = self.parent["parent"]
        if self.match(TokenType.INDENT):
            self.indent_level += 1
            self.advance()
            if self.last_task:
                self.parent = self.last_task
            return True
        return False

    def parse_guard(self) -> dict:
        "Parse and return a Guard."
        token = self.advance()
        if token.tokenType != TokenType.OPAREN:
            self.error("expected opening parenthesis!")
        task = self.parse_task(is_guard=True)
        token = self.advance()
        if token.tokenType != TokenType.CPAREN:
            self.error("expected closing parenthesis!")
        return task

    def parse_guardable_task(self) -> dict:
        "Parse and return a task with 0 or more guards."
        guards = []
        while self.match(TokenType.OPAREN):
            guards.append(self.parse_guard())
        task = self.parse_task()
        [self.add_guard_to_task(task, guard) for guard in guards]
        return task
        

    def parse_attr_value_pair(self) -> tuple:
        "Parse and return an (attr, value) token pair."
        attr = self.advance()
        if attr.tokenType != TokenType.IDENTIFIER:
            self.error("expected identifier!")
        colon = self.advance()
        if colon.tokenType != TokenType.COLON:
            self.error("expected colon!")
        value = self.advance()
        if value.tokenType != TokenType.STRING:
            self.error("expected string!")
        return (attr, value)

    def create_task(self, token:Token) -> dict:
        "Create a new task given a token."
        task = { "name": token.literal,
                 "guards": [],
                 "token": token,
                 "parent": self.parent,
                 "children": [],
                 "attributes": {} }
        self.last_task = task
        return task

    def add_attr_to_task(self, task:dict, attr:Token, val:Token):
        "add ATTR to task with val VAL."
        if attr.literal in task["attributes"]:
            self.error(f"duplicate attribute {attr.literal}")
        task["attributes"][attr.literal] = val.literal

    def add_guard_to_task(self, task:dict, guard:dict):
        "Add a guard to given task."
        task["guards"].append(guard)

    def set_task_parent(self, task:dict, is_guard=False):
        "Set the parent of the task then add task to parent's children."
        if self.parent is None:
            self.parent = task
        else:
            task["parent"] = self.parent
            if not is_guard:
                self.parent["children"].append(task)


    def parse_task(self, is_guard=False) -> dict:
        "Parse and return a task."
        # TODO subtree ref
        attrs = []
        name_token = self.advance()
        if name_token.tokenType != TokenType.IDENTIFIER:
            self.error("expected task identifier name not found!")
            print("got ", str(name_token.tokenType))
        task = self.create_task(name_token)
        while (self.match(TokenType.IDENTIFIER) and
               self.match2(TokenType.COLON)):
            attr, val = self.parse_attr_value_pair()
            self.add_attr_to_task(task, attr, val)
        self.set_task_parent(task, is_guard)
        return task

    def parse(self, tokens: list):
        "Parse a list of btree tokens."
        self.tokens = tokens
        self.current = 0
        self.indent_level = 0
        self.imports = {}
        self.parent = None
        self.last_task = None

        token = self.peek()
        while token.tokenType != TokenType.EOF:
            try:
                if token.tokenType == TokenType.IMPORT:
                    name, class_path = self.parse_import()
                    self.add_import(name, class_path)
                    #print("parsed import!")
                elif (token.tokenType == TokenType.INDENT or
                      token.tokenType == TokenType.DEDENT):
                    self.parse_indent_level()
                else:
                    self.parse_guardable_task()
                    #print("parsed task!")
                token = self.peek()
            except BTreeParseException:
                token = self.next_line_token()




def print_tree(node: dict, indent=0, print_attr=True):
    "Print a behavior tree."
    print(" " * indent, end="")
    print(f'{node["name"]} ', end="")
    if print_attr:
        for attr in node["attributes"]:
            print(f"{attr}:{node['attributes'][attr]}", end="")
    print()
    for child in node["children"]:
        print_tree(child, indent + 2, print_attr)

def main(source: str):
    "Parse SOURCE."
    tokens = Tokenizer(source).tokenize()
    parser = Parser("file.btree")
    parser.parse(tokens)
    #print_tree(parser.parent)
    analyser = Analyser("file.btree", "unknown")
    analyser.analyse(parser.parent, parser.imports)
    #return parser
