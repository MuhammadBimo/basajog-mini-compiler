# ast_nodes.py — Dhefinisi kabeh node AST kanggo BasaJog


class Node:
    """Klas dhasar kanggo kabeh node AST."""
    pass


class ProgramNode(Node):
    def __init__(self, statements):
        self.statements = statements  # list[Node]

    def __repr__(self):
        return f"PROGRAM({len(self.statements)} statements)"


class NumberNode(Node):
    def __init__(self, value, line=0):
        self.value = value  # str, tuladha "10" utawa "3.14"
        self.line  = line

    def __repr__(self):
        return f"NUMBER({self.value})"


class StringNode(Node):
    def __init__(self, value, line=0):
        self.value = value  # str tanpa tandha pethik
        self.line  = line

    def __repr__(self):
        return f'STRING("{self.value}")'


class BoolNode(Node):
    def __init__(self, value, line=0):
        self.value = value  # bool Python: True / False
        self.line  = line

    def __repr__(self):
        return f"BOOL({'bener' if self.value else 'salah'})"


class IdentifierNode(Node):
    def __init__(self, name, line=0):
        self.name = name  # str
        self.line = line

    def __repr__(self):
        return f"ID({self.name})"


class AssignNode(Node):
    def __init__(self, name, value, line=0):
        self.name  = name   # str — jeneng variabel
        self.value = value  # Node
        self.line  = line

    def __repr__(self):
        return f"ASSIGN({self.name})"


class BinOpNode(Node):
    def __init__(self, left, op, right, line=0):
        self.left  = left   # Node
        self.op    = op     # str, tuladha "+", "==", "&&"
        self.right = right  # Node
        self.line  = line

    def __repr__(self):
        return f"BINOP({self.op})"


class UnaryOpNode(Node):
    def __init__(self, op, operand, line=0):
        self.op      = op       # str: "-" utawa "!"
        self.operand = operand  # Node
        self.line    = line

    def __repr__(self):
        return f"UNARY({self.op})"


class IfNode(Node):
    def __init__(self, condition, then_block, else_block=None, line=0):
        self.condition  = condition   # Node
        self.then_block = then_block  # BlockNode
        self.else_block = else_block  # BlockNode | None
        self.line       = line

    def __repr__(self):
        return "IF(yen)"


class WhileNode(Node):
    def __init__(self, condition, body, line=0):
        self.condition = condition  # Node
        self.body      = body       # BlockNode
        self.line      = line

    def __repr__(self):
        return "WHILE(baleni)"


class FunctionNode(Node):
    def __init__(self, name, params, body, line=0):
        self.name   = name    # str
        self.params = params  # list[str]
        self.body   = body    # BlockNode
        self.line   = line

    def __repr__(self):
        return f"FUNC({self.name})"


class CallNode(Node):
    def __init__(self, name, args, line=0):
        self.name = name  # str
        self.args = args  # list[Node]
        self.line = line

    def __repr__(self):
        return f"CALL({self.name})"


class PrintNode(Node):
    def __init__(self, value, line=0):
        self.value = value  # Node
        self.line  = line

    def __repr__(self):
        return "PRINT(tulis)"


class InputNode(Node):
    def __init__(self, prompt=None, line=0):
        self.prompt = prompt  # StringNode | None
        self.line   = line

    def __repr__(self):
        return "INPUT(takon)"


class ReturnNode(Node):
    def __init__(self, value=None, line=0):
        self.value = value  # Node | None
        self.line  = line

    def __repr__(self):
        return "RETURN(bali)"


class BlockNode(Node):
    def __init__(self, statements, line=0):
        self.statements = statements  # list[Node]
        self.line       = line

    def __repr__(self):
        return f"BLOCK({len(self.statements)} stmts)"
