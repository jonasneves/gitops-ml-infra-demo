"""
Unit tests for ML inference sentiment analysis.
Tests the core analyze_sentiment function and related logic.
"""
import pytest

# Import the sentiment analysis function and word sets
from app import analyze_sentiment, POSITIVE_WORDS, NEGATIVE_WORDS


class TestAnalyzeSentiment:
    """Tests for the analyze_sentiment function."""

    @pytest.mark.unit
    @pytest.mark.inference
    def test_positive_sentiment_single_word(self):
        """Test positive sentiment detection with a single positive word."""
        sentiment, confidence = analyze_sentiment("This is amazing")
        assert sentiment == "positive"
        assert 0.6 <= confidence <= 0.95

    @pytest.mark.unit
    @pytest.mark.inference
    def test_positive_sentiment_multiple_words(self):
        """Test positive sentiment with multiple positive words."""
        sentiment, confidence = analyze_sentiment("This is amazing wonderful excellent")
        assert sentiment == "positive"
        assert confidence >= 0.7

    @pytest.mark.unit
    @pytest.mark.inference
    def test_negative_sentiment_single_word(self):
        """Test negative sentiment detection with a single negative word."""
        sentiment, confidence = analyze_sentiment("This is terrible")
        assert sentiment == "negative"
        assert 0.6 <= confidence <= 0.95

    @pytest.mark.unit
    @pytest.mark.inference
    def test_negative_sentiment_multiple_words(self):
        """Test negative sentiment with multiple negative words."""
        sentiment, confidence = analyze_sentiment("This is terrible awful horrible")
        assert sentiment == "negative"
        assert confidence >= 0.7

    @pytest.mark.unit
    @pytest.mark.inference
    def test_neutral_sentiment_no_keywords(self):
        """Test neutral sentiment when no sentiment keywords present."""
        sentiment, confidence = analyze_sentiment("The weather is cloudy today")
        assert sentiment == "neutral"
        assert 0.5 <= confidence <= 0.95

    @pytest.mark.unit
    @pytest.mark.inference
    def test_neutral_sentiment_balanced(self):
        """Test neutral sentiment when positive and negative are balanced."""
        sentiment, confidence = analyze_sentiment("good bad")
        assert sentiment == "neutral"

    @pytest.mark.unit
    @pytest.mark.inference
    def test_case_insensitivity(self):
        """Test that sentiment analysis is case-insensitive."""
        sentiment1, _ = analyze_sentiment("AMAZING")
        sentiment2, _ = analyze_sentiment("amazing")
        sentiment3, _ = analyze_sentiment("Amazing")
        assert sentiment1 == sentiment2 == sentiment3 == "positive"

    @pytest.mark.unit
    @pytest.mark.inference
    def test_confidence_upper_bound(self):
        """Test that confidence never exceeds 0.95."""
        # Text with many positive words
        text = " ".join(list(POSITIVE_WORDS)[:10])
        _, confidence = analyze_sentiment(text)
        assert confidence <= 0.95

    @pytest.mark.unit
    @pytest.mark.inference
    def test_confidence_lower_bound(self):
        """Test that confidence is always reasonable."""
        sentiment, confidence = analyze_sentiment("test")
        assert confidence >= 0.5

    @pytest.mark.unit
    @pytest.mark.inference
    def test_empty_text(self):
        """Test handling of minimal text."""
        sentiment, confidence = analyze_sentiment("x")
        assert sentiment == "neutral"
        assert isinstance(confidence, float)


class TestSentimentEdgeCases:
    """Edge case tests for sentiment analysis."""

    @pytest.mark.unit
    @pytest.mark.inference
    def test_special_characters(self):
        """Test that special characters don't break analysis."""
        sentiment, confidence = analyze_sentiment("This is amazing!!! @#$%")
        # 'amazing!!!' won't match because of punctuation
        assert isinstance(sentiment, str)
        assert isinstance(confidence, float)

    @pytest.mark.unit
    @pytest.mark.inference
    def test_numbers_in_text(self):
        """Test text containing numbers."""
        sentiment, confidence = analyze_sentiment("Product 123 is amazing")
        assert sentiment == "positive"
        assert isinstance(confidence, float)

    @pytest.mark.unit
    @pytest.mark.inference
    def test_mixed_content(self):
        """Test text with mixed positive/negative but positive bias."""
        sentiment, _ = analyze_sentiment("amazing great but one bad thing")
        assert sentiment == "positive"

    @pytest.mark.unit
    @pytest.mark.inference
    def test_whitespace_handling(self):
        """Test text with extra whitespace."""
        sentiment, confidence = analyze_sentiment("  amazing   wonderful  ")
        assert sentiment == "positive"
        assert isinstance(confidence, float)


class TestWordSets:
    """Tests for the word sets used in sentiment analysis."""

    @pytest.mark.unit
    @pytest.mark.inference
    def test_positive_words_not_empty(self):
        """Ensure positive words set is populated."""
        assert len(POSITIVE_WORDS) > 0

    @pytest.mark.unit
    @pytest.mark.inference
    def test_negative_words_not_empty(self):
        """Ensure negative words set is populated."""
        assert len(NEGATIVE_WORDS) > 0

    @pytest.mark.unit
    @pytest.mark.inference
    def test_word_sets_are_disjoint(self):
        """Ensure positive and negative word sets don't overlap."""
        overlap = POSITIVE_WORDS & NEGATIVE_WORDS
        assert len(overlap) == 0, f"Words appear in both sets: {overlap}"

    @pytest.mark.unit
    @pytest.mark.inference
    def test_word_sets_are_lowercase(self):
        """Ensure all words in sets are lowercase."""
        for word in POSITIVE_WORDS:
            assert word == word.lower(), f"Positive word not lowercase: {word}"
        for word in NEGATIVE_WORDS:
            assert word == word.lower(), f"Negative word not lowercase: {word}"


class TestSentimentRealWorld:
    """Real-world example tests."""

    @pytest.mark.unit
    @pytest.mark.inference
    def test_product_review_positive(self):
        """Test a realistic positive product review."""
        text = "This product is excellent and I love using it every day"
        sentiment, confidence = analyze_sentiment(text)
        assert sentiment == "positive"
        assert confidence >= 0.6

    @pytest.mark.unit
    @pytest.mark.inference
    def test_product_review_negative(self):
        """Test a realistic negative product review."""
        text = "Terrible experience, I hate this poor quality product"
        sentiment, confidence = analyze_sentiment(text)
        assert sentiment == "negative"
        assert confidence >= 0.6

    @pytest.mark.unit
    @pytest.mark.inference
    def test_gitops_demo_text(self):
        """Test with the example from the API docs."""
        text = "This GitOps demo is amazing!"
        sentiment, confidence = analyze_sentiment(text)
        assert sentiment == "positive"
