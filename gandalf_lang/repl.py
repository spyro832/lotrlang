from __future__ import annotations
from .runtime import Interpreter
from .tokens import GandalfError

def needs_more_lines(buffer: str) -> bool:
    lower = buffer.lower()

    def count_word(w: str) -> int:
        return lower.count(f" {w} ") + lower.count(f"\n{w} ") + (1 if lower.lstrip().startswith(w + " ") else 0)

    opens = 0
    opens += count_word("if")
    opens += count_word("when")
    opens += count_word("while")
    opens += count_word("endure")
    opens += count_word("spell")
    opens += count_word("weave")
    opens += count_word("in")
    opens += count_word("within")

    ends = lower.count("end")
    return opens > ends

def repl() -> None:
    itp = Interpreter()
    print("GandalfLang REPL — Speak, friend, and enter.")
    print("Type Ctrl+C or Ctrl+D to leave Middle-earth.")
    buf_lines: list[str] = []

    while True:
        try:
            prompt = "… " if buf_lines else ">> "
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print("\nYou shall not pass! (session ended)")
            return

        buf_lines.append(line)
        src = "\n".join(buf_lines)

        if needs_more_lines("\n" + src + "\n"):
            continue

        try:
            itp.run(src)
        except GandalfError as e:
            print(f"Fizzle: {e}")
        except Exception as e:
            print(f"Fizzle (unexpected): {e}")

        buf_lines.clear()
