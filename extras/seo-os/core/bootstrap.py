"""
Nexus Initialization
Registers all module tasks into the pipeline engine.
"""
from core.pipeline import nexus_engine
from modules.search.tasks import run_serp_analysis_task
from modules.brief_gen.tasks import generate_brief_task
from modules.intelligence_hub.tasks import find_competitor_gaps_task

def bootstrap_nexus():
    # Register Search Tasks
    nexus_engine.register_task("search_studio", "serp_analysis", run_serp_analysis_task)
    
    # Register Brief Gen Tasks
    nexus_engine.register_task("brief_gen", "generate_brief", generate_brief_task)

    # Register Intelligence Hub Tasks
    nexus_engine.register_task("intelligence_hub", "find_gaps", find_competitor_gaps_task)
    
    return nexus_engine
