# parser.py — Recursive Descent Parser kanggo BasaJog
#
# GRAMMAR (EBNF):
# ============================================================
# Program      ::= Statement*
# Statement    ::= IfStmt
#               |  WhileStmt
#               |  FuncDef
#               |  ReturnStmt
#               |  PrintStmt
#               |  Assignment
#               |  ExprStmt
#
# Assignment   ::= IDENTIFIER '=' Expression ';'?
# IfStmt       ::= 'yen' '(' Expression ')' Block
#                  ( 'liyane' Block )?
# WhileStmt    ::= 'baleni' '(' Expression ')' Block
# FuncDef      ::= 'fungsi' IDENTIFIER '(' ParamList? ')' Block
# ReturnStmt   ::= 'bali' Expression? ';'?
# PrintStmt    ::= 'tulis' '(' Expression ')' ';'?
# ExprStmt     ::= Expression ';'?
# Block        ::= '{' Statement* '}'
# ParamList    ::= IDENTIFIER ( ',' IDENTIFIER )*
#
# Expression   ::= LogicOr
# LogicOr      ::= LogicAnd ( '||' LogicAnd )*
# LogicAnd     ::= Comparison ( '&&' Comparison )*
# Comparison   ::= Addition ( ('=='|'!='|'<'|'>'|'<='|'>=') Addition )?
# Addition     ::= Multiplication ( ('+'|'-') Multiplication )*
# Multiplication ::= Unary ( ('*'|'/') Unary )*
# Unary        ::= ('!'|'-') Unary | Primary
# Primary      ::= NUMBER | STRING | 'bener' | 'salah'
#               |  'takon' '(' STRING? ')'
#               |  IDENTIFIER '(' ArgList? ')'   (pangundang fungsi)
#               |  IDENTIFIER
#               |  '(' Expression ')'
# ArgList      ::= Expression ( ',' Expression )*
# ============================================================

