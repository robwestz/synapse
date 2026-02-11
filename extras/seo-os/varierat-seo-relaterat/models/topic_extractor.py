"""
spaCy-based Topic and Entity Extraction
Extracts topics, named entities, and key phrases from content
"""
import spacy
from typing import Dict, List, Optional, Set
from collections import Counter, defaultdict
from app.config import get_settings
from app.logger import get_logger

settings = get_settings()
logger = get_logger()


class TopicExtractor:
    """spaCy-based topic and entity extraction"""

    def __init__(self):
        self.nlp: Optional[spacy.language.Language] = None
        self.is_loaded = False

    def load_model(self, model_name: Optional[str] = None):
        """Load spaCy model"""
        try:
            logger.info("Loading spaCy NLP model...")

            model_name = model_name or settings.SPACY_MODEL
            self.nlp = spacy.load(model_name)

            self.is_loaded = True
            logger.info(f"spaCy model '{model_name}' loaded successfully")

        except Exception as e:
            logger.error(f"Error loading spaCy model: {e}")
            raise

    def extract_topics(
        self,
        text: str,
        max_topics: int = 10,
        include_entities: bool = True,
        include_keyphrases: bool = True
    ) -> Dict:
        """
        Extract topics from text

        Args:
            text: Input text
            max_topics: Maximum number of topics to return
            include_entities: Include named entities
            include_keyphrases: Include key phrases

        Returns:
            Dict with topics, entities, and key phrases
        """
        if not self.is_loaded:
            self.load_model()

        try:
            # Process text
            doc = self.nlp(text)

            result = {}

            # Extract main topics (noun chunks)
            if include_keyphrases:
                topics = self._extract_noun_chunks(doc, max_topics)
                result['topics'] = topics

            # Extract named entities
            if include_entities:
                entities = self._extract_entities(doc)
                result['entities'] = entities

            # Extract keywords
            keywords = self._extract_keywords(doc, max_topics)
            result['keywords'] = keywords

            # Content statistics
            result['statistics'] = {
                'sentence_count': len(list(doc.sents)),
                'word_count': len([token for token in doc if not token.is_punct]),
                'unique_words': len(set([token.lemma_.lower() for token in doc if not token.is_stop and not token.is_punct])),
                'avg_sentence_length': round(len(doc) / max(1, len(list(doc.sents))), 2)
            }

            logger.debug(f"Extracted {len(result.get('topics', []))} topics from text")

            return result

        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            raise

    def _extract_noun_chunks(self, doc, max_topics: int) -> List[Dict]:
        """Extract noun chunks as topics"""
        chunks = []
        chunk_counts = Counter()

        for chunk in doc.noun_chunks:
            # Filter out short or stop-word-only chunks
            if len(chunk.text.split()) >= 2:
                normalized = chunk.text.lower().strip()
                chunk_counts[normalized] += 1

        # Get most common
        topics = []
        for chunk, count in chunk_counts.most_common(max_topics):
            topics.append({
                'phrase': chunk,
                'frequency': count,
                'type': 'noun_phrase'
            })

        return topics

    def _extract_entities(self, doc) -> Dict[str, List[Dict]]:
        """Extract named entities"""
        entities = defaultdict(list)

        for ent in doc.ents:
            entities[ent.label_].append({
                'text': ent.text,
                'label': ent.label_,
                'description': spacy.explain(ent.label_)
            })

        # Remove duplicates and count
        entity_result = {}
        for label, ent_list in entities.items():
            # Count occurrences
            ent_counter = Counter([e['text'] for e in ent_list])

            # Build unique list
            unique_entities = []
            seen = set()
            for ent in ent_list:
                if ent['text'] not in seen:
                    ent['count'] = ent_counter[ent['text']]
                    unique_entities.append(ent)
                    seen.add(ent['text'])

            # Sort by count
            unique_entities.sort(key=lambda x: x['count'], reverse=True)
            entity_result[label] = unique_entities

        return entity_result

    def _extract_keywords(self, doc, max_keywords: int) -> List[Dict]:
        """Extract keywords using frequency and POS tagging"""
        # Focus on nouns, proper nouns, and adjectives
        target_pos = {'NOUN', 'PROPN', 'ADJ'}

        word_freq = Counter()
        for token in doc:
            if (token.pos_ in target_pos and
                not token.is_stop and
                not token.is_punct and
                len(token.text) >= settings.MIN_WORD_LENGTH):
                word_freq[token.lemma_.lower()] += 1

        # Get top keywords
        keywords = []
        for word, freq in word_freq.most_common(max_keywords):
            keywords.append({
                'word': word,
                'frequency': freq,
                'relevance': round(freq / len(doc), 4)
            })

        return keywords

    def extract_relationships(self, text: str) -> List[Dict]:
        """Extract subject-verb-object relationships"""
        if not self.is_loaded:
            self.load_model()

        try:
            doc = self.nlp(text)
            relationships = []

            for sent in doc.sents:
                # Find root verb
                root = [token for token in sent if token.dep_ == "ROOT"]
                if not root:
                    continue

                verb = root[0]

                # Find subject
                subject = None
                for child in verb.children:
                    if child.dep_ in ("nsubj", "nsubjpass"):
                        subject = child
                        break

                # Find object
                obj = None
                for child in verb.children:
                    if child.dep_ in ("dobj", "pobj", "attr"):
                        obj = child
                        break

                if subject and obj:
                    relationships.append({
                        'subject': subject.text,
                        'verb': verb.text,
                        'object': obj.text,
                        'sentence': sent.text
                    })

            return relationships

        except Exception as e:
            logger.error(f"Error extracting relationships: {e}")
            return []

    def analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment using spaCy's built-in capabilities"""
        if not self.is_loaded:
            self.load_model()

        try:
            doc = self.nlp(text)

            # Count positive/negative words (simple heuristic)
            positive_words = ['good', 'great', 'excellent', 'best', 'amazing', 'wonderful', 'fantastic']
            negative_words = ['bad', 'poor', 'terrible', 'worst', 'awful', 'horrible', 'disappointing']

            pos_count = 0
            neg_count = 0

            for token in doc:
                lemma = token.lemma_.lower()
                if lemma in positive_words:
                    pos_count += 1
                elif lemma in negative_words:
                    neg_count += 1

            total = pos_count + neg_count
            if total > 0:
                sentiment_score = (pos_count - neg_count) / total
                if sentiment_score > 0.2:
                    sentiment = "positive"
                elif sentiment_score < -0.2:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"
            else:
                sentiment = "neutral"
                sentiment_score = 0.0

            return {
                'sentiment': sentiment,
                'score': round(sentiment_score, 3),
                'positive_words': pos_count,
                'negative_words': neg_count
            }

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {'sentiment': 'neutral', 'score': 0.0}

    def extract_questions(self, text: str) -> List[str]:
        """Extract questions from text"""
        if not self.is_loaded:
            self.load_model()

        try:
            doc = self.nlp(text)
            questions = []

            for sent in doc.sents:
                sent_text = sent.text.strip()
                # Check if sentence is a question
                if sent_text.endswith('?'):
                    questions.append(sent_text)
                else:
                    # Check for question patterns
                    first_token = sent[0] if sent else None
                    if first_token and first_token.text.lower() in ['who', 'what', 'when', 'where', 'why', 'how', 'which']:
                        questions.append(sent_text)

            return questions

        except Exception as e:
            logger.error(f"Error extracting questions: {e}")
            return []

    def get_content_summary(self, text: str, num_sentences: int = 3) -> str:
        """Generate simple extractive summary"""
        if not self.is_loaded:
            self.load_model()

        try:
            doc = self.nlp(text)
            sentences = list(doc.sents)

            if len(sentences) <= num_sentences:
                return text

            # Score sentences by keyword density
            sentence_scores = []
            for sent in sentences:
                score = len([token for token in sent if not token.is_stop and not token.is_punct])
                sentence_scores.append((sent, score))

            # Get top sentences
            top_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)[:num_sentences]

            # Sort by original order
            top_sentences_ordered = sorted(top_sentences, key=lambda x: x[0].start)

            summary = ' '.join([sent.text for sent, _ in top_sentences_ordered])

            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return text[:500] + "..."
