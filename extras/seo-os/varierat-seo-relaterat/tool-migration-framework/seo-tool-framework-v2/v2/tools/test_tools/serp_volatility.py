"""
SERP Volatility Monitor Service
===============================

Monitors SERP volatility and detects algorithm updates.
This is a functional mock implementation for testing the framework.

Archetype: monitor
Category: serp
"""

import asyncio
import random
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


@dataclass
class SerpVolatilityServiceConfig:
    """Configuration for the SERP Volatility Service."""
    lookback_days: int = 30
    volatility_threshold: float = 5.0  # Standard deviations
    categories: List[str] = field(default_factory=lambda: ["all"])
    alert_on_spike: bool = True
    
    def __init__(
        self,
        lookback_days: int = 30,
        volatility_threshold: float = 5.0,
        categories: List[str] = None,
        alert_on_spike: bool = True,
    ):
        self.lookback_days = lookback_days
        self.volatility_threshold = volatility_threshold
        self.categories = categories or ["all"]
        self.alert_on_spike = alert_on_spike


@dataclass
class VolatilityDataPoint:
    """A single day's volatility measurement."""
    date: str
    volatility_score: float
    category: str
    affected_keywords_pct: float
    avg_position_change: float
    is_spike: bool


@dataclass
class AlgorithmUpdateSignal:
    """Signal indicating potential algorithm update."""
    date: str
    confidence: float  # 0-100
    affected_categories: List[str]
    severity: str  # low, medium, high
    description: str


@dataclass
class SerpVolatilityServiceResult:
    """Result from SERP volatility monitoring."""
    success: bool
    current_volatility: float
    trend: str  # stable, increasing, decreasing
    volatility_history: List[VolatilityDataPoint]
    detected_updates: List[AlgorithmUpdateSignal]
    category_breakdown: Dict[str, float]
    alert_triggered: bool
    processing_time_ms: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "current_volatility": self.current_volatility,
            "trend": self.trend,
            "volatility_history": [asdict(v) for v in self.volatility_history],
            "detected_updates": [asdict(u) for u in self.detected_updates],
            "category_breakdown": self.category_breakdown,
            "alert_triggered": self.alert_triggered,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp,
        }


