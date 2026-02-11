"""
Data Recipes UI
Visual builder for creating and testing extraction recipes.
"""
import streamlit as st
import json
import uuid
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.database import save_asset, get_assets
from core.search_provider import get_provider

# st.set_page_config is NOT called here because it runs inside main.py context

st.title("🍳 Nexus Data Recipes")
st.markdown("Skapa och hantera återanvändbara sökprofiler.")

# Tabs
tab_create, tab_library = st.tabs(["🏗️ Skapa Recept", "📚 Bibliotek"])

with tab_create:
    st.subheader("Konfigurera Sökprofil")
    
    col1, col2 = st.columns(2)
    
    with col1:
        recipe_name = st.text_input("Namn på profil", placeholder="t.ex. Google.se Organisk Top 10")
        provider = st.selectbox("Datakälla", ["ddg", "serper"], help="DDG är gratis, Serper är Google API")
        
        # Region Selection
        region_options = {
            "wt-wt": "Global / US (google.com)",
            "se-sv": "Sverige (google.se)",
            "no-no": "Norge (google.no)",
            "dk-no": "Danmark (google.dk)",
            "fi-da": "Finland (google.fi)",
            "de-de": "Tyskland (google.de)",
            "uk-en": "Storbritannien (google.co.uk)"
        }
        region_code = st.selectbox("Marknad / Region", options=list(region_options.keys()), format_func=lambda x: region_options[x])
        
        limit = st.number_input("Antal resultat", min_value=1, max_value=100, value=10)

    with col2:
        st.markdown("### 🛡️ Filter & Fält")
        organic_only = st.checkbox("Endast Organiska Resultat (Ta bort annonser)", value=True)
        
        st.markdown("Vilken data vill du ha med?")
        field_options = {
            "rank": "Ranking Position",
            "title": "Meta Title",
            "snippet": "Meta Description / Snippet",
            "link": "Full URL Path",
            "domain": "Endast Domän (ex. aftonbladet.se)",
            "date": "Publiceringsdatum"
        }
        
        selected_fields = []
        for key, label in field_options.items():
            if st.checkbox(label, value=True):
                selected_fields.append(key)

    st.divider()
    
    # Test Lab
    st.subheader("🧪 Testkör Profil")
    test_query = st.text_input("Test-sökord (för validering)", placeholder="skriv sökord...")
    
    if st.button("Kör Test"):
        if not test_query:
            st.warning("Du måste ange ett sökord för att testa.")
        else:
            with st.spinner(f"Hämtar data från {provider} ({region_code})..."):
                try:
                    # 1. Fetch
                    prov = get_provider(provider)
                    response = prov.search(test_query, num_results=limit, region=region_code)
                    results = [r.to_dict() for r in response.results]
                    
                    # 2. Filter (Organic)
                    # Note: Ideally this logic lives in a shared 'processor', but we simulate it here to show WYSIWYG
                    if organic_only:
                        # Simple heuristic: remove ad tracking links if any slip through
                        results = [r for r in results if "googleadservices" not in r['link']]
                        
                    # 3. Project Fields
                    processed_results = []
                    for r in results:
                        row = {}
                        if "rank" in selected_fields: row["rank"] = r.get("rank")
                        if "title" in selected_fields: row["title"] = r.get("title")
                        if "snippet" in selected_fields: row["snippet"] = r.get("snippet")
                        if "link" in selected_fields: row["link"] = r.get("link")
                        if "date" in selected_fields: row["date"] = r.get("extra_data", {}).get("date", "")
                        
                        if "domain" in selected_fields:
                            try: row["domain"] = r.get("link").split("/")[2]
                            except: row["domain"] = ""
                            
                        processed_results.append(row)
                    
                    st.success(f"Hämtade {len(processed_results)} resultat!")
                    st.dataframe(processed_results)
                    
                    # Save state for saving
                    st.session_state['ready_to_save'] = {
                        "provider": provider,
                        "region": region_code,
                        "limit": limit,
                        "filters": {"organic_only": organic_only},
                        "fields": selected_fields
                    }
                    
                except Exception as e:
                    st.error(f"Fel vid hämtning: {e}")

    # Save
    if st.button("💾 Spara Preset"):
        if not recipe_name:
            st.error("Namnge din preset först.")
        elif 'ready_to_save' not in st.session_state:
            st.error("Kör en testkörning först.")
        else:
            recipe_data = {
                "version": "1.0.0",
                "name": recipe_name,
                "config": st.session_state['ready_to_save']
            }
            save_asset(str(uuid.uuid4()), 1, "data_recipes", "recipe", recipe_data)
            st.success(f"Preset '{recipe_name}' sparad!")

with tab_library:
    st.subheader("Sparade Presets")
    recipes = get_assets(asset_type="recipe")
    if recipes:
        for r in recipes:
            data = r['content']
            with st.expander(f"📜 {data['name']}"):
                st.json(data['config'])
                if st.button("Radera (TODO)", key=r['id']):
                    st.info("Radera funktion kommer snart.")
    else:
        st.info("Inga presets sparade.")