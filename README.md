Features
Core Language

Variables and expressions

Arithmetic and comparisons

if / else conditionals

while loops

User-defined functions (“spells”)

Return values

Errors with clear diagnostics (“Fizzle”)

Data Structures

Lists

Dictionaries (maps)

Indexing (xs[0], m["key"])

Built-ins: length, push, pop, get, put, keys, values

LOTR Lore System

Regions: shire, moria, rivendell, mordor

Races: man, elf, dwarf, hobbit, wizard

Artifacts: ring, mithril, phial

The runtime reacts dynamically to lore context:

Output formatting changes by region

Power and corruption depend on race, region, and artifacts

Some actions are forbidden by lore rules

Example:

Invoking magic while bearing the Ring in Mordor will backfire.

Built-in Spells
Lore-aware

palantir(x)

vision(x)

stamina(x)

craft(x)

spellcraft()

inventory()

power()

corruption()

Base

ring(), precious()

mellon()

gandalf()

you_shall_not_pass()

Safe Python Invocations

Whitelisted only:

math.sqrt, math.floor, math.ceil, math.pow

abs, len

All other Python calls are blocked for safety.

Running Examples

From the project root:

python -m gandalf_lang examples/moria.gandalf
python -m gandalf_lang examples/regions_showcase.gandalf
python -m gandalf_lang examples/races_showcase.gandalf
python -m gandalf_lang examples/artifacts_showcase.gandalf
python -m gandalf_lang examples/collections_showcase.gandalf

Example Code
be race hobbit
in region shire do
    proclaim power()
    claim ring
    bear ring
    proclaim corruption()
end

 Design Goals

Clean interpreter architecture (lexer → parser → AST → runtime)

Strong error handling with thematic messages

Python-like semantics where it makes sense

Lore-based constraints as first-class language features

Easy extensibility (new syntax, new regions, new artifacts)
