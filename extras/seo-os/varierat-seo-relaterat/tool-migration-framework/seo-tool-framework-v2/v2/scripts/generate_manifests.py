#!/usr/bin/env python3
"""
Batch Manifest Generator
========================

Automatically generates YAML manifests for all tools based on the
analysis data from tool_signature_scanner.

Usage:
    python generate_manifests.py --analysis COMBINED_ANALYSIS.json --output manifests/

This will:
1. Read the analysis JSON
2. Generate a YAML manifest for each unique tool
3. Skip duplicates (ml_features vs generated)
4. Apply archetype detection based on method names
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional


# Archetype detection rules
ARCHETYPE_RULES = {
    'discoverer': ['gap', 'discovery', 'find', 'opportunity', 'search'],
    'analyzer': ['analyze', 'analysis', 'audit', 'check', 'score', 'metrics', 'clustering'],
    'generator': ['generate', 'create', 'brief', 'content', 'rag', 'translation'],
    'optimizer': ['optimize', 'optimizer', 'improve', 'link', 'internal'],
    'monitor': ['monitor', 'track', 'serp', 'velocity', 'volatility', 'historical'],
}

# Category detection rules
CATEGORY_RULES = {
    'content': ['content', 'brief', 'rag', 'translation', 'freshness', 'decay', 'genome'],
    'keywords': ['keyword', 'clustering', 'intent', 'voice', 'search'],
    'links': ['link', 'anchor', 'equity', 'internal', 'backlink'],
    'technical': ['crawl', 'schema', 'duplicate', 'cannibalization'],
    'competitors': ['competitor', 'gap', 'strategy'],
    'serp': ['serp', 'serp_', 'ranking', 'position'],
    'entities': ['entity', 'ner', 'semantic'],
    'analytics': ['roi', 'metrics', 'ab_testing', 'console'],
    'ml': ['embedding', 'ml', 'graph', 'federated', 'active_learning'],
}

# Icon mapping
ARCHETYPE_ICONS = {
    'discoverer': '🎯',
    'analyzer': '🔍',
    'generator': '✨',
    'optimizer': '⚡',
    'monitor': '📊',
}

ARCHETYPE_COLORS = {
    'discoverer': '#EF4444',
    'analyzer': '#3B82F6',
    'generator': '#10B981',
    'optimizer': '#8B5CF6',
    'monitor': '#F59E0B',
}


def detect_archetype(tool_id: str, methods: List[str]) -> str:
    """Detect archetype based on tool name and methods."""
    tool_lower = tool_id.lower()
    methods_str = ' '.join(methods).lower()
    
    for archetype, keywords in ARCHETYPE_RULES.items():
        for keyword in keywords:
            if keyword in tool_lower or keyword in methods_str:
                return archetype
    
    # Default based on primary method
    if 'analyze' in methods:
        return 'analyzer'
    elif 'generate' in methods:
        return 'generator'
    elif 'optimize' in methods:
        return 'optimizer'
    elif 'monitor' in methods:
        return 'monitor'
    
    return 'analyzer'  # Default


def detect_category(tool_id: str) -> str:
    """Detect category based on tool name."""
    tool_lower = tool_id.lower()
    
    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            if keyword in tool_lower:
                return category
    
    return 'general'


def detect_entry_method(classes: List[Dict]) -> str:
    """Detect the main entry method from class methods."""
    priority = ['analyze', 'generate', 'optimize', 'monitor', 'process', 'execute', 'run']
    
    for cls in classes:
        if cls.get('type') in ['engine', 'other']:  # Main service class
            methods = cls.get('methods', [])
            for method in priority:
                if method in methods:
                    return method
    
    return 'analyze'  # Default


def to_human_name(tool_id: str) -> str:
    """Convert tool_id to human-readable name."""
    # Replace underscores with spaces and title case
    name = tool_id.replace('_', ' ').title()
    
    # Fix common abbreviations
    name = name.replace('Seo', 'SEO')
    name = name.replace('Ml', 'ML')
    name = name.replace('Ner', 'NER')
    name = name.replace('Rag', 'RAG')
    name = name.replace('Serp', 'SERP')
    name = name.replace('Ab ', 'A/B ')
    name = name.replace('Roi', 'ROI')
    
    return name


def generate_manifest(tool: Dict, source: str) -> str:
    """Generate YAML manifest for a tool."""
    tool_id = tool['file'].replace('.py', '')
    
    # Get class info
    classes = tool.get('classes', [])
    methods = []
    service_class = None
    config_class = None
    
    for cls in classes:
        class_type = cls.get('type', 'other')
        class_name = cls.get('name', '')
        
        if class_type == 'engine' or class_type == 'other':
            service_class = class_name
            methods = cls.get('methods', [])
        elif 'config' in class_name.lower():
            config_class = class_name
    
    # Detect attributes
    archetype = detect_archetype(tool_id, methods)
    category = detect_category(tool_id)
    entry_method = detect_entry_method(classes)
    name = to_human_name(tool_id)
    icon = ARCHETYPE_ICONS.get(archetype, '⚙️')
    color = ARCHETYPE_COLORS.get(archetype, '#6B7280')
    
    # Build module path
    module = f"{source}.{tool_id}"
    
    # Generate YAML
    manifest = f"""# Auto-generated manifest for {name}
