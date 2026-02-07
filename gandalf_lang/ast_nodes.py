from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple

# =========================
# Expressions
# =========================

@dataclass(frozen=True)
class Expr:
    pass

@dataclass(frozen=True)
class Num(Expr):
    value: float | int

@dataclass(frozen=True)
class Str(Expr):
    value: str

@dataclass(frozen=True)
class BoolLit(Expr):
    value: bool

@dataclass(frozen=True)
class NilLit(Expr):
    pass

@dataclass(frozen=True)
class Var(Expr):
    name: str

@dataclass(frozen=True)
class UnaryOp(Expr):
    op: str  # "NEG"
    expr: Expr

@dataclass(frozen=True)
class BinOp(Expr):
    left: Expr
    op: str
    right: Expr

@dataclass(frozen=True)
class Call(Expr):
    name: str
    args: List[Expr]

@dataclass(frozen=True)
class Invoke(Expr):
    target: str
    args: List[Expr]

@dataclass(frozen=True)
class ListLit(Expr):
    items: List[Expr]

@dataclass(frozen=True)
class DictLit(Expr):
    items: List[Tuple[Expr, Expr]]  # (key, value)

@dataclass(frozen=True)
class Index(Expr):
    target: Expr
    index: Expr

# =========================
# Statements
# =========================

@dataclass(frozen=True)
class Stmt:
    pass

@dataclass(frozen=True)
class Inscribe(Stmt):
    name: str
    expr: Expr

@dataclass(frozen=True)
class Proclaim(Stmt):
    expr: Expr

@dataclass(frozen=True)
class ExprStmt(Stmt):
    expr: Expr

@dataclass(frozen=True)
class IfStmt(Stmt):
    cond: Expr
    then_body: List[Stmt]
    else_body: List[Stmt]

@dataclass(frozen=True)
class WhileStmt(Stmt):
    cond: Expr
    body: List[Stmt]

@dataclass(frozen=True)
class SpellDef(Stmt):
    name: str
    params: List[str]
    body: List[Stmt]

@dataclass(frozen=True)
class ReturnStmt(Stmt):
    expr: Optional[Expr]

@dataclass(frozen=True)
class InRegion(Stmt):
    region: str
    body: List[Stmt]

@dataclass(frozen=True)
class BeRace(Stmt):
    race: str

@dataclass(frozen=True)
class ArtifactAction(Stmt):
    action: str
    artifact: str