class SerpVolatilityService:
    """
    Service for monitoring SERP volatility and detecting algorithm updates.
    
    This is a mock implementation that generates realistic volatility data
    for testing the framework. In production, this would track actual SERPs.
    """
    
    CATEGORIES = [
        "technology", "health", "finance", "ecommerce", 
        "local", "news", "entertainment", "education"
    ]
    
    def __init__(self, config: Optional[SerpVolatilityServiceConfig] = None):
        self.config = config or SerpVolatilityServiceConfig()
        self._initialized = False
        self._metrics = {
            "total_executions": 0,
            "alerts_triggered": 0,
            "updates_detected": 0,
        }
    
    async def initialize(self) -> None:
        """Initialize the service."""
        if self._initialized:
            return
        await asyncio.sleep(0.1)
        self._initialized = True
    
    async def close(self) -> None:
        """Clean up resources."""
        self._initialized = False
    
    async def monitor(self, targets: Dict[str, Any]) -> SerpVolatilityServiceResult:
        """
        Monitor SERP volatility.
        
        Args:
            targets: Dictionary containing:
                - categories: List of categories to monitor (optional)
                - lookback_days: Number of days to analyze (optional)
        
        Returns:
            SerpVolatilityServiceResult with volatility data
        """
        start_time = asyncio.get_event_loop().time()
        
        categories = targets.get("categories", self.config.categories)
        if isinstance(categories, str):
            categories = [c.strip() for c in categories.split(",") if c.strip()]
        
        lookback_days = targets.get("lookback_days", self.config.lookback_days)
        
        # Generate mock volatility data
        history = await self._generate_volatility_history(categories, lookback_days)
        
        # Detect algorithm updates
        updates = self._detect_updates(history)
        
        # Calculate current state
        recent = history[-7:] if len(history) >= 7 else history
        current_volatility = sum(h.volatility_score for h in recent) / len(recent) if recent else 0
        
        # Determine trend
        if len(history) >= 14:
            first_half = sum(h.volatility_score for h in history[:len(history)//2]) / (len(history)//2)
            second_half = sum(h.volatility_score for h in history[len(history)//2:]) / (len(history) - len(history)//2)
            
            if second_half > first_half * 1.2:
                trend = "increasing"
            elif second_half < first_half * 0.8:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        # Category breakdown
        category_breakdown = {}
        for cat in (categories if "all" not in categories else self.CATEGORIES):
            cat_data = [h for h in history if h.category == cat or cat == "all"]
            if cat_data:
                category_breakdown[cat] = round(
                    sum(h.volatility_score for h in cat_data) / len(cat_data), 2
                )
        
        # Check for alert
        alert_triggered = current_volatility > self.config.volatility_threshold
        
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        # Update metrics
        self._metrics["total_executions"] += 1
        if alert_triggered:
            self._metrics["alerts_triggered"] += 1
        self._metrics["updates_detected"] += len(updates)
        
        return SerpVolatilityServiceResult(
            success=True,
            current_volatility=round(current_volatility, 2),
            trend=trend,
            volatility_history=history,
            detected_updates=updates,
            category_breakdown=category_breakdown,
            alert_triggered=alert_triggered,
            processing_time_ms=processing_time,
        )
    
    async def _generate_volatility_history(
        self,
        categories: List[str],
        lookback_days: int,
    ) -> List[VolatilityDataPoint]:
        """Generate mock volatility history."""
        
        await asyncio.sleep(0.05)
        
        history = []
        today = datetime.utcnow().date()
        
        # Seed for reproducible results
        base_seed = int(hashlib.md5(str(today).encode()).hexdigest()[:8], 16)
        
        for day_offset in range(lookback_days, 0, -1):
            date = today - timedelta(days=day_offset)
            date_str = date.isoformat()
            
            for category in (categories if "all" not in categories else ["all"]):
                random.seed(base_seed + day_offset + hash(category))
                
                # Base volatility with some noise
                base_vol = 2.5 + random.gauss(0, 1)
                
                # Add occasional spikes (simulating algorithm updates)
                spike = 0
                if random.random() < 0.05:  # 5% chance of spike
                    spike = random.uniform(3, 8)
                
                volatility = max(0, base_vol + spike)
                is_spike = spike > 2
                
                history.append(VolatilityDataPoint(
                    date=date_str,
                    volatility_score=round(volatility, 2),
                    category=category,
                    affected_keywords_pct=round(volatility * 3 + random.uniform(0, 10), 1),
                    avg_position_change=round(volatility * 0.8 + random.uniform(0, 2), 1),
                    is_spike=is_spike,
                ))
        
        random.seed()
        return history
    
    def _detect_updates(
        self, 
        history: List[VolatilityDataPoint]
    ) -> List[AlgorithmUpdateSignal]:
        """Detect potential algorithm updates from volatility spikes."""
        
        updates = []
        spike_dates = {}
        
        for point in history:
            if point.is_spike:
                if point.date not in spike_dates:
                    spike_dates[point.date] = {
                        "categories": [],
                        "max_volatility": 0,
                    }
                spike_dates[point.date]["categories"].append(point.category)
                spike_dates[point.date]["max_volatility"] = max(
                    spike_dates[point.date]["max_volatility"],
                    point.volatility_score
                )
        
        for date, data in spike_dates.items():
            confidence = min(data["max_volatility"] * 10, 95)
            
            if data["max_volatility"] > 8:
                severity = "high"
            elif data["max_volatility"] > 5:
                severity = "medium"
            else:
                severity = "low"
            
            updates.append(AlgorithmUpdateSignal(
                date=date,
                confidence=round(confidence, 1),
                affected_categories=data["categories"],
                severity=severity,
                description=f"Potential algorithm update detected affecting {', '.join(data['categories'])}",
            ))
        
        return sorted(updates, key=lambda u: u.date, reverse=True)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return {
            **self._metrics,
            "config": vars(self.config),
            "initialized": self._initialized,
        }
    
    async def batch_process(
        self, 
        items: List[Dict[str, Any]]
    ) -> List[SerpVolatilityServiceResult]:
        """Process multiple monitoring requests."""
        results = []
        for item in items:
            result = await self.monitor(item)
            results.append(result)
        return results
