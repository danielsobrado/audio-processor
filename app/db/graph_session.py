"""Graph database session manager with database-agnostic interface."""

import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, cast

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class GraphDatabaseDriver(ABC):
    """Abstract base class for graph database drivers."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to graph database."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to graph database."""
        pass

    @abstractmethod
    async def execute_read_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """Execute read query and return results."""
        pass

    @abstractmethod
    async def execute_write_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """Execute write query and return results."""
        pass

    @abstractmethod
    async def execute_batch_queries(self, queries: List[tuple]) -> List[Dict]:
        """Execute multiple queries in batch."""
        pass


class Neo4jDriver(GraphDatabaseDriver):
    """Neo4j implementation of graph database driver."""

    def __init__(self, url: str, username: str, password: str):
        self.url = url
        self.username = username
        self.password = password
        self._driver = None

    async def connect(self) -> None:
        """Establish connection to Neo4j."""
        try:
            from neo4j import AsyncGraphDatabase

            self._driver = AsyncGraphDatabase.driver(
                self.url, auth=(self.username, self.password)
            )
            logger.info(f"Connected to Neo4j at {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection to Neo4j."""
        if self._driver:
            await self._driver.close()
            logger.info("Disconnected from Neo4j")

    async def execute_read_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """Execute read query in Neo4j."""
        parameters = parameters or {}

        if self._driver is None:
            raise RuntimeError("Neo4j driver not initialized.")
        async with self._driver.session() as session:
            result = await session.run(query, parameters)  # type: ignore[arg-type]
            records = []
            async for record in result:
                records.append(dict(record))
            return records

    async def execute_write_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """Execute write query in Neo4j."""
        parameters = parameters or {}

        if self._driver is None:
            raise RuntimeError("Neo4j driver not initialized.")
        async with self._driver.session() as session:
            result = await session.run(query, parameters)  # type: ignore[arg-type]
            records = []
            async for record in result:
                records.append(dict(record))
            return records

    async def execute_batch_queries(self, queries: List[tuple]) -> List[Dict]:
        """Execute multiple queries in batch in Neo4j."""
        results = []

        if self._driver is None:
            raise RuntimeError("Neo4j driver not initialized.")
        async with self._driver.session() as session:
            for query, parameters in queries:
                result = await session.run(query, parameters or {})
                batch_records = []
                async for record in result:
                    batch_records.append(dict(record))
                results.extend(batch_records)

        return results


class ArangoDBDriver(GraphDatabaseDriver):
    """ArangoDB implementation of graph database driver."""

    def __init__(self, url: str, username: str, password: str, database: str):
        self.url = url
        self.username = username
        self.password = password
        self.database = database
        self._client = None
        self._db = None

    async def connect(self) -> None:
        """Establish connection to ArangoDB."""
        try:
            from arango import ArangoClient

            self._client = ArangoClient(hosts=self.url)
            self._db = self._client.db(
                self.database, username=self.username, password=self.password
            )
            logger.info(f"Connected to ArangoDB at {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to ArangoDB: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection to ArangoDB."""
        if self._client:
            # ArangoDB client doesn't need explicit close
            logger.info("Disconnected from ArangoDB")

    async def execute_read_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """Execute read query in ArangoDB."""
        import asyncio
        import concurrent.futures

        parameters = parameters or {}

        if self._db is None:
            raise RuntimeError("ArangoDB client not initialized.")

        # Run blocking operation in thread pool to avoid blocking event loop
        db = self._db  # Local reference for type safety

        def _execute_blocking():
            cursor = db.aql.execute(query, bind_vars=parameters)
            return list(cursor)

        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, _execute_blocking)

    async def execute_write_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """Execute write query in ArangoDB."""
        import asyncio
        import concurrent.futures

        parameters = parameters or {}

        if self._db is None:
            raise RuntimeError("ArangoDB client not initialized.")

        # Run blocking operation in thread pool to avoid blocking event loop
        db = self._db  # Local reference for type safety

        def _execute_blocking():
            cursor = db.aql.execute(query, bind_vars=parameters)
            return list(cursor)

        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, _execute_blocking)

    async def execute_batch_queries(self, queries: List[tuple]) -> List[Dict]:
        """Execute multiple queries in batch in ArangoDB."""
        import asyncio
        import concurrent.futures

        if self._db is None:
            raise RuntimeError("ArangoDB client not initialized.")

        # Run blocking operation in thread pool to avoid blocking event loop
        db = self._db  # Local reference for type safety

        def _execute_blocking():
            results = []
            for query, parameters in queries:
                cursor = db.aql.execute(query, bind_vars=parameters or {})
                results.extend(list(cursor))
            return results

        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, _execute_blocking)


