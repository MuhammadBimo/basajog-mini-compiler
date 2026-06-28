# semantic.py — Analisis Makna (Semantik) kanggo BasaJog
#
# Pamriksan sing dilakoni:
#   1. Variabel durung dideklarasi
#   2. Fungsi durung didefinisi
#   3. Cacah argumen ora cocog
#   4. Tipe ora cocog (etung-etungan ing non-angka, NOT ing non-bool)
#   5. 'bali' (return) dienggo ing njaba fungsi
#   6. Manajemen scope susun-susun (global vs lokal fungsi)
#
# Format pesen kaluputan:
#   [Kaluputan Makna]
#     Larik : <nomer larik>
#     Pesen : <katrangan masalah>

from ast_nodes import (
    ProgramNode, NumberNode, StringNode, BoolNode,
    IdentifierNode, AssignNode, BinOpNode, UnaryOpNode,
    IfNode, WhileNode, FunctionNode, CallNode,
    PrintNode, InputNode, ReturnNode, BlockNode,
)
from symbol_table import SymbolTable


class SemanticError(Exception):
    pass


class SemanticAnalyzer:
    def __init__(self):
        self.global_table  = SymbolTable('global')
        self.current_table = self.global_table
        self._functions    = {}     # name -> FunctionNode (diklumpukake ing pass-1)
        self._errors       = []
        self._in_function  = False  # FIX Bug #1: nglacak apa lagi ana ing njero fungsi

    # ----------------------------------------------------------
    # Lawang umum
    # ----------------------------------------------------------

    def analyze(self, tree):
        """
        Analisis makna kabeh AST.
        Klumpukake kabeh kaluputan dhisik, banjur nguncalake SemanticError.
        """
        self._visit(tree)
        if self._errors:
            raise SemanticError('\n\n'.join(self._errors))
        return self.global_table

    def get_symbol_table(self):
        return self.global_table

    # ----------------------------------------------------------
    # Pambantu
    # ----------------------------------------------------------

    def _visit(self, node):
        if node is None:
            return 'unknown'
        method = f'_v_{type(node).__name__}'
        return getattr(self, method, self._v_default)(node)

    def _v_default(self, node):
        return 'unknown'

    def _err(self, message, line=None):
        """Nambahake siji entri kaluputan menyang dhaftar kanthi format seragam."""
        entry = '[Kaluputan Makna]'
        if line is not None:
            entry += f'\n  Larik : {line}'
        entry += f'\n  Pesen : {message}'
        self._errors.append(entry)

    # ----------------------------------------------------------
    # Visitor saben node
    # ----------------------------------------------------------

    def _v_ProgramNode(self, node):
        # Pass 1 — dhaftar kabeh dhefinisi fungsi dhisik
        # (supaya fungsi bisa diundang sadurunge larik dhefinisine)
        for stmt in node.statements:
            if isinstance(stmt, FunctionNode):
                if stmt.name in self._functions:
                    self._err(
                        f"Fungsi '{stmt.name}' wis didefinisi sadurunge",
                        stmt.line,
                    )
                else:
                    self._functions[stmt.name] = stmt
                    self.global_table.define(stmt.name, 'fungsi')

        # Pass 2 — kunjungi kabeh statement
        for stmt in node.statements:
            self._visit(stmt)

    def _v_BlockNode(self, node):
        for stmt in node.statements:
            self._visit(stmt)

    def _v_AssignNode(self, node):
        val_type = self._visit(node.value)
        existing = self.current_table.lookup(node.name)
        if existing:
            existing.type = val_type
        else:
            self.current_table.define(node.name, val_type)
        return val_type

    def _v_IdentifierNode(self, node):
        sym = self.current_table.lookup(node.name)
        if sym is None:
            self._err(
                f"Variabel '{node.name}' durung dideklarasi",
                node.line,
            )
            return 'unknown'
        return sym.type

    def _v_NumberNode(self, node):
        return 'float' if '.' in str(node.value) else 'int'

    def _v_StringNode(self, node):
        return 'string'

    def _v_BoolNode(self, node):
        return 'bool'

    def _v_BinOpNode(self, node):
        lt = self._visit(node.left)
        rt = self._visit(node.right)

        # Operator etung-etungan — loro sisihe kudu jinis angka
        if node.op in ('+', '-', '*', '/'):
            _numeric = ('int', 'float', 'unknown')
            if lt not in _numeric or rt not in _numeric:
                self._err(
                    f"Tipe ora cocog: operator '{node.op}' ora bisa ditrapake "
                    f"ing jinis '{lt}' lan '{rt}'",
                    node.line,
                )
            return 'float' if 'float' in (lt, rt) else 'int'

        # Operator pambandhing & logika — asile tansah bool
        if node.op in ('==', '!=', '<', '>', '<=', '>=', '&&', '||'):
            return 'bool'

        return 'unknown'

    def _v_UnaryOpNode(self, node):
        ot = self._visit(node.operand)
        if node.op == '!' and ot not in ('bool', 'unknown'):
            self._err(
                f"Tipe ora cocog: operator '!' mung kanggo jinis bool, "
                f"dudu '{ot}'",
                node.line,
            )
        if node.op == '-' and ot not in ('int', 'float', 'unknown'):
            self._err(
                f"Tipe ora cocog: operator unary '-' mung kanggo jinis angka, "
                f"dudu '{ot}'",
                node.line,
            )
        return ot

    def _v_PrintNode(self, node):
        self._visit(node.value)
        return None

    def _v_InputNode(self, node):
        return 'string'   # takon tansah mbalekake string

    def _v_IfNode(self, node):
        self._visit(node.condition)
        self._visit(node.then_block)
        if node.else_block:
            self._visit(node.else_block)
        return None

    def _v_WhileNode(self, node):
        self._visit(node.condition)
        self._visit(node.body)
        return None

    def _v_FunctionNode(self, node):
        # Gawe scope anyar kanggo parameter lan variabel lokal fungsi
        func_table = SymbolTable(f'fungsi:{node.name}', self.current_table)

        # FIX Bug #1 & Bug #3:
        #   - simpen kahanan sadurunge
        #   - nganggo try/finally supaya scope TANSAH dibalekake,
        #     senajan ana exception ing njero body
        prev_table   = self.current_table
        prev_in_func = self._in_function

        self.current_table = func_table
        self._in_function  = True

        for param in node.params:
            func_table.define(param, 'unknown')

        try:
            self._visit(node.body)
        finally:
            self.current_table = prev_table
            self._in_function  = prev_in_func

        return None

    def _v_CallNode(self, node):
        func = self._functions.get(node.name)
        if func is None:
            # Bisa wae diundang liwat variabel — cek tabel simbol
            sym = self.current_table.lookup(node.name)
            if sym is None or sym.type != 'fungsi':
                self._err(
                    f"Fungsi '{node.name}' durung didefinisi",
                    node.line,
                )
                return 'unknown'
        else:
            if len(node.args) != len(func.params):
                self._err(
                    f"Fungsi '{node.name}' mbutuhake {len(func.params)} argumen "
                    f"nanging diwenehi {len(node.args)}",
                    node.line,
                )

        for arg in node.args:
            self._visit(arg)
        return 'unknown'

    def _v_ReturnNode(self, node):
        # FIX Bug #1 — cek apa 'bali' dienggo ing njero fungsi
        if not self._in_function:
            self._err(
                "'bali' (return) dienggo ing njaba fungsi",
                node.line,
            )
        if node.value:
            return self._visit(node.value)
        return None
