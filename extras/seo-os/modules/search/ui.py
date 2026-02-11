import streamlit as st
import pandas as pd
import json
import sys
import uuid
from pathlib import Path

# Add project root to path (seo-os folder)
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.search_provider import get_provider
from core.database import save_asset, get_assets
from core.intelligence import classify_intent, cluster_results, extract_entities_simple, analyze_seo_title, get_serp_insights

# Load Templates from current module folder
TEMPLATE_PATH = Path(__file__).parent / "templates.json"
with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
    TEMPLATES = json.load(f)["tools"]

st.set_page_config(page_title="Gemini Search Studio", page_icon="🔍", layout="wide")

st.title("🔍 Gemini Search Studio")
st.markdown("Generera dataverktyg genom att välja mallar och datapunkter.")

# Sidebar - Settings
st.sidebar.header("⚙️ Inställningar")
provider_name = st.sidebar.radio("Sökmotor", ["ddg", "serper", "mock"], captions=["Gratis", "Google API", "Testdata"])
api_key = ""
if provider_name == "serper":
    api_key = st.sidebar.text_input("Serper API Key", type="password")

st.sidebar.divider()
st.sidebar.header("🧠 Intelligence")
use_ml = st.sidebar.toggle("High Fidelity ML (BERT/BERT-base)", value=False, help="Använd den tunga ML-tjänsten för bättre intent och klustring.")

# Sidebar - Tool Selection
st.sidebar.header("🛠️ Välj Verktyg")
tool_key = st.sidebar.selectbox("Mall", options=list(TEMPLATES.keys()), format_func=lambda x: TEMPLATES[x]["name"])
current_tool = TEMPLATES[tool_key]

st.sidebar.info(current_tool["description"])

# Main Input Area
with st.form("search_form"):
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_mode = st.radio("Sökläge", ["Enskilt sökord", "Bulk (Ett sökord per rad)"], horizontal=True)
        if search_mode == "Enskilt sökord":
            keyword = st.text_input("Sökord", placeholder="t.ex. bästa hörlurarna 2026")
            keywords = [keyword] if keyword else []
        else:
            bulk_text = st.text_area("Sökordslista", placeholder="sökord 1\nsökord 2\nsökord 3")
            keywords = [k.strip() for k in bulk_text.split("\n") if k.strip()]
    
    with col2:
        count = st.number_input("Resultat per sökord", min_value=1, max_value=50, value=10)
        
    # Dynamic fields based on template
    if "my_url" in current_tool["inputs"]:
        my_url = st.text_input("Min URL (för jämförelse)")
        
    # Field Selection (The "Clickable Interfaces" part)
    st.subheader("📊 Välj Datapunkter")
    selected_fields = st.multiselect(
        "Vilken data vill du extrahera?",
        options=current_tool["selectable_fields"] + ["rank", "title", "link", "snippet"],
        default=current_tool["default_fields"]
    )
    
        submitted = st.form_submit_button("🚀 Kör Analys")
    
    if submitted and keywords:
        all_processed_data = []
        
        progress_bar = st.progress(0)
        for idx, kw in enumerate(keywords):
            st.write(f"Arbetar med: **{kw}** ({idx+1}/{len(keywords)})")
            
            with st.spinner(f"Hämtar data för '{kw}'..."):
                # 1. Fetch Data via Provider
                from consolid.tools.search.provider import get_provider
                provider = get_provider(provider_name, api_key=api_key)
                response = provider.search(kw, num_results=count)
                raw_results = [r.to_dict() for r in response.results]
                
                if response.metadata.get("error"):
                    st.error(f"Fel vid sökning på '{kw}': {response.metadata['error']}")
                    continue
                
                            # 1.5 APPLY SUPERPOWERS (Clustering)
                            if "cluster_name" in selected_fields:
                                raw_results = cluster_results(raw_results, num_clusters=min(5, count//2), use_ml=use_ml)
                            
                            # 2. Process/Enhance Data
                            kw_data = []
                            for r in raw_results:
                                row = r.copy()
                                row["search_query"] = kw # Keep track of which keyword it belongs to
                                
                                if "intent" in selected_fields:
                                    row["intent"] = classify_intent(row.get("title", "") + " " + row.get("snippet", ""), use_ml=use_ml)
                                
                                if "entities" in selected_fields:                        row["entities"] = ", ".join(extract_entities_simple(row.get("snippet", "")))
                    
                    if "domain" in selected_fields or "domain" in current_tool["default_fields"]:
                        try: row["domain"] = row["link"].split("/")[2]
                        except: row["domain"] = "unknown"
                    
                    seo_metrics = analyze_seo_title(row.get("title", ""))
                    row.update(seo_metrics)
                    kw_data.append(row)
                
                            # 3. Save to Unified Database
                
                            asset_id = str(uuid.uuid4())
                
                            save_asset(
                
                                asset_id=asset_id,
                
                                project_id=1, # Default Project
                
                                module_id="search_studio",
                
                                asset_type="serp_results",
                
                                content={"query": kw, "results": raw_results},
                
                                metadata={"tool_type": tool_key, "provider": provider_name}
                
                            )
                
                            all_processed_data.extend(kw_data)
                
                            
                
                        progress_bar.progress((idx + 1) / len(keywords))
                
                
                
                    if all_processed_data:
                
                        df = pd.DataFrame(all_processed_data)
                
                        
                
                        # 2.5 Display Executive Insights (Summary of all keywords)
                
                        insights = get_serp_insights(all_processed_data)
                
                        if tool_key == "seo_audit":
                
                            st.subheader("📊 Global Executive Summary")
                
                            m1, m2, m3, m4 = st.columns(4)
                
                            m1.metric("Avg Difficulty", insights["serp_difficulty"])
                
                            m2.metric("Dominant Intent", insights["dominant_intent"])
                
                            m3.metric("CTR Year Adoption", insights["ctr_year_adoption"])
                
                            m4.metric("Top Competitor", insights["top_competitor"])
                
                
                
                        # 4. Filter Columns for Display
                
                        cols_to_show = ["search_query"] + selected_fields
                
                        display_cols = [c for c in cols_to_show if c in df.columns]
                
                        
                
                        st.subheader("📄 Analysresultat")
                
                        st.dataframe(df[display_cols], use_container_width=True)
                
                        
                
                        csv = df.to_csv(index=False).encode('utf-8')
                
                        st.download_button("📥 Ladda ner ALL data (CSV)", csv, "bulk_analysis.csv", "text/csv")
                
                
                
                # History Section (Unified)
                
                st.divider()
                
                st.subheader("📜 Historik (Universal Nexus Memory)")
                
                history = get_assets(asset_type="serp_results")
                
                if history:
                
                    # Flatten for display
                
                    display_history = []
                
                    for h in history:
                
                        display_history.append({
                
                            "Time": h["created_at"],
                
                            "Query": h["content"]["query"],
                
                            "Module": h["module_id"],
                
                            "Tool": h["metadata"].get("tool_type")
                
                        })
                
                    st.dataframe(pd.DataFrame(display_history), use_container_width=True)
                
                else:
                
                    st.text("Ingen historik än.")
                
                
