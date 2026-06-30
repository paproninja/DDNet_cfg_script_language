from pathlib import Path

def gen_command(gen, value):
    lines = []

    if isinstance(value, list):
        for v in value:
            lines.append(gen.resolve(v))
    else:
        lines.append(gen.resolve(value))

    return lines

def gen_unbind(gen, value):
    lines = []

    if isinstance(value, list):
        for v in value:
            v = gen.resolve(v)
            lines.append(f"unbind {v}")
    else:
        lines.append(gen.resolve(value))

    return lines

def gen_exec(gen, value):
    rel = Path(*gen.path_stack) # get the relative path unpacking the path stack
    target = gen.resolve(value) # resolve the target

    return f"exec {Path(*gen.path_stack) / target}" # return the exec command

def gen_echo(gen, value):
    lines = []

    for item in value:
        for k, v in item.items():
            if k == "color":
                lines.append(f"cl_message_client_color {gen.resolve(v)}")
            elif k == "text":
                if isinstance(v, list):
                    for echo in v:
                        lines.append(f"echo {gen.resolve(echo)}")
                else:
                    lines.append(f"echo {gen.resolve(v)}")

    return lines

def gen_bind(gen, value):
    lines = []

    for item in value:
        key = gen.resolve(item["key"])
        cmds = []
        for k, v in item.items(): # iterates through the properties of the item
            if k == "key":
                continue

            result = PROPERTY_TABLE[k](gen, v) # calls the appropriate generator function for each property
            if isinstance(result, list):
                cmds.extend(result)
            else:
                cmds.append(str(result))

        lines.append(f'bind {key} "' + ";".join(cmds) + '"')

    return lines

PROPERTY_TABLE = {
    "command": gen_command,
    "echo": gen_echo,
    "bind": gen_bind,
    "unbind": gen_unbind,
    "exec": gen_exec,
}

class Token: # token class
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return f"{self.key}({self.value})"

class Lexer: # lexer class. This class is used to tokenize the input file
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current = self.text[self.pos] if text else None

    def advance(self): # advances to the next character
        self.pos += 1
        if self.pos >= len(self.text):
            self.current = None
        else:
            self.current = self.text[self.pos]

    def skip_whitespace(self): # skips whitespaces until it finds a non-whitespace character
        while self.current is not None and self.current.isspace():
            self.advance()

    def read_identifier(self): # it will read until a character is not alphanumeric
        result = ""
        while self.current is not None and (self.current.isalnum() or self.current == "_"):
            result += self.current
            self.advance()
        return result

    def read_string(self): # it will read text between quotes
        result = ""
        self.advance() # skips the first quote
        while self.current is not None:
            if self.current == "'":
                self.advance()
                return result

            result += self.current
            self.advance()

        raise Exception("Unterminated string")

    def tokenize(self): # main function that will create the tokens
        tokens = []

        while self.current is not None:
            # skips
            if self.current.isspace(): # skips whitespaces
                self.skip_whitespace()
                continue

            # symbols
            if self.current == "{":
                tokens.append(Token("LBRACE", "{"))
                self.advance()
                continue

            if self.current == "}":
                tokens.append(Token("RBRACE", "}"))
                self.advance()
                continue

            if self.current == "[":
                tokens.append(Token("LBRACKET", "["))
                self.advance()
                continue

            if self.current == "]":
                tokens.append(Token("RBRACKET", "]"))
                self.advance()
                continue

            if self.current == ":":
                tokens.append(Token("COLON", ":"))
                self.advance()
                continue

            if self.current == ",": # commas are ignored
                self.advance()
                continue

            #strings
            if self.current == "'":
                value = self.read_string()
                tokens.append(Token("STRING", value))
                continue

            # identifiers
            if self.current.isalnum() or self.current == "_":
                value = self.read_identifier()
                tokens.append(Token("IDENT", value))
                continue

            # fallback
            raise Exception(f"Unexpected character: {self.current}")

        return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current = self.tokens[self.pos] if tokens else None

    def advance(self): # advances to the next token
        self.pos += 1
        if self.pos >= len(self.tokens):
            self.current = None
        else:
            self.current = self.tokens[self.pos]

    def expect(self, token_key): # checks if the current token matches the expected token. if not, it raises an exception
        if self.current is None:
            raise Exception(f"Unexpected end of input. Expected {token_key}")

        if self.current.key != token_key:
            raise Exception(f"Expected {token_key}, got {self.current}")

        token = self.current
        self.advance()
        return token

    def parse(self): # main function that will parse the input file
        return self.parse_object()

    def parse_object(self): # parses an object { ... }
        obj = {} # create an empty object
        self.expect("LBRACE")
        while self.current and self.current.key != "RBRACE": # loop until it finds the closing brace
            key = self.expect("IDENT").value # the identifier is the key for the object
            self.expect("COLON")
            value = self.parse_value() # the value is the value for the key
            obj[key] = value # create the key-value pair in the object

        self.expect("RBRACE")
        return obj

    def parse_array(self):
        arr = [] # create an empty array
        self.expect("LBRACKET")
        while self.current and self.current.key != "RBRACKET": # loop until it finds the closing bracket
            arr.append(self.parse_value()) # append the value to the array

        self.expect("RBRACKET")
        return arr

    def parse_value(self):
        if self.current.key == "STRING" or self.current.key == "IDENT": # if the current token is a string or identifier, it returns the value
            val = self.current.value
            self.advance()
            return val

        if self.current.key == "LBRACE": # if the current token is an object, it calls the parse_object function
            return self.parse_object()

        if self.current.key == "LBRACKET": # if the current token is an array, it calls the parse_array function
            return self.parse_array()

        raise Exception(f"Unexpected token: {self.current}") # if the current token is not a string, identifier, object, or array, it raises an exception

