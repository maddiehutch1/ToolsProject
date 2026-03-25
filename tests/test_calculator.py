import pytest
from backend.tools.calculator import calculator


@pytest.mark.unit
def test_basic_addition():
    assert calculator.invoke("2 + 3") == "5"


@pytest.mark.unit
def test_basic_multiplication():
    assert calculator.invoke("6 * 7") == "42"


@pytest.mark.unit
def test_phq9_sum():
    assert calculator.invoke("2+3+1+0+2+1+3+2+1") == "15"


@pytest.mark.unit
def test_gad7_sum():
    assert calculator.invoke("1+2+3+1+2+1+2") == "12"


@pytest.mark.unit
def test_sqrt():
    assert calculator.invoke("sqrt(144)") == "12.0"


@pytest.mark.unit
def test_zero_division():
    result = calculator.invoke("1 / 0")
    assert "division by zero" in result.lower()


@pytest.mark.unit
def test_invalid_syntax():
    result = calculator.invoke("not a number !!!")
    assert "Error" in result


@pytest.mark.unit
def test_import_attempt_blocked():
    result = calculator.invoke("__import__('os').system('ls')")
    assert "Error" in result


@pytest.mark.unit
def test_sleep_efficiency():
    result = calculator.invoke("(7/8)*100")
    assert result == "87.5"
