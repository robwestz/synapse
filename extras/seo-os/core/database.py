"""
Project Nexus - Core Database
Unified storage for all SEO modules.
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).parent.parent / "data" / "nexus.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Projects Table
    c.execute('''CREATE TABLE IF NOT EXISTS projects
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  created_at DATETIME)''')
                  
    # 2. Universal Assets Table (The shared memory)
    c.execute('''CREATE TABLE IF NOT EXISTS assets
                 (id TEXT PRIMARY KEY,
                  project_id INTEGER,
                  module_id TEXT,
                  asset_type TEXT,
                  content JSON,
                  metadata JSON,
                  created_at DATETIME,
                  FOREIGN KEY(project_id) REFERENCES projects(id))''')

    # 3. KNOWLEDGE GRAPH TABLES (New in v2)
    
    # Entities: Unique objects found in analysis
    c.execute('''CREATE TABLE IF NOT EXISTS entities
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE,
                  type TEXT,
                  frequency INTEGER DEFAULT 1,
                  first_seen DATETIME,
                  last_seen DATETIME)''')

    # Intent History: Tracking keyword intent over time
    c.execute('''CREATE TABLE IF NOT EXISTS keyword_intent
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  keyword TEXT,
                  intent TEXT,
                  confidence REAL,
                  timestamp DATETIME)''')

    # Clusters: Saved thematic groups
    c.execute('''CREATE TABLE IF NOT EXISTS clusters
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  keywords JSON,
                  created_at DATETIME)''')

    # 4. EXTERNAL DATA TABLES (New in v3)
    
    # Organic Keywords (Source: Ahrefs/Semrush/GSC)
    c.execute('''CREATE TABLE IF NOT EXISTS external_keywords
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  project_id INTEGER,
                  keyword TEXT,
                  volume INTEGER,
                  difficulty INTEGER,
                  position INTEGER,
                  traffic REAL,
                  url TEXT,
                  parent_topic TEXT,
                  source TEXT, -- 'ahrefs', 'gsc', etc.
                  is_primary_site BOOLEAN, -- True if it's the user's site, False for competitors
                  imported_at DATETIME,
                  FOREIGN KEY(project_id) REFERENCES projects(id))''')

    # Backlinks / Referring Domains
    c.execute('''CREATE TABLE IF NOT EXISTS external_links
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  project_id INTEGER,
                  source_url TEXT,
                  target_url TEXT,
                  dr INTEGER,
                  traffic REAL,
                  imported_at DATETIME,
                  FOREIGN KEY(project_id) REFERENCES projects(id))''')
    
    # Create a default project if none exists
    c.execute("SELECT count(*) FROM projects")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO projects (name, created_at) VALUES (?, ?)", 
                  ("Default Project", datetime.now().isoformat()))
        
    conn.commit()
    conn.close()

def save_asset(asset_id: str, project_id: int, module_id: str, asset_type: str, content: Dict, metadata: Dict = None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO assets 
                 (id, project_id, module_id, asset_type, content, metadata, created_at) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (asset_id, project_id, module_id, asset_type, 
               json.dumps(content), json.dumps(metadata or {}), 
               datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_assets(project_id: int = 1, asset_type: str = None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if asset_type:
        c.execute("SELECT * FROM assets WHERE project_id = ? AND asset_type = ? ORDER BY created_at DESC", 
                  (project_id, asset_type))
    else:
        c.execute("SELECT * FROM assets WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
    
    rows = [dict(r) for r in c.fetchall()]
    for r in rows:
        r['content'] = json.loads(r['content'])
        r['metadata'] = json.loads(r['metadata'])
    conn.close()
    return rows

# --- KNOWLEDGE GRAPH API ---

def save_entity(name: str, entity_type: str = "Concept"):
    """Upsert an entity: Create new or increment frequency."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    
    # Check if exists
    c.execute("SELECT id, frequency FROM entities WHERE name = ?", (name,))
    row = c.fetchone()
    
    if row:
        c.execute("UPDATE entities SET frequency = frequency + 1, last_seen = ? WHERE id = ?", (now, row[0]))
    else:
        c.execute("INSERT INTO entities (name, type, first_seen, last_seen) VALUES (?, ?, ?, ?)", 
                  (name, entity_type, now, now))
    
    conn.commit()
    conn.close()

def log_keyword_intent(keyword: str, intent: str, confidence: float = 1.0):
    """Log an intent classification event."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO keyword_intent (keyword, intent, confidence, timestamp) VALUES (?, ?, ?, ?)",
              (keyword, intent, confidence, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def save_cluster(name: str, keywords: List[str]):
    """Save a topic cluster."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO clusters (name, keywords, created_at) VALUES (?, ?, ?)",
              (name, json.dumps(keywords), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_knowledge_graph_stats():
    """Get overview stats."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    stats = {}
    stats["entities"] = c.execute("SELECT count(*) FROM entities").fetchone()[0]
    stats["intents_logged"] = c.execute("SELECT count(*) FROM keyword_intent").fetchone()[0]
    stats["clusters"] = c.execute("SELECT count(*) FROM clusters").fetchone()[0]
    conn.close()
    return stats

# Init on first run
init_db()
