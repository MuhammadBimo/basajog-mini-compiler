# evaluator.py — Penerjemah (Interpreter) Pohon Sintaks BasaJog
#
# Backend ALTERNATIF kanggo pipeline. Tinimbang ngasilake pseudo-assembly
# (kaya code_generator.py), modul iki LANGSUNG nglakoni AST lan nyetak asile.
# Migunani kanggo nuduhake "output nyata" saka program BasaJog ing video.
#
# Cathetan:
#   - Iki backend OPSIONAL, ora kalebu pipeline utama ing main.py.
#   - Jalanke kanthi : python evaluator.py program.bj

import sys

from lexer  import tokenize
from parser import Parser
from ast_nodes import (
    ProgramNode, NumberNode, StringNode, BoolNode,
    IdentifierNode, AssignNode, BinOpNode, UnaryOpNode,
    IfNode, WhileNode, FunctionNode, CallNode,
    PrintNode, InputNode, ReturnNode, BlockNode,
)

_MAX_ITER = 100_000   # tameng supaya pengulangan tanpa wates ora ngebekake mesin


class RuntimeErrorBJ(Exception):
    """Kaluputan nalika program dilakoni (runtime)."""
    pass


class _ReturnSignal(Exception):
    """Sinyal internal kanggo nggawa aji 'bali' metu saka njero fungsi."""
    def __init__(self, value):
        self.value = value


