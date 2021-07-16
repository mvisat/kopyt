# Kopyt

Kopyt is a Kotlin programming language parser in pure Python, inspired by [javalang](https://github.com/c2nes/javalang) library.

## Features
- Supports Kotlin 1.5
- Zero dependency

## Requirements
- Python 3.6+

## Usage

```python
from kopyt import Parser, node

code = """\
package main

import a.b
import x.y.z.*

fun main() {
    println("Hello, world!")
}
"""

parser = Parser(code)
result = parser.parse()

assert result.package is not None
assert result.package.name == "main"

assert len(result.imports) == 2
assert result.imports[0].name == "a.b"
assert result.imports[1].name == "x.y.z"
assert result.imports[1].wildcard

assert len(result.declarations) == 1
assert isinstance(result.declarations[0], node.FunctionDeclaration)
assert result.declarations[0].name == "main"

print(result) # this will output a string similar to the original code
```

All nodes and its members can be found on [kopyt/node.py](kopyt/node.py).