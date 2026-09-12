from src.preprocessing.cleaner import TextCleaner


def test_collapses_multiple_spaces():
    cleaner = TextCleaner()
    assert cleaner.clean("This   has     extra   spaces") == "This has extra spaces"


def test_collapses_excess_blank_lines():
    cleaner = TextCleaner()
    result = cleaner.clean("Para one.\n\n\n\n\nPara two.")
    assert result == "Para one.\n\nPara two."


def test_strips_page_numbers():
    cleaner = TextCleaner(strip_page_numbers=True)
    text = "Section 1. Terms\nPage 3 of 12\nSection 2. More terms"
    result = cleaner.clean(text)
    assert "Page 3 of 12" not in result


def test_empty_input_returns_empty_string():
    cleaner = TextCleaner()
    assert cleaner.clean("") == ""


def test_unicode_normalization_does_not_crash():
    cleaner = TextCleaner()
    result = cleaner.clean("Café — naïve résumé\u200b test")
    assert "Café" in result
