from __future__ import annotations
from typing import List, Set, Tuple
from .tokens import Token, ParseError
from .ast_nodes import (
    Expr, Num, Str, BoolLit, NilLit, Var, UnaryOp, BinOp, Call, Invoke,
    ListLit, DictLit, Index,
    Stmt, Inscribe, Proclaim, ExprStmt, IfStmt, WhileStmt, SpellDef, ReturnStmt,
    InRegion, BeRace, ArtifactAction
)

class Parser:
    def __init__(self, tokens: List[Token]):
        self.toks = tokens
        self.i = 0

    def peek(self) -> Token:
        return self.toks[self.i]

    def at(self, typ: str) -> bool:
        return self.peek().type == typ

    def advance(self) -> Token:
        t = self.peek()
        if t.type != "EOF":
            self.i += 1
        return t

    def error(self, msg: str) -> None:
        t = self.peek()
        raise ParseError(f"{msg} (line {t.line}, col {t.col})")

    def expect(self, typ: str) -> Token:
        t = self.peek()
        if t.type != typ:
            self.error(f"Expected {typ}, got {t.type}")
        return self.advance()

    def skip_newlines(self) -> None:
        while self.at("NEWLINE"):
            self.advance()

    def parse_program(self) -> List[Stmt]:
        stmts: List[Stmt] = []
        self.skip_newlines()
        while not self.at("EOF"):
            stmts.append(self.parse_stmt())
            self.skip_newlines()
        return stmts

    def parse_block_until(self, end_tokens: Set[str]) -> List[Stmt]:
        body: List[Stmt] = []
        self.skip_newlines()
        while self.peek().type not in end_tokens:
            if self.at("EOF"):
                self.error(f"Unexpected EOF; expected one of {sorted(end_tokens)}")
            body.append(self.parse_stmt())
            self.skip_newlines()
        return body

    def parse_stmt(self) -> Stmt:
        t = self.peek().type

        if t == "INSCRIBE":
            self.advance()
            name = self.expect("IDENT").value
            self.expect("EQ")
            expr = self.parse_expr()
            return Inscribe(name, expr)

        if t == "PROCLAIM":
            self.advance()
            expr = self.parse_expr()
            return Proclaim(expr)

        if t == "BE":
            self.advance()
            race = self.expect("IDENT").value
            return BeRace(race)

        if t == "IN":
            self.advance()
            region = self.expect("IDENT").value
            self.expect("DO")
            body = self.parse_block_until({"END"})
            self.expect("END")
            return InRegion(region, body)

        if t in ("CLAIM", "BEAR", "UNBEAR", "DESTROY"):
            action = self.advance().type
            artifact = self.expect("IDENT").value
            return ArtifactAction(action, artifact)

        if t == "IF":
            self.advance()
            cond = self.parse_expr()
            self.expect("THEN")
            then_body = self.parse_block_until({"ELSE", "END"})
            else_body: List[Stmt] = []
            if self.at("ELSE"):
                self.advance()
                else_body = self.parse_block_until({"END"})
            self.expect("END")
            return IfStmt(cond, then_body, else_body)

        if t == "WHILE":
            self.advance()
            cond = self.parse_expr()
            self.expect("DO")
            body = self.parse_block_until({"END"})
            self.expect("END")
            return WhileStmt(cond, body)

        if t == "SPELL":
            self.advance()
            name = self.expect("IDENT").value
            self.expect("LPAREN")
            params: List[str] = []
            if not self.at("RPAREN"):
                params.append(self.expect("IDENT").value)
                while self.at("COMMA"):
                    self.advance()
                    params.append(self.expect("IDENT").value)
            self.expect("RPAREN")
            self.expect("DO")
            body = self.parse_block_until({"END"})
            self.expect("END")
            return SpellDef(name, params, body)

        if t == "RETURN":
            self.advance()
            if self.at("NEWLINE") or self.at("END") or self.at("ELSE") or self.at("EOF"):
                return ReturnStmt(None)
            expr = self.parse_expr()
            return ReturnStmt(expr)

        # NEW: expression as statement (e.g. push(xs, 1))
        expr = self.parse_expr()
        return ExprStmt(expr)

    # ---- Expressions ----
    def parse_expr(self) -> Expr:
        return self.parse_equality()

    def parse_equality(self) -> Expr:
        expr = self.parse_comparison()
        while self.at("EQEQ") or self.at("NE"):
            op = self.advance().type
            right = self.parse_comparison()
            expr = BinOp(expr, op, right)
        return expr

    def parse_comparison(self) -> Expr:
        expr = self.parse_term()
        while self.at("LT") or self.at("GT") or self.at("LE") or self.at("GE"):
            op = self.advance().type
            right = self.parse_term()
            expr = BinOp(expr, op, right)
        return expr

    def parse_term(self) -> Expr:
        expr = self.parse_factor()
        while self.at("PLUS") or self.at("MINUS"):
            op = self.advance().type
            right = self.parse_factor()
            expr = BinOp(expr, op, right)
        return expr

    def parse_factor(self) -> Expr:
        expr = self.parse_unary()
        while self.at("STAR") or self.at("SLASH"):
            op = self.advance().type
            right = self.parse_unary()
            expr = BinOp(expr, op, right)
        return expr

    def parse_unary(self) -> Expr:
        if self.at("MINUS"):
            self.advance()
            return UnaryOp("NEG", self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self) -> Expr:
        expr = self.parse_primary()
        while self.at("LBRACK"):
            self.advance()
            idx = self.parse_expr()
            self.expect("RBRACK")
            expr = Index(expr, idx)
        return expr

    def parse_primary(self) -> Expr:
        t = self.peek()

        if t.type == "NUMBER":
            self.advance()
            return Num(t.value)

        if t.type == "STRING":
            self.advance()
            return Str(t.value)

        if t.type == "TRUE":
            self.advance()
            return BoolLit(True)

        if t.type == "FALSE":
            self.advance()
            return BoolLit(False)

        if t.type == "NIL":
            self.advance()
            return NilLit()

        if t.type == "INVOKE":
            self.advance()
            target_tok = self.expect("STRING")
            args: List[Expr] = []
            if self.at("WITH"):
                self.advance()
                args.append(self.parse_expr())
                while self.at("COMMA"):
                    self.advance()
                    args.append(self.parse_expr())
            return Invoke(target_tok.value, args)

        if t.type == "LBRACK":
            self.advance()
            items: List[Expr] = []
            if not self.at("RBRACK"):
                items.append(self.parse_expr())
                while self.at("COMMA"):
                    self.advance()
                    items.append(self.parse_expr())
            self.expect("RBRACK")
            return ListLit(items)

        if t.type == "LBRACE":
            self.advance()
            items: List[Tuple[Expr, Expr]] = []
            if not self.at("RBRACE"):
                k = self.parse_dict_key()
                self.expect("COLON")
                v = self.parse_expr()
                items.append((k, v))
                while self.at("COMMA"):
                    self.advance()
                    k = self.parse_dict_key()
                    self.expect("COLON")
                    v = self.parse_expr()
                    items.append((k, v))
            self.expect("RBRACE")
            return DictLit(items)

        if t.type == "IDENT":
            name = self.advance().value
            if self.at("LPAREN"):
                self.advance()
                args: List[Expr] = []
                if not self.at("RPAREN"):
                    args.append(self.parse_expr())
                    while self.at("COMMA"):
                        self.advance()
                        args.append(self.parse_expr())
                self.expect("RPAREN")
                return Call(name, args)
            return Var(name)

        if t.type == "LPAREN":
            self.advance()
            expr = self.parse_expr()
            self.expect("RPAREN")
            return expr

        self.error(f"Unexpected token in expression: {t.type}")

    def parse_dict_key(self) -> Expr:
        t = self.peek()
        if t.type == "STRING":
            self.advance()
            return Str(t.value)
        if t.type == "IDENT":
            self.advance()
            return Str(t.value)
        self.error("Dict key must be STRING or IDENT")
        raise AssertionError("unreachable")