class Environment:
    """Lingkungan variabel kanthi scope susun-susun (global vs lokal fungsi)."""

    def __init__(self, parent=None):
        self.vars   = {}
        self.parent = parent

    def get(self, name):
        if name in self.vars:
            return self.vars[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise RuntimeErrorBJ(f"Variabel '{name}' durung didefinisi")

    def set(self, name, value):
        self.vars[name] = value


class Evaluator:
    def __init__(self):
        self.global_env = Environment()
        self.functions  = {}   # jeneng -> FunctionNode

    # ----------------------------------------------------------
    # Lawang mlebu
    # ----------------------------------------------------------

    def run(self, tree):
        """Lakoni kabeh program saka oyod AST."""
        self._exec(tree, self.global_env)

    # ----------------------------------------------------------
    # Dispatcher
    # ----------------------------------------------------------

    def _eval(self, node, env):
        method = f'_v_{type(node).__name__}'
        handler = getattr(self, method, None)
        if handler is None:
            raise RuntimeErrorBJ(f"Node ora dikenal: {type(node).__name__}")
        return handler(node, env)

    def _exec(self, node, env):
        return self._eval(node, env)

    # ----------------------------------------------------------
    # Struktur program
    # ----------------------------------------------------------

    def _v_ProgramNode(self, node, env):
        # Pass 1 — dhaftar kabeh fungsi dhisik (bisa diundang sadurunge didefinisi)
        for stmt in node.statements:
            if isinstance(stmt, FunctionNode):
                self.functions[stmt.name] = stmt
        # Pass 2 — lakoni statement liyane
        for stmt in node.statements:
            if not isinstance(stmt, FunctionNode):
                self._eval(stmt, env)

    def _v_BlockNode(self, node, env):
        for stmt in node.statements:
            self._eval(stmt, env)

    # ----------------------------------------------------------
    # Literal
    # ----------------------------------------------------------

    def _v_NumberNode(self, node, env):
        return float(node.value) if '.' in str(node.value) else int(node.value)

    def _v_StringNode(self, node, env):
        return node.value

    def _v_BoolNode(self, node, env):
        return bool(node.value)

    def _v_IdentifierNode(self, node, env):
        return env.get(node.name)

    # ----------------------------------------------------------
    # Operasi
    # ----------------------------------------------------------

    def _v_BinOpNode(self, node, env):
        left  = self._eval(node.left, env)
        right = self._eval(node.right, env)
        op = node.op

        if op == '+':  return left + right
        if op == '-':  return left - right
        if op == '*':  return left * right
        if op == '/':
            if right == 0:
                raise RuntimeErrorBJ("Pamerang nganggo nol (kebagi nol)")
            return left / right
        if op == '==': return left == right
        if op == '!=': return left != right
        if op == '<':  return left < right
        if op == '>':  return left > right
        if op == '<=': return left <= right
        if op == '>=': return left >= right
        if op == '&&': return bool(left) and bool(right)
        if op == '||': return bool(left) or bool(right)
        raise RuntimeErrorBJ(f"Operator ora dikenal: '{op}'")

    def _v_UnaryOpNode(self, node, env):
        val = self._eval(node.operand, env)
        if node.op == '-':  return -val
        if node.op == '!':  return not val
        raise RuntimeErrorBJ(f"Operator unary ora dikenal: '{node.op}'")

    # ----------------------------------------------------------
    # Statement
    # ----------------------------------------------------------

    def _v_AssignNode(self, node, env):
        value = self._eval(node.value, env)
        env.set(node.name, value)
        return value

    def _v_PrintNode(self, node, env):
        value = self._eval(node.value, env)
        print(self._to_text(value))

    def _v_InputNode(self, node, env):
        if node.prompt:
            print(node.prompt.value, end='')
        try:
            return input()
        except EOFError:
            return ''

    def _v_IfNode(self, node, env):
        if self._truthy(self._eval(node.condition, env)):
            self._eval(node.then_block, env)
        elif node.else_block:
            self._eval(node.else_block, env)

    def _v_WhileNode(self, node, env):
        count = 0
        while self._truthy(self._eval(node.condition, env)):
            self._eval(node.body, env)
            count += 1
            if count > _MAX_ITER:
                raise RuntimeErrorBJ("Pengulangan kakehan (bisa uga tanpa wates)")

    # ----------------------------------------------------------
    # Fungsi
    # ----------------------------------------------------------

    def _v_FunctionNode(self, node, env):
        # Dhefinisi fungsi ing tengah-tengah program — dhaftarake wae.
        self.functions[node.name] = node

    def _v_CallNode(self, node, env):
        func = self.functions.get(node.name)
        if func is None:
            raise RuntimeErrorBJ(f"Fungsi '{node.name}' durung didefinisi")
        if len(node.args) != len(func.params):
            raise RuntimeErrorBJ(
                f"Fungsi '{node.name}' mbutuhake {len(func.params)} argumen "
                f"nanging diwenehi {len(node.args)}"
            )

        # Scope lokal anyar: parameter ditalekake menyang aji argumen
        local_env = Environment(self.global_env)
        for param, arg in zip(func.params, node.args):
            local_env.set(param, self._eval(arg, env))

        try:
            self._eval(func.body, local_env)
        except _ReturnSignal as r:
            return r.value
        return None

    def _v_ReturnNode(self, node, env):
        value = self._eval(node.value, env) if node.value else None
        raise _ReturnSignal(value)

    # ----------------------------------------------------------
    # Pambantu
    # ----------------------------------------------------------

    def _truthy(self, value):
        return bool(value)

    def _to_text(self, value):
        """Owahi aji Python dadi teks gaya BasaJog (True/False -> bener/salah)."""
        if isinstance(value, bool):
            return 'bener' if value else 'salah'
        return str(value)


# ============================================================
# Jalanke minangka program mandhiri
# ============================================================

def main():
    args = sys.argv[1:]
    if args:
        with open(args[0], encoding='utf-8') as f:
            source = f.read()
    else:
        print("Cara nganggo: python evaluator.py <berkas.bj>")
        return

    tokens = tokenize(source)
    ast    = Parser(tokens).parse()

    print("===== Output Program (Interpreter BasaJog) =====")
    try:
        Evaluator().run(ast)
    except RuntimeErrorBJ as e:
        print(f"\n[Kaluputan Runtime]\n  Pesen : {e}")


if __name__ == '__main__':
    main()
