"""
Comprehensive data lineage and audit trail system.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json
from enum import Enum
import asyncio
from sqlalchemy import Column, String, DateTime, JSON, Float, Integer, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, relationship
import networkx as nx

Base = declarative_base()


class AuditEventType(Enum):
    """Types of audit events."""
    EXTRACTION_STARTED = "extraction_started"
    EXTRACTION_COMPLETED = "extraction_completed"
    EXTRACTION_FAILED = "extraction_failed"
    MODEL_LOADED = "model_loaded"
    MODEL_UPDATED = "model_updated"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    USER_ACTION = "user_action"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    SECURITY_EVENT = "security_event"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"


@dataclass
class DataLineageNode:
    """Node in the data lineage graph."""
    node_id: str
    node_type: str  # 'input', 'process', 'output', 'model', 'cache'
    timestamp: datetime
    metadata: Dict[str, Any]
    parent_ids: List[str] = field(default_factory=list)
    child_ids: List[str] = field(default_factory=list)


# Database Models
class AuditLog(Base):
    """Audit log database model."""
    __tablename__ = 'audit_logs'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String(50), index=True)
    user_id = Column(String(255), index=True)
    session_id = Column(String(36), index=True)
    resource_id = Column(String(255), index=True)
    resource_type = Column(String(50))
    action = Column(String(100))
    status = Column(String(20))
    duration_ms = Column(Float)
    metadata = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(255))

    __table_args__ = (
        Index('idx_audit_user_time', 'user_id', 'timestamp'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )


class DataLineage(Base):
    """Data lineage tracking model."""
    __tablename__ = 'data_lineage'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    node_id = Column(String(36), unique=True, index=True)
    node_type = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    operation = Column(String(100))
    input_hash = Column(String(64))
    output_hash = Column(String(64))
    metadata = Column(JSON)

    # Self-referential many-to-many for lineage graph
    parent_edges = relationship(
        "LineageEdge",
        foreign_keys="LineageEdge.child_id",
        back_populates="child_node"
    )
    child_edges = relationship(
        "LineageEdge",
        foreign_keys="LineageEdge.parent_id",
        back_populates="parent_node"
    )


class LineageEdge(Base):
    """Edge in the lineage graph."""
    __tablename__ = 'lineage_edges'

    id = Column(Integer, primary_key=True)
    parent_id = Column(String(36), ForeignKey('data_lineage.node_id'))
    child_id = Column(String(36), ForeignKey('data_lineage.node_id'))
    edge_type = Column(String(50))
    metadata = Column(JSON)

    parent_node = relationship("DataLineage", foreign_keys=[parent_id])
    child_node = relationship("DataLineage", foreign_keys=[child_id])

    __table_args__ = (
        Index('idx_lineage_parent', 'parent_id'),
        Index('idx_lineage_child', 'child_id'),
    )


class ComplianceLog(Base):
    """Compliance-specific audit log."""
    __tablename__ = 'compliance_logs'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    regulation = Column(String(50))  # 'GDPR', 'CCPA', 'HIPAA'
    event_type = Column(String(50))
    data_subject = Column(String(255))
    purpose = Column(String(255))
    legal_basis = Column(String(100))
    retention_period = Column(Integer)  # days
    metadata = Column(JSON)


class AuditManager:
    """Central audit and lineage management system."""

    def __init__(self, database_url: str, enable_compliance: bool = True):
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.enable_compliance = enable_compliance
        self.lineage_graph = nx.DiGraph()
        self._audit_queue = asyncio.Queue(maxsize=1000)
        self._running = False

    async def initialize(self):
        """Initialize database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Start background worker
        self._running = True
        asyncio.create_task(self._audit_worker())

    async def log_event(
            self,
            event_type: AuditEventType,
            user_id: Optional[str] = None,
            session_id: Optional[str] = None,
            resource_id: Optional[str] = None,
            resource_type: Optional[str] = None,
            action: Optional[str] = None,
            status: str = "success",
            duration_ms: Optional[float] = None,
            metadata: Optional[Dict[str, Any]] = None,
            ip_address: Optional[str] = None,
            user_agent: Optional[str] = None
    ):
        """Log an audit event."""
        audit_log = AuditLog(
            event_type=event_type.value,
            user_id=user_id,
            session_id=session_id,
            resource_id=resource_id,
            resource_type=resource_type,
            action=action,
            status=status,
            duration_ms=duration_ms,
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Queue for async processing
        await self._audit_queue.put(audit_log)

    async def track_lineage(
            self,
            node_type: str,
            operation: str,
            input_data: Optional[Any] = None,
            output_data: Optional[Any] = None,
            parent_nodes: Optional[List[str]] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track data lineage for an operation."""
        node_id = str(uuid.uuid4())

        # Calculate data hashes
        input_hash = self._calculate_hash(input_data) if input_data else None
        output_hash = self._calculate_hash(output_data) if output_data else None

        # Create lineage node
        lineage_node = DataLineage(
            node_id=node_id,
            node_type=node_type,
            operation=operation,
            input_hash=input_hash,
            output_hash=output_hash,
            metadata=metadata or {}
        )

        async with self.async_session() as session:
            session.add(lineage_node)

            # Create edges to parent nodes
            if parent_nodes:
                for parent_id in parent_nodes:
                    edge = LineageEdge(
                        parent_id=parent_id,
                        child_id=node_id,
                        edge_type="data_flow",
                        metadata={}
                    )
                    session.add(edge)

            await session.commit()

        # Update in-memory graph
        self.lineage_graph.add_node(
            node_id,
            node_type=node_type,
            operation=operation,
            timestamp=datetime.utcnow()
        )

        if parent_nodes:
            for parent_id in parent_nodes:
                self.lineage_graph.add_edge(parent_id, node_id)

        return node_id

    async def log_compliance_event(
            self,
            regulation: str,
            event_type: str,
            data_subject: str,
            purpose: str,
            legal_basis: str,
            retention_period: int,
            metadata: Optional[Dict[str, Any]] = None
    ):
        """Log compliance-specific events."""
        if not self.enable_compliance:
            return

        compliance_log = ComplianceLog(
            regulation=regulation,
            event_type=event_type,
            data_subject=data_subject,
            purpose=purpose,
            legal_basis=legal_basis,
            retention_period=retention_period,
            metadata=metadata or {}
        )

        async with self.async_session() as session:
            session.add(compliance_log)
            await session.commit()

    async def get_lineage_trace(
            self,
            node_id: str,
            direction: str = "both",
            max_depth: int = 10
    ) -> Dict[str, Any]:
        """Get lineage trace for a node."""
        async with self.async_session() as session:
            # Build lineage graph from database
            if direction in ["upstream", "both"]:
                upstream = await self._trace_upstream(session, node_id, max_depth)
            else:
                upstream = []

            if direction in ["downstream", "both"]:
                downstream = await self._trace_downstream(session, node_id, max_depth)
            else:
                downstream = []

            return {
                "node_id": node_id,
                "upstream": upstream,
                "downstream": downstream,
                "graph": self._build_lineage_graph_viz(node_id, upstream, downstream)
            }

    async def _trace_upstream(
            self,
            session: AsyncSession,
            node_id: str,
            max_depth: int,
            current_depth: int = 0
    ) -> List[Dict[str, Any]]:
        """Trace upstream lineage."""
        if current_depth >= max_depth:
            return []

        result = await session.execute(
            """
            SELECT dl.*, le.metadata as edge_metadata
            FROM data_lineage dl
                     JOIN lineage_edges le ON dl.node_id = le.parent_id
            WHERE le.child_id = :node_id
            """,
            {"node_id": node_id}
        )

        upstream_nodes = []
        for row in result:
            node_data = {
                "node_id": row.node_id,
                "node_type": row.node_type,
                "operation": row.operation,
                "created_at": row.created_at.isoformat(),
                "metadata": row.metadata,
                "edge_metadata": row.edge_metadata
            }

            # Recursive trace
            node_data["upstream"] = await self._trace_upstream(
                session, row.node_id, max_depth, current_depth + 1
            )

            upstream_nodes.append(node_data)

        return upstream_nodes

    async def _trace_downstream(
            self,
            session: AsyncSession,
            node_id: str,
            max_depth: int,
            current_depth: int = 0
    ) -> List[Dict[str, Any]]:
        """Trace downstream lineage."""
        if current_depth >= max_depth:
            return []

        result = await session.execute(
            """
            SELECT dl.*, le.metadata as edge_metadata
            FROM data_lineage dl
                     JOIN lineage_edges le ON dl.node_id = le.child_id
            WHERE le.parent_id = :node_id
            """,
            {"node_id": node_id}
        )

        downstream_nodes = []
        for row in result:
            node_data = {
                "node_id": row.node_id,
                "node_type": row.node_type,
                "operation": row.operation,
                "created_at": row.created_at.isoformat(),
                "metadata": row.metadata,
                "edge_metadata": row.edge_metadata
            }

            # Recursive trace
            node_data["downstream"] = await self._trace_downstream(
                session, row.node_id, max_depth, current_depth + 1
            )

            downstream_nodes.append(node_data)

        return downstream_nodes

    async def query_audit_logs(
            self,
            filters: Dict[str, Any],
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None,
            limit: int = 100,
            offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query audit logs with filters."""
        async with self.async_session() as session:
            query = session.query(AuditLog)

            # Apply filters
            if 'user_id' in filters:
                query = query.filter(AuditLog.user_id == filters['user_id'])
            if 'event_type' in filters:
                query = query.filter(AuditLog.event_type == filters['event_type'])
            if 'resource_type' in filters:
                query = query.filter(AuditLog.resource_type == filters['resource_type'])
            if 'status' in filters:
                query = query.filter(AuditLog.status == filters['status'])

            # Time range
            if start_time:
                query = query.filter(AuditLog.timestamp >= start_time)
            if end_time:
                query = query.filter(AuditLog.timestamp <= end_time)

            # Order and paginate
            query = query.order_by(AuditLog.timestamp.desc())
            query = query.limit(limit).offset(offset)

            result = await session.execute(query)

            return [
                {
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat(),
                    "event_type": log.event_type,
                    "user_id": log.user_id,
                    "resource_id": log.resource_id,
                    "resource_type": log.resource_type,
                    "action": log.action,
                    "status": log.status,
                    "duration_ms": log.duration_ms,
                    "metadata": log.metadata
                }
                for log in result.scalars()
            ]

    async def generate_compliance_report(
            self,
            regulation: str,
            start_date: datetime,
            end_date: datetime
    ) -> Dict[str, Any]:
        """Generate compliance report."""
        async with self.async_session() as session:
            # Get compliance events
            result = await session.execute(
                """
                SELECT *
                FROM compliance_logs
                WHERE regulation = :regulation
                  AND timestamp BETWEEN :start_date AND :end_date
                ORDER BY timestamp
                """,
                {
                    "regulation": regulation,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )

            events = result.fetchall()

            # Analyze events
            report = {
                "regulation": regulation,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "summary": {
                    "total_events": len(events),
                    "by_type": {},
                    "by_purpose": {},
                    "by_legal_basis": {}
                },
                "events": []
            }

            for event in events:
                # Update summaries
                event_type = event.event_type
                report["summary"]["by_type"][event_type] = \
                    report["summary"]["by_type"].get(event_type, 0) + 1

                purpose = event.purpose
                report["summary"]["by_purpose"][purpose] = \
                    report["summary"]["by_purpose"].get(purpose, 0) + 1

                legal_basis = event.legal_basis
                report["summary"]["by_legal_basis"][legal_basis] = \
                    report["summary"]["by_legal_basis"].get(legal_basis, 0) + 1

                # Add event details
                report["events"].append({
                    "id": event.id,
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    "data_subject": event.data_subject,
                    "purpose": event.purpose,
                    "legal_basis": event.legal_basis,
                    "retention_period": event.retention_period
                })

            return report

    async def _audit_worker(self):
        """Background worker for processing audit logs."""
        batch = []
        last_flush = asyncio.get_event_loop().time()

        while self._running:
            try:
                # Get audit log from queue
                try:
                    audit_log = await asyncio.wait_for(
                        self._audit_queue.get(),
                        timeout=1.0
                    )
                    batch.append(audit_log)
                except asyncio.TimeoutError:
                    pass

                # Flush batch if needed
                should_flush = (
                        len(batch) >= 100 or
                        asyncio.get_event_loop().time() - last_flush > 5.0
                )

                if should_flush and batch:
                    async with self.async_session() as session:
                        session.add_all(batch)
                        await session.commit()

                    batch = []
                    last_flush = asyncio.get_event_loop().time()

            except Exception as e:
                logger.error(f"Audit worker error: {e}")

    def _calculate_hash(self, data: Any) -> str:
        """Calculate hash of data for lineage tracking."""
        import hashlib

        if isinstance(data, str):
            content = data
        elif isinstance(data, (dict, list)):
            content = json.dumps(data, sort_keys=True)
        else:
            content = str(data)

        return hashlib.sha256(content.encode()).hexdigest()

    def _build_lineage_graph_viz(
            self,
            node_id: str,
            upstream: List[Dict],
            downstream: List[Dict]
    ) -> Dict[str, Any]:
        """Build visualization data for lineage graph."""
        nodes = []
        edges = []

        # Add center node
        nodes.append({
            "id": node_id,
            "label": f"Current: {node_id[:8]}",
            "type": "center"
        })

        # Add upstream nodes
        def add_upstream_nodes(node_list, parent_id):
            for node in node_list:
                nodes.append({
                    "id": node["node_id"],
                    "label": f"{node['node_type']}: {node['node_id'][:8]}",
                    "type": "upstream"
                })
                edges.append({
                    "from": node["node_id"],
                    "to": parent_id
                })
                add_upstream_nodes(node.get("upstream", []), node["node_id"])

        add_upstream_nodes(upstream, node_id)

        # Add downstream nodes
        def add_downstream_nodes(node_list, parent_id):
            for node in node_list:
                nodes.append({
                    "id": node["node_id"],
                    "label": f"{node['node_type']}: {node['node_id'][:8]}",
                    "type": "downstream"
                })
                edges.append({
                    "from": parent_id,
                    "to": node["node_id"]
                })
                add_downstream_nodes(node.get("downstream", []), node["node_id"])

        add_downstream_nodes(downstream, node_id)

        return {
            "nodes": nodes,
            "edges": edges
        }