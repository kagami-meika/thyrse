# Chrysalis

[![License: CC0 1.0 Universal](https://img.shields.io/badge/License-CC0%201.0-lightgrey.svg)](http://creativecommons.org/publicdomain/zero/1.0/)
[![Python >= 3.8](https://img.shields.io/badge/Python-%3E%3D%203.8-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/chrysalis.svg)](https://pypi.org/project/chrysalis/)

> A fast and elegant functional programming toolkit for Python

**Chrysalis** is a comprehensive toolkit for functional programming in Python. It provides lambda calculus combinators, higher-order functions, algebraic data types, lenses, and many other tools to help you write elegant, functional Python code.

## Features

- **Pure Functional**: Based on lambda calculus and functional programming principles
- **Combinators**: Classic S, K, I combinators and more for function abstraction
- **Function Utilities**: Composition, piping, currying, memoization, and more
- **Algebraic Data Types**: Optional, Result, and other ADTs for safer code
- **Async Support**: First-class support for async/await patterns
- **Type Hints**: Full type annotation support for better IDE experience
- **Type Safe**: Optional, Result, and Safe types for handling errors elegantly
- **Zero Dependencies**: Pure Python implementation, no external dependencies
- **Pythonic**: Leverages Python's language features naturally

## Installation

```bash
pip install chrysalis
```

## Quick Start

### Basic Combinators

```python
from chrysalis import I, K, S, curry, pipe, tap

# Identity combinator
assert I(42) == 42

# Constant combinator  
greet = K("Hello")
assert greet("World") == "Hello"

# Function currying and composition
add = curry(lambda x, y: x + y)
add5 = add(5)
assert add5(3) == 8

# Pipeline data processing
pipeline = pipe(
    [1, 2, 3],
    lambda x: map(lambda i: i * 2, x),
    list,
)
assert pipeline == [2, 4, 6]

# Debug output with tap
result = pipe(
    42,
    tap(print),           # prints 42
    lambda x: x + 1,      # returns 43
)
```

### Working with Optional and Result

```python
from chrysalis import Some, Nothing, Ok, Err

# Optional type
opt_value = Some(5)
result = opt_value.map(lambda x: x * 2).map(lambda x: x + 1)
# Result: Some(11)

# Result type  
computation = Ok(10).map(lambda x: x / 2).map(lambda x: x - 1)
# Result: Ok(4.0)

# Chain operations safely
def safe_divide(x, y):
    return Ok(x / y) if y != 0 else Err("Division by zero")

result = (
    Ok(20)
    .flat_map(lambda x: safe_divide(x, 2))
    .flat_map(lambda x: safe_divide(x, 4))
)
# Result: Ok(2.5)
```

### Function Composition

```python
from chrysalis import compose, curry

# Compose functions right-to-left
add_one = lambda x: x + 1
double = lambda x: x * 2
triple = lambda x: x * 3

# Result is: triple(double(add_one(x)))
f = compose(triple, double, add_one)
assert f(2) == 18  # triple(double(3)) = triple(6) = 18

# Or use pipe for left-to-right
from chrysalis import pipe
assert pipe(2, add_one, double, triple) == 18
```

### Predicates and Data Access

```python
from chrysalis import prop, get, get_in, has, is_type

data = {"user": {"name": "Alice", "age": 30}}

# Property access
age = get_in(data, ["user", "age"])
assert age == 30

# Type checking  
is_user = is_type(dict)
assert is_user(data) == True

# Property extraction
get_name = prop("name")
assert get_name({"name": "Bob", "age": 25}) == "Bob"
```

### Lenses for Data Manipulation

```python
from chrysalis import lens, view, set_, over

# Create a lens for a nested property
user_age = lens().user.age

data = {"user": {"name": "Alice", "age": 30}}

# View through the lens
assert view(user_age, data) == 30

# Set a new value
new_data = set_(user_age, 31, data)
assert view(user_age, new_data) == 31

# Transform with a function
incremented = over(user_age, lambda x: x + 1, data)
assert view(user_age, incremented) == 31
```

### Async Support

```python
import asyncio
from chrysalis import async_pipe, async_compose

async def fetch_user(user_id):
    # Simulated async operation
    await asyncio.sleep(0.1)
    return {"id": user_id, "name": "Alice"}

async def fetch_posts(user):
    # Simulated async operation
    await asyncio.sleep(0.1)
    return [{"title": "Post 1", "author_id": user["id"]}]

async def main():
    # Compose async functions
    get_user_posts = async_pipe(
        fetch_user,
        lambda user: fetch_posts(user),
    )
    
    posts = await get_user_posts(1)
    print(posts)  # [{"title": "Post 1", "author_id": 1}]

asyncio.run(main())
```

## Core Modules

### Combinators (`chrysalis.combinators`)

Classic lambda calculus combinators for building higher-order abstractions:

- **I**: Identity combinator `I(x) = x`
- **K**: Constant combinator `K(x)(y) = x`
- **S**: Substitution combinator `S(f)(g)(x) = f(x)(g(x))`
- **B**: Composition combinator `B(f)(g)(x) = f(g(x))`
- **C**: Flip combinator `C(f)(x)(y) = f(y)(x)`
- **W**: Duplicate combinator `W(f)(x) = f(x)(x)`
- **Y**: Fixed-point combinator (for recursion)
- **Omega**: Self-replicating combinator

### Function Utilities (`chrysalis.func`)

High-order functions and functional programming utilities:

- `curry` / `uncurry`: Currying and uncurrying functions
- `compose` / `pipe`: Function composition (right-to-left/left-to-right)
- `tap`: Side-effect debugging (pass-through)
- `peek`: Like tap, but for inspection
- `always`: Constant value factory
- `flip`: Swap argument order
- `complement`: Logical negation of predicates
- `retry`: Function wrapper with retry logic
- `memoize`: Caching function results
- `log`: Logging wrapper
- `partition` / `groupby`: Collection operations
- `async_compose` / `async_pipe`: Async function composition
- `fork` / `branch`: Parallel processing of functions

### Predicates (`chrysalis.predicates`)

Type checking and data access predicates:

- `prop`: Property accessor
- `get` / `get_in`: Safe property access
- `has`: Check property existence
- `is_type`: Type checking predicates
- `and_` / `or_` / `not_`: Logical predicates
- `truthy` / `falsy`: Truthiness checks

### Algebraic Data Types (`chrysalis.adts`)

Type-safe error handling with algebraic data types:

- `Optional` / `Some` / `Nothing`: Optional values
- `Result` / `Ok` / `Err`: Result type for error handling
- `AsyncResult` / `AsyncOk` / `AsyncErr`: Async results
- All support `map()`, `flat_map()`, and other functional operations

### Lenses (`chrysalis.lens`)

Composable getters/setters for nested data structures:

- `lens()`: Create lenses for nested access
- `view()`: Get value through lens
- `set_()`: Set value through lens
- `over()`: Transform value through lens
- Works with any nested data structure

### Lazy Evaluation (`chrysalis.lazy`)

Deferred computation and memoization:

- `Lazy`: Lazy computations with caching
- `AsyncLazy`: Async lazy evaluation
- `thunk()` / `force()`: Quick lazy evaluation

### Control Flow (`chrysalis.declarative_flow`, `chrysalis.inline_flow`)

Declarative and inline control flow constructs:

- `iif`: Inline if-then-else
- `attempt`: Try-catch wrapper
- `match`: Pattern matching
- `using`: Resource management

### Safe Evaluation (`chrysalis.safe`)

Safe function wrapping and execution:

- `Safe`: Safe function wrapper
- `safe`: Decorator for safe function execution

## API Documentation

For detailed API documentation, visit the [GitHub repository](https://github.com/yourusername/chrysalis).

## Examples

### Data Processing Pipeline

```python
from chrysalis import pipe, partition, groupby, prop, map

users = [
    {"name": "Alice", "age": 30, "active": True},
    {"name": "Bob", "age": 25, "active": False},
    {"name": "Carol", "age": 35, "active": True},
]

# Group active users by age and get their names
active_users = pipe(
    users,
    lambda us: filter(prop("active"), us),
    groupby(prop("age")),
    lambda groups: {age: [u["name"] for u in users] for age, users in groups.items()},
)

print(active_users)
# {30: ["Alice"], 35: ["Carol"]}
```

### Error Handling

```python
from chrysalis import Ok, Err, Result

def parse_int(s):
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"Cannot parse '{s}' as integer")

def divide(x, y):
    if y == 0:
        return Err("Division by zero")
    return Ok(x / y)

result = (
    parse_int("20")
    .flat_map(lambda x: divide(x, 4))
    .map(lambda x: round(x, 2))
)

print(result)  # Ok(5.0)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the CC0 1.0 Universal License - See the [LICENSE](LICENSE) file for details.

CC0 1.0 Universal means this work is in the public domain. You can copy, modify, distribute and use the work, even for commercial purposes, all without asking permission.

## Changelog

### 0.1.0 (2026-03-16)

- Initial release
- Core combinators (I, K, S, B, C, W, Y, Omega)
- Function utilities (compose, pipe, curry, etc.)
- Algebraic data types (Optional, Result)
- Lenses for data manipulation
- Async support
- Lazy evaluation
- Predicates and property access
- Error handling with Result type

## Support

For issues, questions, or suggestions, please open an issue on the [GitHub repository](https://github.com/yourusername/chrysalis).
