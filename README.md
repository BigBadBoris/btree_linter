# Behavior Tree Linter v0.1

## WARNING

`btree_linter` is currently under development and is *NOT* in a fully
functional state. Use at your own peril!

## About

`btree_linter` is a linter for [LibGdx's Behavior Tree
Language](https://github.com/libgdx/gdx-ai/wiki/Behavior-Trees)
written in Python. Features will include the following:

- checks for valid behavior tree syntax, including proper indentation
- validates task names, warning if any are misspelled/undefined
- validates task attributes, such as catching undefined attributes and
  missing required attributes
- validates task types, such as warning if a leaf task contains
  children or a composite task contains no children
  
## How it works

`btree_linter` tokenizes and parses behavior trees source files to catch
and lexical or syntax errors. It then passes information to an
analyser which uses the python `javalang` library to validate it
using your Java code.

## Rationale 

`btree_linter` is intented to be used as an on-the-fly syntax checker
to be used during development. Once it reaches a mature state, it can
be integrated into ide's or text editors that support linter
plugins. Using `btree_linter` allows you to avoid having to constantly
re-launch your game to catch the most common errors.

 
## Requirements

- Python 3
- `javalang` library (`pip install javalang` or [from source](https://github.com/c2nes/javalang)).
- `libGdx` [Link](https://libgdx.badlogicgames.com/).
