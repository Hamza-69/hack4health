import pytest

from app.places import CAZAS, caza_at


@pytest.mark.parametrize(
    "town, lat, lon, caza",
    [
        ("Hamra", 33.8963, 35.4826, "Beirut"),
        ("Jounieh", 33.9808, 35.6178, "Kesrouane"),
        ("Zahle", 33.8463, 35.9020, "Zahle"),
        ("Saida", 33.5631, 35.3688, "Saida"),
        ("Tripoli", 34.4367, 35.8497, "Tripoli"),
        ("Tyre", 33.2705, 35.2038, "Sour"),
        ("Baalbek", 34.0058, 36.2181, "Baalbek"),
    ],
)
def test_caza_at_known_towns(town, lat, lon, caza):
    assert caza_at(lat, lon).name == caza, town


def test_caza_at_outside_lebanon_or_swapped():
    assert caza_at(33.5130, 36.2920) is None  # Damascus
    assert caza_at(35.4826, 33.8963) is None  # Hamra with lat and lon swapped


def test_all_26_cazas():
    assert len({c.name for c in CAZAS}) == 26
