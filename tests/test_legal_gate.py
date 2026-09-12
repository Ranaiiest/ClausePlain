from src.product.gate import classify_legal_text

OFFER = """
OFFER OF EMPLOYMENT
This offer letter is made between Acme Inc., the employer, and Jordan Lee, the employee.
In consideration of the salary of ninety thousand dollars ($90,000) per year, you shall
commence work on 1 June 2026. Employment is at-will. Either party may terminate this
agreement upon fourteen (14) days' written notice. This agreement is governed by the
laws of California. You agree to keep confidential information confidential and not to
solicit customers for six (6) months after termination.
"""

RECIPE = """
Chocolate cake recipe for a birthday party. Preheat the oven to 350 degrees. Mix flour,
sugar, cocoa powder, eggs, and butter until smooth. Pour into a greased pan and bake
for thirty minutes. Let the cake cool, then frost with vanilla icing. Serve with ice cream
and berries. This has nothing to do with work or school. Enjoy dessert with friends this
weekend after you buy groceries at the market.
"""

NEWS = """
""" + ("The city council met last night to discuss parks, buses, and library hours. " * 40) + (
    "One speaker mentioned a court parking ticket. Then they approved the budget for flowers."
)


def test_offer_letter_is_legal():
    result = classify_legal_text(OFFER)
    assert result.is_legal is True
    assert result.matched_cues


def test_recipe_is_not_legal():
    result = classify_legal_text(RECIPE)
    assert result.is_legal is False
    assert "Not a legal document" in result.reason


def test_long_nonlegal_text_with_one_weak_mention_is_rejected():
    result = classify_legal_text(NEWS)
    assert result.is_legal is False


def test_tiny_file_is_rejected():
    result = classify_legal_text("Hello world this is short.")
    assert result.is_legal is False
    assert "too short" in result.reason.lower()
