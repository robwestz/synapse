"""
Keyword Clustering using Word2Vec + K-means
Groups keywords by semantic similarity
"""
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from gensim.models import Word2Vec
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from app.config import get_settings
from app.logger import get_logger
from app.utils.preprocessing import TextPreprocessor

settings = get_settings()
logger = get_logger()


class KeywordClusterer:
    """Word2Vec + K-means keyword clustering"""

    def __init__(self):
        self.word2vec_model: Optional[Word2Vec] = None
        self.kmeans_model: Optional[KMeans] = None
        self.preprocessor = TextPreprocessor()
        self.is_loaded = False

    def load_model(self, model_path: Optional[str] = None):
        """Load Word2Vec model"""
        try:
            logger.info("Loading Word2Vec model...")

            if model_path:
                self.word2vec_model = Word2Vec.load(model_path)
            else:
                # Will train on-the-fly if no pre-trained model
                logger.info("No pre-trained Word2Vec model, will train on demand")
                self.word2vec_model = None

            self.is_loaded = True
            logger.info("Keyword clusterer ready")

        except Exception as e:
            logger.error(f"Error loading Word2Vec model: {e}")
            self.word2vec_model = None
            self.is_loaded = True

    def cluster_keywords(
        self,
        keywords: List[str],
        n_clusters: Optional[int] = None,
        min_cluster_size: int = None,
        max_cluster_size: int = None
    ) -> Dict:
        """
        Cluster keywords by semantic similarity

        Args:
            keywords: List of keywords to cluster
            n_clusters: Number of clusters (auto-detected if None)
            min_cluster_size: Minimum cluster size
            max_cluster_size: Maximum cluster size

        Returns:
            Dict with clusters and metadata
        """
        if not self.is_loaded:
            self.load_model()

        try:
            # Validate input
            if len(keywords) < 2:
                raise ValueError("Need at least 2 keywords to cluster")

            min_size = min_cluster_size or settings.CLUSTER_MIN_SIZE
            max_size = max_cluster_size or settings.CLUSTER_MAX_SIZE

            # Train Word2Vec if needed
            if self.word2vec_model is None:
                self._train_word2vec(keywords)

            # Get embeddings
            embeddings, valid_keywords = self._get_embeddings(keywords)

            if len(valid_keywords) < 2:
                raise ValueError("Insufficient keywords with valid embeddings")

            # Determine optimal number of clusters
            if n_clusters is None:
                n_clusters = self._find_optimal_clusters(embeddings, valid_keywords, min_size, max_size)

            # Perform clustering
            self.kmeans_model = KMeans(
                n_clusters=n_clusters,
                random_state=42,
                n_init=10
            )
            cluster_labels = self.kmeans_model.fit_predict(embeddings)

            # Build clusters
            clusters = self._build_clusters(valid_keywords, cluster_labels)

            # Calculate metrics
            silhouette = silhouette_score(embeddings, cluster_labels) if len(set(cluster_labels)) > 1 else 0.0

            # Get cluster themes
            cluster_themes = self._extract_cluster_themes(clusters)

            result = {
                "n_clusters": n_clusters,
                "total_keywords": len(valid_keywords),
                "silhouette_score": round(float(silhouette), 3),
                "clusters": clusters,
                "cluster_themes": cluster_themes,
                "metrics": {
                    "avg_cluster_size": round(len(valid_keywords) / n_clusters, 2),
                    "min_cluster_size": min(len(c["keywords"]) for c in clusters),
                    "max_cluster_size": max(len(c["keywords"]) for c in clusters)
                }
            }

            logger.info(f"Clustered {len(valid_keywords)} keywords into {n_clusters} groups")

            return result

        except Exception as e:
            logger.error(f"Error clustering keywords: {e}")
            raise

    def _train_word2vec(self, keywords: List[str]):
        """Train Word2Vec model on keywords"""
        logger.info("Training Word2Vec model on keywords...")

        # Tokenize keywords
        sentences = [self.preprocessor.tokenize(kw) for kw in keywords]

        # Train model
        self.word2vec_model = Word2Vec(
            sentences=sentences,
            vector_size=settings.WORD2VEC_DIM,
            window=settings.WORD2VEC_WINDOW,
            min_count=1,
            workers=4,
            sg=1  # Skip-gram
        )

        logger.info("Word2Vec training complete")

    def _get_embeddings(self, keywords: List[str]) -> Tuple[np.ndarray, List[str]]:
        """Get Word2Vec embeddings for keywords"""
        embeddings = []
        valid_keywords = []

        for keyword in keywords:
            try:
                # Tokenize
                tokens = self.preprocessor.tokenize(keyword)

                # Get average embedding
                word_vectors = []
                for token in tokens:
                    if token in self.word2vec_model.wv:
                        word_vectors.append(self.word2vec_model.wv[token])

                if word_vectors:
                    avg_vector = np.mean(word_vectors, axis=0)
                    embeddings.append(avg_vector)
                    valid_keywords.append(keyword)

            except Exception as e:
                logger.warning(f"Could not embed keyword '{keyword}': {e}")
                continue

        return np.array(embeddings), valid_keywords

    def _find_optimal_clusters(
        self,
        embeddings: np.ndarray,
        keywords: List[str],
        min_size: int,
        max_size: int
    ) -> int:
        """Find optimal number of clusters using elbow method"""
        n_keywords = len(keywords)

        # Calculate range
        min_clusters = max(2, n_keywords // max_size)
        max_clusters = min(n_keywords // min_size, 10)

        if min_clusters >= max_clusters:
            return min(max(2, n_keywords // 10), n_keywords)

        # Try different cluster numbers
        inertias = []
        K_range = range(min_clusters, max_clusters + 1)

        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(embeddings)
            inertias.append(kmeans.inertia_)

        # Find elbow using simple derivative
        if len(inertias) > 2:
            diffs = np.diff(inertias)
            elbow_idx = np.argmin(diffs) + 1
            optimal_k = list(K_range)[elbow_idx]
        else:
            optimal_k = min_clusters

        logger.info(f"Optimal clusters: {optimal_k}")

        return optimal_k

    def _build_clusters(self, keywords: List[str], labels: np.ndarray) -> List[Dict]:
        """Build cluster structure"""
        cluster_dict = defaultdict(list)

        for keyword, label in zip(keywords, labels):
            cluster_dict[int(label)].append(keyword)

        clusters = []
        for cluster_id, kws in sorted(cluster_dict.items()):
            clusters.append({
                "cluster_id": cluster_id,
                "size": len(kws),
                "keywords": sorted(kws)
            })

        return clusters

    def _extract_cluster_themes(self, clusters: List[Dict]) -> Dict[int, str]:
        """Extract theme/topic for each cluster"""
        themes = {}

        for cluster in clusters:
            cluster_id = cluster["cluster_id"]
            keywords = cluster["keywords"]

            # Simple approach: use most common words
            all_tokens = []
            for kw in keywords:
                tokens = self.preprocessor.tokenize(kw)
                all_tokens.extend(tokens)

            # Count token frequency
            token_counts = defaultdict(int)
            for token in all_tokens:
                token_counts[token] += 1

            # Get top tokens as theme
            top_tokens = sorted(token_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            theme = " / ".join([token for token, _ in top_tokens])

            themes[cluster_id] = theme

        return themes

    def get_similar_keywords(self, keyword: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """Find similar keywords using Word2Vec"""
        if self.word2vec_model is None:
            raise ValueError("Word2Vec model not loaded")

        try:
            tokens = self.preprocessor.tokenize(keyword)

            # Get similar words for each token
            similar = []
            for token in tokens:
                if token in self.word2vec_model.wv:
                    sim = self.word2vec_model.wv.most_similar(token, topn=top_n)
                    similar.extend(sim)

            # Remove duplicates and sort
            similar = list(set(similar))
            similar.sort(key=lambda x: x[1], reverse=True)

            return similar[:top_n]

        except Exception as e:
            logger.error(f"Error finding similar keywords: {e}")
            return []
