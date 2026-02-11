"""
Explainable AI features for understanding extraction decisions.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
import numpy as np
from dataclasses import dataclass
import shap
import lime.lime_text
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path


@dataclass
class ExplanationComponent:
    """Component of an explanation."""
    component_type: str  # 'feature', 'rule', 'example', 'graph'
    description: str
    importance: float
    evidence: List[Dict[str, Any]]
    visualization: Optional[Dict[str, Any]] = None


@dataclass
class KeywordExplanation:
    """Complete explanation for a keyword extraction."""
    keyword: str
    score: float
    explanation_components: List[ExplanationComponent]
    confidence: float
    alternative_keywords: List[Tuple[str, float]]
    decision_path: List[str]


class ExplainableExtractor:
    """Explainable AI wrapper for SIE-X engine."""

    def __init__(self, engine: 'SemanticIntelligenceEngine'):
        self.engine = engine
        self.lime_explainer = None
        self.shap_explainer = None
        self._initialize_explainers()

    def _initialize_explainers(self):
        """Initialize explanation frameworks."""
        # LIME text explainer
        self.lime_explainer = lime.lime_text.LimeTextExplainer(
            class_names=['not_keyword', 'keyword'],
            feature_selection='auto',
            split_expression=r'\W+'
        )

    async def explain_extraction(
            self,
            text: str,
            keyword: str,
            detailed: bool = True
    ) -> KeywordExplanation:
        """Explain why a specific keyword was extracted."""
        # Get full extraction results
        all_keywords = await self.engine.extract_async(text, top_k=50)

        # Find the target keyword
        target_kw = None
        for kw in all_keywords:
            if kw.text == keyword:
                target_kw = kw
                break

        if not target_kw:
            raise ValueError(f"Keyword '{keyword}' not found in extraction results")

        # Generate explanation components
        components = []

        # 1. Linguistic features
        linguistic_comp = await self._explain_linguistic_features(text, target_kw)
        components.append(linguistic_comp)

        # 2. Semantic importance
        semantic_comp = await self._explain_semantic_importance(text, target_kw, all_keywords)
        components.append(semantic_comp)

        # 3. Graph centrality
        graph_comp = await self._explain_graph_centrality(target_kw, all_keywords)
        components.append(graph_comp)

        # 4. Context analysis
        context_comp = await self._explain_context(text, target_kw)
        components.append(context_comp)

        if detailed:
            # 5. LIME explanation
            lime_comp = await self._generate_lime_explanation(text, target_kw)
            components.append(lime_comp)

            # 6. Counterfactual analysis
            counter_comp = await self._explain_counterfactuals(text, target_kw)
            components.append(counter_comp)

        # Generate decision path
        decision_path = self._trace_decision_path(target_kw, components)

        # Find alternatives
        alternatives = [
            (kw.text, kw.score)
            for kw in all_keywords
            if kw != target_kw and self._is_similar(kw, target_kw)
        ][:5]

        return KeywordExplanation(
            keyword=keyword,
            score=target_kw.score,
            explanation_components=components,
            confidence=target_kw.confidence,
            alternative_keywords=alternatives,
            decision_path=decision_path
        )

    async def _explain_linguistic_features(
            self,
            text: str,
            keyword: 'Keyword'
    ) -> ExplanationComponent:
        """Explain linguistic features contributing to extraction."""
        features = []
        importance = 0.0

        # Named entity recognition
        if keyword.type in ['ORG', 'PER', 'LOC']:
            features.append({
                'feature': 'Named Entity',
                'value': keyword.type,
                'contribution': 0.3
            })
            importance += 0.3

        # Part of speech
        doc = self.engine.nlp(keyword.text)
        pos_tags = [token.pos_ for token in doc]

        if 'PROPN' in pos_tags:
            features.append({
                'feature': 'Proper Noun',
                'value': True,
                'contribution': 0.2
            })
            importance += 0.2

        # Term frequency
        term_freq = keyword.count / len(text.split())
        features.append({
            'feature': 'Term Frequency',
            'value': f"{term_freq:.3f}",
            'contribution': term_freq * 0.5
        })
        importance += term_freq * 0.5

        return ExplanationComponent(
            component_type='linguistic',
            description='Linguistic features analysis',
            importance=min(importance, 1.0),
            evidence=features
        )

    async def _explain_semantic_importance(
            self,
            text: str,
            keyword: 'Keyword',
            all_keywords: List['Keyword']
    ) -> ExplanationComponent:
        """Explain semantic importance of keyword."""
        # Get embedding
        if keyword.embeddings is None:
            keyword.embeddings = self.engine._generate_embeddings_batch([keyword.text])[0]

        # Calculate semantic coherence with document
        doc_embedding = self.engine._generate_embeddings_batch([text])[0]
        coherence = float(np.dot(keyword.embeddings, doc_embedding) / (
                np.linalg.norm(keyword.embeddings) * np.linalg.norm(doc_embedding)
        ))

        # Find semantic neighbors
        neighbors = []
        for kw in all_keywords[:20]:
            if kw != keyword and kw.embeddings is not None:
                similarity = float(np.dot(keyword.embeddings, kw.embeddings) / (
                        np.linalg.norm(keyword.embeddings) * np.linalg.norm(kw.embeddings)
                ))
                if similarity > 0.5:
                    neighbors.append({
                        'keyword': kw.text,
                        'similarity': similarity
                    })

        evidence = [
            {
                'feature': 'Document Coherence',
                'value': f"{coherence:.3f}",
                'contribution': coherence * 0.4
            },
            {
                'feature': 'Semantic Neighbors',
                'value': len(neighbors),
                'contribution': min(len(neighbors) * 0.1, 0.3)
            },
            {
                'feature': 'Semantic Cluster',
                'value': keyword.semantic_cluster,
                'contribution': 0.2 if keyword.semantic_cluster is not None else 0
            }
        ]

        # Add top neighbors as evidence
        for neighbor in sorted(neighbors, key=lambda x: x['similarity'], reverse=True)[:3]:
            evidence.append({
                'feature': f"Similar to '{neighbor['keyword']}'",
                'value': f"{neighbor['similarity']:.3f}",
                'contribution': neighbor['similarity'] * 0.1
            })

        importance = sum(e['contribution'] for e in evidence)

        return ExplanationComponent(
            component_type='semantic',
            description='Semantic importance analysis',
            importance=min(importance, 1.0),
            evidence=evidence
        )

    async def _explain_graph_centrality(
            self,
            keyword: 'Keyword',
            all_keywords: List['Keyword']
    ) -> ExplanationComponent:
        """Explain graph-based importance."""
        # Build semantic graph
        import networkx as nx

        graph = nx.Graph()
        keyword_dict = {kw.text: kw for kw in all_keywords[:30]}

        # Add nodes
        for kw in all_keywords[:30]:
            graph.add_node(kw.text, keyword=kw)

        # Add edges based on semantic similarity
        for i, kw1 in enumerate(all_keywords[:30]):
            for kw2 in all_keywords[i + 1:30]:
                if kw1.embeddings is not None and kw2.embeddings is not None:
                    similarity = float(np.dot(kw1.embeddings, kw2.embeddings) / (
                            np.linalg.norm(kw1.embeddings) * np.linalg.norm(kw2.embeddings)
                    ))
                    if similarity > 0.3:
                        graph.add_edge(kw1.text, kw2.text, weight=similarity)

        # Calculate centrality metrics
        centrality_metrics = {}

        if keyword.text in graph:
            centrality_metrics['degree'] = nx.degree_centrality(graph).get(keyword.text, 0)
            centrality_metrics['betweenness'] = nx.betweenness_centrality(graph).get(keyword.text, 0)
            centrality_metrics['closeness'] = nx.closeness_centrality(graph).get(keyword.text, 0)

            try:
                centrality_metrics['pagerank'] = nx.pagerank(graph).get(keyword.text, 0)
            except:
                centrality_metrics['pagerank'] = 0

        evidence = [
            {
                'feature': metric.capitalize() + ' Centrality',
                'value': f"{value:.3f}",
                'contribution': value * 0.25
            }
            for metric, value in centrality_metrics.items()
        ]

        # Add graph visualization
        visualization = self._create_graph_visualization(graph, keyword.text)

        importance = sum(e['contribution'] for e in evidence)

        return ExplanationComponent(
            component_type='graph',
            description='Graph-based importance analysis',
            importance=min(importance, 1.0),
            evidence=evidence,
            visualization=visualization
        )

    async def _explain_context(
            self,
            text: str,
            keyword: 'Keyword'
    ) -> ExplanationComponent:
        """Explain contextual importance."""
        evidence = []

        # Find context windows
        sentences = text.split('.')
        keyword_sentences = [
            sent for sent in sentences
            if keyword.text.lower() in sent.lower()
        ]

        # Analyze position
        first_occurrence = text.lower().find(keyword.text.lower())
        position_ratio = first_occurrence / len(text) if first_occurrence >= 0 else 0.5

        evidence.append({
            'feature': 'Document Position',
            'value': 'Beginning' if position_ratio < 0.3 else 'Middle' if position_ratio < 0.7 else 'End',
            'contribution': 0.2 if position_ratio < 0.3 else 0.1
        })

        # Analyze co-occurring terms
        cooccurring = set()
        for sent in keyword_sentences:
            words = sent.split()
            for word in words:
                if word != keyword.text and len(word) > 3:
                    cooccurring.add(word.lower())

        evidence.append({
            'feature': 'Co-occurring Terms',
            'value': len(cooccurring),
            'contribution': min(len(cooccurring) * 0.02, 0.3)
        })

        # Analyze syntactic role
        for sent in keyword_sentences[:1]:  # Just first occurrence
            doc = self.engine.nlp(sent)
            for token in doc:
                if token.text == keyword.text:
                    evidence.append({
                        'feature': 'Syntactic Role',
                        'value': token.dep_,
                        'contribution': 0.3 if token.dep_ in ['nsubj', 'ROOT'] else 0.1
                    })
                    break

        importance = sum(e['contribution'] for e in evidence)

        return ExplanationComponent(
            component_type='context',
            description='Contextual analysis',
            importance=min(importance, 1.0),
            evidence=evidence
        )

    async def _generate_lime_explanation(
            self,
            text: str,
            keyword: 'Keyword'
    ) -> ExplanationComponent:
        """Generate LIME explanation."""

        # Create binary classifier for keyword relevance
        def keyword_predictor(texts):
            predictions = []
            for t in texts:
                # Simple predictor based on extraction
                keywords = self.engine.extract(t, top_k=10)
                keyword_texts = [kw.text.lower() for kw in keywords]

                if keyword.text.lower() in keyword_texts:
                    predictions.append([0.2, 0.8])  # High probability of being keyword
                else:
                    predictions.append([0.8, 0.2])  # Low probability

            return np.array(predictions)

        # Generate explanation
        exp = self.lime_explainer.explain_instance(
            text,
            keyword_predictor,
            num_features=10,
            num_samples=100
        )

        # Extract feature importance
        features = exp.as_list()

        evidence = [
            {
                'feature': f"Word: '{feature}'",
                'value': f"{weight:.3f}",
                'contribution': abs(weight) * 0.1
            }
            for feature, weight in features[:5]
        ]

        importance = sum(e['contribution'] for e in evidence)

        return ExplanationComponent(
            component_type='lime',
            description='LIME feature importance',
            importance=min(importance, 1.0),
            evidence=evidence
        )

    async def _explain_counterfactuals(
            self,
            text: str,
            keyword: 'Keyword'
    ) -> ExplanationComponent:
        """Explain using counterfactual analysis."""
        evidence = []

        # Test 1: Remove the keyword
        text_without = text.replace(keyword.text, "[REMOVED]")
        keywords_without = await self.engine.extract_async(text_without, top_k=10)

        # Check impact on other keywords
        original_keywords = await self.engine.extract_async(text, top_k=10)

        affected_keywords = []
        for orig_kw in original_keywords:
            if orig_kw.text != keyword.text:
                # Check if score changed significantly
                new_kw = next((kw for kw in keywords_without if kw.text == orig_kw.text), None)
                if new_kw:
                    score_change = (new_kw.score - orig_kw.score) / orig_kw.score
                    if abs(score_change) > 0.1:
                        affected_keywords.append({
                            'keyword': orig_kw.text,
                            'change': score_change
                        })

        evidence.append({
            'feature': 'Keywords Affected by Removal',
            'value': len(affected_keywords),
            'contribution': min(len(affected_keywords) * 0.15, 0.5)
        })

        # Test 2: Change context
        alternative_contexts = [
            text.replace(keyword.text, f"the {keyword.text}"),
            text.replace(keyword.text, f"{keyword.text} system"),
            text.replace(keyword.text, f"important {keyword.text}")
        ]

        score_changes = []
        for alt_text in alternative_contexts:
            alt_keywords = await self.engine.extract_async(alt_text, top_k=10)
            alt_kw = next((kw for kw in alt_keywords if keyword.text in kw.text), None)

            if alt_kw:
                score_changes.append(alt_kw.score - keyword.score)

        avg_change = np.mean(score_changes) if score_changes else 0

        evidence.append({
            'feature': 'Sensitivity to Context',
            'value': f"{abs(avg_change):.3f}",
            'contribution': abs(avg_change)
        })

        importance = sum(e['contribution'] for e in evidence)

        return ExplanationComponent(
            component_type='counterfactual',
            description='Counterfactual analysis',
            importance=min(importance, 1.0),
            evidence=evidence
        )

    def _trace_decision_path(
            self,
            keyword: 'Keyword',
            components: List[ExplanationComponent]
    ) -> List[str]:
        """Trace the decision path for keyword extraction."""
        path = []

        # Sort components by importance
        sorted_components = sorted(components, key=lambda c: c.importance, reverse=True)

        for comp in sorted_components:
            if comp.importance > 0.2:
                if comp.component_type == 'linguistic':
                    path.append(f"Identified as {keyword.type} (linguistic analysis)")
                elif comp.component_type == 'semantic':
                    path.append(f"High semantic relevance (score: {comp.importance:.2f})")
                elif comp.component_type == 'graph':
                    path.append(f"Central in semantic network (graph analysis)")
                elif comp.component_type == 'context':
                    path.append(f"Important contextual position")

        path.append(f"Final score calculation: {keyword.score:.3f}")
        path.append(
            f"Ranked #{[kw.text for kw in self.engine.extract(keyword.text)].index(keyword.text) + 1} among candidates")

        return path

    def _is_similar(self, kw1: 'Keyword', kw2: 'Keyword') -> bool:
        """Check if two keywords are similar."""
        if kw1.embeddings is None or kw2.embeddings is None:
            return False

        similarity = float(np.dot(kw1.embeddings, kw2.embeddings) / (
                np.linalg.norm(kw1.embeddings) * np.linalg.norm(kw2.embeddings)
        ))

        return similarity > 0.6

    def _create_graph_visualization(self, graph, highlight_node: str) -> Dict[str, Any]:
        """Create graph visualization data."""
        import networkx as nx

        # Get positions using spring layout
        pos = nx.spring_layout(graph, seed=42)

        # Create edge trace
        edge_trace = []
        for edge in graph.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace.append({
                'x': [x0, x1, None],
                'y': [y0, y1, None],
                'weight': edge[2].get('weight', 0.5)
            })

        # Create node trace
        node_trace = {
            'x': [],
            'y': [],
            'text': [],
            'color': []
        }

        for node in graph.nodes():
            x, y = pos[node]
            node_trace['x'].append(x)
            node_trace['y'].append(y)
            node_trace['text'].append(node)
            node_trace['color'].append('red' if node == highlight_node else 'blue')

        return {
            'type': 'network_graph',
            'edges': edge_trace,
            'nodes': node_trace,
            'highlighted': highlight_node
        }


class ExplanationVisualizer:
    """Visualize explanations using Plotly."""

    @staticmethod
    def create_importance_chart(explanation: KeywordExplanation) -> go.Figure:
        """Create importance chart for explanation components."""
        components = explanation.explanation_components

        fig = go.Figure()

        # Add bars for each component
        fig.add_trace(go.Bar(
            x=[comp.importance for comp in components],
            y=[comp.description for comp in components],
            orientation='h',
            marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'][:len(components)],
            text=[f"{comp.importance:.2f}" for comp in components],
            textposition='auto'
        ))

        fig.update_layout(
            title=f"Explanation Components for '{explanation.keyword}'",
            xaxis_title="Importance Score",
            yaxis_title="Component",
            showlegend=False,
            height=400,
            margin=dict(l=150)
        )

        return fig

    @staticmethod
    def create_evidence_sunburst(explanation: KeywordExplanation) -> go.Figure:
        """Create sunburst chart of evidence."""
        # Prepare hierarchical data
        labels = [explanation.keyword]
        parents = ['']
        values = [explanation.score]

        for comp in explanation.explanation_components:
            labels.append(comp.description)
            parents.append(explanation.keyword)
            values.append(comp.importance)

            for evidence in comp.evidence[:3]:  # Top 3 evidence items
                labels.append(evidence['feature'])
                parents.append(comp.description)
                values.append(evidence['contribution'])

        fig = go.Figure(go.Sunburst(
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total"
        ))

        fig.update_layout(
            title=f"Evidence Hierarchy for '{explanation.keyword}'",
            height=600
        )

        return fig

    @staticmethod
    def create_decision_path_diagram(explanation: KeywordExplanation) -> go.Figure:
        """Create decision path diagram."""
        fig = go.Figure()

        # Create nodes for each decision step
        y_positions = list(range(len(explanation.decision_path)))

        fig.add_trace(go.Scatter(
            x=[0.5] * len(explanation.decision_path),
            y=y_positions,
            mode='markers+text',
            marker=dict(size=20, color='lightblue'),
            text=explanation.decision_path,
            textposition="middle right",
            textfont=dict(size=10)
        ))

        # Add arrows between steps
        for i in range(len(y_positions) - 1):
            fig.add_annotation(
                x=0.5,
                y=y_positions[i],
                xref="x",
                yref="y",
                axref="x",
                ayref="y",
                ax=0.5,
                ay=y_positions[i + 1],
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="gray"
            )

        fig.update_layout(
            title=f"Decision Path for '{explanation.keyword}'",
            showlegend=False,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=400
        )

        return fig

    @staticmethod
    def create_explanation_report(
            explanation: KeywordExplanation,
            output_path: Path
    ):
        """Create comprehensive HTML report."""
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Component Importance',
                'Evidence Distribution',
                'Alternative Keywords',
                'Decision Path'
            ),
            specs=[
                [{'type': 'bar'}, {'type': 'pie'}],
                [{'type': 'scatter'}, {'type': 'table'}]
            ]
        )

        # Component importance
        components = explanation.explanation_components
        fig.add_trace(
            go.Bar(
                x=[comp.importance for comp in components],
                y=[comp.description for comp in components],
                orientation='h',
                showlegend=False
            ),
            row=1, col=1
        )

        # Evidence distribution
        evidence_counts = {}
        for comp in components:
            for evidence in comp.evidence:
                feature_type = evidence['feature'].split(':')[0]
                evidence_counts[feature_type] = evidence_counts.get(feature_type, 0) + 1

        fig.add_trace(
            go.Pie(
                labels=list(evidence_counts.keys()),
                values=list(evidence_counts.values()),
                showlegend=True
            ),
            row=1, col=2
        )

        # Alternative keywords
        if explanation.alternative_keywords:
            alts = explanation.alternative_keywords
            fig.add_trace(
                go.Scatter(
                    x=[score for _, score in alts],
                    y=[kw for kw, _ in alts],
                    mode='markers+text',
                    text=[f"{score:.3f}" for _, score in alts],
                    textposition="middle right",
                    showlegend=False
                ),
                row=2, col=1
            )

        # Decision path table
        fig.add_trace(
            go.Table(
                header=dict(values=['Step', 'Decision']),
                cells=dict(values=[
                    list(range(1, len(explanation.decision_path) + 1)),
                    explanation.decision_path
                ])
            ),
            row=2, col=2
        )

        fig.update_layout(height=800, title_text=f"Explanation Report: '{explanation.keyword}'")

        # Save as HTML
        html_content = f"""
        <html>
        <head>
            <title>SIE-X Explanation: {explanation.keyword}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric {{ background-color: #f0f0f0; padding: 10px; margin: 10px 0; }}
                .evidence {{ margin-left: 20px; }}
            </style>
        </head>
        <body>
            <h1>Keyword Extraction Explanation</h1>
            <div class="metric">
                <strong>Keyword:</strong> {explanation.keyword}<br>
                <strong>Score:</strong> {explanation.score:.4f}<br>
                <strong>Confidence:</strong> {explanation.confidence:.4f}
            </div>

            <h2>Detailed Evidence</h2>
        """

        for comp in components:
            html_content += f"""
            <div class="metric">
                <strong>{comp.description}</strong> (Importance: {comp.importance:.3f})
                <div class="evidence">
            """
            for evidence in comp.evidence:
                html_content += f"""
                    <p>• {evidence['feature']}: {evidence['value']} 
                    (Contribution: {evidence['contribution']:.3f})</p>
                """
            html_content += "</div></div>"

        html_content += f"""
            <h2>Visualization</h2>
            {fig.to_html(include_plotlyjs='cdn')}
        </body>
        </html>
        """

        output_path.write_text(html_content)

        return output_path