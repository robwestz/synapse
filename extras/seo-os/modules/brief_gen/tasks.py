"""
Brief Generator Module - Pipeline Tasks
"""
from core.database import save_asset
import uuid

async def generate_brief_task(context: dict, config: dict, project_id: int):
    """
    Input: context['serp_results_batch']
    Output: Adds 'briefs_generated' to context.
    """
    batch = context.get("serp_results_batch", {})
    if not batch:
        # Fallback for single result
        if "serp_results" in context:
            batch = {context.get("last_keyword", "Unknown"): context["serp_results"]}
            
    if not batch:
        raise ValueError("No SERP results found in context to build briefs from")

    generated_count = 0
    for keyword, results in batch.items():
        # Simple logic: Take top 3 titles as inspiration
        top_titles = [r.get('title', 'N/A') for r in results[:3]]
        
        brief_content = f"# Content Brief: {keyword}\n\n"
        brief_content += "## Top Competitor Titles\n"
        for title in top_titles:
            brief_content += f"- {title}\n"
        
        brief_content += "\n## Suggested Outline\n1. Introduction\n2. Key Benefits\n3. Comparison\n4. Conclusion"

        # Save to DB
        save_asset(
            asset_id=str(uuid.uuid4()),
            project_id=project_id,
            module_id="brief_gen",
            asset_type="content_brief",
            content={"keyword": keyword, "brief_md": brief_content},
            metadata={"source": "pipeline", "batch_run": True}
        )
        generated_count += 1

    return {
        "briefs_generated_count": generated_count
    }