class GraphDatabaseManager:
    """Manager for graph database operations with pluggable drivers."""

    def __init__(self):
        self._settings = get_settings()
        self._driver: Optional[GraphDatabaseDriver] = None
        self._is_connected = False

    async def initialize(self) -> None:
        """Initialize graph database connection."""
        if not self._settings.graph.enabled:
            logger.info("Graph database is disabled")
            return

        try:
            # Factory pattern for database drivers
            self._driver = self._create_driver()
            await self._driver.connect()
            self._is_connected = True
            logger.info("Graph database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize graph database: {e}")
            self._is_connected = False
            raise

    def _create_driver(self) -> GraphDatabaseDriver:
        """Create appropriate driver based on configuration."""
        db_type = self._settings.graph.database.type.lower()

        if db_type == "neo4j":
            return Neo4jDriver(
                url=self._settings.graph.database.url,
                username=self._settings.graph.database.username,
                password=self._settings.graph.database.password,
            )
        elif db_type == "arangodb":
            return ArangoDBDriver(
                url=self._settings.graph.database.url,
                username=self._settings.graph.database.username,
                password=self._settings.graph.database.password,
                database=self._settings.graph.database.name,
            )
        else:
            raise ValueError(f"Unsupported graph database type: {db_type}")

    async def shutdown(self) -> None:
        """Shutdown graph database connection."""
        if self._driver and self._is_connected:
            await self._driver.disconnect()
            self._is_connected = False
            logger.info("Graph database shutdown complete")

    @property
    def is_enabled(self) -> bool:
        """Check if graph database is enabled."""
        return self._settings.graph.enabled

    @property
    def is_connected(self) -> bool:
        """Check if graph database is connected."""
        return self._is_connected

    async def execute_read_transaction(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """Execute read transaction."""
        if not self.is_enabled or not self.is_connected:
            logger.debug("Graph database not available")
            return []

        try:
            if self._driver is None:
                raise RuntimeError("Graph database driver not initialized.")
            return await self._driver.execute_read_query(query, parameters or {})
        except Exception as e:
            logger.error(f"Failed to execute read transaction: {e}")
            return []

    async def execute_write_transaction(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """Execute write transaction."""
        if not self.is_enabled or not self.is_connected:
            logger.debug("Graph database not available")
            return []

        try:
            if self._driver is None:
                raise RuntimeError("Graph database driver not initialized.")
            return await self._driver.execute_write_query(query, parameters or {})
        except Exception as e:
            logger.error(f"Failed to execute write transaction: {e}")
            raise

    async def execute_batch_transactions(self, queries: List[tuple]) -> List[Dict]:
        """Execute batch transactions."""
        if not self.is_enabled or not self.is_connected:
            logger.debug("Graph database not available")
            return []

        try:
            if self._driver is None:
                raise RuntimeError("Graph database driver not initialized.")
            return await self._driver.execute_batch_queries(queries)
        except Exception as e:
            logger.error(f"Failed to execute batch transactions: {e}")
            raise

    @asynccontextmanager
    async def transaction(self):
        """Context manager for transactions."""
        if not self.is_enabled or not self.is_connected:
            yield None
            return

        try:
            # For now, we don't implement explicit transactions
            # This can be extended per database type
            yield self
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            raise


# Global manager instance
graph_db_manager = GraphDatabaseManager()


# Dependency injection functions
async def get_graph_db_manager() -> GraphDatabaseManager:
    """Get graph database manager instance."""
    return graph_db_manager


async def get_graph_db_session():
    """Get graph database session."""
    manager = await get_graph_db_manager()
    if not manager.is_connected:
        await manager.initialize()
    return manager
