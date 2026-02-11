import streamlit as st
import json
import os
from pathlib import Path
import asyncio
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from core.ml_client import ml_client
from core.bootstrap import bootstrap_nexus
from core.pipeline import PipelineNode
from core.database import get_assets, get_knowledge_graph_stats

# Initialize Engine
engine = bootstrap_nexus()

# Project Nexus - Main Dashboard
st.set_page_config(page_title="Project Nexus | SEO-OS", page_icon="🚀", layout="wide")

st.sidebar.title("🚀 Project Nexus")
st.sidebar.markdown("The Ultimate SEO Operating System")

# Discover Modules
# ... (module discovery code) ...

# Navigation
# ... (navigation code) ...

# --- PAGE: DASHBOARD ---
if page == "Dashboard":
    st.title("Nexus Dashboard")
    st.write("Welcome to the new infrastructure. All modules are connected via a unified memory.")
    
    # Check ML Health
    ml_healthy = ml_client.check_health()
    
    # Fetch Knowledge Graph Stats
    kg_stats = get_knowledge_graph_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active Modules", len(modules))
    col2.metric("🧠 Entities Tracked", kg_stats.get("entities", 0))
    col3.metric("🎯 Intents Logged", kg_stats.get("intents_logged", 0))
    col4.metric("📚 Clusters Saved", kg_stats.get("clusters", 0))
    
    st.caption(f"ML Service Status: {'Online ✅' if ml_healthy else 'Offline ❌'}")
    
    st.divider()
    st.subheader("Project Status")
    st.success("Phase 4: Knowledge Graph (Active)")

# --- PAGE: ACTIVE MODULE RUNNER ---
elif page.startswith("▶"):
    # This is the "App Runner" logic
    st.session_state["active_module_id"] # Just to ensure it stays alive
    
    active_mod = next((m for m in modules if m["id"] == st.session_state["active_module_id"]), None)
    if active_mod:
        st.caption(f"Module: {active_mod['name']} v{active_mod['version']}")
        
        # Execute Module UI
        module_script = active_mod["dir"] / active_mod["entry_point"]
        
        # We read and exec the file. 
        # Note: We pass a copy of globals to avoid polluting the main namespace too much,
        # but we need to ensure Streamlit ('st') is passed.
        with open(module_script, "r", encoding="utf-8") as f:
            code = f.read()
            exec(code, globals())
            
    else:
        st.error("Module not found.")

# --- PAGE: MODULES LIBRARY ---
elif page == "Modules":
    st.title("Nexus Modules")
    
    cols = st.columns(3)
    for idx, mod in enumerate(modules):
        with cols[idx % 3]:
            with st.container(border=True):
                st.subheader(f"{mod['icon']} {mod['name']}")
                st.caption(f"v{mod['version']}")
                st.write(mod["description"])
                
                if st.button(f"Launch", key=f"launch_{mod['id']}", use_container_width=True):
                    st.session_state["active_module_id"] = mod["id"]
                    st.rerun()

# --- PAGE: PIPELINES ---
elif page == "Pipelines":
    st.title("Nexus Pipelines")
    st.write("Automate workflows across multiple modules.")
    
    # PIPELINE 1: Manual Single Keyword
    with st.expander("🚀 Manual: Search + Brief"):
        col1, col2 = st.columns([2, 1])
        # ... (existing UI code) ...
        # (Actually I will just append the second one)

    # PIPELINE 2: Competitor Gap Machine (Data Lake Powered)
    with st.expander("⚡ Advanced: Competitor Gap to Briefs (Data Lake Powered)", expanded=True):
        st.write("Finds keywords your competitors rank for but you don't, then generates briefs for them.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            min_traf = st.number_input("Min Competitor Traffic", value=500)
        with col2:
            max_gaps = st.number_input("Max Briefs to Generate", value=3, min_value=1, max_value=10)
        with col3:
            # Recipe selector
            recipes = get_assets(asset_type="recipe")
            recipe_opts = {r['content']['name']: r['id'] for r in recipes}
            sel_recipe = st.selectbox("Search Recipe", options=["Default"] + list(recipe_opts.keys()), key="gap_recipe")

        if st.button("🔥 Run Gap Machine"):
            nodes = [
                PipelineNode("find", "intelligence_hub", "find_gaps", {"min_traffic": min_traf, "max_gaps": max_gaps}),
                PipelineNode("search", "search_studio", "serp_analysis", {"recipe_id": recipe_opts.get(sel_recipe) if sel_recipe != "Default" else None}),
                PipelineNode("write", "brief_gen", "generate_brief", {})
            ]
            
            with st.status("Executing Gap Machine...") as status:
                run = asyncio.run(engine.run_pipeline(nodes))
                for log in run.logs:
                    st.text(log)
                if run.status == "Completed":
                    status.update(label="Gap Machine Finished! ✅", state="complete")
                    st.success(f"Generated {max_gaps} briefs for your top competitor gaps.")
                    
                    st.divider()
                    st.subheader("📝 Latest Generated Briefs")
                    all_briefs = get_assets(asset_type="content_brief")
                    for b in all_briefs[:max_gaps]:
                        with st.expander(f"Brief: {b['content']['keyword']}"):
                            st.markdown(b['content']['brief_md"])
                else:
                    status.update(label="Failed ❌", state="error")

# --- PAGE: SETTINGS ---
elif page == "Settings":
    st.title("System Settings")
    st.write("Configure ML Service URL, API Keys, and Database paths.")
    st.text_input("ML Service URL", value="http://localhost:8003")
    st.text_input("Database Path", value=str(Path("seo-os/data/nexus.db").absolute()))