class Generator:
    def __init__(self, tree):
        self.tree = tree
        self.path_stack = []
        self.globals = {}

    def generate(self): # main function that will generate the output files
        self.handle_globals(self.tree)
        if "ROOT" not in self.globals: # if ROOT is not defined in the root object, it raises an exception
            raise Exception("Global variable ROOT is required and must be defined")
        self.generate_node(self.tree)

    def generate_node(self, node): # generates node (object with files and folders)
        self.handle_globals(node)

        for folder in node.get("folders", []): # generates folders
            self.generate_folder(folder)

        for file in node.get("files", []): # generates files
            self.generate_file(file)

    def handle_globals(self, node):
        for key, value in node.items():
            if key.startswith("_"): # if we find a global variable, we add it to the globals dictionary
                var = key[1:]
                if var == "PATH": # if PATH is defined, we raise an exception
                    raise Exception("Global variable PATH is reserved and must not be defined")
                else:
                    self.globals[var] = value

    def generate_folder(self, folder):
        name = folder["name"]
        self.path_stack.append(name) # adds the folder name to the path stack
        self.generate_node(folder) # generates the files and folders inside the folder
        self.path_stack.pop() # removes the folder name from the path stack

    def generate_file(self, file):
        lines = []

        for key, value in file.items():
            if key == "name":
                continue

            handler = PROPERTY_TABLE.get(key)
            if handler:
                lines.extend(handler(self, value))
            else:
                raise Exception(f"Unknown property: {key}")

        self.write_file(file["name"], lines)

    def get_root_path(self):
        return Path(self.globals.get("ROOT", "."))

    def write_file(self, name, lines):
        base = self.get_root_path()
        full_path = base / Path("/".join(self.path_stack)) / name # base path, path stack, and file name
        full_path.parent.mkdir(parents=True, exist_ok=True) # creates the parent directories if they don't exist
        full_path.write_text("\n".join(lines), encoding="utf-8") # writes the lines to the file

    def resolve(self, value):
        if isinstance(value, dict): # if the value is a dictionary, it resolves the dictionary and concatenates the values
            if "concat" in value:
                return "".join(self.resolve(v) for v in value["concat"])

        if value == "$PATH":
            return str(self.get_root_path() / Path(*self.path_stack))

        if isinstance(value, str) and value.startswith("$"): # if the value is a string and starts with a dollar sign, it resolves the variable
            key = value[1:] # removes the dollar sign
            resolved = self.globals.get(key) # returns the value of the variable
            if resolved is None:
                raise Exception(f"Undefined variable: {key}")
            return resolved
        return value



text = Path("file.dcsl").read_text(encoding="utf-8")

lexer = Lexer(text) # create a lexer object with the input text
tokens = lexer.tokenize() # tokenize the input file
parser = Parser(tokens) # create a parser object with the tokens
parsed_tree = parser.parse()
gen = Generator(parsed_tree)
gen.generate()