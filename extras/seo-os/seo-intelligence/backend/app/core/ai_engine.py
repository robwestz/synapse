"""
AI Engine for intelligence extraction
Orchestrates Claude API calls for all 50+ modes
"""

import os
from typing import Dict, List, Optional, Any
from anthropic import AsyncAnthropic
import json
from datetime import datetime


class AIEngine:
    """
    Centralized AI orchestration for intelligence extraction
    """

    def __init__(self):
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model_complex = os.getenv("AI_MODEL_COMPLEX", "claude-3-opus-20240229")
        self.model_fast = os.getenv("AI_MODEL_FAST", "claude-3-sonnet-20240229")
        self.max_tokens = int(os.getenv("AI_MAX_TOKENS", "4096"))
        self.temperature = float(os.getenv("AI_TEMPERATURE", "0.7"))

    async def generate_insight(
        self,
        prompt: str,
        mode: str,
        context: Optional[Dict] = None,
        use_complex_model: bool = False
    ) -> Dict[str, Any]:
        """
        Generate AI-powered insight for a specific intelligence mode

        Args:
            prompt: The analysis prompt
            mode: Intelligence mode name (e.g., "cluster_dominance")
            context: Additional context data
            use_complex_model: Whether to use Opus (complex) vs Sonnet (fast)

        Returns:
            Dict with insight, reasoning, confidence, etc.
        """

        model = self.model_complex if use_complex_model else self.model_fast

        # Build system prompt
        system_prompt = self._get_system_prompt(mode)

        # Add context if provided
        if context:
            prompt = f"{prompt}\n\nContext:\n{json.dumps(context, indent=2)}"

        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            insight_text = response.content[0].text

            # Parse response
            result = {
                "insight": insight_text,
                "mode": mode,
                "model_used": model,
                "timestamp": datetime.utcnow().isoformat(),
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "cost_usd": self._calculate_cost(response.usage, model),
            }

            # Try to extract structured data if present
            try:
                # Check if response contains JSON
                if "```json" in insight_text:
                    json_start = insight_text.find("```json") + 7
                    json_end = insight_text.find("```", json_start)
                    json_str = insight_text[json_start:json_end].strip()
                    structured_data = json.loads(json_str)
                    result["structured_data"] = structured_data
            except:
                pass

            return result

        except Exception as e:
            return {
                "error": str(e),
                "mode": mode,
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _get_system_prompt(self, mode: str) -> str:
        """
        Get system prompt for specific intelligence mode
        """

        base_prompt = """You are an elite SEO intelligence analyst specializing in competitive intelligence extraction.

Your role is to analyze SEO data and provide STRATEGIC, ACTIONABLE insights that go beyond what traditional SEO tools like Ahrefs provide.

Key principles:
1. Focus on STRATEGY, not just data
2. Identify PATTERNS, not just metrics
3. Provide ACTIONABLE recommendations
4. Explain WHY, not just WHAT
5. Be specific, not generic
6. Use competitive context
7. Prioritize high-impact opportunities

Your insights should make the user say: "Fuck, why doesn't Ahrefs show me this?"
"""

        mode_prompts = {
            "cluster_dominance": """
For cluster dominance analysis:
- Calculate coverage percentages
- Identify ownership patterns
- Spot opportunity gaps (competitor 80%+, user <20%)
- Recommend content strategies
- Estimate traffic potential
            """,

            "longtail_gap": """
For longtail gap analysis:
- Focus on keywords with 5+ words
- Calculate total missing traffic
- Cluster by semantic similarity
- Identify low-competition opportunities
- Recommend specific content angles
            """,

            "backlink_common_linker": """
For common linker discovery:
- Find domains linking to 3+ competitors
- Prioritize by domain authority
- Suggest pitch angles based on content they link to
- Estimate link acquisition difficulty
- Provide outreach strategy
            """,

            "serp_paa_hijack": """
For PAA question hijacking:
- Extract all People Also Ask questions
- Cluster by semantic similarity
- Identify gaps in user's content
- Recommend comprehensive FAQ strategy
- Suggest content format (list, guide, video, etc.)
            """,

            "competitive_moat": """
For competitive moat analysis:
- Calculate moat strength (0-100)
- Break down by factors: brand, backlinks, content, age
- Identify vulnerabilities
- Recommend attack or avoid strategy
- Estimate time/cost to compete
            """,

            "traffic_potential": """
For traffic potential analysis:
- Calculate realistic traffic estimates
- Account for SERP features (reduce CTR)
- Estimate based on current position improvements
- Show ROI calculation
- Prioritize by effort vs reward
            """,
        }

        mode_specific = mode_prompts.get(mode, "")

        return base_prompt + "\n\n" + mode_specific

    def _calculate_cost(self, usage, model: str) -> float:
        """
        Calculate API cost in USD
        """
        # Anthropic pricing (as of Dec 2024)
        pricing = {
            "claude-3-opus-20240229": {
                "input": 0.015 / 1000,   # $15 per 1M input tokens
                "output": 0.075 / 1000,  # $75 per 1M output tokens
            },
            "claude-3-sonnet-20240229": {
                "input": 0.003 / 1000,   # $3 per 1M input tokens
                "output": 0.015 / 1000,  # $15 per 1M output tokens
            },
        }

        rates = pricing.get(model, pricing["claude-3-sonnet-20240229"])

        input_cost = usage.input_tokens * rates["input"]
        output_cost = usage.output_tokens * rates["output"]

        return input_cost + output_cost


class PromptTemplates:
    """
    Prompt templates for each intelligence mode
    """

    @staticmethod
    def cluster_dominance(your_clusters: Dict, competitor_clusters: Dict) -> str:
        return f"""
Analyze this cluster dominance data and provide strategic insights:

YOUR CLUSTERS:
{json.dumps(your_clusters, indent=2)}

COMPETITOR CLUSTERS:
{json.dumps(competitor_clusters, indent=2)}

Provide analysis in this format:

1. TOP 5 OPPORTUNITIES
   - List clusters where competitor dominates (>80%) but you don't (<20%)
   - For each: traffic potential, difficulty, recommended action

2. COMPETITIVE INSIGHTS
   - What patterns emerge in competitor's cluster ownership?
   - What topics do they ignore?
   - What's their content strategy?

3. STRATEGIC RECOMMENDATIONS
   - Which 3 clusters to attack first (prioritized)
   - Specific content recommendations per cluster
   - Timeline estimate

Be brutally honest. If a cluster is too competitive, say so.
        """

    @staticmethod
    def longtail_gap(longtail_gaps: List[Dict]) -> str:
        return f"""
Analyze these longtail keyword gaps:

MISSING LONGTAILS (competitor ranks, you don't):
{json.dumps(longtail_gaps[:50], indent=2)}

Total gaps: {len(longtail_gaps)}

Provide analysis:

1. TOTAL OPPORTUNITY
   - Sum of traffic potential
   - Why longtails matter for this niche

2. PATTERNS
   - What themes emerge? (e.g., "how to", "vs", "best", etc.)
   - What user intent is missed?

3. TOP 10 QUICK WINS
   - Easiest longtails to rank for
   - Specific content recommendations

4. CONTENT STRATEGY
   - Should these be separate articles or consolidated?
   - What's the pillar + cluster approach?

Focus on ACTIONABLE recommendations.
        """

    @staticmethod
    def backlink_common_linkers(common_linkers: List[Dict]) -> str:
        return f"""
Analyze these "warm prospect" domains that link to competitors but not you:

COMMON LINKERS:
{json.dumps(common_linkers, indent=2)}

For each top prospect, provide:

1. WHY THEY'LL LINK TO YOU
   - What content do they link to from competitors?
   - What's their editorial angle?

2. PITCH STRATEGY
   - Specific pitch angle
   - What content to create/promote
   - Best approach (email, Twitter, etc.)

3. DIFFICULTY SCORE (1-10)
   - How hard to get this link?
   - What's required?

Prioritize top 10 by combination of DR and ease of acquisition.
        """

    @staticmethod
    def serp_paa_questions(paa_questions: List[str], keyword_context: str) -> str:
        return f"""
Analyze these People Also Ask questions for keyword: "{keyword_context}"

PAA QUESTIONS:
{json.dumps(paa_questions, indent=2)}

Provide:

1. QUESTION CLUSTERS
   - Group related questions
   - Identify themes

2. GAP ANALYSIS
   - Which questions are NOT answered by current content?
   - What's the content gap?

3. CONTENT RECOMMENDATIONS
   - Should this be one comprehensive FAQ page?
   - Or separate articles per question?
   - Suggested H2/H3 structure

4. QUICK WIN
   - Which ONE question to answer first for fastest impact?

Make it immediately actionable.
        """
