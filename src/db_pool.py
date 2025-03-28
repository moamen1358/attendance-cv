"""
Database Connection Pool

This module provides a connection pooling implementation for SQLite
to improve performance and resource utilization by reusing database connections.

Features:
- Configurable connection pool size
- Thread-safe connection management
- Performance-optimized SQLite settings
- Context manager for automatic connection return
- Helper functions for common database operations
"""
import sqlite3
import threading
import logging
import time
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Generator, Union
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConnectionPool:
    """
    A connection pool for SQLite connections that improves performance
    by reusing database connections instead of creating new ones.
    """
    
    def __init__(self, database_path: Union[str, Path], max_connections: int = 10, timeout: float = 5.0):
        """
        Initialize the connection pool
        
        Args:
            database_path: Path to the SQLite database file
            max_connections: Maximum number of connections to maintain
            timeout: Maximum time to wait for a connection
        """
        self.database_path = database_path
        self.max_connections = max_connections
        self.timeout = timeout
        self._available_connections = []
        self._in_use_connections = set()
        self._lock = threading.RLock()
        self._connection_count = 0
        
        # Initialize with some connections
        self._fill_pool(min(3, max_connections))
    
    def _fill_pool(self, count: int) -> None:
        """Add new connections to the pool"""
        for _ in range(count):
            if self._connection_count < self.max_connections:
                conn = self._create_connection()
                self._available_connections.append(conn)
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection"""
        try:
            # Create connection with extended timeout and WAL mode
            conn = sqlite3.connect(
                str(self.database_path), 
                timeout=30.0,
                check_same_thread=False
            )
            
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Use WAL journal mode for better concurrency
            conn.execute("PRAGMA journal_mode = WAL")
            
            # Increase cache size for performance
            conn.execute("PRAGMA cache_size = 10000")
            
            # Set synchronous mode to NORMAL for better performance
            conn.execute("PRAGMA synchronous = NORMAL")
            
            with self._lock:
                self._connection_count += 1
                
            return conn
        except Exception as e:
            logger.error(f"Error creating database connection: {e}")
            raise
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool or create a new one"""
        start_time = time.time()
        
        while True:
            with self._lock:
                if self._available_connections:
                    # Get connection from the pool
                    conn = self._available_connections.pop()
                    self._in_use_connections.add(conn)
                    return conn
                elif self._connection_count < self.max_connections:
                    # Create new connection if under limit
                    conn = self._create_connection()
                    self._in_use_connections.add(conn)
                    return conn
            
            # Wait if we're at max connections
            if time.time() - start_time > self.timeout:
                raise TimeoutError("Timeout waiting for database connection")
            
            # Sleep before retrying
            time.sleep(0.1)
    
    def return_connection(self, conn: sqlite3.Connection) -> None:
        """Return a connection to the pool"""
        with self._lock:
            self._in_use_connections.remove(conn)
            self._available_connections.append(conn)
    
    def close_all(self) -> None:
        """Close all connections in the pool"""
        with self._lock:
            # Close all available connections
            for conn in self._available_connections:
                try:
                    conn.close()
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")
            
            # Close all in-use connections
            for conn in self._in_use_connections:
                try:
                    conn.close()
                except Exception as e:
                    logger.error(f"Error closing in-use connection: {e}")
            
            # Reset connection tracking
            self._available_connections = []
            self._in_use_connections = set()
            self._connection_count = 0

# Singleton pool instance
_pool: Optional[ConnectionPool] = None

def init_pool(database_path: Union[str, Path] = 'attendance_system.db', max_connections: int = 10) -> ConnectionPool:
    """Initialize the connection pool"""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(database_path, max_connections)
    return _pool

def get_db_connection() -> sqlite3.Connection:
    """Get a connection from the pool"""
    global _pool
    if _pool is None:
        init_pool()
    return _pool.get_connection()

@contextmanager
def db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database connections"""
    conn = None
    try:
        conn = get_db_connection()
        yield conn
    finally:
        if conn:
            _pool.return_connection(conn)

def execute_query(query: str, params: Optional[Union[List[Any], Dict[str, Any]]] = None, commit: bool = True) -> sqlite3.Cursor:
    """Execute a query using a connection from the pool"""
    with db_connection() as conn:
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            if commit:
                conn.commit()
                
            return cursor
        except Exception as e:
            conn.rollback()
            logger.error(f"Query execution error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise

def execute_query_df(query: str, params: Optional[Union[List[Any], Dict[str, Any]]] = None) -> Any:
    """Execute a query and return results as a pandas DataFrame"""
    import pandas as pd
    
    with db_connection() as conn:
        try:
            if params:
                df = pd.read_sql_query(query, conn, params=params)
            else:
                df = pd.read_sql_query(query, conn)
            return df
        except Exception as e:
            logger.error(f"DataFrame query error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
