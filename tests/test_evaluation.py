import pytest

from evaluation import QUESTIONS, is_correct, numbers_in


@pytest.mark.parametrize("text,expected", [
    ("Ci sono 40 clienti italiani.", 40),
    ("n\n40\n(1 rows)", 40),
    ("Il fatturato è di 741.458,03.", 741458.03),
    ("Il fatturato è di 741458.03", 741458.03),
    ("Il fatturato totale è 741,458.03 euro", 741458.03),
    ("C'è 1 cliente italiano (country = 'IT').", 1),
    ("Ci sono **24** clienti tedeschi", 24),
])
def test_accepts_the_expected_value(text, expected):
    assert is_correct(text, expected)


@pytest.mark.parametrize("text,expected", [
    ("Ci sono 120 clienti.", 20),
    ("Non ci sono clienti italiani, il conteggio è 0.", 40),
    ("count\n0\n(1 rows)", 40),
    ("No rows returned.", 40),
    ("Query failed: no such table: customer", 40),
])
def test_rejects_a_wrong_answer(text, expected):
    assert not is_correct(text, expected)


def test_ignores_dates_and_identifiers():
    assert numbers_in("ordine 4 del 2024-06-15") >= {4.0}


def test_every_question_has_a_numeric_expectation():
    for question, expected in QUESTIONS:
        assert isinstance(expected, (int, float))
        assert question.strip().endswith("?")
