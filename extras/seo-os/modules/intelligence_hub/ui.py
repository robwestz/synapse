"""
Intelligence Hub UI
Houses advanced SEO diagnostic modes ported from the Intelligence project.
"""
import streamlit as st
import pandas as pd
import sqlite3
import json
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.database import DB_PATH

st.title("🧠 Nexus Intelligence Hub")
st.markdown("Diagnostiska verktyg som fokuserar på kunskap snarare än bara rådata.")

# Select Mode
mode = st.selectbox("Välj Analys-läge", [
    "1.1 Cluster Dominance (Coverage Map)",
    "9.7 KD is Bullshit (Difficulty Exposure)",
    "1.5 Intent Gap Analysis"
])

if mode.startswith("1.1"):
    st.header("⚔️ Cluster Dominance Analyzer")
    st.info("Denna analys jämför din täckning av 'Parent Topics' mot dina konkurrenter.")
    
    conn = sqlite3.connect(DB_PATH)
    # Get all keywords
    df_all = pd.read_sql_query("SELECT keyword, parent_topic, traffic, is_primary_site FROM external_keywords", conn)
    conn.close()
    
    if df_all.empty:
        st.warning("Ingen extern data hittades. Gå till 'Data Importer' och ladda upp Ahrefs-filer först.")
    else:
        # Step 3: Group by parent topic
        topics = df_all.groupby(['parent_topic', 'is_primary_site']).agg(
            kw_count=('keyword', 'count'),
            total_traffic=('traffic', 'sum')
        ).reset_index()
        
        # Pivot for comparison
        pivot_topics = topics.pivot(index='parent_topic', columns='is_primary_site', values=['kw_count', 'total_traffic']).fillna(0)
        
        # Flatten columns
        pivot_topics.columns = ['Count_Competitor', 'Count_Me', 'Traffic_Competitor', 'Traffic_Me']
        
        # Calculate coverage %
        pivot_topics['Total_Count'] = pivot_topics['Count_Competitor'] + pivot_topics['Count_Me']
        pivot_topics['My_Coverage_%'] = (pivot_topics['Count_Me'] / pivot_topics['Total_Count']) * 100
        pivot_topics['Opportunity_Score'] = (pivot_topics['Traffic_Competitor'] - pivot_topics['Traffic_Me']).clip(lower=0)
        
        # Display
        st.subheader("Coverage Map")
        st.dataframe(pivot_topics.sort_values(by='Opportunity_Score', reverse=True))
        
        # Insight
        top_opp = pivot_topics.index[0] if not pivot_topics.empty else "N/A"
        st.success(f"💡 Din största möjlighet finns inom klustret: **{top_opp}**")

elif mode.startswith("9.7"):
    st.header("💩 KD is Bullshit Exposer")
    st.info("Visar fall där sökord med hög svårighetsgrad (KD) faktiskt är lätta att ranka för, och vice versa.")
    
    conn = sqlite3.connect(DB_PATH)
    df_kd = pd.read_sql_query("""
        SELECT keyword, difficulty, position, traffic 
        FROM external_keywords 
        WHERE is_primary_site = 1 AND difficulty > 0
    """, conn)
    conn.close()
    
    if df_kd.empty:
        st.warning("Ingen data med KD-värden hittades.")
    else:
        # Find KD prediction failures
        # Overestimated: KD > 50 but Position < 10
        failures = df_kd[(df_kd['difficulty'] >= 50) & (df_kd['position'] <= 10)]
        
        st.subheader("Överskattad svårighet (Du rankar trots hög KD)")
        st.write("Dessa sökord bevisar att Ahrefs KD missar din faktiska 'Topical Authority'.")
        st.dataframe(failures.sort_values(by='difficulty', ascending=False))

else:
    st.write("Fler lägen kommer snart...")
