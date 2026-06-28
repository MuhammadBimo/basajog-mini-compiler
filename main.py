# main.py - Pipeline Utama Mini Compiler BasaJog
#
# Urutan tahap:
#   1. Lexer          - tokenisasi source code
#   2. Parser         - mbentuk AST saka token
#   3. Semantic       - analisis makna + tabel simbol
#   4. Optimizer      - constant folding + dead code elimination
#   5. Code Generator - ngasilake pseudo-assembly
#   6. Visual AST     - nampilake lan nyimpen wit sintaks

import sys

from lexer          import tokenize,   LexerError
from parser         import Parser,     ParseError
from semantic       import SemanticAnalyzer, SemanticError
from optimizer      import Optimizer
from code_generator import CodeGenerator
from visual_ast     import VisualAST

# ============================================================
BANNER = """
+======================================================+
|          BasaJog Mini Compiler  v1.0                 |
|   Basa Pemrograman Adhedhasar Tembung Jawa           |
|   Ngayogyakarta -- Teknik Kompilasi -- 06TPLP014     |
+======================================================+"""

CONTOH_PROGRAM = '''\
// Program tuladha BasaJog
x = 5 + 3

yen (x > 5) {
    tulis("Gedhe")
} liyane {
    tulis("Cilik")
}

// Fungsi panambahan
fungsi wuwuh(a, b) {
    bali a + b
}

asil = wuwuh(10, 20)
tulis(asil)

// Pengulangan
i = 0
baleni (i < 3) {
    tulis(i)
    i = i + 1
}
'''

# ============================================================
# Piranti tampilan
# ============================================================

def _sep(title='', width=60):
    if title:
        pad = (width - len(title) - 4) // 2
        print(f"\n{'-'*pad}  {title}  {'-'*pad}")
    else:
        print('-' * width)


def _print_ast_text(node, indent=0, prefix=''):
    """Cetak AST ing format teks kanthi indentasi."""
    if node is None:
        return
    sp = '    ' * indent
    n  = type(node).__name__

    if n == 'ProgramNode':
        print(f"{sp}{prefix}PROGRAM")
        for s in node.statements:
            _print_ast_text(s, indent + 1, '+-- ')

    elif n == 'BlockNode':
        print(f"{sp}{prefix}BLOCK")
        for s in node.statements:
            _print_ast_text(s, indent + 1, '+-- ')

    elif n == 'NumberNode':
        print(f"{sp}{prefix}NUMBER({node.value})")

    elif n == 'StringNode':
        print(f'{sp}{prefix}STRING("{node.value}")')

    elif n == 'BoolNode':
        print(f"{sp}{prefix}BOOL({'bener' if node.value else 'salah'})")

    elif n == 'IdentifierNode':
        print(f"{sp}{prefix}ID({node.name})")

    elif n == 'AssignNode':
        print(f"{sp}{prefix}ASSIGN({node.name})")
        _print_ast_text(node.value, indent + 1, '+-- ')

    elif n == 'BinOpNode':
        print(f"{sp}{prefix}BINOP({node.op})")
        _print_ast_text(node.left,  indent + 1, 'L-- ')
        _print_ast_text(node.right, indent + 1, 'R-- ')

    elif n == 'UnaryOpNode':
        print(f"{sp}{prefix}UNARY({node.op})")
        _print_ast_text(node.operand, indent + 1, '+-- ')

    elif n == 'PrintNode':
        print(f"{sp}{prefix}PRINT(tulis)")
        _print_ast_text(node.value, indent + 1, '+-- ')

    elif n == 'InputNode':
        print(f"{sp}{prefix}INPUT(takon)")
        if node.prompt:
            _print_ast_text(node.prompt, indent + 1, '+-- ')

    elif n == 'IfNode':
        print(f"{sp}{prefix}IF(yen)")
        _print_ast_text(node.condition,  indent + 1, 'COND-- ')
        _print_ast_text(node.then_block, indent + 1, 'THEN-- ')
        if node.else_block:
            _print_ast_text(node.else_block, indent + 1, 'ELSE-- ')

    elif n == 'WhileNode':
        print(f"{sp}{prefix}WHILE(baleni)")
        _print_ast_text(node.condition, indent + 1, 'COND-- ')
        _print_ast_text(node.body,      indent + 1, 'BODY-- ')

    elif n == 'FunctionNode':
        params = ', '.join(node.params) if node.params else '(ora ana)'
        print(f"{sp}{prefix}FUNC({node.name})  params=[{params}]")
        _print_ast_text(node.body, indent + 1, '+-- ')

    elif n == 'CallNode':
        print(f"{sp}{prefix}CALL({node.name})")
        for a in node.args:
            _print_ast_text(a, indent + 1, '+-- ')

    elif n == 'ReturnNode':
        print(f"{sp}{prefix}RETURN(bali)")
        if node.value:
            _print_ast_text(node.value, indent + 1, '+-- ')

    else:
        print(f"{sp}{prefix}{n}")


