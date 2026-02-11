"""
Search Module - Pipeline Tasks
"""
from core.search_provider import get_provider
from core.intelligence import classify_intent, cluster_results
from core.database import save_asset
import uuid

async def run_serp_analysis_task(context: dict, config: dict, project_id: int):
    """
    Input: config['keyword'] OR context['discovered_keywords']
    Output: Adds 'serp_results_batch' to context.
    """
    # 1. Determine which keywords to search
    # Priority: Context (discovered) > Config (explicit)
    keywords = context.get("discovered_keywords", [])
    if not keywords and config.get("keyword"):
        keywords = [config.get("keyword")]
        
    if not keywords:
        raise ValueError("No keywords provided for search task")

    count = config.get("count", 10)
    provider_name = config.get("provider", "ddg")
    use_ml = config.get("use_ml", False)
    
    provider = get_provider(provider_name)
    batch_results = {}

    for kw in keywords:
        response = provider.search(kw, num_results=count)
        results = provider.refine_results(response, config)
        
        if config.get("cluster", True):
            results = cluster_results(results, use_ml=use_ml)
        
        # Save to DB
        asset_id = str(uuid.uuid4())
        save_asset(
            asset_id=asset_id,
            project_id=project_id,
            module_id="search_studio",
            asset_type="serp_results",
            content={"query": kw, "results": results},
            metadata={"source": "pipeline", "task": "serp_analysis"}
        )
        batch_results[kw] = results

    return {
        "serp_results_batch": batch_results,
        "last_keyword": keywords[-1]
    }
