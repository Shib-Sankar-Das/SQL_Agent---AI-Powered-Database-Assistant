"""
Universal Database Adapter
Provides a unified interface for working with both local SQLite and external SQL databases
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
import pandas as pd
import logging
from datetime import datetime

from external_database_manager import ExternalDatabaseManager, DatabaseConnection

logger = logging.getLogger(__name__)

class UniversalDatabaseAdapter:
    """
    Universal adapter for working with both SQLite and external databases
    Provides a consistent interface regardless of the database type
    """
    
    def __init__(self):
        self.external_manager = ExternalDatabaseManager()
        self.sqlite_databases = {}  # Cache of SQLite connections
        
    def get_all_databases(self) -> Dict[str, Dict[str, Any]]:
        """Get all available databases (both SQLite and external)"""
        all_databases = {}
        
        # Get local SQLite databases
        sqlite_dbs = self._discover_sqlite_databases()
        for db_name, db_info in sqlite_dbs.items():
            all_databases[db_name] = {
                'type': 'sqlite',
                'path': db_info['path'],
                'tables': db_info.get('tables', []),
                'size': db_info.get('size', 0),
                'connection_name': db_name,
                'is_external': False
            }
        
        # Get external databases
        external_connections = self.external_manager.list_connections()
        for conn in external_connections:
            if conn.is_active and conn.test_status == 'success':
                try:
                    schema_info = self.external_manager.get_database_schema(conn.name)
                    all_databases[f"🌐 {conn.name}"] = {
                        'type': conn.db_type,
                        'connection_name': conn.name,
                        'host': f"{conn.host}:{conn.port}",
                        'database': conn.database,
                        'tables': schema_info.get('tables', []),
                        'is_external': True,
                        'connection_info': conn
                    }
                except Exception as e:
                    logger.warning(f"Could not get schema for external database {conn.name}: {str(e)}")
                    # Still include it but mark as problematic
                    all_databases[f"🌐 {conn.name} ⚠️"] = {
                        'type': conn.db_type,
                        'connection_name': conn.name,
                        'host': f"{conn.host}:{conn.port}",
                        'database': conn.database,
                        'tables': [],
                        'is_external': True,
                        'connection_info': conn,
                        'error': str(e)
                    }
        
        return all_databases
    
    def _discover_sqlite_databases(self) -> Dict[str, Dict[str, Any]]:
        """Discover local SQLite databases"""
        databases = {}
        
        # Look in the database directory
        database_dir = Path("database")
        if database_dir.exists():
            for db_file in database_dir.glob("*.db"):
                try:
                    db_name = db_file.stem
                    if db_name == "sql_agent":
                        db_name = "Main Database"
                    else:
                        # Capitalize and format name
                        db_name = db_name.replace("_", " ").title()
                    
                    # Get database info
                    db_info = self._get_sqlite_info(db_file)
                    databases[db_name] = db_info
                    
                except Exception as e:
                    logger.warning(f"Could not process SQLite database {db_file}: {str(e)}")
        
        return databases
    
    def _get_sqlite_info(self, db_path: Path) -> Dict[str, Any]:
        """Get information about a SQLite database"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            table_names = [row[0] for row in cursor.fetchall()]
            
            tables = []
            for table_name in table_names:
                try:
                    # Get table info
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns_info = cursor.fetchall()
                    
                    columns = []
                    for col_info in columns_info:
                        columns.append({
                            'name': col_info[1],
                            'type': col_info[2],
                            'nullable': not col_info[3],
                            'primary_key': bool(col_info[5]),
                            'default': col_info[4]
                        })
                    
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    
                    tables.append({
                        'name': table_name,
                        'columns': columns,
                        'row_count': row_count
                    })
                    
                except Exception as e:
                    logger.warning(f"Error getting info for table {table_name}: {str(e)}")
            
            conn.close()
            
            return {
                'path': str(db_path),
                'tables': tables,
                'size': db_path.stat().st_size
            }
            
        except Exception as e:
            logger.error(f"Error getting SQLite info for {db_path}: {str(e)}")
            return {
                'path': str(db_path),
                'tables': [],
                'size': 0,
                'error': str(e)
            }
    
    def execute_query(self, database_name: str, query: str, params: Optional[List] = None) -> Dict[str, Any]:
        """Execute a query on any database (SQLite or external)"""
        try:
            # Check if it's an external database
            if database_name.startswith("🌐"):
                # Extract connection name
                conn_name = database_name.replace("🌐 ", "").replace(" ⚠️", "")
                return self.external_manager.execute_query(conn_name, query, params)
            else:
                # SQLite database
                return self._execute_sqlite_query(database_name, query, params)
                
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'query_type': 'ERROR'
            }
    
    def _execute_sqlite_query(self, database_name: str, query: str, params: Optional[List] = None) -> Dict[str, Any]:
        """Execute query on SQLite database"""
        try:
            # Get database path
            db_path = self._get_sqlite_path(database_name)
            if not db_path:
                return {
                    'success': False,
                    'error': f"SQLite database '{database_name}' not found"
                }
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Execute query
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Check if it's a SELECT query
            query_upper = query.strip().upper()
            if query_upper.startswith('SELECT'):
                # Fetch results
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                # Convert to list of dictionaries
                data = []
                for row in rows:
                    data.append(dict(zip(columns, row)))
                
                conn.close()
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
                rows_affected = cursor.rowcount
                conn.close()
                return {
                    'success': True,
                    'message': f"Query executed successfully. Rows affected: {rows_affected}",
                    'rows_affected': rows_affected,
                    'query_type': 'MODIFY'
                }
                
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            logger.error(f"SQLite query execution error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'query_type': 'ERROR'
            }
    
    def _get_sqlite_path(self, database_name: str) -> Optional[str]:
        """Get the file path for a SQLite database"""
        if database_name == "Main Database":
            return "database/sql_agent.db"
        
        # Try to find the database file
        database_dir = Path("database")
        if database_dir.exists():
            # Convert display name back to filename
            filename_base = database_name.lower().replace(" ", "_")
            db_file = database_dir / f"{filename_base}.db"
            if db_file.exists():
                return str(db_file)
            
            # Also try exact match
            for db_file in database_dir.glob("*.db"):
                if db_file.stem.replace("_", " ").title() == database_name:
                    return str(db_file)
        
        return None
    
    def get_table_data(self, database_name: str, table_name: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get data from any table in any database"""
        try:
            # Check if it's an external database
            if database_name.startswith("🌐"):
                conn_name = database_name.replace("🌐 ", "").replace(" ⚠️", "")
                return self.external_manager.get_table_data(conn_name, table_name, limit, offset)
            else:
                # SQLite database
                query = f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}"
                return self._execute_sqlite_query(database_name, query)
                
        except Exception as e:
            logger.error(f"Error getting table data: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_table_count(self, database_name: str, table_name: str) -> int:
        """Get total number of rows in any table"""
        try:
            query = f"SELECT COUNT(*) as total FROM {table_name}"
            result = self.execute_query(database_name, query)
            
            if result['success'] and result['data']:
                return result['data'][0]['total']
            return 0
            
        except Exception as e:
            logger.error(f"Error getting table count: {str(e)}")
            return 0
    
    def get_database_schema(self, database_name: str) -> Dict[str, Any]:
        """Get schema information for any database"""
        try:
            # Check if it's an external database
            if database_name.startswith("🌐"):
                conn_name = database_name.replace("🌐 ", "").replace(" ⚠️", "")
                return self.external_manager.get_database_schema(conn_name)
            else:
                # SQLite database - use existing discovery method
                sqlite_dbs = self._discover_sqlite_databases()
                for db_name, db_info in sqlite_dbs.items():
                    if db_name == database_name:
                        return {
                            'tables': db_info['tables'],
                            'connection_name': database_name,
                            'db_type': 'sqlite'
                        }
                
                return {'tables': [], 'connection_name': database_name, 'db_type': 'sqlite'}
                
        except Exception as e:
            logger.error(f"Error getting database schema: {str(e)}")
            return {'tables': [], 'error': str(e)}
    
    def insert_record(self, database_name: str, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a record into any database"""
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' if not database_name.startswith("🌐") else '%s' for _ in data])
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            
            # For external databases, we might need different parameter styles
            if database_name.startswith("🌐"):
                conn_name = database_name.replace("🌐 ", "").replace(" ⚠️", "")
                connection = self.external_manager.get_connection(conn_name)
                
                if connection.db_type == 'postgresql':
                    # PostgreSQL uses numbered parameters
                    placeholders = ', '.join([f'${i+1}' for i in range(len(data))])
                    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                elif connection.db_type == 'mysql':
                    # MySQL uses %s
                    placeholders = ', '.join(['%s' for _ in data])
                    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                elif connection.db_type == 'sqlserver':
                    # SQL Server uses ?
                    placeholders = ', '.join(['?' for _ in data])
                    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                
            result = self.execute_query(database_name, query, list(data.values()))
            
            if result['success']:
                return {
                    'success': True,
                    'message': f"Record inserted successfully into {table_name}"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error inserting record: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_record(self, database_name: str, table_name: str, record_id: Any, id_column: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a record in any database"""
        try:
            set_clause = ', '.join([f"{col} = ?" for col in data.keys()])
            query = f"UPDATE {table_name} SET {set_clause} WHERE {id_column} = ?"
            
            # Adjust parameter style for external databases
            if database_name.startswith("🌐"):
                conn_name = database_name.replace("🌐 ", "").replace(" ⚠️", "")
                connection = self.external_manager.get_connection(conn_name)
                
                if connection.db_type in ['postgresql', 'mysql']:
                    if connection.db_type == 'postgresql':
                        # PostgreSQL numbered parameters
                        set_parts = [f"{col} = ${i+1}" for i, col in enumerate(data.keys())]
                        set_clause = ', '.join(set_parts)
                        query = f"UPDATE {table_name} SET {set_clause} WHERE {id_column} = ${len(data)+1}"
                    else:
                        # MySQL %s parameters
                        set_clause = ', '.join([f"{col} = %s" for col in data.keys()])
                        query = f"UPDATE {table_name} SET {set_clause} WHERE {id_column} = %s"
            
            values = list(data.values()) + [record_id]
            result = self.execute_query(database_name, query, values)
            
            if result['success']:
                return {
                    'success': True,
                    'message': f"Record updated successfully in {table_name}"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error updating record: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_record(self, database_name: str, table_name: str, record_id: Any, id_column: str) -> Dict[str, Any]:
        """Delete a record from any database"""
        try:
            query = f"DELETE FROM {table_name} WHERE {id_column} = ?"
            
            # Adjust parameter style for external databases
            if database_name.startswith("🌐"):
                conn_name = database_name.replace("🌐 ", "").replace(" ⚠️", "")
                connection = self.external_manager.get_connection(conn_name)
                
                if connection.db_type == 'postgresql':
                    query = f"DELETE FROM {table_name} WHERE {id_column} = $1"
                elif connection.db_type == 'mysql':
                    query = f"DELETE FROM {table_name} WHERE {id_column} = %s"
            
            result = self.execute_query(database_name, query, [record_id])
            
            if result['success']:
                return {
                    'success': True,
                    'message': f"Record deleted successfully from {table_name}"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error deleting record: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_external_connections_summary(self) -> Dict[str, Any]:
        """Get summary of external database connections"""
        return self.external_manager.get_connection_summary()
    
    def add_external_connection(self, connection: DatabaseConnection) -> Tuple[bool, str]:
        """Add a new external database connection"""
        return self.external_manager.add_connection(connection)
    
    def test_external_connection(self, connection: DatabaseConnection) -> Tuple[bool, str]:
        """Test an external database connection"""
        return self.external_manager.test_connection(connection)
    
    def remove_external_connection(self, connection_name: str) -> Tuple[bool, str]:
        """Remove an external database connection"""
        return self.external_manager.remove_connection(connection_name)
    
    def get_external_connection(self, name: str) -> Optional[DatabaseConnection]:
        """Get external connection details"""
        return self.external_manager.get_connection(name)
    
    def list_external_connections(self) -> List[DatabaseConnection]:
        """List all external connections"""
        return self.external_manager.list_connections()
    
    def refresh_all_database_info(self):
        """Refresh cached information for all databases"""
        try:
            # Clear SQLite cache
            self.sqlite_databases.clear()
            
            # Reload external connections
            self.external_manager.load_connections()
            
            logger.info("Database information refreshed")
            
        except Exception as e:
            logger.error(f"Error refreshing database info: {str(e)}")

# Example usage
if __name__ == "__main__":
    adapter = UniversalDatabaseAdapter()
    
    # Get all databases
    databases = adapter.get_all_databases()
    print(f"Found {len(databases)} databases:")
    
    for db_name, db_info in databases.items():
        db_type = db_info['type']
        is_external = "External" if db_info['is_external'] else "Local"
        table_count = len(db_info['tables'])
        print(f"  {db_name}: {db_type} ({is_external}) - {table_count} tables")
    
    # Get external connections summary
    ext_summary = adapter.get_external_connections_summary()
    print(f"\nExternal connections: {ext_summary['total_connections']}")