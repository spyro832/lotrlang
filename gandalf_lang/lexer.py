from __future__ import annotations
from typing import List
from .tokens import Token, LexError

KEYWORDS = {
    # original
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

    # regions
    "in": "IN",
    "within": "IN",

    # races
    "be": "BE",
    "as": "BE",

    # artifacts
    "claim": "CLAIM",
    "bear": "BEAR",
    "unbear": "UNBEAR",
    "destroy": "DESTROY",

    # literals (NEW)
    "true": "TRUE",
    "false": "FALSE",
    "nil": "NIL",
    "none": "NIL",

    # LOTR flavor aliases
    "bind": "INSCRIBE",
    "say": "PROCLAIM",
    "speak": "PROCLAIM",
    "when": "IF",
    "otherwise": "ELSE",
    "endure": "WHILE",
    "upon": "THEN",
    "weave": "SPELL",
    "yield": "RETURN",
    "summon": "INVOKE",

    # artifact aliases
    "take": "CLAIM",
    "wear": "BEAR",
    "remove": "UNBEAR",
    "unmake": "DESTROY",
}

TWO_CHAR_OPS = {"==": "EQEQ", "!=": "NE", "<=": "LE", ">=": "GE"}
ONE_CHAR = {
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
    "(": "LPAREN",
    ")": "RPAREN",
    "[": "LBRACK",
    "]": "RBRACK",
    "{": "LBRACE",
    "}": "RBRACE",
    "<": "LT",
    ">": "GT",
    "=": "EQ",
    ",": "COMMA",
    ":": "COLON",
}

def tokenize(src: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    line, col = 1, 1
    n = len(src)

    def peek(k: int = 0) -> str:
        return src[i + k] if i + k < n else "\0"

    while i < n:
        ch = src[i]

        if ch == "\n":
            tokens.append(Token("NEWLINE", "\n", line, col))
            i += 1
            line += 1
            col = 1
            continue

        if ch.isspace():
            i += 1
            col += 1
            continue

        if ch == "#":
            while i < n and src[i] != "\n":
                i += 1
                col += 1
            continue

        start_line, start_col = line, col

        op2 = ch + peek(1)
        if op2 in TWO_CHAR_OPS:
            tokens.append(Token(TWO_CHAR_OPS[op2], op2, start_line, start_col))
            i += 2
            col += 2
            continue

        if ch in ONE_CHAR:
            tokens.append(Token(ONE_CHAR[ch], ch, start_line, start_col))
            i += 1
            col += 1
            continue

        if ch == '"':
            i += 1
            col += 1
            out = []
            while i < n:
                c = src[i]
                if c == '"':
                    i += 1
                    col += 1
                    tokens.append(Token("STRING", "".join(out), start_line, start_col))
                    break
                if c == "\\":
                    if i + 1 >= n:
                        raise LexError(f"Unterminated escape in string (line {line}, col {col})")
                    nxt = src[i + 1]
                    if nxt == "n":
                        out.append("\n")
                    elif nxt == '"':
                        out.append('"')
                    elif nxt == "\\":
                        out.append("\\")
                    else:
                        out.append(nxt)
                    i += 2
                    col += 2
                    continue
                if c == "\n":
                    raise LexError(f"Unterminated string literal (line {line}, col {col})")
                out.append(c)
                i += 1
                col += 1
            else:
                raise LexError(f"Unterminated string literal (line {start_line}, col {start_col})")
            continue

        if ch.isdigit():
            j = i
            has_dot = False
            while j < n and (src[j].isdigit() or (src[j] == "." and not has_dot)):
                if src[j] == ".":
                    has_dot = True
                j += 1
            num_str = src[i:j]
            try:
                value = float(num_str) if "." in num_str else int(num_str)
            except ValueError:
                raise LexError(f"Invalid number '{num_str}' (line {start_line}, col {start_col})")
            tokens.append(Token("NUMBER", value, start_line, start_col))
            col += (j - i)
            i = j
            continue

        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"):
                j += 1
            word = src[i:j]
            typ = KEYWORDS.get(word, "IDENT")
            tokens.append(Token(typ, word, start_line, start_col))
            col += (j - i)
            i = j
            continue

        raise LexError(f"Unexpected character '{ch}' (line {line}, col {col})")

    tokens.append(Token("EOF", None, line, col))
    return tokens
