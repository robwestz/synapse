"""
Feature Extraction Utilities
Extract features from content for ML models
"""
import re
from bs4 import BeautifulSoup
from typing import Dict, List
import numpy as np
from app.logger import get_logger

logger = get_logger()


class ContentFeatureExtractor:
    """Extract features from HTML/text content"""

    def __init__(self):
        pass

    def extract_features(
        self,
        content: str,
        title: str = "",
        keywords: List[str] = None,
        url: str = ""
    ) -> Dict:
        """
        Extract comprehensive features from content

        Args:
            content: HTML or text content
            title: Page title
            keywords: Target keywords
            url: Page URL

        Returns:
            Dict of extracted features
        """
        try:
            keywords = keywords or []

            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')

            # Extract text
            text = self._extract_text(soup)

            # Basic text features
            text_features = self._extract_text_features(text)

            # Keyword features
            keyword_features = self._extract_keyword_features(text, keywords)

            # Structure features
            structure_features = self._extract_structure_features(soup)

            # Link features
            link_features = self._extract_link_features(soup)

            # Title features
            title_features = self._extract_title_features(title, keywords)

            # URL features
            url_features = self._extract_url_features(url)

            # Combine all features
            features = {
                **text_features,
                **keyword_features,
                **structure_features,
                **link_features,
                **title_features,
                **url_features
            }

            return features

        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            raise

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract clean text from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text

    def _extract_text_features(self, text: str) -> Dict:
        """Extract text-based features"""
        # Word count
        words = text.split()
        word_count = len(words)

        # Sentence count
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)

        # Average sentence length
        avg_sentence_length = word_count / max(sentence_count, 1)

        # Paragraph count (simple heuristic)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)

        # Character count
        char_count = len(text)

        # Average word length
        avg_word_length = sum(len(word) for word in words) / max(word_count, 1)

        # Unique words
        unique_words = len(set(word.lower() for word in words))
        unique_words_ratio = unique_words / max(word_count, 1)

        # Readability score (simplified Flesch Reading Ease)
        readability_score = self._calculate_readability(
            word_count, sentence_count, char_count
        )

        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count,
            'char_count': char_count,
            'avg_sentence_length': round(avg_sentence_length, 2),
            'avg_word_length': round(avg_word_length, 2),
            'unique_words': unique_words,
            'unique_words_ratio': round(unique_words_ratio, 3),
            'readability_score': round(readability_score, 2)
        }

    def _extract_keyword_features(self, text: str, keywords: List[str]) -> Dict:
        """Extract keyword-related features"""
        if not keywords:
            return {
                'keyword_density': 0.0,
                'keyword_count': 0,
                'keyword_in_first_100': False
            }

        text_lower = text.lower()
        words = text.split()
        word_count = len(words)

        # Count keyword occurrences
        keyword_count = 0
        for keyword in keywords:
            keyword_lower = keyword.lower()
            keyword_count += text_lower.count(keyword_lower)

        # Keyword density
        keyword_density = keyword_count / max(word_count, 1)

        # Check if keyword appears in first 100 words
        first_100_words = ' '.join(words[:100]).lower()
        keyword_in_first_100 = any(
            kw.lower() in first_100_words for kw in keywords
        )

        return {
            'keyword_density': round(keyword_density, 4),
            'keyword_count': keyword_count,
            'keyword_in_first_100': keyword_in_first_100
        }

    def _extract_structure_features(self, soup: BeautifulSoup) -> Dict:
        """Extract HTML structure features"""
        # Headings
        h1_count = len(soup.find_all('h1'))
        h2_count = len(soup.find_all('h2'))
        h3_count = len(soup.find_all('h3'))
        heading_count = h1_count + h2_count + h3_count

        # Images
        images = soup.find_all('img')
        image_count = len(images)
        images_with_alt = len([img for img in images if img.get('alt')])

        # Lists
        list_count = len(soup.find_all(['ul', 'ol']))

        # Tables
        table_count = len(soup.find_all('table'))

        return {
            'h1_count': h1_count,
            'h2_count': h2_count,
            'h3_count': h3_count,
            'heading_count': heading_count,
            'image_count': image_count,
            'images_with_alt': images_with_alt,
            'list_count': list_count,
            'table_count': table_count
        }

    def _extract_link_features(self, soup: BeautifulSoup) -> Dict:
        """Extract link-related features"""
        links = soup.find_all('a', href=True)

        internal_links = 0
        external_links = 0

        for link in links:
            href = link['href']
            if href.startswith('http'):
                external_links += 1
            else:
                internal_links += 1

        return {
            'total_links': len(links),
            'internal_link_count': internal_links,
            'external_link_count': external_links
        }

    def _extract_title_features(self, title: str, keywords: List[str]) -> Dict:
        """Extract title-related features"""
        if not title:
            return {
                'title_length': 0,
                'title_word_count': 0,
                'keyword_in_title': False
            }

        title_length = len(title)
        title_word_count = len(title.split())

        # Check if keyword in title
        title_lower = title.lower()
        keyword_in_title = any(kw.lower() in title_lower for kw in keywords)

        return {
            'title_length': title_length,
            'title_word_count': title_word_count,
            'keyword_in_title': keyword_in_title
        }

    def _extract_url_features(self, url: str) -> Dict:
        """Extract URL-related features"""
        if not url:
            return {
                'url_length': 0,
                'url_depth': 0
            }

        url_length = len(url)

        # URL depth (number of slashes)
        url_depth = url.count('/') - 2 if url.startswith('http') else url.count('/')

        return {
            'url_length': url_length,
            'url_depth': max(0, url_depth)
        }

    def _calculate_readability(
        self,
        word_count: int,
        sentence_count: int,
        char_count: int
    ) -> float:
        """
        Calculate simplified readability score
        Based on Flesch Reading Ease formula
        """
        if word_count == 0 or sentence_count == 0:
            return 0.0

        # Average words per sentence
        avg_words_per_sentence = word_count / sentence_count

        # Average syllables per word (approximated by characters)
        avg_syllables_per_word = char_count / word_count / 3

        # Flesch Reading Ease
        score = 206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)

        # Clamp between 0 and 100
        return max(0, min(100, score))
