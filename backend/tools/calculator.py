from langchain_core.tools import tool
from simpleeval import simple_eval
import math

_FUNCTIONS = {
    "sqrt": math.sqrt,
    "abs": abs,
    "round": round,
    "pow": pow,
    "floor": math.floor,
    "ceil": math.ceil,
}


@tool
def calculator(expression: str) -> str:
    """Evaluates a math expression safely.
    Use for PHQ-9, GAD-7, sleep efficiency, or any arithmetic."""
    try:
        result = simple_eval(expression, functions=_FUNCTIONS)
        return str(result)
    except ZeroDivisionError:
        return "Error: division by zero."
    except Exception as e:
        return f"Error: {e}"
