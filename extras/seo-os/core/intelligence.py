"""
Superpowers Module
Lightweight implementations of Intent Classification and Clustering for the Search Studio.
Upgraded to support Remote ML Service.
"""
import numpy as np
import pandas as pd
from core.ml_client import ml_client
from core.database import log_keyword_intent, save_entity, save_cluster

# --- INTENT CLASSIFIER ---

INTENT_PATTERNS = {
# ... (patterns remain same) ...
}

def classify_intent(text: str, use_ml: bool = False, log_db: bool = True) -> str:
    """
    Classifies intent and optionally logs it to the Knowledge Graph.
    """
    intent = "Informational"
    confidence = 0.8
    
    if use_ml:
        res = ml_client.classify_intent(text)
        if res and "intent" in res:
            intent = res["intent"]
            confidence = res.get("confidence", 0.9)
    else:
        # Rule based
        text_lower = text.lower()
        scores = {k: 0 for k in INTENT_PATTERNS}
        for i, patterns in INTENT_PATTERNS.items():
            for p in patterns:
                if re.search(p, text_lower):
                    scores[i] += 1
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            intent = best
            confidence = 0.6 # Lower confidence for regex

    # Log to Knowledge Graph
    if log_db:
        # We treat the input text as the "keyword" for logging purposes
        # Ideally, we should pass the clean keyword separately, but this works for now.
        log_keyword_intent(text[:50], intent, confidence)

    return intent

# --- CLUSTERING ---

def cluster_results(results: List[Dict[str, Any]], num_clusters: int = 5, use_ml: bool = False) -> List[Dict[str, Any]]:
    # ... (logic remains) ...
    # Note: We should probably log the final clusters to DB here too, 
    # but the logic currently modifies the list in place.
    # Let's add saving logic if we detect clusters.
    
    # (Keeping original logic but ensuring imports work)
    if use_ml:
        keywords = [r.get('title', '') for r in results]
        res = ml_client.cluster_keywords(keywords)
        if res and "clusters" in res:
            cluster_map = {}
            for c in res["clusters"]:
                theme_name = res["cluster_themes"].get(str(c["cluster_id"]), "Theme " + str(c["cluster_id"]))
                # Save to Knowledge Graph
                save_cluster(theme_name, c["keywords"])
                
                for kw in c["keywords"]:
                    cluster_map[kw] = {"id": c["cluster_id"], "name": theme_name}
            
            for r in results:
                title = r.get('title', '')
                if title in cluster_map:
                    r['cluster_id'] = cluster_map[title]['id']
                    r['cluster_name'] = cluster_map[title]['name']
            return results

    # Lightweight Fallback
    if not results: return results
    titles = [r.get('title', '') for r in results]
    vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
    try:
        X = vectorizer.fit_transform(titles)
        true_k = min(num_clusters, len(titles))
        if true_k < 2: return results
        model = KMeans(n_clusters=true_k, init='k-means++', max_iter=100, n_init=1)
        model.fit(X)
        order_centroids = model.cluster_centers_.argsort()[:, ::-1]
        terms = vectorizer.get_feature_names_out()
        
        cluster_names = {}
        for i in range(true_k):
            top_terms = [terms[ind] for ind in order_centroids[i, :3]]
            name = ", ".join(top_terms)
            cluster_names[i] = name
            
            # Save lightweight cluster to DB
            # We need to find which titles belong to this cluster
            cluster_keywords = [titles[j] for j in range(len(titles)) if model.labels_[j] == i]
            save_cluster(name, cluster_keywords)

        for idx, label in enumerate(model.labels_):
            results[idx]['cluster_id'] = int(label)
            results[idx]['cluster_name'] = cluster_names[int(label)]
    except: pass
    return results

def extract_entities_simple(text: str) -> List[str]:
    words = text.split()
    entities = []
    for i, w in enumerate(words):
        if i > 0 and w[0].isupper() and w.isalpha():
            entities.append(w)
            # Log entity discovery
            save_entity(w)
            
    return list(set(entities))

# --- SEO SPECIFIC ---

SEO_POWER_WORDS = ["bästa", "test", "guide", "tips", "billigaste", "recension", "topp", "lista", "hur", "så"]

def analyze_seo_title(title: str) -> Dict[str, Any]:
    length = len(title)
    has_year = bool(re.search(r"202\d", title))
    found_power_words = [w for w in SEO_POWER_WORDS if w in title.lower()]
    status = "Good"
    if length > 60: status = "Too Long"
    elif length < 30: status = "Too Short"
    return {
        "title_length": length,
        "title_status": status,
        "has_year": has_year,
        "power_words_count": len(found_power_words),
        "power_words": ", ".join(found_power_words)
    }

def get_serp_insights(results: List[Dict]) -> Dict[str, Any]:
    if not results: return {}
    domains, intents, years_count = [], [], 0
    for r in results:
        try: domains.append(r['link'].split('/')[2])
        except: pass
        if "intent" in r: intents.append(r['intent'])
        if "202" in r.get('title', ''): years_count += 1
    unique_domains = len(set(domains))
    dominant_intent = max(set(intents), key=intents.count) if intents else "Unknown"
    difficulty = "Hard"
    if unique_domains > 7: difficulty = "Low/Medium"
    elif unique_domains < 4: difficulty = "Very Hard"
    return {
        "unique_domains": unique_domains,
        "dominant_intent": dominant_intent,
        "serp_difficulty": difficulty,
        "ctr_year_adoption": f"{int((years_count/len(results))*100)}%",
        "top_competitor": domains[0] if domains else "N/A"
    }