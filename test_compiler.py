# test_compiler.py — Test Suite BasaJog Mini Compiler
#
# 15 test case:
#   Test  1- 5 : Program sah (kudu kasil)
#   Test  6-10 : Kaluputan Sintaks / Lexer (kudu gagal kanthi error sing trep)
#   Test 11-15 : Kaluputan Makna (kudu gagal kanthi error sing trep)
#
# Jalanke:
#   python test_compiler.py

import sys

from lexer          import tokenize,   LexerError
from parser         import Parser,     ParseError
from semantic       import SemanticAnalyzer, SemanticError
from optimizer      import Optimizer
from code_generator import CodeGenerator, CodeGenError


# ============================================================
# Fungsi pambantu: jalanke kabeh pipeline
# ============================================================

def _pipeline(source):
    """
    Jalanke pipeline jangkep (Lexer -> Parser -> Semantic -> Optimizer -> CodeGen).
    Mbalekake (success:bool, result:any, opt_log:list)
      - success=True  -> result = string output pseudo-assembly
      - success=False -> result = (jeneng_klas_exception, pesen_error)
    """
    try:
        tokens  = tokenize(source)
        ast     = Parser(tokens).parse()
        SemanticAnalyzer().analyze(ast)
        opt     = Optimizer()
        opt_ast = opt.optimize(ast)
        gen     = CodeGenerator()
        gen.generate(opt_ast)
        return True, gen.get_output(), opt.log
    except LexerError    as e:
        return False, ('LexerError',    str(e)), []
    except ParseError    as e:
        return False, ('ParseError',    str(e)), []
    except SemanticError as e:
        return False, ('SemanticError', str(e)), []
    except CodeGenError  as e:
        return False, ('CodeGenError',  str(e)), []


# ============================================================
# DHAFTAR TEST CASE
# ============================================================

TESTS = [

    # ─────────────────────────────────────────────
    # TEST 1-5: PROGRAM SAH
    # ─────────────────────────────────────────────

    {
        'id': 1,
        'name': 'Assignment lan Tulis Prasaja',
        'category': 'Sah',
        'source': (
            'x = 42\n'
            'tulis(x)'
        ),
        'expect': 'success',
        'check_asm': 'PUSH 42',
    },

    {
        'id': 2,
        'name': 'Pamilihan yen / liyane',
        'category': 'Sah',
        'source': (
            'x = 7\n'
            'yen (x > 5) {\n'
            '    tulis("gedhe")\n'
            '} liyane {\n'
            '    tulis("cilik")\n'
            '}'
        ),
        'expect': 'success',
        'check_asm': 'JUMP_IF_FALSE',
    },

    {
        'id': 3,
        'name': 'Pengulangan baleni',
        'category': 'Sah',
        'source': (
            'cacah = 1\n'
            'baleni (cacah <= 3) {\n'
            '    tulis(cacah)\n'
            '    cacah = cacah + 1\n'
            '}'
        ),
        'expect': 'success',
        'check_asm': 'LABEL',
    },

    {
        'id': 4,
        'name': 'Dhefinisi lan Pangundang Fungsi',
        'category': 'Sah',
        'source': (
            'fungsi wuwuh(a, b) {\n'
            '    bali a + b\n'
            '}\n'
            'asil = wuwuh(3, 7)\n'
            'tulis(asil)'
        ),
        'expect': 'success',
        'check_asm': 'CALL wuwuh 2',
    },

    {
        'id': 5,
        'name': 'Constant Folding: 2 + 3 * 4 = 14',
        'category': 'Sah',
        'source': (
            'x = 2 + 3 * 4\n'
            'tulis(x)'
        ),
        'expect': 'success',
        'check_asm': 'PUSH 14',   # sawise optimasi, 2+3*4 kudu dilempit dadi 14
    },

    # ─────────────────────────────────────────────
    # TEST 6-10: KALUPUTAN SINTAKS / LEXER
    # ─────────────────────────────────────────────

    {
        'id': 6,
        'name': "Tandha '(' ilang sawise yen",
        'category': 'Kaluputan Sintaks',
        'source': (
            'x = 5\n'
            'yen x > 5 { tulis("x") }'
        ),
        'expect': 'ParseError',
    },

    {
        'id': 7,
        'name': "Tandha '}' ilang ing blok yen",
        'category': 'Kaluputan Sintaks',
        'source': (
            'yen (bener) {\n'
            '    tulis("ok")'
            # ora ana tutup }
        ),
        'expect': 'ParseError',
    },

    {
        'id': 8,
        'name': "liyane tanpa yen sadurunge",
        'category': 'Kaluputan Sintaks',
        'source': 'liyane { tulis("salah") }',
        'expect': 'ParseError',
    },

    {
        'id': 9,
        'name': "Aksara ora sah '@'",
        'category': 'Kaluputan Sintaks',
        'source': 'x = 10 @ 5',
        'expect': 'LexerError',
    },

    {
        'id': 10,
        'name': "Tandha ')' ilang ing pangundang tulis",
        'category': 'Kaluputan Sintaks',
        'source': 'tulis("halo"',
        'expect': 'ParseError',
    },

    # ─────────────────────────────────────────────
    # TEST 11-15: KALUPUTAN MAKNA
    # ─────────────────────────────────────────────

    {
        'id': 11,
        'name': 'Variabel durung dideklarasi',
        'category': 'Kaluputan Makna',
        'source': 'tulis(variabelOraAna)',
        'expect': 'SemanticError',
    },

    {
        'id': 12,
        'name': 'Fungsi durung didefinisi',
        'category': 'Kaluputan Makna',
        'source': 'asil = etungRahasia(5, 3)',
        'expect': 'SemanticError',
    },

    {
        'id': 13,
        'name': 'Cacah argumen salah (1 param, 2 argumen)',
        'category': 'Kaluputan Makna',
        'source': (
            'fungsi f(a) { bali a }\n'
            'asil = f(1, 2)'
        ),
        'expect': 'SemanticError',
    },

    {
        'id': 14,
        'name': 'Tipe ora cocog: string + int',
        'category': 'Kaluputan Makna',
        'source': 'x = "teks" + 5',
        'expect': 'SemanticError',
    },

    {
        'id': 15,
        'name': "'bali' dienggo ing njaba fungsi",
        'category': 'Kaluputan Makna',
        'source': (
            'x = 5\n'
            'bali x'
        ),
        'expect': 'SemanticError',
    },
]


