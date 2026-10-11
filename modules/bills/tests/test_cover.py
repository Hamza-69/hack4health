"""The bill check against the ministry's rules (cover.json) and the Facility Locator's hospitals."""

import pytest

from app import cover


def hospital(name: str):
    return cover.match(name, cover.hospitals())


def test_every_listed_hospital_is_found():
    data = cover.data()
    assert len([h for h in data["hospitals"] if h["kind"] == "government"]) == 33
    assert len([h for h in data["hospitals"] if h["kind"] == "private"]) == 44
    listed = [h for h in cover.hospitals() if h.listed]
    assert len(listed) == 77
    assert len({h.id for h in cover.hospitals()}) == len(cover.hospitals())


@pytest.mark.parametrize("name, expected", [
    ("مستشفى رفيق الحريري الجامعي", "f84388"),
    ("Hariri hospital", "f84388"),
    ("مستشفى نبيه بري", "f84371"),
    ("مستشفى الجبل", "f84570"),  # not Mays al-Jabal
    ("مستشفى حمود الجامعي", "f84651"),
    ("Hotel Dieu de France", "f84549"),
    ("Kartaba governmental hospital", "f84366"),
    ("مستشفى اهدن الخيري", "f84648"),
])
def test_names_on_bills(name, expected):
    h, _ = hospital(name)
    assert h is not None and h.id == expected


@pytest.mark.parametrize("name", ["اهدن", "مستشفى طرابلس"])
def test_ambiguous_names_ask(name):
    h, candidates = hospital(name)
    assert h is None and len(candidates) >= 2


@pytest.mark.parametrize("name, patient, injury, verdict", [
    ("Hariri hospital", "uninsured_lebanese", "none", "no_extra_charge"),  # government
    ("Hammoud Hospital University Medical Center", "uninsured_lebanese", "none", "no_extra_charge"),  # listed private
    ("Hotel Dieu de France", "uninsured_lebanese", "none", "usual_share"),  # private, not listed
    ("Hariri hospital", "nssf", "none", "not_ministry"),
    ("Hariri hospital", "not_lebanese", "none", "cannot_confirm"),
    ("Hotel Dieu de France", "nssf", "port_blast", "no_extra_charge"),
    ("Hotel Dieu de France", "unknown", "war", "no_extra_charge"),
])
def test_verdicts(name, patient, injury, verdict):
    result = cover.check(name, patient, injury)
    assert result["found"] and result["verdict"] == verdict
    assert all(s["url"].startswith("https://www.moph.gov.lb/") and s["date"] for s in result["sources"])


def test_asks_for_cover_first():
    result = cover.check("Hariri hospital", "unknown", "none")
    assert not result["found"] and result["need_to_know"] == [cover.ASK_COVER]
