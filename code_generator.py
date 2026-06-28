# code_generator.py — Generator Kode Pseudo-Assembly kanggo BasaJog
#
# Instruksi sing diasilake:
#   START / HALT        — tandha wiwitan lan pungkasan program
#   PUSH <val>          — dorong aji konstan menyang stack
#   LOAD <var>          — muat aji variabel menyang stack
#   STORE <var>         — simpen aji saka stack menyang variabel
#   ADD / SUB / MUL     — operasi etung-etungan
#   DIV / NEG / NOT     — etung-etungan lan logika
#   EQ / NEQ / LT / GT — pambandhing (asil: 0 utawa 1)
#   LEQ / GEQ           — pambandhing
#   AND / OR            — logika
#   JUMP <label>        — mlumpat tanpa syarat
#   JUMP_IF_FALSE <lbl> — mlumpat yen aji stack = 0 (false)
#   LABEL <label>       — tandha posisi
#   PRINT               — cetak aji saka pucuk stack
#   PROMPT <str>        — tampilake teks sadurunge input
#   INPUT               — maca input, dorong menyang stack
#   FUNC <name>         — tandha wiwitan dhefinisi fungsi
#   PARAM <name>        — deklarasi parameter
#   CALL <name> <n>     — undang fungsi nganggo n argumen
#   RET                 — bali saka fungsi
#   DEFINE_FUNC <name>  — dhaftarake fungsi menyang tabel fungsi runtime

from ast_nodes import (
    ProgramNode, NumberNode, StringNode, BoolNode,
    IdentifierNode, AssignNode, BinOpNode, UnaryOpNode,
    IfNode, WhileNode, FunctionNode, CallNode,
    PrintNode, InputNode, ReturnNode, BlockNode,
)


class CodeGenError(Exception):
    pass


class CodeGenerator:
    def __init__(self):
        self._code    = []
        self._label_n = 0

    # ----------------------------------------------------------
    # Antarmuka umum
    # ----------------------------------------------------------

    def generate(self, tree):
        """Asilake kode saka AST; mbalekake list string instruksi."""
        self._visit(tree)
        return self._code

    def get_output(self):
        return '\n'.join(self._code)

    # ----------------------------------------------------------
    # Pambantu
    # ----------------------------------------------------------

    def _new_label(self):
        self._label_n += 1
        return f"L{self._label_n}"

    def _emit(self, instr):
        self._code.append(instr)

    # ----------------------------------------------------------
    # Dispatcher
    # ----------------------------------------------------------

    def _visit(self, node):
        if node is None:
            return
        method = f'_v_{type(node).__name__}'
        getattr(self, method, self._noop)(node)

    def _noop(self, node):
        pass

    # ----------------------------------------------------------
    # Visitor saben node
    # ----------------------------------------------------------

    def _v_ProgramNode(self, node):
        self._emit('; ================================================')
        self._emit('; BasaJog Pseudo-Assembly Output')
        self._emit('; ================================================')
        self._emit('START')
        for stmt in node.statements:
            self._visit(stmt)
        self._emit('HALT')

    def _v_BlockNode(self, node):
        for stmt in node.statements:
            self._visit(stmt)

    # --- Literal ---

    def _v_NumberNode(self, node):
        self._emit(f'PUSH {node.value}')

    def _v_StringNode(self, node):
        self._emit(f'PUSH "{node.value}"')

    def _v_BoolNode(self, node):
        val  = '1' if node.value else '0'
        kw   = 'bener' if node.value else 'salah'
        self._emit(f'PUSH {val}        ; {kw}')

    def _v_IdentifierNode(self, node):
        self._emit(f'LOAD {node.name}')

    # --- Operasi ---

    def _v_BinOpNode(self, node):
        self._visit(node.left)
        self._visit(node.right)
        _op_map = {
            '+': 'ADD',  '-': 'SUB',  '*': 'MUL', '/': 'DIV',
            '==': 'EQ',  '!=': 'NEQ', '<': 'LT',  '>': 'GT',
            '<=': 'LEQ', '>=': 'GEQ', '&&': 'AND', '||': 'OR',
        }
        self._emit(_op_map.get(node.op, f'OP_{node.op}'))

    def _v_UnaryOpNode(self, node):
        self._visit(node.operand)
        if node.op == '-':
            self._emit('NEG')
        elif node.op == '!':
            self._emit('NOT')

    # --- Statement ---

    def _v_AssignNode(self, node):
        self._visit(node.value)
        self._emit(f'STORE {node.name}')

    def _v_PrintNode(self, node):
        self._visit(node.value)
        self._emit('PRINT')

    def _v_InputNode(self, node):
        if node.prompt:
            self._emit(f'PROMPT "{node.prompt.value}"')
        self._emit('INPUT')

    # --- Pamilihan ---

    def _v_IfNode(self, node):
        label_else = self._new_label()
        label_end  = self._new_label()

        self._visit(node.condition)
        self._emit(f'JUMP_IF_FALSE {label_else}')

        self._visit(node.then_block)
        self._emit(f'JUMP {label_end}')

        self._emit(f'LABEL {label_else}')
        if node.else_block:
            self._visit(node.else_block)

        self._emit(f'LABEL {label_end}')

    # --- Pengulangan ---

    def _v_WhileNode(self, node):
        label_start = self._new_label()
        label_end   = self._new_label()

        self._emit(f'LABEL {label_start}')
        self._visit(node.condition)
        self._emit(f'JUMP_IF_FALSE {label_end}')

        self._visit(node.body)
        self._emit(f'JUMP {label_start}')

        self._emit(f'LABEL {label_end}')

    # --- Fungsi ---

    def _v_FunctionNode(self, node):
        label_skip = self._new_label()

        # Wektu dhefinisi, lompati body supaya ora langsung dilakoni
        self._emit(f'JUMP {label_skip}         ; mlumpat menyang sawise dhefinisi fungsi')
        self._emit(f'FUNC {node.name}')
        for param in node.params:
            self._emit(f'PARAM {param}')

        self._visit(node.body)

        # FIX Bug #2 — double RET:
        # Emit RET cadhangan mung yen statement pungkasan body dudu ReturnNode.
        # Yen ana 'bali' eksplisit, _v_ReturnNode wis emit RET — ora perlu dobel.
        body_stmts = node.body.statements if isinstance(node.body, BlockNode) else []
        if not body_stmts or not isinstance(body_stmts[-1], ReturnNode):
            self._emit('RET        ; cadhangan: ora ana bali eksplisit')

        self._emit(f'LABEL {label_skip}')
        self._emit(f'DEFINE_FUNC {node.name}')

    def _v_CallNode(self, node):
        for arg in node.args:
            self._visit(arg)
        self._emit(f'CALL {node.name} {len(node.args)}')

    def _v_ReturnNode(self, node):
        if node.value:
            self._visit(node.value)
        self._emit('RET')
