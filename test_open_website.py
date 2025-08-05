import sys
import types


def test_open_website_direct_url(monkeypatch):
    called = {"search": False, "open": False, "extract": False, "summarize": False}

    def fake_search_web(query, max_results=3):
        called["search"] = True
        return ""

    def fake_open_page(url):
        called["open"] = True

    def fake_extract_text(selector):
        called["extract"] = True
        return "sample text " * 50  # >500 chars

    def fake_summarize(text, max_sentences=5):
        called["summarize"] = True
        return "summary"

    fake_search_module = types.SimpleNamespace(search_web=fake_search_web)
    monkeypatch.setitem(sys.modules, "search", fake_search_module)
    monkeypatch.setitem(sys.modules, "numpy", types.SimpleNamespace())
    monkeypatch.setitem(sys.modules, "file_index", types.SimpleNamespace(file_index=None))
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=None))

    import tools
    monkeypatch.setattr(tools, "open_page_sandbox", fake_open_page)
    monkeypatch.setattr(tools, "extract_text_sandbox", fake_extract_text)
    monkeypatch.setattr(tools, "summarize_text", fake_summarize)
    from tools import open_website

    result = open_website("https://example.com")

    assert result == "summary"
    assert called["open"]
    assert called["extract"]
    assert called["summarize"]
    assert not called["search"]
