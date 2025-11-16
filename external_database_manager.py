"""
External Database Connection Manager
Manages connections to external SQL databases (PostgreSQL, MySQL, SQL Server, Supabase, etc.)
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass, asdict
import urllib.parse
from datetime import datetime

try:
    import sqlalchemy
    from sqlalchemy import create_engine, text, MetaData, inspect
    from sqlalchemy.exc import SQLAlchemyError
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConnection:
    """Represents an external database connection configuration"""
    name: str
    db_type: str  # 'postgresql', 'mysql', 'sqlserver', 'sqlite'
    host: str
    port: int
    database: str
    username: str
    password: str
    connection_string: Optional[str] = None
    is_active: bool = True
    created_at: str = None
    last_tested: str = None
    test_status: str = "not_tested"  # 'success', 'failed', 'not_tested'
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatabaseConnection':
        """Create from dictionary"""
        return cls(**data)

class ExternalDatabaseManager:
    """Manages external database connections and operations"""
    
    def __init__(self, config_path: str = "database/external_connections.json"):
        self.config_path = Path(config_path)
        self.connections: Dict[str, DatabaseConnection] = {}
        self.engines: Dict[str, Any] = {}  # SQLAlchemy engines cache
        
        # Ensure config directory exists
        self.config_path.parent.mkdir(exist_ok=True)
        
        # Load existing connections
        self.load_connections()
    
    def get_available_db_types(self) -> Dict[str, Dict[str, Any]]:
        """Get available database types and their requirements"""
        db_types = {
            'postgresql': {
                'name': 'PostgreSQL',
                'default_port': 5432,
                'available': PSYCOPG2_AVAILABLE and SQLALCHEMY_AVAILABLE,
                'driver': 'psycopg2',
                'example_host': 'localhost or your-server.com',
                'notes': 'Supports Supabase, AWS RDS, Google Cloud SQL'
            },
            'mysql': {
                'name': 'MySQL',
                'default_port': 3306,
                'available': PYMYSQL_AVAILABLE and SQLALCHEMY_AVAILABLE,
                'driver': 'pymysql',
                'example_host': 'localhost or your-server.com',
                'notes': 'Supports AWS RDS, Google Cloud SQL, PlanetScale'
            },
            'sqlserver': {
                'name': 'SQL Server',
                'default_port': 1433,
                'available': PYODBC_AVAILABLE and SQLALCHEMY_AVAILABLE,
                'driver': 'pyodbc',
                'example_host': 'localhost or your-server.com',
                'notes': 'Supports Azure SQL Database, SQL Server Express'
            },
            'sqlite': {
                'name': 'SQLite (Local)',
                'default_port': None,
                'available': True,
                'driver': 'sqlite3',
                'example_host': 'N/A (file-based)',
                'notes': 'Local file database, already supported'
            }
        }
        
        return db_types
    
    def get_missing_dependencies(self) -> List[str]:
        """Get list of missing dependencies for external databases"""
        missing = []
        
        if not SQLALCHEMY_AVAILABLE:
            missing.append("sqlalchemy")
        
        if not PSYCOPG2_AVAILABLE:
            missing.append("psycopg2-binary")
        
        if not PYMYSQL_AVAILABLE:
            missing.append("pymysql")
        
        if not PYODBC_AVAILABLE:
            missing.append("pyodbc")
        
        return missing
    
    def build_connection_string(self, connection: DatabaseConnection) -> str:
        """Build SQLAlchemy connection string from connection details"""
        if connection.connection_string:
            return connection.connection_string
        
        if connection.db_type == 'postgresql':
            # Support for Supabase and other PostgreSQL hosts
            return f"postgresql+psycopg2://{connection.username}:{urllib.parse.quote_plus(connection.password)}@{connection.host}:{connection.port}/{connection.database}"
        
        elif connection.db_type == 'mysql':
            return f"mysql+pymysql://{connection.username}:{urllib.parse.quote_plus(connection.password)}@{connection.host}:{connection.port}/{connection.database}"
        
        elif connection.db_type == 'sqlserver':
            # For SQL Server with Windows Authentication, username can be empty
            if connection.username:
                return f"mssql+pyodbc://{connection.username}:{urllib.parse.quote_plus(connection.password)}@{connection.host}:{connection.port}/{connection.database}?driver=ODBC+Driver+17+for+SQL+Server"
            else:
                return f"mssql+pyodbc://{connection.host}:{connection.port}/{connection.database}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
        
        elif connection.db_type == 'sqlite':
            return f"sqlite:///{connection.database}"
        
        else:
            raise ValueError(f"Unsupported database type: {connection.db_type}")
    
    def add_connection(self, connection: DatabaseConnection) -> Tuple[bool, str]:
        """Add a new external database connection"""
        try:
            # Validate connection name is unique
            if connection.name in self.connections:
                return False, f"Connection '{connection.name}' already exists"
            
            # Test the connection
            success, message = self.test_connection(connection)
            connection.test_status = "success" if success else "failed"
            connection.last_tested = datetime.now().isoformat()
            
            # Add to connections
            self.connections[connection.name] = connection
            
            # Save to file
            self.save_connections()
            
            status_msg = "and tested successfully" if success else f"but connection test failed: {message}"
            return True, f"Connection '{connection.name}' added {status_msg}"
            
        except Exception as e:
            logger.error(f"Error adding connection: {str(e)}")
            return False, f"Error adding connection: {str(e)}"
    
    def test_connection(self, connection: DatabaseConnection) -> Tuple[bool, str]:
        """Test a database connection"""
        if not SQLALCHEMY_AVAILABLE:
            return False, "SQLAlchemy not installed. Install with: pip install sqlalchemy"
        
        try:
            # Build connection string
            conn_str = self.build_connection_string(connection)
            
            # Create engine with timeout
            engine = create_engine(
                conn_str, 
                connect_args={'connect_timeout': 10} if connection.db_type == 'postgresql' else {},
                pool_timeout=10,
                pool_recycle=3600
            )
            
            # Test connection
            with engine.connect() as conn:
                if connection.db_type in ['postgresql', 'mysql']:
                    result = conn.execute(text("SELECT 1"))
                elif connection.db_type == 'sqlserver':
                    result = conn.execute(text("SELECT 1"))
                elif connection.db_type == 'sqlite':
                    result = conn.execute(text("SELECT 1"))
                
                result.fetchone()
            
            # Cache the engine if connection successful
            self.engines[connection.name] = engine
            
            return True, "Connection successful"
            
        except Exception as e:
            logger.error(f"Connection test failed for {connection.name}: {str(e)}")
            return False, str(e)
    
    def get_connection_engine(self, connection_name: str):
        """Get SQLAlchemy engine for a connection"""
        if connection_name in self.engines:
            return self.engines[connection_name]
        
        if connection_name in self.connections:
            connection = self.connections[connection_name]
            success, message = self.test_connection(connection)
            if success:
                return self.engines[connection_name]
            else:
                raise Exception(f"Cannot connect to {connection_name}: {message}")
        
        raise Exception(f"Connection '{connection_name}' not found")
    
    def get_database_schema(self, connection_name: str) -> Dict[str, Any]:
        """Get database schema information"""
        try:
            engine = self.get_connection_engine(connection_name)
            inspector = inspect(engine)
            
            schema_info = {
                'tables': [],
                'connection_name': connection_name,
                'db_type': self.connections[connection_name].db_type
            }
            
            # Get all tables
            table_names = inspector.get_table_names()
            
            for table_name in table_names:
                table_info = {
                    'name': table_name,
                    'columns': [],
                    'row_count': None  # Will be filled later if needed
                }
                
                # Get column information
                columns = inspector.get_columns(table_name)
                for column in columns:
                    table_info['columns'].append({
                        'name': column['name'],
                        'type': str(column['type']),
                        'nullable': column['nullable'],
                        'primary_key': column.get('primary_key', False),
                        'default': column.get('default', None)
                    })
                
                schema_info['tables'].append(table_info)
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Error getting schema for {connection_name}: {str(e)}")
            raise
    
    def execute_query(self, connection_name: str, query: str, params: Optional[List] = None) -> Dict[str, Any]:
        """Execute a query on an external database"""
        try:
            engine = self.get_connection_engine(connection_name)
            
            with engine.connect() as conn:
                # Execute query
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))
                
                # Check if it's a SELECT query
                query_upper = query.strip().upper()
                if query_upper.startswith('SELECT'):
                    # Fetch results
                    rows = result.fetchall()
                    columns = list(result.keys())
                    
                    # Convert to list of dictionaries
                    data = []
                    for row in rows:
                        data.append(dict(zip(columns, row)))
                    
                    return {
                        'success': True,
                        'data': data,
                        'columns': columns,
                        'row_count': len(data),
                        'query_type': 'SELECT'
                    }
                else:
                    # For non-SELECT queries
                    conn.commit()
                    return {
                        'success': True,
                        'message': f"Query executed successfully. Rows affected: {result.rowcount}",
                        'rows_affected': result.rowcount,
                        'query_type': 'MODIFY'
                    }
                    
        except Exception as e:
            logger.error(f"Query execution error on {connection_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'query_type': 'ERROR'
            }
    
    def get_table_data(self, connection_name: str, table_name: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get data from a table with pagination"""
        try:
            connection = self.connections[connection_name]
            
            # Build appropriate LIMIT/OFFSET syntax for different databases
            if connection.db_type == 'sqlserver':
                # SQL Server uses OFFSET...FETCH
                query = f"SELECT * FROM {table_name} ORDER BY (SELECT NULL) OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"
            elif connection.db_type == 'postgresql':
                # PostgreSQL uses LIMIT/OFFSET
                query = f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}"
            elif connection.db_type == 'mysql':
                # MySQL uses LIMIT with OFFSET
                query = f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}"
            else:
                # Default LIMIT/OFFSET
                query = f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}"
            
            return self.execute_query(connection_name, query)
            
        except Exception as e:
            logger.error(f"Error getting table data: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_table_count(self, connection_name: str, table_name: str) -> int:
        """Get total number of rows in a table"""
        try:
            query = f"SELECT COUNT(*) as total FROM {table_name}"
            result = self.execute_query(connection_name, query)
            
            if result['success'] and result['data']:
                return result['data'][0]['total']
            return 0
            
        except Exception as e:
            logger.error(f"Error getting table count: {str(e)}")
            return 0
    
    def remove_connection(self, connection_name: str) -> Tuple[bool, str]:
        """Remove a database connection"""
        try:
            if connection_name not in self.connections:
                return False, f"Connection '{connection_name}' not found"
            
            # Remove from connections
            del self.connections[connection_name]
            
            # Remove cached engine
            if connection_name in self.engines:
                try:
                    self.engines[connection_name].dispose()
                    del self.engines[connection_name]
                except:
                    pass
            
            # Save updated connections
            self.save_connections()
            
            return True, f"Connection '{connection_name}' removed successfully"
            
        except Exception as e:
            logger.error(f"Error removing connection: {str(e)}")
            return False, f"Error removing connection: {str(e)}"
    
    def list_connections(self) -> List[DatabaseConnection]:
        """Get list of all connections"""
        return list(self.connections.values())
    
    def get_connection(self, name: str) -> Optional[DatabaseConnection]:
        """Get a specific connection by name"""
        return self.connections.get(name)
    
    def save_connections(self):
        """Save connections to file"""
        try:
            connections_data = {
                name: conn.to_dict() 
                for name, conn in self.connections.items()
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(connections_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving connections: {str(e)}")
    
    def load_connections(self):
        """Load connections from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    connections_data = json.load(f)
                
                for name, conn_data in connections_data.items():
                    self.connections[name] = DatabaseConnection.from_dict(conn_data)
                    
        except Exception as e:
            logger.error(f"Error loading connections: {str(e)}")
    
    def get_connection_summary(self) -> Dict[str, Any]:
        """Get summary of all connections"""
        summary = {
            'total_connections': len(self.connections),
            'active_connections': len([c for c in self.connections.values() if c.is_active]),
            'by_type': {},
            'recent_activity': []
        }
        
        # Count by database type
        for conn in self.connections.values():
            db_type = conn.db_type
            if db_type not in summary['by_type']:
                summary['by_type'][db_type] = 0
            summary['by_type'][db_type] += 1
        
        # Recent activity
        sorted_connections = sorted(
            self.connections.values(), 
            key=lambda x: x.last_tested or x.created_at, 
            reverse=True
        )
        
        for conn in sorted_connections[:5]:  # Last 5 activities
            summary['recent_activity'].append({
                'name': conn.name,
                'db_type': conn.db_type,
                'last_tested': conn.last_tested,
                'test_status': conn.test_status
            })
        
        return summary

# Example usage and testing
if __name__ == "__main__":
    # Initialize manager
    manager = ExternalDatabaseManager()
    
    # Show available database types
    print("Available database types:")
    db_types = manager.get_available_db_types()
    for db_type, info in db_types.items():
        status = "✅ Available" if info['available'] else "❌ Missing dependencies"
        print(f"  {info['name']}: {status}")
    
    # Show missing dependencies
    missing = manager.get_missing_dependencies()
    if missing:
        print(f"\nTo enable all database types, install: pip install {' '.join(missing)}")
    
    print(f"\nConnections loaded: {len(manager.connections)}")