from app.text import normalize


def test_normalize_unifies_letters_and_digits():
    assert normalize("إجازة") == normalize("اجازه")
    assert normalize("مستشفى") == "مستشفي"
    assert normalize("٢٠٢٦") == "2026"
    assert normalize("دَوَاء") == "دواء"
