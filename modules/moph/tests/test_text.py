from app.bm25 import BM25
from app.text import normalize, tokens


def test_normalize_unifies_letters_and_digits():
    assert normalize("إجازة") == normalize("اجازه")
    assert normalize("مستشفى") == "مستشفي"
    assert normalize("٢٠٢٦") == "2026"
    assert normalize("دَوَاء") == "دواء"


def test_plural_and_article_share_a_stem():
    assert tokens("المستشفيات") == tokens("مستشفى") == tokens("مستشفيات")
    assert tokens("الأدوية") == tokens("أدوية")


def test_stopwords_dropped():
    assert tokens("كيف بدي جيب الدواء") == tokens("الدواء")
    assert tokens("how do I get a license") == tokens("license")


def test_bm25_prefers_documents_with_more_query_terms():
    index = BM25(["أدوية السرطان", "السرطان", "أدوية الضغط"])
    assert index.search("أدوية السرطان")[0].index == 0
    assert index.search("شيء آخر") == []
