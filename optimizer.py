# optimizer.py — Optimasi AST kanggo BasaJog
#
# Teknik sing diimplementasi:
#   1. Constant Folding  — nglempit ekspresi konstan ing wektu-kompilasi
#      Tuladha: 5 + 3  →  8
#               !salah  →  bener
#   2. Dead Code Elimination — mbusak kode sing ora tau dilakoni
#      Tuladha: yen (salah) { ... }      → dibusak kabeh
#               yen (bener) { A } liyane { B }  → mung A sing isih

from ast_nodes import (
    ProgramNode, NumberNode, StringNode, BoolNode,
    IdentifierNode, AssignNode, BinOpNode, UnaryOpNode,
    IfNode, WhileNode, FunctionNode, CallNode,
    PrintNode, InputNode, ReturnNode, BlockNode,
)


class Optimizer:
    def __init__(self):
        self.log = []   # cathetan optimasi sing dilakoni

    def optimize(self, node):
        """Jalanke kabeh optimasi, mbalekake AST sing wis dioptimasi."""
        return self._visit(node)

    # ----------------------------------------------------------
    # Dispatcher
    # ----------------------------------------------------------

    def _visit(self, node):
        if node is None:
            return None
        method = f'_v_{type(node).__name__}'
        return getattr(self, method, self._identity)(node)

    def _identity(self, node):
        return node

    # ----------------------------------------------------------
    # Node sing perlu ditelusuri anak-anake
    # ----------------------------------------------------------

    def _v_ProgramNode(self, node):
        stmts = [self._visit(s) for s in node.statements]
        node.statements = [s for s in stmts if s is not None]
        return node

    def _v_BlockNode(self, node):
        stmts = [self._visit(s) for s in node.statements]
        node.statements = [s for s in stmts if s is not None]
        return node

    def _v_AssignNode(self, node):
        node.value = self._visit(node.value)
        return node

    def _v_PrintNode(self, node):
        node.value = self._visit(node.value)
        return node

    def _v_ReturnNode(self, node):
        if node.value:
            node.value = self._visit(node.value)
        return node

    def _v_FunctionNode(self, node):
        node.body = self._visit(node.body)
        return node

    def _v_CallNode(self, node):
        node.args = [self._visit(a) for a in node.args]
        return node

    # ----------------------------------------------------------
    # Constant Folding — BinOpNode
    # ----------------------------------------------------------

    def _v_BinOpNode(self, node):
        node.left  = self._visit(node.left)
        node.right = self._visit(node.right)
        left, right = node.left, node.right

        # --- lempit loro NumberNode ---
        if isinstance(left, NumberNode) and isinstance(right, NumberNode):
            lv = float(left.value) if '.' in str(left.value) else int(left.value)
            rv = float(right.value) if '.' in str(right.value) else int(right.value)
            result = self._fold_num(lv, rv, node.op)
            if result is not None:
                self.log.append(
                    f"  Constant Folding : {left.value} {node.op} {right.value}  ->  {result}"
                )
                if isinstance(result, bool):
                    return BoolNode(result, node.line)
                # simpen minangka string; ngindhari ".0" sing ora perlu
                out = str(int(result)) if isinstance(result, float) and result == int(result) \
                      else str(result)
                return NumberNode(out, node.line)

        # --- lempit loro BoolNode ---
        if isinstance(left, BoolNode) and isinstance(right, BoolNode):
            result = self._fold_bool(left.value, right.value, node.op)
            if result is not None:
                self.log.append(
                    f"  Constant Folding : "
                    f"{'bener' if left.value else 'salah'} {node.op} "
                    f"{'bener' if right.value else 'salah'}  ->  "
                    f"{'bener' if result else 'salah'}"
                )
                return BoolNode(result, node.line)

        return node

    def _fold_num(self, lv, rv, op):
        try:
            if op == '+':  return lv + rv
            if op == '-':  return lv - rv
            if op == '*':  return lv * rv
            if op == '/' and rv != 0: return lv / rv
            if op == '==': return lv == rv
            if op == '!=': return lv != rv
            if op == '<':  return lv < rv
            if op == '>':  return lv > rv
            if op == '<=': return lv <= rv
            if op == '>=': return lv >= rv
        except Exception:
            pass
        return None

    def _fold_bool(self, lv, rv, op):
        if op == '&&': return lv and rv
        if op == '||': return lv or rv
        if op == '==': return lv == rv
        if op == '!=': return lv != rv
        return None

    # ----------------------------------------------------------
    # Constant Folding — UnaryOpNode
    # ----------------------------------------------------------

    def _v_UnaryOpNode(self, node):
        node.operand = self._visit(node.operand)

        if isinstance(node.operand, NumberNode) and node.op == '-':
            val = node.operand.value
            n   = float(val) if '.' in str(val) else int(val)
            res = -n
            out = str(int(res)) if isinstance(res, float) and res == int(res) else str(res)
            self.log.append(f"  Constant Folding : -{val}  ->  {out}")
            return NumberNode(out, node.line)

        if isinstance(node.operand, BoolNode) and node.op == '!':
            res = not node.operand.value
            self.log.append(
                f"  Constant Folding : !{'bener' if node.operand.value else 'salah'}"
                f"  ->  {'bener' if res else 'salah'}"
            )
            return BoolNode(res, node.line)

        return node

    # ----------------------------------------------------------
    # Dead Code Elimination — IfNode
    # ----------------------------------------------------------

    def _v_IfNode(self, node):
        node.condition = self._visit(node.condition)

        if isinstance(node.condition, BoolNode):
            if node.condition.value:
                # kahanan tansah BENER → buwang cabang liyane
                self.log.append(
                    f"  Dead Code Elim.  : blok 'liyane' ing larik {node.line} "
                    f"dibusak (kahanan tansah bener)"
                )
                return self._visit(node.then_block)
            else:
                # kahanan tansah SALAH → buwang kabeh blok yen
                if node.else_block:
                    self.log.append(
                        f"  Dead Code Elim.  : blok 'yen' ing larik {node.line} "
                        f"dibusak (kahanan tansah salah), 'liyane' ditahan"
                    )
                    return self._visit(node.else_block)
                else:
                    self.log.append(
                        f"  Dead Code Elim.  : blok 'yen' ing larik {node.line} "
                        f"dibusak kabeh (kahanan tansah salah)"
                    )
                    return None   # dibusak saka parent

        node.then_block = self._visit(node.then_block)
        if node.else_block:
            node.else_block = self._visit(node.else_block)
        return node

    # ----------------------------------------------------------
    # Dead Code Elimination — WhileNode
    # ----------------------------------------------------------

    def _v_WhileNode(self, node):
        node.condition = self._visit(node.condition)

        if isinstance(node.condition, BoolNode) and not node.condition.value:
            self.log.append(
                f"  Dead Code Elim.  : blok 'baleni' ing larik {node.line} "
                f"dibusak (kahanan tansah salah)"
            )
            return None

        node.body = self._visit(node.body)
        return node

    # ----------------------------------------------------------
    # Laporan
    # ----------------------------------------------------------

    def print_log(self):
        if self.log:
            print("Optimasi sing dilakoni:")
            for entry in self.log:
                print(entry)
        else:
            print("Ora ana optimasi sing bisa ditrapake.")
