"""
SERP Adapter for SEO Tools
Provides a simple interface for SEO tools to fetch and use search data.
"""
import subprocess
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

class SerpAdapter:
    """
    Adapter that bridges the Search CLI with internal SEO tools.
    """
    
    def __init__(self, python_path: Optional[str] = None):
        # Default to the batch file if on Windows, or find python
        self.base_path = Path(__file__).parent
        self.batch_file = self.base_path / "search.bat"
        self.cli_file = self.base_path / "search_cli.py"
        
        # Determine the best way to run the search
        if sys.platform == "win32" and self.batch_file.exists():
            self.run_cmd = [str(self.batch_file)]
        else:
            # Fallback to python + cli script
            self.run_cmd = [python_path or sys.executable, str(self.cli_file)]

    def fetch_serp(self, query: str, count: int = 10, provider: str = "ddg") -> List[Dict[str, Any]]:
        """
        Fetches SERP results for a query.
        Returns a list of dicts: [{'rank': 1, 'title': '...', 'link': '...', 'snippet': '...'}]
        """
        cmd = self.run_cmd + [query, "--count", str(count), "--provider", provider]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding="utf-8")
            data = json.loads(result.stdout)
            return data.get("results", [])
        except Exception as e:
            print(f"SERP Fetch Error: {e}", file=sys.stderr)
            return []

    def get_competitors(self, query: str, count: int = 5) -> List[str]:
        """Convenience method to just get URLs of top competitors."""
        results = self.fetch_serp(query, count=count)
        return [r['link'] for r in results]

# Global instance for easy import
serp = SerpAdapter()
