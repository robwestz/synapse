"""
Real-time streaming extraction pipeline.
"""

import asyncio
import json
import logging
from typing import AsyncIterator, Optional, Dict, Any, List
from dataclasses import dataclass

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
except ImportError:
    AIOKafkaConsumer = None
    AIOKafkaProducer = None

try:
    import msgpack
except ImportError:
    msgpack = None

from sie_x.core.engine import SemanticIntelligenceEngine

logger = logging.getLogger(__name__)


@dataclass
class StreamConfig:
    """Streaming configuration."""
    kafka_brokers: List[str]
    input_topic: str
    output_topic: str
    redis_url: str
    batch_size: int = 10
    batch_timeout: float = 1.0


class StreamingPipeline:
    """Real-time document processing pipeline."""

    def __init__(self, engine: SemanticIntelligenceEngine, config: StreamConfig):
        self.engine = engine
        self.config = config
        self.consumer = None
        self.producer = None
        self.redis = None
        self._running = False
        self._tasks = []

    async def start(self):
        """Start the streaming pipeline."""
        if AIOKafkaConsumer is None or AIOKafkaProducer is None or msgpack is None:
            raise RuntimeError(
                "Streaming dependencies not installed. Install 'aiokafka' and 'msgpack' to use Kafka streaming."
            )
        if aioredis is None:
            raise RuntimeError(
                "Redis asyncio dependency not installed. Install 'redis' to use streaming cache."
            )

        # Initialize connections
        self.consumer = AIOKafkaConsumer(
            self.config.input_topic,
            bootstrap_servers=self.config.kafka_brokers,
            value_deserializer=lambda v: msgpack.unpackb(v, raw=False)
        )

        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.config.kafka_brokers,
            value_serializer=lambda v: msgpack.packb(v, use_bin_type=True)
        )

        self.redis = await aioredis.from_url(self.config.redis_url)

        await self.consumer.start()
        await self.producer.start()

        self._running = True

        # Start processing tasks
        for i in range(4):  # 4 parallel processors
            task = asyncio.create_task(self._process_stream(i))
            self._tasks.append(task)

        logger.info("Streaming pipeline started")

    async def stop(self):
        """Stop the streaming pipeline."""
        self._running = False

        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)

        # Close connections
        await self.consumer.stop()
        await self.producer.stop()
        await self.redis.close()

        logger.info("Streaming pipeline stopped")

    async def _process_stream(self, worker_id: int):
        """Process messages from stream."""
        batch = []
        last_batch_time = asyncio.get_event_loop().time()

        try:
            async for message in self.consumer:
                if not self._running:
                    break

                batch.append(message)

                # Process batch if full or timeout
                should_process = (
                        len(batch) >= self.config.batch_size or
                        asyncio.get_event_loop().time() - last_batch_time > self.config.batch_timeout
                )

                if should_process and batch:
                    await self._process_batch(batch, worker_id)
                    batch = []
                    last_batch_time = asyncio.get_event_loop().time()

        except Exception as e:
            logger.error(f"Worker {worker_id} error: {e}")
            raise

    async def _process_batch(self, messages: List[Any], worker_id: int):
        """Process a batch of messages."""
        logger.info(f"Worker {worker_id} processing batch of {len(messages)}")

        for msg in messages:
            try:
                # Extract document
                doc_id = msg.value.get('id')
                text = msg.value.get('text')
                options = msg.value.get('options', {})

                # Check cache
                cache_key = f"stream_result:{doc_id}"
                cached = await self.redis.get(cache_key)

                if cached:
                    result = msgpack.unpackb(cached, raw=False)
                else:
                    # Process document
                    keywords = await self.engine.extract_async(
                        text,
                        **options
                    )

                    result = {
                        'id': doc_id,
                        'keywords': [kw.to_dict() for kw in keywords],
                        'timestamp': asyncio.get_event_loop().time()
                    }

                    # Cache result
                    await self.redis.setex(
                        cache_key,
                        300,  # 5 minute TTL
                        msgpack.packb(result, use_bin_type=True)
                    )

                # Send to output topic
                await self.producer.send(
                    self.config.output_topic,
                    value=result,
                    key=doc_id.encode() if isinstance(doc_id, str) else doc_id
                )

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # Send to dead letter queue
                await self._send_to_dlq(msg, str(e))

    async def _send_to_dlq(self, message: Any, error: str):
        """Send failed messages to dead letter queue."""
        await self.producer.send(
            f"{self.config.output_topic}.dlq",
            value={
                'original': message.value,
                'error': error,
                'timestamp': asyncio.get_event_loop().time()
            }
        )


class WebSocketStreaming:
    """WebSocket-based real-time streaming."""

    def __init__(self, engine: SemanticIntelligenceEngine):
        self.engine = engine
        self.connections: Dict[str, Any] = {}

    async def handle_connection(self, websocket, path):
        """Handle WebSocket connection."""
        conn_id = f"ws_{id(websocket)}"
        self.connections[conn_id] = websocket

        try:
            async for message in websocket:
                data = json.loads(message)

                if data['type'] == 'extract':
                    # Start extraction
                    asyncio.create_task(
                        self._stream_extraction(
                            conn_id,
                            data['text'],
                            data.get('options', {})
                        )
                    )
        finally:
            del self.connections[conn_id]

    async def _stream_extraction(self, conn_id: str, text: str, options: Dict):
        """Stream extraction results as they're generated."""
        websocket = self.connections.get(conn_id)
        if not websocket:
            return

        # Chunk the text
        chunks = self.engine.chunker.chunk(text)

        for i, chunk in enumerate(chunks):
            # Extract keywords from chunk
            keywords = await self.engine.extract_async(
                chunk,
                top_k=5,
                **options
            )

            # Send intermediate result
            await websocket.send(json.dumps({
                'type': 'chunk_result',
                'chunk_index': i,
                'total_chunks': len(chunks),
                'keywords': [kw.to_dict() for kw in keywords]
            }))

        # Send completion
        await websocket.send(json.dumps({
            'type': 'complete',
            'total_chunks': len(chunks)
        }))
