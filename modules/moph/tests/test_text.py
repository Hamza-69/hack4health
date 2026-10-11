from app.text import claim_key, normalize


def test_normalize_unifies_letters_and_digits():
    assert normalize("إجازة") == normalize("اجازه")
    assert normalize("مستشفى") == "مستشفي"
    assert normalize("٢٠٢٦") == "2026"
    assert normalize("دَوَاء") == "دواء"


def test_claim_key_groups_rewordings():
    first = claim_key("وزارة الصحة أوقفت تغطية الاستشفاء لغير النازحين")
    assert claim_key("الوزارة أوقفت تغطية الإستشفاء لغير النازحين!") == first
    assert claim_key("وزارة الصحة أوقفت تغطية الطوارئ والاستشفاء للبنانيين غير النازحين", [first]) == first
    assert claim_key("The ministry covers organ transplants") == claim_key("ministry covers organ transplants now")


def test_claim_key_keeps_different_claims_apart():
    covers = claim_key("الوزارة تغطي عمليات زرع الأعضاء")
    assert claim_key("الوزارة لا تغطي عمليات زرع الأعضاء", [covers]) != covers
    assert claim_key("الوزارة تغطي عمليات الجلطة الدماغية", [covers]) != covers
