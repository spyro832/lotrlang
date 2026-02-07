an experimental programming language implemented in Python.
It provides a small, Python-like core language together with a themed standard library inspired by The Lord of the Rings.

The project is intended as a learning and experimentation platform for interpreter design, language semantics, and runtime behavior.

Overview

Gandalf Language is:

Dynamically typed

Interpreted

Expression-based

Executed through a custom interpreter (lexer → parser → AST → runtime)

Most of the language behaves like a small scripting language.
The Lord of the Rings elements appear only in specific keywords and built-in functions, not in the core syntax.

Context Keywords

The language provides special statements that modify the runtime context:

be race hobbit
in region shire do
    proclaim power()
end

Built-in Functions

Several built-in functions use LOTR-themed names:

proclaim palantir("A shadow moves in the deep")
proclaim vision(100)
proclaim spellcraft()

Examples include:

palantir

vision

stamina

craft

spellcraft

inventory

power

corruption

They behave like normal functions and can be used anywhere expressions are allowed.

Runtime Rules

claim ring
bear ring
in region mordor do
    invoke math.sqrt(9)   # this will fail
end

Certain combinations of state (such as region and artifacts) can restrict operations.
These rules are enforced at runtime and produce clear error messages.

Core Language Features
Language Constructs

Variables and assignment

Arithmetic and comparison operators

Strings and string concatenation

if / else conditionals

while loops

User-defined functions

Return statements

Runtime error handling

Data Structures

Lists

Dictionaries (maps)

Indexing for lists, dictionaries, and strings

Built-in helpers:

length

push, pop

get, put

keys, values

Running Examples

Programs are executed through the module entry point.

From the project root directory:

python -m gandalf_lang examples/moria.gandalf