# lexer.py — Analisis Leksikal kanggo BasaJog
# Ngasilake 7 kategori token: KEYWORD, IDENTIFIER, NUMBER, STRING,
#                             OPERATOR, DELIMITER, EOF

import re

# ============================================================
# DHAFTAR TEMBUNG KUNCI BasaJog
# ============================================================
KEYWORDS = frozenset({
    'tulis',   # print
    'takon',   # input
    'yen',     # if
    'liyane',  # else
    'baleni',  # while
    'fungsi',  # function
    'bali',    # return
    'bener',   # true
    'salah',   # false
})

# ============================================================
# SPESIFIKASI TOKEN — urutan PENTING kanggo longest-match
# ============================================================
_TOKEN_SPEC = [
    # 1. Komentar (diproses dhisik sadurunge operator /)
    ('_COMMENT_MULTI',   r'/\*[\s\S]*?\*/'),
    ('_COMMENT_SINGLE',  r'//[^\n]*'),

    # 2. String literal (pethik rangkep)
    ('STRING',           r'"([^"\\]|\\.)*"'),

    # 3. Angka — float dhisik supaya longest-match bener
    ('NUMBER',           r'\d+\.\d+|\d+'),

    # 4. Operator akeh-aksara KUDU sadurunge siji-aksara
    ('OPERATOR',         r'==|!=|<=|>=|&&|\|\||[+\-*/=<>!]'),

    # 5. Delimiter
    ('DELIMITER',        r'[(){};,]'),

    # 6. Identifier / Keyword (dibedakake sawise match)
    ('IDENTIFIER',       r'[a-zA-Z_]\w*'),

    # 7. Spasi kosong — dibuwang
    ('_WHITESPACE',      r'[ \t\r\n]+'),

    # 8. Aksara ora sah
    ('_ILLEGAL',         r'.'),
]

_MASTER_RE = re.compile(
    '|'.join(f'(?P<{name}>{pat})' for name, pat in _TOKEN_SPEC),
    re.DOTALL,
)


# ============================================================
# KLAS TOKEN
# ============================================================
class Token:
    __slots__ = ('type', 'value', 'line', 'col')

    def __init__(self, type_, value, line, col):
        self.type  = type_   # salah siji saka 7 kategori
        self.value = value   # teks asli saka source
        self.line  = line
        self.col   = col

    def __repr__(self):
        return (f"Token({self.type:<12} | {self.value!r:<22} "
                f"| larik {self.line:>3}, kol {self.col:>3})")


class LexerError(Exception):
    pass


# ============================================================
# FUNGSI UTAMA LEXER
# ============================================================
def tokenize(source: str):
    """
    Tokenisasi source code BasaJog.
    Mbalekake list Token; token pungkasan tansah jinis 'EOF'.
    """
    tokens     = []
    line       = 1
    line_start = 0

    for mo in _MASTER_RE.finditer(source):
        kind  = mo.lastgroup
        raw   = mo.group()
        col   = mo.start() - line_start + 1

        # ----- buwang spasi & komentar, nganyari nomer larik -----
        if kind in ('_WHITESPACE', '_COMMENT_SINGLE', '_COMMENT_MULTI'):
            nl = raw.count('\n')
            if nl:
                line      += nl
                line_start = mo.start() + raw.rfind('\n') + 1
            continue

        # ----- aksara ora sah -----
        if kind == '_ILLEGAL':
            raise LexerError(
                f"[Kaluputan Lexer]\n"
                f"  Larik : {line}\n"
                f"  Kolom : {col}\n"
                f"  Pesen : aksara ora dikenal '{raw}'"
            )

        # ----- owahi IDENTIFIER → KEYWORD yen perlu -----
        if kind == 'IDENTIFIER' and raw in KEYWORDS:
            kind = 'KEYWORD'

        # ----- simpen STRING tanpa tandha pethik njaba -----
        value = raw[1:-1] if kind == 'STRING' else raw

        tokens.append(Token(kind, value, line, col))

    tokens.append(Token('EOF', '<EOF>', line, 0))
    return tokens
