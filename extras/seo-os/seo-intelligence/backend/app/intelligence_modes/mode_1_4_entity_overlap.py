"""
MODE 1.4: Entity Overlap Analysis
Identifies entities mentioned by competitors that you don't mention
"""

from typing import Dict, List, Any, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from collections import Counter
import re

from app.models.uploads import OrganicKeyword, Upload
from app.core.ai_engine import AIEngine


class EntityOverlapAnalyzer:
    """
    Analyzes entity mentions in keywords to find gaps in entity associations

    Entities can be: people, organizations, products, concepts
    Search engines associate domains with entities they frequently mention
    """

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.ai_engine = AIEngine()

    async def execute(self) -> Dict[str, Any]:
        """
        Execute entity overlap analysis
        """

        # Step 1: Get keywords with entities (if available in data)
        your_keywords = await self._get_keywords_with_content(is_primary=True)
        competitor_keywords = await self._get_keywords_with_content(is_primary=False)

        if not your_keywords or not competitor_keywords:
            return {
                "error": "No keyword data found. Upload Organic Keywords report."
            }

        # Step 2: Extract entities from keywords/URLs
        # Note: In real implementation, this would use the 'entities' column if available
        # For now, we extract from keywords themselves as a proxy
        your_entities = self._extract_entities_from_keywords(your_keywords)
        competitor_entities = self._extract_entities_from_keywords(competitor_keywords)

        # Step 3: Find gaps
        entity_gaps = self._find_entity_gaps(your_entities, competitor_entities)

        # Step 4: Calculate entity association strength
        entity_analysis = self._analyze_entity_associations(
            your_entities,
            competitor_entities,
            entity_gaps
        )

        # Step 5: Generate AI insight
        ai_insight = await self._generate_ai_insight(entity_analysis)

        return {
            "mode": "1.4_entity_overlap",
            "status": "completed",
            "summary": {
                "your_unique_entities": len(your_entities['unique']),
                "competitor_unique_entities": len(competitor_entities['unique']),
                "shared_entities": len(your_entities['entities'] & competitor_entities['entities']),
                "entity_gaps": len(entity_gaps),
                "top_missing_entities": entity_gaps[:10],
            },
            "your_entity_profile": {
                "total_entities": len(your_entities['entities']),
                "top_entities": your_entities['top_entities'][:20],
                "entity_frequency": your_entities['frequency'],
            },
            "competitor_entity_profile": {
                "total_entities": len(competitor_entities['entities']),
                "top_entities": competitor_entities['top_entities'][:20],
                "entity_frequency": competitor_entities['frequency'],
            },
            "entity_gaps": entity_gaps,
            "ai_insight": ai_insight,
        }

    async def _get_keywords_with_content(self, is_primary: bool) -> List[Dict]:
        """
        Get keywords and associated data
        """
        query = (
            select(OrganicKeyword, Upload.source_domain)
            .join(Upload, OrganicKeyword.upload_id == Upload.id)
            .where(Upload.user_id == self.user_id)
            .where(Upload.is_primary == is_primary)
            .where(Upload.processing_status == "completed")
            .where(OrganicKeyword.keyword.isnot(None))
        )

        result = await self.session.execute(query)
        rows = result.fetchall()

        keywords = []
        for row in rows:
            kw_obj, domain = row
            keywords.append({
                "keyword": kw_obj.keyword,
                "parent_topic": kw_obj.parent_topic,
                "url": kw_obj.url,
                "volume": kw_obj.volume or 0,
                "domain": domain,
            })

        return keywords

    def _extract_entities_from_keywords(self, keywords: List[Dict]) -> Dict:
        """
        Extract entity-like terms from keywords

        Real implementation would use:
        1. Entities column from Ahrefs (if available)
        2. spaCy NER on keyword text
        3. Brand/product name recognition

        For now, we extract capitalized terms and known entities
        """
        entity_counter = Counter()
        all_entities = set()

        # Common entity patterns
        entity_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # Capitalized words
            r'\b(AI|SEO|CRM|SaaS|API|ML|NLP|UX|UI)\b',  # Acronyms
        ]

        for kw in keywords:
            keyword_text = kw['keyword']
            url_text = kw['url'] or ""

            # Extract from keyword
            for pattern in entity_patterns:
                matches = re.findall(pattern, keyword_text)
                for match in matches:
                    # Filter out common words
                    if match.lower() not in ['how', 'what', 'best', 'top', 'guide', 'tutorial']:
                        entity_counter[match] += 1
                        all_entities.add(match)

            # Extract from URL paths
            if url_text:
                path_parts = url_text.split('/')
                for part in path_parts:
                    # Clean and extract meaningful parts
                    clean_part = re.sub(r'[-_]', ' ', part).title()
                    if len(clean_part) > 3 and clean_part not in ['Https', 'Http', 'Www']:
                        entity_counter[clean_part] += 1
                        all_entities.add(clean_part)

        # Get top entities by frequency
        top_entities = [
            {
                'entity': entity,
                'mention_count': count,
                'frequency': round(count / len(keywords) * 100, 1)
            }
            for entity, count in entity_counter.most_common(100)
        ]

        return {
            'entities': all_entities,
            'unique': all_entities,
            'top_entities': top_entities,
            'frequency': dict(entity_counter),
        }

    def _find_entity_gaps(
        self,
        your_entities: Dict,
        competitor_entities: Dict
    ) -> List[Dict]:
        """
        Find entities competitors mention frequently that you don't
        """
        your_set = your_entities['entities']
        comp_set = competitor_entities['entities']

        # Entities only competitors have
        gaps = comp_set - your_set

        # Calculate importance of each missing entity
        gap_analysis = []
        for entity in gaps:
            comp_frequency = competitor_entities['frequency'].get(entity, 0)

            gap_analysis.append({
                'entity': entity,
                'competitor_mentions': comp_frequency,
                'importance_score': comp_frequency,  # Simple: more mentions = more important
                'recommendation': self._get_entity_recommendation(entity, comp_frequency),
            })

        # Sort by importance
        gap_analysis.sort(key=lambda x: x['importance_score'], reverse=True)

        return gap_analysis[:50]  # Top 50 gaps

    def _get_entity_recommendation(self, entity: str, mentions: int) -> str:
        """
        Generate recommendation based on entity and mention frequency
        """
        if mentions > 50:
            return f"CRITICAL: Create dedicated content about {entity}"
        elif mentions > 20:
            return f"HIGH: Mention {entity} in related content"
        elif mentions > 10:
            return f"MEDIUM: Consider adding {entity} to content strategy"
        else:
            return f"LOW: Optional inclusion of {entity}"

    def _analyze_entity_associations(
        self,
        your_entities: Dict,
        competitor_entities: Dict,
        gaps: List[Dict]
    ) -> Dict:
        """
        Analyze overall entity association strength
        """
        your_set = your_entities['entities']
        comp_set = competitor_entities['entities']

        shared = your_set & comp_set
        only_yours = your_set - comp_set
        only_theirs = comp_set - your_set

        # Calculate association score
        total_possible = len(your_set | comp_set)
        association_coverage = len(shared) / total_possible * 100 if total_possible > 0 else 0

        return {
            'shared_entities': list(shared)[:30],
            'unique_to_you': list(only_yours)[:30],
            'unique_to_competitors': list(only_theirs)[:30],
            'association_coverage_percent': round(association_coverage, 1),
            'entity_gaps_critical': [g for g in gaps if g['importance_score'] > 50],
            'entity_gaps_high': [g for g in gaps if 20 < g['importance_score'] <= 50],
            'entity_gaps_medium': [g for g in gaps if 10 < g['importance_score'] <= 20],
        }

    async def _generate_ai_insight(self, analysis: Dict) -> Dict:
        """
        Generate AI strategic insight on entity associations
        """

        critical_gaps = "\n".join([
            f"- {g['entity']} ({g['competitor_mentions']} competitor mentions)"
            for g in analysis['entity_gaps_critical'][:10]
        ]) if analysis['entity_gaps_critical'] else "None"

        prompt = f"""
Analyze this entity association analysis:

ASSOCIATION COVERAGE: {analysis['association_coverage_percent']:.1f}%

CRITICAL MISSING ENTITIES:
{critical_gaps}

TOP SHARED ENTITIES:
{', '.join(analysis['shared_entities'][:15])}

Provide:

1. ENTITY ASSOCIATION GAP DIAGNOSIS
   - Why are these entities important?
   - What does their absence mean for topical authority?

2. STRATEGIC ENTITY PLAN
   - Which missing entities to incorporate first?
   - How to naturally mention them in content?

3. TOPICAL AUTHORITY IMPACT
   - How do entity associations affect rankings?
   - What's the long-term impact of these gaps?

4. CONTENT RECOMMENDATIONS
   - Specific content pieces to create around missing entities
   - How to build entity-rich content

Be specific about WHY entity associations matter for SEO.
        """

        ai_result = await self.ai_engine.generate_insight(
            prompt=prompt,
            mode="entity_overlap",
            use_complex_model=True
        )

        return ai_result
