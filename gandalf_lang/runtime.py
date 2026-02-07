from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .tokens import RuntimeError
from .lexer import tokenize
from .parser import Parser
from .ast_nodes import (
    # expr
    Expr, Num, Str, BoolLit, NilLit, Var, UnaryOp, BinOp, Call, Invoke,
    ListLit, DictLit, Index,
    # stmt
    Stmt, Inscribe, Proclaim, ExprStmt, IfStmt, WhileStmt, SpellDef, ReturnStmt,
    InRegion, BeRace, ArtifactAction
)

# -------------------------
# Helpers
# -------------------------
def is_number(x: Any) -> bool:
    return type(x) in (int, float)

def truthy(x: Any) -> bool:
    return bool(x)

class ReturnSignal(Exception):
    def __init__(self, value: Any):
        self.value = value

class Env:
    def __init__(self, parent: Optional["Env"] = None):
        self.parent = parent
        self.values: Dict[str, Any] = {}

    def get(self, name: str) -> Any:
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name)
        raise RuntimeError(f"Unknown name: {name}")

    def set_local(self, name: str, value: Any) -> None:
        self.values[name] = value

    def set(self, name: str, value: Any) -> None:
        if name in self.values:
            self.values[name] = value
            return
        if self.parent:
            self.parent.set(name, value)
            return
        self.values[name] = value

@dataclass(frozen=True)
class Spell:
    params: List[str]
    body: List[Stmt]

# -------------------------
# SAFE invoke
# -------------------------
import math
SAFE_INVOKE: Dict[str, Callable[..., Any]] = {
    "math.sqrt": math.sqrt,
    "math.floor": math.floor,
    "math.ceil": math.ceil,
    "math.pow": math.pow,
    "abs": abs,
    "len": len,
}

# -------------------------
# LOTR built-ins base
# -------------------------
def _ring_name() -> str:
    return "One Ring"

def _mellon() -> str:
    return "mellon"

def _gandalf(name: Any = "the Grey") -> str:
    return f"A wizard is never late, nor is he early. He arrives precisely when he means to. ({name})"

def _you_shall_not_pass() -> str:
    return "You shall not pass!"

BUILTINS_BASE: Dict[str, Callable[..., Any]] = {
    "ring": _ring_name,
    "mellon": _mellon,
    "gandalf": _gandalf,
    "you_shall_not_pass": _you_shall_not_pass,
    "precious": _ring_name,
}