# ============================================================
# Runner
# ============================================================

def run_all(verbose=False):
    W      = 74
    LULUS  = 'LULUS'
    GAGAL  = 'GAGAL'

    print('=' * W)
    print('  BasaJog Mini Compiler -- Test Suite (15 Test Case)')
    print('=' * W)
    header = f"  {'No':<4} {'Jeneng Test':<36} {'Kategori':<18} Asil"
    print(header)
    print('-' * W)

    passed  = 0
    failed  = []

    for t in TESTS:
        ok, out, opt_log = _pipeline(t['source'])
        expected = t['expect']

        result = GAGAL
        note   = ''

        if expected == 'success':
            if ok:
                # cek instruksi assembly spesifik yen dijaluk
                if 'check_asm' in t and t['check_asm'] not in out:
                    note = f"Assembly ora ngandhut '{t['check_asm']}'"
                else:
                    result = LULUS
                    note   = 'Pipeline rampung tanpa error'
            else:
                note = f"Error ora dinyana: {out[0]} -- {out[1][:60]}"
        else:
            # test sing kudu ngasilake error
            if not ok:
                got = out[0]
                if got == expected:
                    result = LULUS
                    note   = f'{expected} kadeteksi kanthi bener'
                else:
                    note   = f"Dikarepake {expected}, nanging {got}"
            else:
                note = 'Mesthine error, nanging pipeline kasil tanpa error'

        if result == LULUS:
            passed += 1
            mark = '[OK]'
        else:
            failed.append((t['id'], t['name'], note))
            mark = '[XX]'

        print(f"  {t['id']:<4} {t['name'][:35]:<36} {t['category']:<18} {result} {mark}")

    print('-' * W)
    print(f"  Gunggung: {len(TESTS)}  |  Lulus: {passed}  |  Gagal: {len(TESTS)-passed}")
    print('=' * W)

    if failed:
        print('\nRincian kagagalan:')
        for fid, fname, fnote in failed:
            print(f"  Test {fid:>2}: {fname}")
            print(f"           {fnote}")

    if verbose and passed == len(TESTS):
        print('\nKabeh test lulus. Compiler BasaJog siap dienggo.')

    return passed == len(TESTS)


# ============================================================
# Rincian output saben test (mode verbose)
# ============================================================

def run_detail(test_id):
    """Nampilake output jangkep kanggo siji test case."""
    t = next((t for t in TESTS if t['id'] == test_id), None)
    if t is None:
        print(f"Test {test_id} ora ketemu.")
        return

    print(f"\n{'='*60}")
    print(f"Test {t['id']}: {t['name']}")
    print(f"Kategori: {t['category']}")
    print(f"{'='*60}")
    print("Source:")
    for ln, line in enumerate(t['source'].splitlines(), 1):
        print(f"  {ln:>3}: {line}")

    print('\nAsil pipeline:')
    ok, out, opt_log = _pipeline(t['source'])
    if ok:
        print(f"  Status: KASIL")
        if opt_log:
            print(f"  Optimasi ({len(opt_log)} langkah):")
            for entry in opt_log:
                print(f"  {entry}")
        print(f"\n  Pseudo-Assembly:")
        for line in out.splitlines():
            print(f"    {line}")
    else:
        print(f"  Status: GAGAL")
        print(f"  Jinis Error: {out[0]}")
        print(f"  Pesen:\n{out[1]}")


# ============================================================

if __name__ == '__main__':
    args = sys.argv[1:]

    if args and args[0].isdigit():
        run_detail(int(args[0]))
    else:
        success = run_all(verbose=True)
        sys.exit(0 if success else 1)
