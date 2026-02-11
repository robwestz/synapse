"""
Text Preprocessing Utilities
"""
import re
import string
from typing import List
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from app.logger import get_logger

logger = get_logger()

# Download required NLTK data (silent if already downloaded)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)


class TextPreprocessor:
    """Text preprocessing utilities for NLP tasks"""

    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()

    def clean_text(self, text: str, lowercase: bool = True) -> str:
        """
        Clean text by removing special characters and extra whitespace

        Args:
            text: Input text
            lowercase: Convert to lowercase

        Returns:
            Cleaned text
        """
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove URLs
        text = re.sub(r'http\S+|www.\S+', '', text)

        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Convert to lowercase
        if lowercase:
            text = text.lower()

        return text

    def tokenize(self, text: str, remove_punctuation: bool = True) -> List[str]:
        """
        Tokenize text into words

        Args:
            text: Input text
            remove_punctuation: Remove punctuation marks

        Returns:
            List of tokens
        """
        # Clean text first
        text = self.clean_text(text)

        # Remove punctuation if requested
        if remove_punctuation:
            text = text.translate(str.maketrans('', '', string.punctuation))

        # Tokenize
        tokens = word_tokenize(text)

        return tokens

    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """
        Remove stopwords from token list

        Args:
            tokens: List of tokens

        Returns:
            Filtered tokens
        """
        return [token for token in tokens if token.lower() not in self.stop_words]

    def lemmatize(self, tokens: List[str]) -> List[str]:
        """
        Lemmatize tokens to their base form

        Args:
            tokens: List of tokens

        Returns:
            Lemmatized tokens
        """
        return [self.lemmatizer.lemmatize(token) for token in tokens]

    def preprocess(
        self,
        text: str,
        lowercase: bool = True,
        remove_stopwords: bool = True,
        lemmatize: bool = True,
        remove_punctuation: bool = True
    ) -> List[str]:
        """
        Complete preprocessing pipeline

        Args:
            text: Input text
            lowercase: Convert to lowercase
            remove_stopwords: Remove stopwords
            lemmatize: Apply lemmatization
            remove_punctuation: Remove punctuation

        Returns:
            Preprocessed tokens
        """
        # Clean text
        text = self.clean_text(text, lowercase=lowercase)

        # Tokenize
        tokens = self.tokenize(text, remove_punctuation=remove_punctuation)

        # Remove stopwords
        if remove_stopwords:
            tokens = self.remove_stopwords(tokens)

        # Lemmatize
        if lemmatize:
            tokens = self.lemmatize(tokens)

        # Filter short tokens
        tokens = [t for t in tokens if len(t) > 2]

        return tokens

    def extract_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Use NLTK sentence tokenizer
        sentences = nltk.sent_tokenize(text)
        return sentences

    def normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text

        Args:
            text: Input text

        Returns:
            Text with normalized whitespace
        """
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)

        # Replace multiple newlines with double newline
        text = re.sub(r'\n+', '\n\n', text)

        return text.strip()

    def remove_numbers(self, text: str) -> str:
        """
        Remove numbers from text

        Args:
            text: Input text

        Returns:
            Text without numbers
        """
        return re.sub(r'\d+', '', text)

    def expand_contractions(self, text: str) -> str:
        """
        Expand common English contractions

        Args:
            text: Input text

        Returns:
            Text with expanded contractions
        """
        contractions = {
            "don't": "do not",
            "doesn't": "does not",
            "didn't": "did not",
            "can't": "cannot",
            "cannot": "can not",
            "won't": "will not",
            "wouldn't": "would not",
            "shouldn't": "should not",
            "couldn't": "could not",
            "isn't": "is not",
            "aren't": "are not",
            "wasn't": "was not",
            "weren't": "were not",
            "haven't": "have not",
            "hasn't": "has not",
            "hadn't": "had not",
            "i'm": "i am",
            "you're": "you are",
            "he's": "he is",
            "she's": "she is",
            "it's": "it is",
            "we're": "we are",
            "they're": "they are",
            "i've": "i have",
            "you've": "you have",
            "we've": "we have",
            "they've": "they have",
            "i'll": "i will",
            "you'll": "you will",
            "he'll": "he will",
            "she'll": "she will",
            "we'll": "we will",
            "they'll": "they will",
            "i'd": "i would",
            "you'd": "you would",
            "he'd": "he would",
            "she'd": "she would",
            "we'd": "we would",
            "they'd": "they would"
        }

        # Replace contractions
        for contraction, expansion in contractions.items():
            text = re.sub(r'\b' + contraction + r'\b', expansion, text, flags=re.IGNORECASE)

        return text

    def get_ngrams(self, tokens: List[str], n: int = 2) -> List[str]:
        """
        Generate n-grams from tokens

        Args:
            tokens: List of tokens
            n: Size of n-grams

        Returns:
            List of n-grams as strings
        """
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = ' '.join(tokens[i:i+n])
            ngrams.append(ngram)
        return ngrams

    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """
        Extract top keywords from text (simple frequency-based)

        Args:
            text: Input text
            top_n: Number of top keywords to return

        Returns:
            List of top keywords
        """
        # Preprocess text
        tokens = self.preprocess(text)

        # Count frequencies
        from collections import Counter
        freq = Counter(tokens)

        # Get top n
        top_keywords = [word for word, _ in freq.most_common(top_n)]

        return top_keywords
