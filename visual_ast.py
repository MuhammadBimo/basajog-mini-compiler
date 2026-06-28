# visual_ast.py — Visualisasi AST BasaJog nganggo matplotlib + networkx

import matplotlib.pyplot as plt
import networkx as nx
from ast_nodes import (
    ProgramNode, NumberNode, StringNode, BoolNode,
    IdentifierNode, AssignNode, BinOpNode, UnaryOpNode,
    IfNode, WhileNode, FunctionNode, CallNode,
    PrintNode, InputNode, ReturnNode, BlockNode,
)

# Peta warna saben jinis node
_COLORS = {
    'ProgramNode':    '#D5DBDB',  # abu-abu    — oyod
    'BlockNode':      '#EAEDED',  # abu padhang
    'NumberNode':     '#AED6F1',  # biru enom  — literal angka
    'StringNode':     '#A9DFBF',  # ijo enom   — literal string
    'BoolNode':       '#FAD7A0',  # oranye     — bener/salah
    'IdentifierNode': '#F9E79F',  # kuning     — variabel
    'AssignNode':     '#F1948A',  # abang enom — assignment
    'BinOpNode':      '#F8C471',  # oranye tuwa — operasi biner
    'UnaryOpNode':    '#F8C471',
    'IfNode':         '#D7BDE2',  # ungu       — pamilihan
    'WhileNode':      '#A9CCE3',  # biru tuwa  — pengulangan
    'FunctionNode':   '#A9DFBF',  # ijo        — fungsi
    'CallNode':       '#D5F5E3',  # ijo enom   — pangundang fungsi
    'PrintNode':      '#ABEBC6',  # ijo        — tulis
    'InputNode':      '#ABEBC6',  # ijo        — takon
    'ReturnNode':     '#F1948A',  # abang enom — bali
}


