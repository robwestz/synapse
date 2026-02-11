"""
Data Importer UI
Handles CSV uploads from Ahrefs, Semrush, etc., and saves to Nexus DB.
"""
import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.database import DB_PATH

st.title("📥 Nexus Data Importer")
st.markdown("Ladda upp dina exporter från Ahrefs, Semrush eller GSC för att berika din SEO-hjärna.")

# Tabs
tab_upload, tab_manage = st.tabs(["📤 Ladda upp", "📊 Hantera Data"])

with tab_upload:
    st.subheader("Importera Organiska Sökord")
    
    source = st.selectbox("Källa", ["Ahrefs", "Semrush", "GSC (Custom)"])
    data_type = st.radio("Typ av data", ["Mina egna sökord (Primary)", "Konkurrentens sökord"])
    
    uploaded_file = st.file_uploader("Välj CSV-fil", type="csv")
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("Preview av datan:")
        st.dataframe(df.head())
        
        # Mapping Logic
        st.divider()
        st.subheader("Normalisering")
        st.info("Vi mappar automatiskt kolumnerna till Nexus standard-schema.")
        
        # Simple Ahrefs mapper (heuristic)
        mapping = {}
        cols = df.columns.tolist()
        
        mapping['keyword'] = next((c for c in cols if 'Keyword' in c), None)
        mapping['volume'] = next((c for c in cols if 'Volume' in c), None)
        mapping['difficulty'] = next((c for c in cols if 'Difficulty' in c or 'KD' in c), None)
        mapping['position'] = next((c for c in cols if 'Position' in c), None)
        mapping['traffic'] = next((c for c in cols if 'Traffic' in c), None)
        mapping['url'] = next((c for c in cols if 'URL' in c or 'Url' in c), None)
        mapping['parent_topic'] = next((c for c in cols if 'Parent topic' in c), None)
        
        # Show mapping to user
        st.json(mapping)
        
        if st.button("🚀 Starta Import"):
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                imported_count = 0
                for _, row in df.iterrows():
                    # Extract values based on mapping
                    kw = str(row[mapping['keyword']]) if mapping['keyword'] else ""
                    vol = int(row[mapping['volume']]) if mapping['volume'] and not pd.isna(row[mapping['volume']]) else 0
                    diff = int(row[mapping['difficulty']]) if mapping['difficulty'] and not pd.isna(row[mapping['difficulty']]) else 0
                    pos = int(row[mapping['position']]) if mapping['position'] and not pd.isna(row[mapping['position']]) else 0
                    traf = float(row[mapping['traffic']]) if mapping['traffic'] and not pd.isna(row[mapping['traffic']]) else 0.0
                    url = str(row[mapping['url']]) if mapping['url'] else ""
                    parent = str(row[mapping['parent_topic']]) if mapping['parent_topic'] else "Unknown"
                    
                    cursor.execute('''INSERT INTO external_keywords 
                                     (project_id, keyword, volume, difficulty, position, traffic, url, parent_topic, source, is_primary_site, imported_at)
                                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                  (1, kw, vol, diff, pos, traf, url, parent, source.lower(), (data_type == "Mina egna sökord (Primary)"), datetime.now().isoformat()))
                    imported_count += 1
                
                conn.commit()
                conn.close()
                st.success(f"Klart! {imported_count} sökord har importerats till Nexus.")
                
            except Exception as e:
                st.error(f"Ett fel uppstod vid importen: {e}")

with tab_manage:
    st.subheader("Data-statistik")
    
    conn = sqlite3.connect(DB_PATH)
    stats_df = pd.read_sql_query("""
        SELECT source, is_primary_site, count(*) as count, avg(difficulty) as avg_kd, sum(traffic) as total_traffic 
        FROM external_keywords 
        GROUP BY source, is_primary_site
    """, conn)
    conn.close()
    
    if not stats_df.empty:
        st.dataframe(stats_df)
        if st.button("Rensa all extern data (⚠️ Farligt!)"):
            conn = sqlite3.connect(DB_PATH)
            conn.execute("DELETE FROM external_keywords")
            conn.commit()
            conn.close()
            st.warning("All data raderad.")
            st.rerun()
    else:
        st.info("Ingen data importerad ännu.")
