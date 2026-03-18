# simpleeval Guide
## Usage in This Project

**Source:** [PyPI — simpleeval](https://pypi.org/project/simpleeval/) + [GitHub](https://github.com/danthedeckie/simpleeval) — verified March 2026  
**Package:** `simpleeval>=1.0.0`  
**Used in:** `backend/tools/calculator.py`

---

## Why simpleeval

The calculator tool needs to evaluate user-supplied arithmetic expressions (e.g., PHQ-9 scoring: `"2+3+1+0+2+1+3+2+1"`). Using Python's built-in `eval()` would be a critical security vulnerability — `eval` can execute arbitrary code.

`simpleeval` is a safe alternative:
- Parses expressions via the `ast` module — no `exec` or `eval`
- Restricts what operators and functions are allowed
- Widely used (17M+ monthly downloads), actively maintained, supports Python 3.9–3.13
- Raises `SimpleEval` exceptions for disallowed operations rather than executing them

---

## Installation

```bash
pip install simpleeval
```

---

## Implementation: `calculator.py`

```python
# backend/tools/calculator.py
import math
from simpleeval import simple_eval, EvalWithCompoundTypes
from langchain_core.tools import tool

SAFE_FUNCTIONS = {
    "sqrt": math.sqrt,
    "abs": abs,
    "round": round,
    "pow": pow,
    "floor": math.floor,
    "ceil": math.ceil,
    "log": math.log,
}

SAFE_NAMES = {
    "pi": math.pi,
    "e": math.e,
}

@tool
def calculator(expression: str) -> str:
    """Evaluates a mathematical expression safely. Use for PHQ-9 scoring, GAD-7 scoring, \
sleep efficiency calculations, or any arithmetic. Example inputs: '2+3+1+0+2', 'sqrt(144)', \
'round(7/3, 2)'."""
    try:
        result = simple_eval(
            expression,
            functions=SAFE_FUNCTIONS,
            names=SAFE_NAMES,
        )
        return str(result)
    except ZeroDivisionError:
        return "Error: division by zero"
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"
```

---

## Core Function: `simple_eval`

```python
from simpleeval import simple_eval

# Basic arithmetic
simple_eval("2 + 2")          # → 4
simple_eval("10 / 3")         # → 3.3333...
simple_eval("2 ** 8")         # → 256
simple_eval("(3 + 4) * 2")    # → 14

# With functions
simple_eval("sqrt(16)", functions={"sqrt": math.sqrt})   # → 4.0
simple_eval("round(3.14159, 2)")                          # → 3.14 (round is built in)
simple_eval("abs(-7)")                                    # → 7

# With named constants
simple_eval("pi * r ** 2", names={"pi": math.pi, "r": 5})  # → 78.539...
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `expr` | `str` | The expression string to evaluate |
| `functions` | `dict` | Mapping of function names → callables (whitelisted) |
| `names` | `dict` | Mapping of variable names → values (whitelisted) |
| `operators` | `dict` | Override allowed operators (advanced — leave default) |

---

## PHQ-9 and GAD-7 Scoring Examples

These are the primary use cases for the calculator in this project:

```python
# PHQ-9 (9 items, each 0-3, max score 27)
simple_eval("2+3+1+0+2+1+3+2+1")  # → 15 (moderately severe)

# GAD-7 (7 items, each 0-3, max score 21)
simple_eval("1+2+1+0+1+2+1")      # → 8 (mild)

# Sleep efficiency
simple_eval("round(420/480*100, 1)")  # → 87.5 (%)
```

The LLM will call `calculator` with expressions like these after extracting the numbers from the user's message.

---

## Safety Boundaries

`simpleeval` is safe against:
- Arbitrary code execution (`__import__`, `open`, `os.system`, etc.)
- Attribute access on objects
- Calling non-whitelisted functions

`simpleeval` is **not** a defense against:
- Expressions that consume large amounts of memory (e.g., `9**9**9`)
- Very long loops in comprehensions (if `EvalWithCompoundTypes` is used)

For this project, the whitelist in `SAFE_FUNCTIONS` is narrow enough that these edge cases are not a concern.

---

## Error Handling

```python
from simpleeval import simple_eval, InvalidExpression, FeatureNotAvailable

try:
    result = simple_eval(expression, functions=SAFE_FUNCTIONS)
    return str(result)
except ZeroDivisionError:
    return "Error: division by zero"
except InvalidExpression:
    return "Error: invalid expression syntax"
except FeatureNotAvailable:
    return "Error: operation not permitted"
except Exception as e:
    return f"Error: {str(e)}"
```

A broad `except Exception` at the end ensures the `@tool` function never raises an unhandled exception into the LangGraph node, which would abort the agent loop.

---

## Testing

```python
# tests/test_calculator.py
from backend.tools.calculator import calculator

def test_basic_addition():
    assert calculator.invoke({"expression": "2 + 2"}) == "4"

def test_phq9_sum():
    assert calculator.invoke({"expression": "2+3+1+0+2+1+3+2+1"}) == "15"

def test_sqrt():
    assert calculator.invoke({"expression": "sqrt(144)"}) == "12.0"

def test_division_by_zero():
    result = calculator.invoke({"expression": "10 / 0"})
    assert "zero" in result.lower()

def test_invalid_expression():
    result = calculator.invoke({"expression": "import os"})
    assert "Error" in result

def test_rounding():
    result = calculator.invoke({"expression": "round(3.14159, 2)"})
    assert result == "3.14"

def test_exponentiation():
    assert calculator.invoke({"expression": "2 ** 10"}) == "1024"
```

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| `NameNotDefined` error for `sqrt` | Pass `functions={"sqrt": math.sqrt}` explicitly — it is not built in |
| `round()` not working | `round` is a Python builtin — `simple_eval` includes builtins by default, no extra config needed |
| Negative number confusion (`-5`) | `simple_eval("-5")` works; `-` as unary is supported |
| LLM passes non-numeric expressions | Catch `Exception` broadly and return a descriptive error string |
| Expression with spaces fails | `simple_eval` handles whitespace fine — no preprocessing needed |

---

## Key References

- [PyPI — simpleeval](https://pypi.org/project/simpleeval/)
- [GitHub — danthedeckie/simpleeval](https://github.com/danthedeckie/simpleeval)
