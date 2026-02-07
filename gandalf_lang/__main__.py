import sys

from .repl import repl
from .runtime import run_file
from .tokens import GandalfError

def main(argv: list[str]) -> int:
    # Script mode
    if len(argv) >= 2:
        try:
            run_file(argv[1])
            return 0
        except GandalfError as e:
            # Pretty language-level error (no Python traceback)
            print(f"Fizzle: {e}")
            return 1
        except Exception as e:
            # Unexpected internal error
            print(f"Fizzle (unexpected): {e}")
            return 2

    # REPL mode
    repl()
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