from ast_nodes import (
    ProgramNode, NumberNode, StringNode, BoolNode,
    IdentifierNode, AssignNode, BinOpNode, UnaryOpNode,
    IfNode, WhileNode, FunctionNode, CallNode,
    PrintNode, InputNode, ReturnNode, BlockNode,
)


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0

    # ----------------------------------------------------------
    # Pambantu
    # ----------------------------------------------------------

    def _cur(self):
        """Token saiki."""
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _peek(self, offset=1):
        """Token sabanjure (offset=1 = siji langkah ngarep)."""
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else None

    def _advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _expect(self, type_, value=None):
        """Njupuk token sing dikarepake; nguncalake ParseError yen ora cocog."""
        tok = self._cur()
        if tok is None or tok.type == 'EOF':
            desc = f"'{value}'" if value else type_
            raise ParseError(
                f"[Kaluputan Sintaks]\n"
                f"  Larik : (pungkasan berkas)\n"
                f"  Pesen : dikarepake {desc}, nanging berkas rampung dadakan"
            )
        if tok.type != type_:
            desc = f"'{value}'" if value else type_
            raise ParseError(
                f"[Kaluputan Sintaks]\n"
                f"  Larik : {tok.line}\n"
                f"  Kolom : {tok.col}\n"
                f"  Pesen : dikarepake {desc}, nanging ketemu '{tok.value}'"
            )
        if value is not None and tok.value != value:
            raise ParseError(
                f"[Kaluputan Sintaks]\n"
                f"  Larik : {tok.line}\n"
                f"  Kolom : {tok.col}\n"
                f"  Pesen : dikarepake '{value}', nanging ketemu '{tok.value}'"
            )
        return self._advance()

    def _match(self, type_, value=None):
        """Njupuk token yen cocog; mbalekake token utawa None."""
        tok = self._cur()
        if tok and tok.type == type_:
            if value is None or tok.value == value:
                return self._advance()
        return None

    def _is_kw(self, val):
        tok = self._cur()
        return tok and tok.type == 'KEYWORD' and tok.value == val

    def _is_delim(self, val):
        tok = self._cur()
        return tok and tok.type == 'DELIMITER' and tok.value == val

    def _is_op(self, val):
        tok = self._cur()
        return tok and tok.type == 'OPERATOR' and tok.value == val

    # ----------------------------------------------------------
    # Lawang mlebu
    # ----------------------------------------------------------

    def parse(self):
        stmts = []
        while self._cur() and self._cur().type != 'EOF':
            stmts.append(self._statement())
        return ProgramNode(stmts)

    # ----------------------------------------------------------
    # Statement
    # ----------------------------------------------------------

    def _statement(self):
        tok = self._cur()

        if tok.type == 'KEYWORD':
            if tok.value == 'yen':
                return self._if_stmt()
            if tok.value == 'baleni':
                return self._while_stmt()
            if tok.value == 'fungsi':
                return self._func_def()
            if tok.value == 'bali':
                return self._return_stmt()
            if tok.value == 'tulis':
                return self._print_stmt()
            if tok.value == 'liyane':
                raise ParseError(
                    f"[Kaluputan Sintaks]\n"
                    f"  Larik : {tok.line}\n"
                    f"  Pesen : 'liyane' ora oleh metu tanpa 'yen' sadurunge"
                )
            # 'takon', 'bener', 'salah' → expression statement
            node = self._expression()
            self._match('DELIMITER', ';')
            return node

        # assignment: IDENTIFIER '=' expr  (dudu '==')
        if (tok.type == 'IDENTIFIER'
                and self._peek()
                and self._peek().type == 'OPERATOR'
                and self._peek().value == '='):
            return self._assignment()

        # expression statement
        node = self._expression()
        self._match('DELIMITER', ';')
        return node

    def _assignment(self):
        name_tok = self._expect('IDENTIFIER')
        self._expect('OPERATOR', '=')
        value = self._expression()
        self._match('DELIMITER', ';')
        return AssignNode(name_tok.value, value, name_tok.line)

    def _if_stmt(self):
        tok = self._expect('KEYWORD', 'yen')
        self._expect('DELIMITER', '(')
        condition = self._expression()
        self._expect('DELIMITER', ')')
        self._expect('DELIMITER', '{')
        then_block = self._block()
        self._expect('DELIMITER', '}')

        else_block = None
        if self._is_kw('liyane'):
            self._advance()
            self._expect('DELIMITER', '{')
            else_block = self._block()
            self._expect('DELIMITER', '}')

        return IfNode(condition, then_block, else_block, tok.line)

    def _while_stmt(self):
        tok = self._expect('KEYWORD', 'baleni')
        self._expect('DELIMITER', '(')
        condition = self._expression()
        self._expect('DELIMITER', ')')
        self._expect('DELIMITER', '{')
        body = self._block()
        self._expect('DELIMITER', '}')
        return WhileNode(condition, body, tok.line)

    def _func_def(self):
        tok      = self._expect('KEYWORD', 'fungsi')
        name_tok = self._expect('IDENTIFIER')

        self._expect('DELIMITER', '(')
        params = []
        if self._cur() and self._cur().type == 'IDENTIFIER':
            params.append(self._advance().value)
            while self._match('DELIMITER', ','):
                params.append(self._expect('IDENTIFIER').value)
        self._expect('DELIMITER', ')')

        self._expect('DELIMITER', '{')
        body = self._block()
        self._expect('DELIMITER', '}')

        return FunctionNode(name_tok.value, params, body, tok.line)

    def _return_stmt(self):
        tok = self._expect('KEYWORD', 'bali')
        value = None
        cur = self._cur()
        # Mung parse ekspresi yen token sabanjure bisa MIWITI sawijining ekspresi.
        # Iki nyegah 'bali' sing diterusake tembung kunci kontrol (yen, baleni, fungsi, lsp.)
        # supaya ora keliru nyoba mem-parse tembung kunci kasebut dadi ekspresi.
        _expr_start_types = {'NUMBER', 'STRING', 'IDENTIFIER'}
        _expr_start_kw    = {'bener', 'salah', 'takon'}
        can_start = (
            cur is not None and cur.type != 'EOF' and (
                cur.type in _expr_start_types
                or (cur.type == 'OPERATOR'  and cur.value in ('-', '!'))
                or (cur.type == 'DELIMITER' and cur.value == '(')
                or (cur.type == 'KEYWORD'   and cur.value in _expr_start_kw)
            )
        )
        if can_start:
            value = self._expression()
        self._match('DELIMITER', ';')
        return ReturnNode(value, tok.line)

    def _print_stmt(self):
        tok = self._expect('KEYWORD', 'tulis')
        self._expect('DELIMITER', '(')
        value = self._expression()
        self._expect('DELIMITER', ')')
        self._match('DELIMITER', ';')
        return PrintNode(value, tok.line)

    def _block(self):
        stmts = []
        while self._cur() and not self._is_delim('}') and self._cur().type != 'EOF':
            stmts.append(self._statement())
        return BlockNode(stmts)

    # ----------------------------------------------------------
    # Expression — undhak-undhakan precedence
    # ----------------------------------------------------------

    def _expression(self):
        return self._logic_or()

    def _logic_or(self):
        node = self._logic_and()
        while self._is_op('||'):
            op   = self._advance().value
            node = BinOpNode(node, op, self._logic_and(), node.line)
        return node

    def _logic_and(self):
        node = self._comparison()
        while self._is_op('&&'):
            op   = self._advance().value
            node = BinOpNode(node, op, self._comparison(), node.line)
        return node

    def _comparison(self):
        node = self._addition()
        while self._cur() and self._cur().type == 'OPERATOR' and \
              self._cur().value in ('==', '!=', '<', '>', '<=', '>='):
            op   = self._advance().value
            node = BinOpNode(node, op, self._addition(), node.line)
        return node

    def _addition(self):
        node = self._multiplication()
        while self._cur() and self._cur().type == 'OPERATOR' and \
              self._cur().value in ('+', '-'):
            op   = self._advance().value
            node = BinOpNode(node, op, self._multiplication(), node.line)
        return node

    def _multiplication(self):
        node = self._unary()
        while self._cur() and self._cur().type == 'OPERATOR' and \
              self._cur().value in ('*', '/'):
            op   = self._advance().value
            node = BinOpNode(node, op, self._unary(), node.line)
        return node

    def _unary(self):
        tok = self._cur()
        if tok and tok.type == 'OPERATOR' and tok.value in ('-', '!'):
            op = self._advance().value
            return UnaryOpNode(op, self._unary(), tok.line)
        return self._primary()

    def _primary(self):
        tok = self._cur()

        if tok is None or tok.type == 'EOF':
            raise ParseError("Kaluputan Sintaks: Ekspresi ora jangkep ing pungkasan berkas")

        # Angka
        if tok.type == 'NUMBER':
            self._advance()
            return NumberNode(tok.value, tok.line)

        # String
        if tok.type == 'STRING':
            self._advance()
            return StringNode(tok.value, tok.line)   # aji wis tanpa pethik

        # Boolean
        if tok.type == 'KEYWORD' and tok.value == 'bener':
            self._advance()
            return BoolNode(True, tok.line)

        if tok.type == 'KEYWORD' and tok.value == 'salah':
            self._advance()
            return BoolNode(False, tok.line)

        # takon (input)
        if tok.type == 'KEYWORD' and tok.value == 'takon':
            return self._input_expr()

        # Identifier utawa pangundang fungsi
        if tok.type == 'IDENTIFIER':
            self._advance()
            if self._is_delim('('):
                return self._call_expr(tok)
            return IdentifierNode(tok.value, tok.line)

        # Ekspresi ing njero kurung
        if tok.type == 'DELIMITER' and tok.value == '(':
            self._advance()
            node = self._expression()
            self._expect('DELIMITER', ')')
            return node

        raise ParseError(
            f"[Kaluputan Sintaks]\n"
            f"  Larik : {tok.line}\n"
            f"  Kolom : {tok.col}\n"
            f"  Pesen : token ora dinyana '{tok.value}' (jinis: {tok.type})"
        )

    def _input_expr(self):
        tok = self._expect('KEYWORD', 'takon')
        self._expect('DELIMITER', '(')
        prompt = None
        if self._cur() and self._cur().type == 'STRING':
            pt = self._advance()
            prompt = StringNode(pt.value, pt.line)
        self._expect('DELIMITER', ')')
        return InputNode(prompt, tok.line)

    def _call_expr(self, name_tok):
        self._expect('DELIMITER', '(')
        args = []
        if not self._is_delim(')'):
            args.append(self._expression())
            while self._match('DELIMITER', ','):
                args.append(self._expression())
        self._expect('DELIMITER', ')')
        return CallNode(name_tok.value, args, name_tok.line)
