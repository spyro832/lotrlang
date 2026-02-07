from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Union, Dict, TypeAlias, Callable
import sys
from pathlib import Path
import math

# ============================
# Errors (Light-side / Gandalf)
# ============================

class FizzleError(Exception):
    pass

def fizzle(msg: str) -> None:
    raise FizzleError(f"The spell fizzles... {msg}")

# ============================
# Tokenizer (Lexer)
# ============================

@dataclass(frozen=True)
class Token:
    kind: str
    value: Optional[str]
    pos: int

KEYWORDS = {
    "inscribe": "INSCRIBE",
    "proclaim": "PROCLAIM",
    "if": "IF",
    "then": "THEN",
    "else": "ELSE",
    "while": "WHILE",
    "do": "DO",
    "end": "END",
    "spell": "SPELL",
    "return": "RETURN",
    "invoke": "INVOKE",
    "with": "WITH",
}

TWO_CHAR = {"==", "!=", "<=", ">="}
ONE_CHAR = set("+-*/()<>=") | {","}

def tokenize(src: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0

    def add(kind: str, value: Optional[str] = None, pos: Optional[int] = None):
        tokens.append(Token(kind, value, i if pos is None else pos))

    while i < len(src):
        ch = src[i]

        if ch == "\n":
            add("NEWLINE", "\n", i); i += 1; continue

        if ch.isspace():
            i += 1; continue

        if ch.isdigit():
            start = i
            while i < len(src) and src[i].isdigit():
                i += 1
            add("NUMBER", src[start:i], start)
            continue

        if ch.isalpha() or ch == "_":
            start = i
            while i < len(src) and (src[i].isalnum() or src[i] == "_"):
                i += 1
            text = src[start:i]
            add(KEYWORDS.get(text, "IDENT"), text, start)
            continue

        if ch == '"':
            start = i
            i += 1
            buf: List[str] = []
            while i < len(src) and src[i] != '"':
                if src[i] == "\\" and i + 1 < len(src):
                    nxt = src[i + 1]
                    if nxt == '"':
                        buf.append('"'); i += 2; continue
                    if nxt == "n":
                        buf.append("\n"); i += 2; continue
                buf.append(src[i])
                i += 1
            if i >= len(src) or src[i] != '"':
                fizzle(f'Unterminated string starting at position {start}')
            i += 1
            add("STRING", "".join(buf), start)
            continue

        if i + 1 < len(src) and src[i:i+2] in TWO_CHAR:
            two = src[i:i+2]
            add(two, two, i)
            i += 2
            continue

        if ch in ONE_CHAR:
            add(ch, ch, i)
            i += 1
            continue

        fizzle(f"Unexpected character '{ch}' at position {i}")

    add("EOF", None, len(src))
    return tokens

# ============================
# AST
# ============================

@dataclass
class Num: value: int

@dataclass
class Str: value: str

@dataclass
class Var: name: str

@dataclass
class BinOp:
    op: str
    left: "Expr"
    right: "Expr"

@dataclass
class Call:
    name: str
    args: List["Expr"]

@dataclass
class Invoke:
    target: str
    args: List["Expr"]

Expr: TypeAlias = Union[Num, Str, Var, BinOp, Call, Invoke]

@dataclass
class Inscribe:
    name: str
    expr: Expr

@dataclass
class Proclaim:
    expr: Expr

@dataclass
class IfStmt:
    cond: Expr
    then_body: List["Stmt"]
    else_body: List["Stmt"]

@dataclass
class WhileStmt:
    cond: Expr
    body: List["Stmt"]

@dataclass
class SpellDef:
    name: str
    params: List[str]
    body: List["Stmt"]

@dataclass
class ReturnStmt:
    expr: Optional[Expr]

Stmt: TypeAlias = Union[Inscribe, Proclaim, IfStmt, WhileStmt, SpellDef, ReturnStmt]

# ============================
# Environment
# ============================

Value: TypeAlias = Union[int, str, bool, None]

class Env:
    def __init__(self, parent: Optional["Env"] = None):
        self.parent = parent
        self.vars: Dict[str, Value] = {}

    def get(self, name: str) -> Value:
        if name in self.vars:
            return self.vars[name]
        if self.parent is not None:
            return self.parent.get(name)
        fizzle(f"Unknown rune '{name}'.")

    def set_local(self, name: str, value: Value) -> None:
        self.vars[name] = value

# ============================
# Parser
# ============================

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.i = 0

    def peek(self) -> Token:
        return self.tokens[self.i]

    def advance(self) -> Token:
        tok = self.tokens[self.i]
        self.i += 1
        return tok

    def match(self, *kinds: str) -> Optional[Token]:
        if self.peek().kind in kinds:
            return self.advance()
        return None

    def expect(self, kind: str) -> Token:
        if self.peek().kind != kind:
            fizzle(f"Expected {kind} but found {self.peek().kind} at position {self.peek().pos}")
        return self.advance()

    def parse_program(self) -> List[Stmt]:
        out: List[Stmt] = []
        while self.peek().kind != "EOF":
            if self.peek().kind == "NEWLINE":
                self.advance()
                continue
            out.append(self.parse_stmt())
        return out

    def parse_block(self, end_kinds: tuple[str, ...]) -> List[Stmt]:
        body: List[Stmt] = []
        while self.peek().kind not in end_kinds:
            if self.peek().kind == "NEWLINE":
                self.advance()
                continue
            body.append(self.parse_stmt())
        return body

    def parse_stmt(self) -> Stmt:
        tok = self.peek()

        if tok.kind == "INSCRIBE":
            self.advance()
            name = self.expect("IDENT").value or ""
            self.expect("=")
            return Inscribe(name, self.parse_expr())

        if tok.kind == "PROCLAIM":
            self.advance()
            return Proclaim(self.parse_expr())

        if tok.kind == "RETURN":
            self.advance()
            if self.peek().kind in ("NEWLINE", "END", "ELSE", "EOF"):
                return ReturnStmt(None)
            return ReturnStmt(self.parse_expr())

        if tok.kind == "IF":
            self.advance()
            cond = self.parse_expr()
            self.expect("THEN")
            then_body = self.parse_block(("ELSE", "END"))
            else_body: List[Stmt] = []
            if self.peek().kind == "ELSE":
                self.advance()
                else_body = self.parse_block(("END",))
            self.expect("END")
            return IfStmt(cond, then_body, else_body)

        if tok.kind == "WHILE":
            self.advance()
            cond = self.parse_expr()
            self.expect("DO")
            body = self.parse_block(("END",))
            self.expect("END")
            return WhileStmt(cond, body)

        if tok.kind == "SPELL":
            self.advance()
            name = self.expect("IDENT").value or ""
            self.expect("(")
            params: List[str] = []
            if self.peek().kind != ")":
                params.append(self.expect("IDENT").value or "")
                while self.match(","):
                    params.append(self.expect("IDENT").value or "")
            self.expect(")")
            self.expect("DO")
            body = self.parse_block(("END",))
            self.expect("END")
            return SpellDef(name=name, params=params, body=body)

        # bare expression in REPL: print it
        return Proclaim(self.parse_expr())

    # ---- Expressions (with comparisons) ----

    def parse_expr(self) -> Expr:
        return self.parse_equality()

    def parse_equality(self) -> Expr:
        node = self.parse_comparison()
        while self.peek().kind in ("==", "!="):
            op = self.advance().kind
            right = self.parse_comparison()
            node = BinOp(op, node, right)
        return node

    def parse_comparison(self) -> Expr:
        node = self.parse_term()
        while self.peek().kind in ("<", ">", "<=", ">="):
            op = self.advance().kind
            right = self.parse_term()
            node = BinOp(op, node, right)
        return node

    def parse_term(self) -> Expr:
        node = self.parse_factor()
        while self.peek().kind in ("+", "-"):
            op = self.advance().kind
            right = self.parse_factor()
            node = BinOp(op, node, right)
        return node

    def parse_factor(self) -> Expr:
        node = self.parse_unary()
        while self.peek().kind in ("*", "/"):
            op = self.advance().kind
            right = self.parse_unary()
            node = BinOp(op, node, right)
        return node

    def parse_unary(self) -> Expr:
        if self.peek().kind == "-":
            self.advance()
            inner = self.parse_unary()
            return BinOp("neg", Num(0), inner)
        return self.parse_primary()

    def parse_primary(self) -> Expr:
        tok = self.peek()

        if tok.kind == "NUMBER":
            self.advance()
            return Num(int(tok.value))

        if tok.kind == "STRING":
            self.advance()
            return Str(tok.value or "")

        if tok.kind == "IDENT":
            name = self.advance().value or ""
            if self.peek().kind == "(":
                self.advance()
                args: List[Expr] = []
                if self.peek().kind != ")":
                    args.append(self.parse_expr())
                    while self.match(","):
                        args.append(self.parse_expr())
                self.expect(")")
                return Call(name, args)
            return Var(name)

        if tok.kind == "INVOKE":
            self.advance()
            target = self.expect("STRING").value or ""
            args: List[Expr] = []
            if self.match("WITH"):
                args.append(self.parse_expr())
                while self.match(","):
                    args.append(self.parse_expr())
            return Invoke(target, args)

        if tok.kind == "(":
            self.advance()
            node = self.parse_expr()
            self.expect(")")
            return node

        fizzle(f"Invalid expression at position {tok.pos}")

# ============================
# Runtime
# ============================

class ReturnSignal(Exception):
    def __init__(self, v: Value):
        self.v = v

SAFE_INVOKE: Dict[str, Callable[..., Value]] = {
    "math.sqrt": math.sqrt,
    "math.floor": math.floor,
    "math.ceil": math.ceil,
    "math.pow": math.pow,
    "abs": abs,
    "len": len,
}

def is_truthy(v: Value) -> bool:
    return bool(v)

def eval_expr(e: Expr, env: Env, spells: Dict[str, SpellDef]) -> Value:
    if isinstance(e, Num):
        return e.value
    if isinstance(e, Str):
        return e.value
    if isinstance(e, Var):
        return env.get(e.name)

    if isinstance(e, Invoke):
        if e.target not in SAFE_INVOKE:
            fizzle(f"Forbidden spell '{e.target}'.")
        fn = SAFE_INVOKE[e.target]
        args = [eval_expr(a, env, spells) for a in e.args]
        try:
            return fn(*args)  # type: ignore[misc]
        except Exception as ex:
            fizzle(f"Invoke failed: {ex}")

    if isinstance(e, Call):
        fn = spells.get(e.name)
        if fn is None:
            fizzle(f"Unknown spell '{e.name}'.")
        if len(e.args) != len(fn.params):
            fizzle(f"Spell '{e.name}' expects {len(fn.params)} args but got {len(e.args)}.")
        local = Env(parent=env)
        for p, a in zip(fn.params, e.args):
            local.set_local(p, eval_expr(a, env, spells))
        try:
            for st in fn.body:
                exec_stmt(st, local, spells)
        except ReturnSignal as r:
            return r.v
        return None

    if isinstance(e, BinOp):
        l = eval_expr(e.left, env, spells)
        r = eval_expr(e.right, env, spells)
        op = e.op

        if op == "neg":
            return -int(r)

        if op == "+":
            if isinstance(l, str) or isinstance(r, str):
                return str(l) + str(r)
            return int(l) + int(r)
        if op == "-":
            return int(l) - int(r)
        if op == "*":
            return int(l) * int(r)
        if op == "/":
            if int(r) == 0:
                fizzle("Division by zero is forbidden in this spell.")
            return int(l) // int(r)

        if op == "==":
            return l == r
        if op == "!=":
            return l != r

        if op in ("<", ">", "<=", ">="):
            if not isinstance(l, int) or not isinstance(r, int):
                fizzle(f"Cannot compare non-numbers with '{op}'.")
            if op == "<": return l < r
            if op == ">": return l > r
            if op == "<=": return l <= r
            if op == ">=": return l >= r

        fizzle(f"Unknown operator '{op}'")

    fizzle("Unknown expression node.")

def exec_stmt(s: Stmt, env: Env, spells: Dict[str, SpellDef]) -> None:
    if isinstance(s, Inscribe):
        env.set_local(s.name, eval_expr(s.expr, env, spells))
        return

    if isinstance(s, Proclaim):
        print(eval_expr(s.expr, env, spells))
        return

    if isinstance(s, SpellDef):
        spells[s.name] = s
        return

    if isinstance(s, ReturnStmt):
        raise ReturnSignal(None if s.expr is None else eval_expr(s.expr, env, spells))

    if isinstance(s, IfStmt):
        if is_truthy(eval_expr(s.cond, env, spells)):
            for x in s.then_body:
                exec_stmt(x, env, spells)
        else:
            for x in s.else_body:
                exec_stmt(x, env, spells)
        return

    if isinstance(s, WhileStmt):
        while is_truthy(eval_expr(s.cond, env, spells)):
            for x in s.body:
                exec_stmt(x, env, spells)
        return

    fizzle("Unknown statement.")

def run_source(src: str, env: Env, spells: Dict[str, SpellDef]) -> None:
    prog = Parser(tokenize(src)).parse_program()
    for st in prog:
        exec_stmt(st, env, spells)

# ============================
# REPL (multiline)
# ============================

def needs_more_lines(buf: str) -> bool:
    toks = tokenize(buf)
    opens = sum(1 for t in toks if t.kind in ("IF", "WHILE", "SPELL"))
    ends = sum(1 for t in toks if t.kind == "END")
    return opens > ends

def repl() -> None:
    print("GandalfLang v0.1 (scripts + safe invoke + spells). Type 'exit' to leave.")
    env = Env()
    spells: Dict[str, SpellDef] = {}
    buf = ""

    while True:
        line = input(">>> " if not buf else "... ")
        if not buf and line.strip().lower() in ("exit", "quit"):
            break

        buf += line + "\n"
        if needs_more_lines(buf):
            continue

        try:
            run_source(buf, env, spells)
        except FizzleError as e:
            print(e)
        except ReturnSignal:
            print("The spell fizzles... 'return' can only be used inside a spell.")
        except Exception as e:
            print(f"The spell fizzles... (internal) {e}")

        buf = ""

# ============================
# Main (file or REPL)
# ============================

def main() -> None:
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if not path.exists():
            fizzle(f"Script not found: {path}")
        src = path.read_text(encoding="utf-8")
        env = Env()
        spells: Dict[str, SpellDef] = {}
        run_source(src, env, spells)
    else:
        repl()

if __name__ == "__main__":
    main()
