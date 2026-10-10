import pytest

from core.identity import user_id_for


def test_phone_formats_map_to_one_user():
    numbers = ["+961 70 123 456", "96170123456", "0096170123456", "+96170123456"]
    assert len({user_id_for("wa", n) for n in numbers}) == 1


def test_same_digits_on_different_apps_are_different_users():
    assert user_id_for("wa", "96170123456") != user_id_for("tg", "96170123456")


def test_web_id_case_does_not_matter():
    raw = "AAE45951-5E3B-4BCD-B5C8-D81E3261328F"
    assert user_id_for("web", raw) == user_id_for("web", raw.lower())


@pytest.mark.parametrize("raw", ["123", "hello", ""])
def test_rejects_non_phone_numbers(raw):
    with pytest.raises(ValueError):
        user_id_for("wa", raw)
