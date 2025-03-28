import sqlite3
import threading
import logging
import time
from contextlib import contextmanager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConnectionPool:
    """A simple connection pool for SQLite connections"""
    
    def __init__(self, database_path, max_connections=10, timeout=5.0):
        self.database_path = database_path
        self.max_connections = max_connections
        self.timeout = timeout
        self._available_connections = []
        self._in_use_connections = set()
        self._lock = threading.RLock()
        self._connection_count = 0
        
        # Initialize with some connections
        self._fill_pool(min(3, max_connections))
    
    def _fill_pool(self, count):
        """Add new connections to the pool"""
        for _ in range(count):
            if self._connection_count < self.max_connections:
                conn = self._create_connection()
                self._available_connections.append(conn)
    
    def _create_connection(self):
        """Create a new database connection"""
        try:
            # Create connection with extended timeout and WAL mode
            conn = sqlite3.connect(
                self.database_path, 
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
    
    def get_connection(self):
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
    
    def return_connection(self, conn):
        """Return a connection to the pool"""
        with self._lock:
            self._in_use_connections.remove(conn)
            self._available_connections.append(conn)
    
    def close_all(self):
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
_pool = None

def init_pool(database_path='attendance_system.db', max_connections=10):
    """Initialize the connection pool"""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(database_path, max_connections)
    return _pool

def get_db_connection():
    """Get a connection from the pool"""
    global _pool
    if _pool is None:
        init_pool()
    return _pool.get_connection()

@contextmanager
def db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = get_db_connection()
        yield conn
    finally:
        if conn:
            _pool.return_connection(conn)

def execute_query(query, params=None, commit=True):
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

def execute_query_df(query, params=None):
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