# -------------------------
# Interpreter
# -------------------------
class Interpreter:
    def __init__(self):
        self.global_env = Env()
        self.spells: Dict[str, Spell] = {}

        # context
        self._region_stack: List[str] = ["wilds"]
        self._race: str = "man"

        # artifacts
        self._owned: Dict[str, bool] = {"ring": False, "mithril": False, "phial": False}
        self._bearing_ring: bool = False
        self._ring_destroyed: bool = False

        self._sync_context_globals()
        self.global_env.set_local("ONE_RING", "One Ring")
        self.global_env.set_local("MELLON", "mellon")

    # -------------------------
    # Context
    # -------------------------
    def current_region(self) -> str:
        return self._region_stack[-1] if self._region_stack else "wilds"

    def current_race(self) -> str:
        return self._race

    def push_region(self, region: str) -> None:
        self._region_stack.append(region)
        self._sync_context_globals()

    def pop_region(self) -> None:
        if len(self._region_stack) > 1:
            self._region_stack.pop()
        self._sync_context_globals()

    def set_race(self, race: str) -> None:
        self._race = race
        self._sync_context_globals()

    def _sync_context_globals(self) -> None:
        # context globals
        self.global_env.set_local("REGION", self.current_region())
        self.global_env.set_local("RACE", self.current_race())

        # artifact globals
        self.global_env.set_local("HAS_RING", bool(self._owned.get("ring", False)))
        self.global_env.set_local("BEARING_RING", bool(self._bearing_ring))
        self.global_env.set_local("RING_DESTROYED", bool(self._ring_destroyed))

    # -------------------------
    # Output flavor (regions + Ring)
    # -------------------------
    def _region_print(self, val: Any) -> None:
        if isinstance(val, float) and val.is_integer():
            val = int(val)

        region = self.current_region()

        # Ring influence
        if self._bearing_ring and not self._ring_destroyed:
            if region == "shire":
                print(f"{val} (a whisper follows you)")
                return
            if region == "moria":
                print(val)
                print(f"(echo) {val}")
                print("(echo) a whisper in the dark...")
                return
            if region == "mordor":
                print(f"[EYE] {val}")
                return
            if region == "rivendell":
                print(f"«{val}»")
                print("«…and the Ring feels heavy.»")
                return

        # normal region behavior
        if region == "shire":
            print(val)
            return
        if region == "moria":
            print(val)
            print(f"(echo) {val}")
            return
        if region == "mordor":
            print(f"[MORDOR] {val}")
            return
        if region == "rivendell":
            print(f"«{val}»")
            return

        print(val)

    # -------------------------
    # LOTR built-ins (region/race/artifact aware)
    # -------------------------
    def _palantir(self, x: Any) -> str:
        region = self.current_region()
        if region == "mordor":
            return f"Palantír burns: {x}"
        if region == "moria":
            return f"Palantír echoes: {x}"
        if region == "shire":
            return f"Palantír gently shows: {x}"
        return f"Palantír shows: {x}"

    def _vision(self, x: Any) -> str:
        race = self.current_race()
        region = self.current_region()

        if race == "elf":
            msg = f"Elf-sight sees beyond {x}"
        elif race == "dwarf":
            msg = f"Dwarf-sight measures exactly {x}"
        elif race == "hobbit":
            msg = f"Hobbit-sight notices small things within {x}"
        elif race == "wizard":
            msg = f"Wizard-sight pierces {x}"
        else:
            msg = f"Man-sight sees {x}"

        if region == "moria":
            msg += " (in darkness)"
        elif region == "rivendell":
            msg += " (in starlight)"
        elif region == "mordor":
            msg += " (under the Eye)"

        if self._bearing_ring and not self._ring_destroyed:
            msg += " (and the Ring calls to you)"
        return msg

    def _stamina(self, x: Any) -> str:
        race = self.current_race()
        if race == "hobbit":
            return f"Hobbit endurance holds for {x} miles"
        if race == "dwarf":
            return f"Dwarf stamina digs through {x} days"
        if race == "elf":
            return f"Elf stamina runs for {x} leagues"
        if race == "wizard":
            return f"Wizard stamina endures for {x} ages"
        return f"Stamina lasts {x}"

    def _craft(self, x: Any) -> str:
        race = self.current_race()
        if race == "dwarf":
            return f"Dwarven craft forges: {x}"
        if race == "elf":
            return f"Elven craft weaves: {x}"
        if race == "hobbit":
            return f"Hobbit craft bakes: {x}"
        if race == "wizard":
            return f"Wizard craft inscribes: {x}"
        return f"Craft makes: {x}"

    def _spellcraft(self) -> str:
        race = self.current_race()
        if race != "wizard":
            return "No spellcraft granted."
        if self._bearing_ring and not self._ring_destroyed:
            return "Spellcraft surges… but the Ring twists your will."
        return "Spellcraft granted: the staff hums with power."

    # -------------------------
    # Artifacts built-ins
    # -------------------------
    def _inventory(self) -> str:
        items = [k for k, v in self._owned.items() if v]
        if not items:
            return "Inventory: (empty)"
        extra = []
        if self._bearing_ring and self._owned.get("ring", False) and not self._ring_destroyed:
            extra.append("ring (borne)")
        return "Inventory: " + ", ".join(sorted(set(items + extra)))

    def _power(self) -> str:
        region = self.current_region()
        race = self.current_race()

        base = 1
        if race == "wizard":
            base += 3
        elif race == "elf":
            base += 2
        elif race == "dwarf":
            base += 1
        elif race == "hobbit":
            base += 1

        if self._owned.get("mithril", False):
            base += 1
        if self._owned.get("phial", False):
            base += 1
        if self._bearing_ring and not self._ring_destroyed:
            base += 5

        if region == "mordor" and self._bearing_ring and not self._ring_destroyed:
            return f"Power: {base} (the Eye turns toward you)"
        if region == "shire":
            return f"Power: {base} (quiet strength)"
        if region == "rivendell":
            return f"Power: {base} (ancient grace)"
        if region == "moria":
            return f"Power: {base} (echoing halls)"
        return f"Power: {base}"

    def _corruption(self) -> str:
        c = 0
        if self._owned.get("ring", False) and not self._ring_destroyed:
            c += 2
        if self._bearing_ring and not self._ring_destroyed:
            c += 6
        if self.current_region() == "mordor":
            c += 2
        if self.current_race() == "hobbit":
            c -= 1
        if self.current_race() == "wizard":
            c += 1
        if self._owned.get("phial", False):
            c -= 1
        if c < 0:
            c = 0
        return f"Corruption: {c}"

    # -------------------------
    # Artifact actions
    # -------------------------
    def _normalize_artifact(self, name: str) -> str:
        return name.strip().lower()

    def do_artifact_action(self, action: str, artifact_raw: str) -> None:
        artifact = self._normalize_artifact(artifact_raw)
        allowed = {"ring", "mithril", "phial"}
        if artifact not in allowed:
            raise RuntimeError(f"Unknown artifact: {artifact_raw}. Allowed: {', '.join(sorted(allowed))}")

        if action == "CLAIM":
            if artifact == "ring" and self._ring_destroyed:
                raise RuntimeError("The Ring is destroyed. It cannot be claimed again.")
            self._owned[artifact] = True

        elif action == "BEAR":
            if artifact != "ring":
                raise RuntimeError("Only the Ring can be borne (bear ring).")
            if not self._owned.get("ring", False):
                raise RuntimeError("You do not possess the Ring. (claim ring first)")
            if self._ring_destroyed:
                raise RuntimeError("The Ring is destroyed. It cannot be borne.")
            self._bearing_ring = True

        elif action == "UNBEAR":
            if artifact != "ring":
                raise RuntimeError("Only the Ring can be unborne (unbear ring).")
            self._bearing_ring = False

        elif action == "DESTROY":
            if artifact == "ring":
                self._owned["ring"] = False
                self._bearing_ring = False
                self._ring_destroyed = True
            else:
                self._owned[artifact] = False
        else:
            raise RuntimeError(f"Unknown artifact action: {action}")

        self._sync_context_globals()

    # -------------------------
    # Generic python-like built-ins
    # -------------------------
    def _length(self, x: Any) -> int:
        try:
            return len(x)
        except Exception:
            raise RuntimeError(f"length(x) not supported for {type(x).__name__}")

    def _push(self, xs: Any, item: Any) -> Any:
        if not isinstance(xs, list):
            raise RuntimeError("push(list, item) expects a list")
        xs.append(item)
        return xs

    def _pop(self, xs: Any) -> Any:
        if not isinstance(xs, list):
            raise RuntimeError("pop(list) expects a list")
        if len(xs) == 0:
            raise RuntimeError("pop(list) on empty list")
        return xs.pop()

    def _get(self, m: Any, k: Any) -> Any:
        if not isinstance(m, dict):
            raise RuntimeError("get(map, key) expects a dict")
        return m.get(k)

    def _put(self, m: Any, k: Any, v: Any) -> Any:
        if not isinstance(m, dict):
            raise RuntimeError("put(map, key, value) expects a dict")
        m[k] = v
        return m

    def _has(self, m: Any, k: Any) -> bool:
        if not isinstance(m, dict):
            raise RuntimeError("has(map, key) expects a dict")
        return k in m

    def _keys(self, m: Any) -> List[Any]:
        if not isinstance(m, dict):
            raise RuntimeError("keys(map) expects a dict")
        return list(m.keys())

    def _values(self, m: Any) -> List[Any]:
        if not isinstance(m, dict):
            raise RuntimeError("values(map) expects a dict")
        return list(m.values())

    # -------------------------
    # Expr evaluation
    # -------------------------
    def eval_expr(self, env: Env, e: Expr) -> Any:
        if isinstance(e, Num):
            return e.value
        if isinstance(e, Str):
            return e.value
        if isinstance(e, BoolLit):
            return e.value
        if isinstance(e, NilLit):
            return None
        if isinstance(e, Var):
            return env.get(e.name)

        if isinstance(e, ListLit):
            return [self.eval_expr(env, it) for it in e.items]

        if isinstance(e, DictLit):
            out: Dict[Any, Any] = {}
            for k_expr, v_expr in e.items:
                k = self.eval_expr(env, k_expr)
                v = self.eval_expr(env, v_expr)
                out[k] = v
            return out

        if isinstance(e, Index):
            target = self.eval_expr(env, e.target)
            idx = self.eval_expr(env, e.index)

            if isinstance(target, dict):
                return target.get(idx)

            if isinstance(target, list):
                if not isinstance(idx, int):
                    raise RuntimeError("List index must be an integer")
                if idx < 0 or idx >= len(target):
                    raise RuntimeError("List index out of range")
                return target[idx]

            if isinstance(target, str):
                if not isinstance(idx, int):
                    raise RuntimeError("String index must be an integer")
                if idx < 0 or idx >= len(target):
                    raise RuntimeError("String index out of range")
                return target[idx]

            raise RuntimeError(f"Indexing not supported for {type(target).__name__}")

        if isinstance(e, UnaryOp):
            v = self.eval_expr(env, e.expr)
            if e.op == "NEG":
                if not is_number(v):
                    raise RuntimeError(f"Unary '-' expects number, got {type(v).__name__}")
                return -v
            raise RuntimeError(f"Unknown unary op: {e.op}")

        if isinstance(e, BinOp):
            l = self.eval_expr(env, e.left)
            r = self.eval_expr(env, e.right)
            op = e.op

            if op == "PLUS":
                if isinstance(l, str) or isinstance(r, str):
                    return str(l) + str(r)
                if is_number(l) and is_number(r):
                    return l + r
                if isinstance(l, list) and isinstance(r, list):
                    return l + r
                raise RuntimeError("Operator '+' expects numbers or strings (or list + list)")

            if op == "MINUS":
                if is_number(l) and is_number(r):
                    return l - r
                raise RuntimeError("Operator '-' expects numbers")

            if op == "STAR":
                if is_number(l) and is_number(r):
                    return l * r
                raise RuntimeError("Operator '*' expects numbers")

            if op == "SLASH":
                if is_number(l) and is_number(r):
                    if r == 0:
                        raise RuntimeError("Division by zero")
                    return l / r
                raise RuntimeError("Operator '/' expects numbers")

            if op in ("LT", "GT", "LE", "GE"):
                if not (is_number(l) and is_number(r)):
                    raise RuntimeError("Comparison expects numbers")
                if op == "LT":
                    return l < r
                if op == "GT":
                    return l > r
                if op == "LE":
                    return l <= r
                if op == "GE":
                    return l >= r

            if op == "EQEQ":
                return l == r
            if op == "NE":
                return l != r

            raise RuntimeError(f"Unknown binary op: {op}")

        if isinstance(e, Invoke):
            # lore rule: in Mordor + bearing Ring, invoke forbidden
            # FIX: remove the extra "The spell backfires:" prefix to avoid duplication in CLI output
            if self.current_region() == "mordor" and self._bearing_ring and not self._ring_destroyed:
                raise RuntimeError('In Mordor, while bearing the Ring, "invoke" is forbidden.')

            fn = SAFE_INVOKE.get(e.target)
            if not fn:
                raise RuntimeError(
                    f"Forbidden spell: {e.target}. Use one of: {', '.join(sorted(SAFE_INVOKE.keys()))}"
                )
            args = [self.eval_expr(env, a) for a in e.args]
            try:
                return fn(*args)
            except Exception as ex:
                raise RuntimeError(f"Invoke failed: {e.target}: {ex}") from ex

        if isinstance(e, Call):
            # user spells
            if e.name in self.spells:
                spell = self.spells[e.name]
                if len(e.args) != len(spell.params):
                    raise RuntimeError(f"Spell '{e.name}' expects {len(spell.params)} args, got {len(e.args)}")
                call_env = Env(parent=self.global_env)
                for p, a in zip(spell.params, e.args):
                    call_env.set_local(p, self.eval_expr(env, a))
                try:
                    self.exec_block(call_env, spell.body)
                except ReturnSignal as rs:
                    return rs.value
                return None

            args = [self.eval_expr(env, a) for a in e.args]

            # LOTR built-ins
            if e.name == "palantir":
                if len(args) != 1:
                    raise RuntimeError("palantir(x) expects exactly 1 argument")
                return self._palantir(args[0])

            if e.name == "vision":
                if len(args) != 1:
                    raise RuntimeError("vision(x) expects exactly 1 argument")
                return self._vision(args[0])

            if e.name == "stamina":
                if len(args) != 1:
                    raise RuntimeError("stamina(x) expects exactly 1 argument")
                return self._stamina(args[0])

            if e.name == "craft":
                if len(args) != 1:
                    raise RuntimeError("craft(x) expects exactly 1 argument")
                return self._craft(args[0])

            if e.name == "spellcraft":
                if len(args) != 0:
                    raise RuntimeError("spellcraft() expects 0 arguments")
                return self._spellcraft()

            # artifacts built-ins
            if e.name == "inventory":
                if len(args) != 0:
                    raise RuntimeError("inventory() expects 0 arguments")
                return self._inventory()

            if e.name == "power":
                if len(args) != 0:
                    raise RuntimeError("power() expects 0 arguments")
                return self._power()

            if e.name == "corruption":
                if len(args) != 0:
                    raise RuntimeError("corruption() expects 0 arguments")
                return self._corruption()

            # python-like built-ins
            if e.name == "length":
                if len(args) != 1:
                    raise RuntimeError("length(x) expects 1 argument")
                return self._length(args[0])

            if e.name == "push":
                if len(args) != 2:
                    raise RuntimeError("push(list, item) expects 2 arguments")
                return self._push(args[0], args[1])

            if e.name == "pop":
                if len(args) != 1:
                    raise RuntimeError("pop(list) expects 1 argument")
                return self._pop(args[0])

            if e.name == "get":
                if len(args) != 2:
                    raise RuntimeError("get(map, key) expects 2 arguments")
                return self._get(args[0], args[1])

            if e.name == "put":
                if len(args) != 3:
                    raise RuntimeError("put(map, key, value) expects 3 arguments")
                return self._put(args[0], args[1], args[2])

            if e.name == "has":
                if len(args) != 2:
                    raise RuntimeError("has(map, key) expects 2 arguments")
                return self._has(args[0], args[1])

            if e.name == "keys":
                if len(args) != 1:
                    raise RuntimeError("keys(map) expects 1 argument")
                return self._keys(args[0])

            if e.name == "values":
                if len(args) != 1:
                    raise RuntimeError("values(map) expects 1 argument")
                return self._values(args[0])

            # base built-ins (ring/mellon/gandalf etc)
            if e.name in BUILTINS_BASE:
                fn = BUILTINS_BASE[e.name]
                try:
                    return fn(*args)
                except TypeError as te:
                    raise RuntimeError(f"Builtin '{e.name}' called with wrong arguments: {te}") from te
                except Exception as ex:
                    raise RuntimeError(f"Builtin '{e.name}' failed: {ex}") from ex

            raise RuntimeError(f"Unknown spell: {e.name}")

        raise RuntimeError(f"Unknown expression type: {type(e).__name__}")

    # -------------------------
    # Statements
    # -------------------------
    def exec_stmt(self, env: Env, s: Stmt) -> None:
        if isinstance(s, Inscribe):
            val = self.eval_expr(env, s.expr)
            env.set(s.name, val)
            return

        if isinstance(s, Proclaim):
            val = self.eval_expr(env, s.expr)
            self._region_print(val)
            return

        if isinstance(s, ExprStmt):
            _ = self.eval_expr(env, s.expr)
            return

        if isinstance(s, BeRace):
            allowed = {"man", "elf", "dwarf", "hobbit", "wizard", "orc"}
            race = s.race.lower()
            if race not in allowed:
                raise RuntimeError(f"Unknown race: {s.race}. Allowed: {', '.join(sorted(allowed))}")
            self.set_race(race)
            return

        if isinstance(s, InRegion):
            self.push_region(s.region)
            try:
                self.exec_block(env, s.body)
            finally:
                self.pop_region()
            return

        if isinstance(s, ArtifactAction):
            self.do_artifact_action(s.action, s.artifact)
            return

        if isinstance(s, IfStmt):
            if truthy(self.eval_expr(env, s.cond)):
                self.exec_block(env, s.then_body)
            else:
                self.exec_block(env, s.else_body)
            return

        if isinstance(s, WhileStmt):
            while truthy(self.eval_expr(env, s.cond)):
                self.exec_block(env, s.body)
            return

        if isinstance(s, SpellDef):
            self.spells[s.name] = Spell(params=s.params, body=s.body)
            return

        if isinstance(s, ReturnStmt):
            val = self.eval_expr(env, s.expr) if s.expr is not None else None
            raise ReturnSignal(val)

        raise RuntimeError(f"Unknown statement type: {type(s).__name__}")

    def exec_block(self, env: Env, body: List[Stmt]) -> None:
        for st in body:
            self.exec_stmt(env, st)

    def run(self, src: str) -> None:
        tokens = tokenize(src)
        program = Parser(tokens).parse_program()
        self.exec_block(self.global_env, program)

# Convenience
def run_source(src: str) -> None:
    Interpreter().run(src)

def run_file(path: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        run_source(f.read())