# Source: {source}/{tool['file']}
# Generated by: generate_manifests.py

tool:
  id: {tool_id}
  name: "{name}"
  description: "AI-powered {name.lower()} for SEO intelligence"
  
  category: {category}
  archetype: {archetype}
  icon: "{icon}"
  color: "{color}"
  
  backend:
    module: "{module}"
    class: "{service_class or tool_id.title().replace('_', '') + 'Service'}"
"""
    
    if config_class:
        manifest += f"    config_class: \"{config_class}\"\n"
    
    manifest += f"    method: \"{entry_method}\"\n"
    
    # Add placeholder inputs (to be customized)
    manifest += """
  # TODO: Customize inputs based on actual Config class
  inputs:
    - name: data
      label: "Input Data"
      type: textarea
      required: true
      placeholder: "Enter input data as JSON"
  
  # TODO: Customize outputs based on actual Result class
  outputs:
    type: json
"""
    
    return manifest


def main():
    parser = argparse.ArgumentParser(description='Generate YAML manifests for tools')
    parser.add_argument('--analysis', '-a', required=True, help='Path to COMBINED_ANALYSIS.json')
    parser.add_argument('--output', '-o', default='manifests', help='Output directory for manifests')
    parser.add_argument('--prefer-source', default='ml_features', help='Preferred source for duplicates')
    
    args = parser.parse_args()
    
    # Load analysis
    analysis_path = Path(args.analysis)
    if not analysis_path.exists():
        print(f"Error: Analysis file not found: {args.analysis}")
        return 1
    
    data = json.loads(analysis_path.read_text())
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Track processed tools to avoid duplicates
    processed = set()
    created = 0
    skipped_duplicates = 0
    
    # Process all tools
    for tool in data.get('all_tools', []):
        tool_id = tool['file'].replace('.py', '')
        source = tool.get('source', 'unknown')
        
        # Skip duplicates (prefer specified source)
        if tool_id in processed:
            skipped_duplicates += 1
            continue
        
        # Skip if from non-preferred source and we'll see preferred later
        if source != args.prefer_source:
            # Check if this tool exists in preferred source
            has_preferred = any(
                t['file'].replace('.py', '') == tool_id and t.get('source') == args.prefer_source
                for t in data.get('all_tools', [])
            )
            if has_preferred:
                continue
        
        processed.add(tool_id)
        
        # Generate manifest
        manifest = generate_manifest(tool, source)
        
        # Write to file
        manifest_path = output_dir / f"{tool_id}.yaml"
        manifest_path.write_text(manifest, encoding='utf-8')
        created += 1
        print(f"Created: {manifest_path}")
    
    print(f"\n✅ Generated {created} manifests")
    print(f"⏭️  Skipped {skipped_duplicates} duplicates")
    print(f"📁 Output directory: {output_dir}")


if __name__ == '__main__':
    main()
