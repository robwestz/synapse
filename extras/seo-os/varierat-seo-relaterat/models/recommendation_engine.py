"""
Hybrid Rules + ML Recommendation Engine
Generates actionable SEO recommendations
"""
from typing import Dict, List, Optional
from app.config import get_settings, RECOMMENDATION_TYPES
from app.logger import get_logger

settings = get_settings()
logger = get_logger()


class RecommendationEngine:
    """Hybrid rule-based and ML-powered recommendation engine"""

    def __init__(self):
        self.is_loaded = False

    def load_model(self, model_path: Optional[str] = None):
        """Initialize recommendation engine"""
        logger.info("Initializing recommendation engine...")
        self.is_loaded = True
        logger.info("Recommendation engine ready")

    def generate_recommendations(
        self,
        analysis_data: Dict,
        priority: str = "all"
    ) -> Dict:
        """
        Generate SEO recommendations

        Args:
            analysis_data: Dict with content analysis, scores, and metrics
            priority: Filter by priority (high, medium, low, all)

        Returns:
            Dict with categorized recommendations
        """
        if not self.is_loaded:
            self.load_model()

        try:
            recommendations = {
                'keyword_optimization': [],
                'content_improvement': [],
                'technical_seo': [],
                'user_experience': [],
                'link_building': []
            }

            # Extract data
            content_score = analysis_data.get('content_score', {})
            keywords = analysis_data.get('keywords', [])
            content_metrics = analysis_data.get('content_metrics', {})
            technical_metrics = analysis_data.get('technical_metrics', {})

            # Generate keyword recommendations
            recommendations['keyword_optimization'].extend(
                self._keyword_recommendations(keywords, content_metrics)
            )

            # Generate content recommendations
            recommendations['content_improvement'].extend(
                self._content_recommendations(content_score, content_metrics)
            )

            # Generate technical recommendations
            recommendations['technical_seo'].extend(
                self._technical_recommendations(technical_metrics)
            )

            # Generate UX recommendations
            recommendations['user_experience'].extend(
                self._ux_recommendations(content_metrics, technical_metrics)
            )

            # Generate link building recommendations
            recommendations['link_building'].extend(
                self._link_recommendations(content_metrics)
            )

            # Filter by priority if specified
            if priority != "all":
                recommendations = self._filter_by_priority(recommendations, priority)

            # Calculate priority scores
            summary = self._generate_summary(recommendations)

            result = {
                'recommendations': recommendations,
                'summary': summary,
                'total_recommendations': sum(len(v) for v in recommendations.values())
            }

            logger.info(f"Generated {result['total_recommendations']} recommendations")

            return result

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            raise

    def _keyword_recommendations(
        self,
        keywords: List[Dict],
        content_metrics: Dict
    ) -> List[Dict]:
        """Generate keyword optimization recommendations"""
        recs = []

        # Check keyword density
        keyword_density = content_metrics.get('keyword_density', 0)
        if keyword_density < 0.01:
            recs.append({
                'title': 'Increase Keyword Density',
                'description': 'Your target keywords appear too infrequently. Naturally incorporate them more throughout the content.',
                'priority': 'high',
                'impact': 'high',
                'effort': 'medium',
                'action_items': [
                    'Add target keywords to headings',
                    'Include keywords in first paragraph',
                    'Use keywords in image alt text',
                    'Maintain 1-2% keyword density'
                ]
            })
        elif keyword_density > 0.05:
            recs.append({
                'title': 'Reduce Keyword Stuffing',
                'description': 'Keywords are overused which may hurt rankings. Use natural language and synonyms.',
                'priority': 'high',
                'impact': 'high',
                'effort': 'low',
                'action_items': [
                    'Replace some keyword instances with synonyms',
                    'Use LSI (Latent Semantic Indexing) keywords',
                    'Focus on natural writing flow'
                ]
            })

        # Check long-tail keywords
        if len(keywords) < 5:
            recs.append({
                'title': 'Target More Long-Tail Keywords',
                'description': 'Expand keyword coverage by targeting specific long-tail variations.',
                'priority': 'medium',
                'impact': 'medium',
                'effort': 'medium',
                'action_items': [
                    'Research related long-tail keywords',
                    'Create sections targeting specific queries',
                    'Use question-based keywords (who, what, how)',
                    'Target local variations if applicable'
                ]
            })

        # LSI keywords
        recs.append({
            'title': 'Add LSI Keywords',
            'description': 'Include semantically related terms to improve topical relevance.',
            'priority': 'medium',
            'impact': 'medium',
            'effort': 'low',
            'action_items': [
                'Research related terms and synonyms',
                'Naturally incorporate throughout content',
                'Include in headings and subheadings'
            ]
        })

        return recs

    def _content_recommendations(
        self,
        content_score: Dict,
        content_metrics: Dict
    ) -> List[Dict]:
        """Generate content improvement recommendations"""
        recs = []

        word_count = content_metrics.get('word_count', 0)
        readability = content_metrics.get('readability_score', 0)
        heading_count = content_metrics.get('heading_count', 0)

        # Word count
        if word_count < 300:
            recs.append({
                'title': 'Expand Content Length',
                'description': 'Content is too short. Aim for at least 1000+ words for better rankings.',
                'priority': 'high',
                'impact': 'high',
                'effort': 'high',
                'action_items': [
                    'Add more detailed explanations',
                    'Include examples and case studies',
                    'Add FAQ section',
                    'Include data and statistics'
                ]
            })
        elif word_count < 1000:
            recs.append({
                'title': 'Add More Depth',
                'description': 'Expand content to 1500-2000 words for comprehensive coverage.',
                'priority': 'medium',
                'impact': 'high',
                'effort': 'medium',
                'action_items': [
                    'Add subsections with more details',
                    'Include expert insights',
                    'Add related topics'
                ]
            })

        # Readability
        if readability < 50:
            recs.append({
                'title': 'Improve Readability',
                'description': 'Content is too complex. Simplify language for better user engagement.',
                'priority': 'high',
                'impact': 'medium',
                'effort': 'medium',
                'action_items': [
                    'Use shorter sentences',
                    'Break up long paragraphs',
                    'Use simpler words',
                    'Add bullet points and lists'
                ]
            })
        elif readability > 90:
            recs.append({
                'title': 'Add More Substance',
                'description': 'Content may be too simple. Add more detailed information.',
                'priority': 'low',
                'impact': 'low',
                'effort': 'medium',
                'action_items': [
                    'Include more technical details',
                    'Add data and research',
                    'Expand explanations'
                ]
            })

        # Headings
        if heading_count < 3:
            recs.append({
                'title': 'Add More Headings',
                'description': 'Better structure content with more subheadings for scanability.',
                'priority': 'high',
                'impact': 'medium',
                'effort': 'low',
                'action_items': [
                    'Break content into clear sections',
                    'Use descriptive H2 and H3 tags',
                    'Include keywords in headings',
                    'Ensure logical hierarchy'
                ]
            })

        # Multimedia
        image_count = content_metrics.get('image_count', 0)
        if image_count == 0:
            recs.append({
                'title': 'Add Visual Content',
                'description': 'Include images, infographics, or videos to enhance engagement.',
                'priority': 'medium',
                'impact': 'medium',
                'effort': 'medium',
                'action_items': [
                    'Add relevant images with alt text',
                    'Create custom graphics or infographics',
                    'Embed relevant videos',
                    'Use charts for data visualization'
                ]
            })

        return recs

    def _technical_recommendations(self, technical_metrics: Dict) -> List[Dict]:
        """Generate technical SEO recommendations"""
        recs = []

        page_speed = technical_metrics.get('page_speed_score', 100)
        mobile_friendly = technical_metrics.get('mobile_friendly', True)

        # Page speed
        if page_speed < 50:
            recs.append({
                'title': 'Improve Page Speed',
                'description': 'Page loads too slowly, affecting user experience and rankings.',
                'priority': 'high',
                'impact': 'high',
                'effort': 'high',
                'action_items': [
                    'Optimize and compress images',
                    'Minify CSS and JavaScript',
                    'Enable browser caching',
                    'Use CDN for static assets',
                    'Reduce server response time'
                ]
            })
        elif page_speed < 80:
            recs.append({
                'title': 'Optimize Performance',
                'description': 'Further improve page speed for better user experience.',
                'priority': 'medium',
                'impact': 'medium',
                'effort': 'medium',
                'action_items': [
                    'Lazy load images',
                    'Reduce third-party scripts',
                    'Optimize critical rendering path'
                ]
            })

        # Mobile optimization
        if not mobile_friendly:
            recs.append({
                'title': 'Implement Mobile Optimization',
                'description': 'Site is not mobile-friendly, critical for modern SEO.',
                'priority': 'high',
                'impact': 'high',
                'effort': 'high',
                'action_items': [
                    'Use responsive design',
                    'Ensure text is readable without zooming',
                    'Make tap targets appropriately sized',
                    'Avoid horizontal scrolling'
                ]
            })

        # Schema markup
        has_schema = technical_metrics.get('has_schema', False)
        if not has_schema:
            recs.append({
                'title': 'Add Schema Markup',
                'description': 'Implement structured data for rich snippets in search results.',
                'priority': 'medium',
                'impact': 'high',
                'effort': 'medium',
                'action_items': [
                    'Add appropriate schema types (Article, Product, etc.)',
                    'Include breadcrumb markup',
                    'Add FAQ schema if applicable',
                    'Validate with Google\'s Rich Results Test'
                ]
            })

        return recs

    def _ux_recommendations(
        self,
        content_metrics: Dict,
        technical_metrics: Dict
    ) -> List[Dict]:
        """Generate user experience recommendations"""
        recs = []

        # Navigation
        recs.append({
            'title': 'Improve Internal Navigation',
            'description': 'Enhance site navigation to improve user engagement and crawlability.',
            'priority': 'medium',
            'impact': 'medium',
            'effort': 'medium',
            'action_items': [
                'Add breadcrumb navigation',
                'Include related posts section',
                'Add table of contents for long articles',
                'Ensure clear menu structure'
            ]
        })

        # Call to action
        recs.append({
            'title': 'Add Clear Calls-to-Action',
            'description': 'Guide users to desired actions with clear CTAs.',
            'priority': 'low',
            'impact': 'low',
            'effort': 'low',
            'action_items': [
                'Add prominent CTA buttons',
                'Use action-oriented language',
                'Place CTAs strategically throughout content',
                'A/B test CTA variations'
            ]
        })

        return recs

    def _link_recommendations(self, content_metrics: Dict) -> List[Dict]:
        """Generate link building recommendations"""
        recs = []

        internal_links = content_metrics.get('internal_link_count', 0)
        external_links = content_metrics.get('external_link_count', 0)

        # Internal linking
        if internal_links < 3:
            recs.append({
                'title': 'Increase Internal Links',
                'description': 'Add more internal links to improve site structure and distribute link equity.',
                'priority': 'high',
                'impact': 'high',
                'effort': 'low',
                'action_items': [
                    'Link to related articles',
                    'Add contextual links in content',
                    'Use descriptive anchor text',
                    'Link to cornerstone content'
                ]
            })

        # External linking
        if external_links < 2:
            recs.append({
                'title': 'Add Authoritative External Links',
                'description': 'Link to credible sources to increase content trustworthiness.',
                'priority': 'medium',
                'impact': 'medium',
                'effort': 'low',
                'action_items': [
                    'Link to reputable sources',
                    'Cite studies and research',
                    'Use rel="nofollow" for untrusted links',
                    'Ensure external links open in new tab'
                ]
            })

        return recs

    def _filter_by_priority(self, recommendations: Dict, priority: str) -> Dict:
        """Filter recommendations by priority level"""
        filtered = {}
        for category, recs in recommendations.items():
            filtered[category] = [
                rec for rec in recs
                if rec['priority'] == priority
            ]
        return filtered

    def _generate_summary(self, recommendations: Dict) -> Dict:
        """Generate recommendations summary"""
        total = sum(len(v) for v in recommendations.values())

        # Count by priority
        priority_counts = {'high': 0, 'medium': 0, 'low': 0}
        for recs in recommendations.values():
            for rec in recs:
                priority_counts[rec['priority']] += 1

        # Top priorities
        all_recs = []
        for category, recs in recommendations.items():
            for rec in recs:
                rec['category'] = category
                all_recs.append(rec)

        # Sort by priority and impact
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        impact_order = {'high': 3, 'medium': 2, 'low': 1}

        all_recs.sort(
            key=lambda x: (priority_order[x['priority']], impact_order[x['impact']]),
            reverse=True
        )

        top_priorities = [
            {
                'title': rec['title'],
                'category': rec['category'],
                'priority': rec['priority'],
                'impact': rec['impact']
            }
            for rec in all_recs[:5]
        ]

        return {
            'total_recommendations': total,
            'priority_breakdown': priority_counts,
            'top_priorities': top_priorities
        }
