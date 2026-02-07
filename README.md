# GandalfLang 🧙‍♂️

A tiny interpreted scripting language inspired by fantasy spellcasting.
Includes a lexer → parser (AST) → interpreter, plus a REPL and script runner.

## Features

- Variables: `inscribe x = <expr>`
- Printing: `proclaim <expr>`
- Control flow: `if/then/else/end`, `while/do/end`
- Functions (“spells”): `spell name(args...) do ... end`
- `return` inside spells
- Safe host calls via `invoke "..." with ...` (whitelist)

## Project layout

gandalf_lang/
gandalf_lang/
init.py
main.py
tokens.py
lexer.py
ast_nodes.py
parser.py
runtime.py
repl.py
test.gandalf
README.md


## Requirements

- Python 3.10+ (recommended)

## Run

### REPL
From the project root:

```bash
python -m gandalf_lang

Run a script
python -m gandalf_lang test.gandalf

Language tour
Basics
inscribe x = 9
proclaim x
proclaim "x + 1 = " + (x + 1)

Math + floats

Division uses / (float division):

inscribe a = 7
inscribe b = 2
proclaim a / b   # 3.5

If / else
inscribe x = 9

if x >= 10 then
  proclaim "x is big"
else
  proclaim "x is small"
end

While loop
inscribe i = 1
inscribe s = 0

while i <= 5 do
  inscribe s = s + i
  inscribe i = i + 1
end

proclaim s  # 15

Spells (functions)
spell add(p, q) do
  return p + q
end

proclaim add(3, 4)  # 7


Factorial example:

spell fact(n) do
  inscribe r = 1
  inscribe k = 2
  while k <= n do
    inscribe r = r * k
    inscribe k = k + 1
  end
  return r
end

proclaim fact(6)  # 720

Safe host calls (invoke)

To call a small set of whitelisted Python functions:

proclaim invoke "math.sqrt" with 9
proclaim invoke "math.pow" with 2, 5
proclaim invoke "abs" with -12
proclaim invoke "len" with "wizard"


Important: the target must be a string, e.g. "math.sqrt".
Writing invoke math.sqrt with 9 will fail because . is not a valid identifier character.

Allowed invoke targets

math.sqrt

math.floor

math.ceil

math.pow

abs

len

(You can extend this list in runtime.py by editing SAFE_INVOKE.)

Comments

Use # for line comments:

# this is a comment
inscribe x = 1

Errors

Errors show line and column:

Fizzle: Unexpected character '.' (line 1, col 28)

Development notes

The interpreter pipeline is: tokenize → Parser → AST → Interpreter.

The runtime is intentionally small and safe by default.

Roadmap ideas

Add a tests/ folder with pytest regression tests

Add boolean literals (true/false)

Add VS Code syntax highlighting

Add better REPL multiline detection
