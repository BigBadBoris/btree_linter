built_in_idents = {
        "include",
        "root",
        "selector",
        "randomSelector",
        "sequence",
        "randomSequence",
        "parallel",
        "dynamicGuardSelector",
        "alwaysFail",
        "alwaysSucceed",
        "invert",
        "repeat",
        "semaphoreGuard",
        "untilFail", 
        "untilSuccess" 
}


class Analyser():

    def __init__(self, filename:str, java_root:str):
        self.java_root = java_root
        self.filename = filename

    def error(self, msg, node):
        token = node["token"]
        print(f"{self.filename}:{token.line}:{token.column}:",
              f"error: {msg}")

    def check_undefined_identifiers(self, root:dict, imports:dict):
        "Check for any idents that are not built-in or imported."
        queue = [root]
        while queue:
            node = queue.pop(0)
            for child in node["children"]:
                queue.append(child)
                for guard in node["guards"]:
                    queue.append(guard)
            name = node["name"]
            if name not in built_in_idents and name not in imports:
                self.error(f'"{name}" is not defined.', node)

    def analyse(self, root:dict, imports:dict):
        "Run several checks on a btree AST."
        self.check_undefined_identifiers(root, imports)
