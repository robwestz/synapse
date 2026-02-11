"""
Intelligence Hub - Pipeline Tasks
Tasks for mining the internal Data Lake.
"""
import sqlite3
import pandas as pd
from core.database import DB_PATH

async def find_competitor_gaps_task(context: dict, config: dict, project_id: int):
    """
    Analyzes external_keywords table to find gaps.
    Input: config['min_traffic'], config['max_gaps']
    Output: Adds 'discovered_keywords' to context.
    """
    min_traffic = config.get("min_traffic", 100)
    max_gaps = config.get("max_gaps", 5)
    
    conn = sqlite3.connect(DB_PATH)
    
    # Logic: 
    # 1. Find keywords where competitors rank (is_primary_site = 0)
    # 2. Where we DON'T rank well (is_primary_site = 1 AND position > 20 OR missing)
    # This is a simplified "Gap" query
    query = f"""
        SELECT keyword, sum(traffic) as total_comp_traffic, parent_topic
        FROM external_keywords
        WHERE is_primary_site = 0
        AND keyword NOT IN (SELECT keyword FROM external_keywords WHERE is_primary_site = 1 AND position <= 10)
        GROUP BY keyword
        HAVING total_comp_traffic >= {min_traffic}
        ORDER BY total_comp_traffic DESC
        LIMIT {max_gaps}
    """
    
    df_gaps = pd.read_sql_query(query, conn)
    conn.close()
    
    if df_gaps.empty:
        return {"discovered_keywords": [], "status": "No gaps found"}
    
    keywords = df_gaps['keyword'].tolist()
    
    return {
        "discovered_keywords": keywords,
        "gap_analysis_summary": f"Discovered {len(keywords)} high-value gaps.",
        "last_keyword": keywords[0] if keywords else None # For single-followup nodes
    }