class VisualAST:
    def __init__(self):
        self._reset()

    def _reset(self):
        self.graph   = nx.DiGraph()
        self.labels  = {}
        self.colors  = {}
        self.counter = 0

    def _new_id(self):
        self.counter += 1
        return self.counter

    # ----------------------------------------------------------
    # Label saben node
    # ----------------------------------------------------------

    def _label(self, node):
        n = type(node).__name__
        if n == 'ProgramNode':    return 'PROGRAM'
        if n == 'BlockNode':      return 'BLOCK'
        if n == 'NumberNode':     return f'NUMBER\n{node.value}'
        if n == 'StringNode':     return f'STRING\n"{node.value[:12]}"'
        if n == 'BoolNode':       return f'BOOL\n{"bener" if node.value else "salah"}'
        if n == 'IdentifierNode': return f'ID\n{node.name}'
        if n == 'AssignNode':     return f'ASSIGN\n{node.name}'
        if n == 'BinOpNode':      return f'BINOP\n{node.op}'
        if n == 'UnaryOpNode':    return f'UNARY\n{node.op}'
        if n == 'IfNode':         return 'IF\n(yen)'
        if n == 'WhileNode':      return 'WHILE\n(baleni)'
        if n == 'FunctionNode':   return f'FUNC\n{node.name}'
        if n == 'CallNode':       return f'CALL\n{node.name}'
        if n == 'PrintNode':      return 'PRINT\n(tulis)'
        if n == 'InputNode':      return 'INPUT\n(takon)'
        if n == 'ReturnNode':     return 'RETURN\n(bali)'
        return n

    # ----------------------------------------------------------
    # Mbangun graph
    # ----------------------------------------------------------

    def _add_node(self, node, parent_id=None):
        nid   = self._new_id()
        nname = type(node).__name__

        self.graph.add_node(nid)
        self.labels[nid] = self._label(node)
        self.colors[nid] = _COLORS.get(nname, '#FDFEFE')

        if parent_id is not None:
            self.graph.add_edge(parent_id, nid)

        return nid

    def _add_param(self, text, parent_id):
        nid = self._new_id()
        self.graph.add_node(nid)
        self.labels[nid] = f'PARAM\n{text}'
        self.colors[nid] = '#FDFEFE'
        self.graph.add_edge(parent_id, nid)

    def build(self, node, parent_id=None):
        if node is None:
            return
        nid = self._add_node(node, parent_id)
        n   = type(node).__name__

        if n == 'ProgramNode':
            for s in node.statements:     self.build(s, nid)
        elif n == 'BlockNode':
            for s in node.statements:     self.build(s, nid)
        elif n == 'AssignNode':
            self.build(node.value, nid)
        elif n == 'BinOpNode':
            self.build(node.left, nid)
            self.build(node.right, nid)
        elif n == 'UnaryOpNode':
            self.build(node.operand, nid)
        elif n == 'PrintNode':
            self.build(node.value, nid)
        elif n == 'InputNode':
            if node.prompt: self.build(node.prompt, nid)
        elif n == 'IfNode':
            self.build(node.condition,  nid)
            self.build(node.then_block, nid)
            if node.else_block: self.build(node.else_block, nid)
        elif n == 'WhileNode':
            self.build(node.condition, nid)
            self.build(node.body,      nid)
        elif n == 'FunctionNode':
            for p in node.params: self._add_param(p, nid)
            self.build(node.body, nid)
        elif n == 'CallNode':
            for a in node.args: self.build(a, nid)
        elif n == 'ReturnNode':
            if node.value: self.build(node.value, nid)

        return nid

    # ----------------------------------------------------------
    # Layout hierarki
    # ----------------------------------------------------------

    def _hierarchy_pos(self, root):
        """
        Layout hierarki adhedhasar cacah godhong (daun).
        Saben node godhong oleh siji slot horizontal dhewe satemah
        ora tau tumpang-tindih; node wong tuwa dipapanake pas ing tengah
        anak-anake. Mbalekake dict {node: (x, y)}.
        """
        pos     = {}
        next_x  = [0]   # pencacah slot godhong sabanjure (nganggo list supaya mutable)

        def _rec(node, depth):
            children = list(self.graph.successors(node))
            if not children:
                x = next_x[0]
                next_x[0] += 1
                pos[node] = (x, -depth)
                return x
            child_xs = [_rec(ch, depth + 1) for ch in children]
            x = sum(child_xs) / len(child_xs)   # wong tuwa ing tengah anak-anake
            pos[node] = (x, -depth)
            return x

        _rec(root, 0)
        return pos

    # ----------------------------------------------------------
    # Nampilake & nyimpen
    # ----------------------------------------------------------

    def show(self, tree, title='AST — BasaJog', save_path='visual_ast.png'):
        self._reset()
        self.build(tree)

        if not self.graph.nodes():
            print("Ora ana node sing bisa divisualisasi.")
            return

        root      = 1
        pos       = self._hierarchy_pos(root)
        color_lst = [self.colors[n] for n in self.graph.nodes()]

        # --- ukuran kanvas nyaketake cacah godhong & jerone wit ---
        n_leaves   = max(1, sum(1 for n in self.graph.nodes()
                                if self.graph.out_degree(n) == 0))
        max_depth  = max(-y for (_x, y) in pos.values()) if pos else 1
        fig_w      = max(18, n_leaves * 1.1)          # luwih amba yen godhong akeh
        fig_h      = max(8,  (max_depth + 1) * 1.9)   # luwih dhuwur yen wite jero

        fig, ax = plt.subplots(figsize=(fig_w, fig_h))
        fig.patch.set_facecolor('#F8F9FA')
        ax.set_facecolor('#F8F9FA')
        ax.set_title(title, fontsize=15, fontweight='bold', pad=18, color='#2C3E50')
        ax.axis('off')
        # wenehi papan ekstra ing kiwa-tengen supaya node pinggir ora kepotong
        ax.margins(x=0.04, y=0.08)

        nx.draw(
            self.graph, pos, ax=ax,
            labels=self.labels,
            with_labels=True,
            node_color=color_lst,
            node_size=1700,
            font_size=7,
            font_weight='bold',
            font_color='#2C3E50',
            arrows=True,
            edge_color='#7F8C8D',
            arrowsize=12,
            width=1.1,
        )

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.show()
        print(f"  AST disimpen menyang '{save_path}'")