# ============================================================
# Pipeline utama
# ============================================================

def run(source):
    print(BANNER)

    # ------------------------------------------
    # TAHAP 1 - LEXER
    # ------------------------------------------
    _sep('TAHAP 1 : LEXER')
    try:
        tokens = tokenize(source)
    except LexerError as e:
        print(f"\n{e}")
        return

    print(f"  {'No.':<4} {'Jinis':<12} {'Aji':<24} {'Larik':<6} Kolom")
    _sep()
    for i, tok in enumerate(tokens, 1):
        print(f"  {i:<4} {tok.type:<12} {tok.value!r:<24} {tok.line:<6} {tok.col}")
    print(f"\n  Gunggung: {len(tokens)} token (kalebu EOF)")

    # ------------------------------------------
    # TAHAP 2 - PARSER -> AST
    # ------------------------------------------
    _sep('TAHAP 2 : PARSER -> AST')
    try:
        ast = Parser(tokens).parse()
        print(f"  Parsing kasil. Oyod: {ast}\n")
        _print_ast_text(ast, indent=1)
    except ParseError as e:
        print(f"\n{e}")
        return

    # ------------------------------------------
    # TAHAP 3 - ANALISIS MAKNA
    # ------------------------------------------
    _sep('TAHAP 3 : ANALISIS MAKNA')
    try:
        analyzer  = SemanticAnalyzer()
        sym_table = analyzer.analyze(ast)
        print("  Analisis makna: OK")
        sym_table.print_table()
    except SemanticError as e:
        print(f"\n{e}")
        return

    # ------------------------------------------
    # TAHAP 4 - OPTIMASI
    # ------------------------------------------
    _sep('TAHAP 4 : OPTIMASI')
    optimizer = Optimizer()
    opt_ast   = optimizer.optimize(ast)
    optimizer.print_log()

    # ------------------------------------------
    # TAHAP 5 - CODE GENERATOR
    # ------------------------------------------
    _sep('TAHAP 5 : CODE GENERATOR (Pseudo-Assembly)')
    gen = CodeGenerator()
    gen.generate(opt_ast)
    print(gen.get_output())

    # ------------------------------------------
    # TAHAP 6 - VISUALISASI AST
    # ------------------------------------------
    _sep('TAHAP 6 : VISUALISASI AST')
    print("  Nampilake wit sintaks...")
    visual = VisualAST()
    visual.show(opt_ast, title='AST - BasaJog Mini Compiler')


# ============================================================
# Maca input
# ============================================================

def _read_source():
    args = sys.argv[1:]

    # Saka berkas: python main.py program.bj
    if args:
        path = args[0]
        try:
            with open(path, encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Berkas ora ketemu: {path}")
            sys.exit(1)

    # Saka stdin interaktif
    print("Lebokna program BasaJog.")
    print("Ketik 'rampung' ing larik anyar, utawa pencet Enter 2x kanggo miwiti kompilasi.\n")

    lines     = []
    blank_row = 0

    while True:
        try:
            line = input()
        except EOFError:
            break

        if line.strip().lower() == 'rampung':
            break

        if line == '':
            blank_row += 1
            if blank_row >= 2:
                break
            lines.append(line)
        else:
            blank_row = 0
            lines.append(line)

    source = '\n'.join(lines).strip()
    if not source:
        print("Ora ana input. Nganggo program tuladha:\n")
        print(CONTOH_PROGRAM)
        return CONTOH_PROGRAM

    return source


# ============================================================

if __name__ == '__main__':
    src = _read_source()
    run(src)
