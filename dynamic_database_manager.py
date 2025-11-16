#!/usr/bin/env python3

"""
Dynamic Database Manager
Comprehensive database management system with full CRUD operations for all databases
"""

import sqlite3
import pandas as pd
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
from datetime import datetime
import shutil
import threading
import time

class DynamicDatabaseManager:
    """
    A comprehensive database manager that provides dynamic access to all databases,
    tables, and records with real-time updates to the AI system
    """
    
    def __init__(self, base_path: str = "database"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # Cache for database schemas and metadata
        self.schema_cache = {}
        self.metadata_cache = {}
        
        # Change tracking for AI system updates
        self.change_log = []
        
        # Setup logging
        self.setup_logging()
        
        # Initialize system
        self.refresh_all_database_info()
    
    def setup_logging(self):
        """Setup logging for database operations"""
        log_file = self.base_path / "database_operations.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log_change(self, operation: str, database: str, table: str = None, details: dict = None):
        """Log database changes for AI system updates"""
        change_record = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'database': database,
            'table': table,
            'details': details or {}
        }
        self.change_log.append(change_record)
        self.logger.info(f"Database change: {operation} on {database}.{table if table else 'DATABASE'}")
    
    def get_all_databases(self) -> Dict[str, Dict[str, Any]]:
        """Discover and return all available databases with metadata"""
        databases = {}
        
        # Scan database directory for .db files
        for db_file in self.base_path.glob("*.db"):
            db_name = db_file.stem
            databases[db_name] = {
                'path': str(db_file),
                'size': db_file.stat().st_size,
                'modified': datetime.fromtimestamp(db_file.stat().st_mtime).isoformat(),
                'tables': self.get_tables_in_database(db_name)
            }
        
        return databases
    
    def get_tables_in_database(self, database_name: str) -> List[Dict[str, Any]]:
        """Get all tables in a specific database with their metadata"""
        db_path = self.base_path / f"{database_name}.db"
        
        if not db_path.exists():
            return []
        
        tables = []
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)
                
                for (table_name,) in cursor.fetchall():
                    # Get table info
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    
                    table_info = {
                        'name': table_name,
                        'columns': [
                            {
                                'id': col[0],
                                'name': col[1],
                                'type': col[2],
                                'not_null': col[3],
                                'default_value': col[4],
                                'primary_key': col[5]
                            }
                            for col in columns
                        ],
                        'row_count': row_count
                    }
                    tables.append(table_info)
                    
        except Exception as e:
            self.logger.error(f"Error reading tables from {database_name}: {e}")
        
        return tables
    
    def view_data(self, database_name: str, table_name: str, 
                  limit: int = 100, offset: int = 0,
                  where_clause: str = None,
                  order_by: str = None) -> Dict[str, Any]:
        """
        View data from any table in any database with flexible filtering
        """
        try:
            db_path = self.base_path / f"{database_name}.db"
            
            if not db_path.exists():
                return {'success': False, 'error': f'Database {database_name} not found'}
            
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Build query
                query = f"SELECT * FROM {table_name}"
                params = []
                
                if where_clause:
                    query += f" WHERE {where_clause}"
                
                if order_by:
                    query += f" ORDER BY {order_by}"
                
                query += f" LIMIT {limit} OFFSET {offset}"
                
                # Execute query
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                data = [dict(row) for row in rows]
                
                # Get total count for pagination
                count_query = f"SELECT COUNT(*) FROM {table_name}"
                if where_clause:
                    count_query += f" WHERE {where_clause}"
                
                total_rows = conn.execute(count_query).fetchone()[0]
                
                return {
                    'success': True,
                    'data': data,
                    'total_rows': total_rows,
                    'current_page': (offset // limit) + 1,
                    'total_pages': (total_rows + limit - 1) // limit,
                    'columns': [description[0] for description in cursor.description] if rows else []
                }
                
        except Exception as e:
            error_msg = f"Error viewing data from {database_name}.{table_name}: {e}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def add_record(self, database_name: str, table_name: str, 
                   record_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new record to any table in any database
        """
        try:
            db_path = self.base_path / f"{database_name}.db"
            
            if not db_path.exists():
                return {'success': False, 'error': f'Database {database_name} not found'}
            
            with sqlite3.connect(db_path) as conn:
                # Get table schema to validate data
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = cursor.fetchall()
                
                # Build insert query
                columns = list(record_data.keys())
                placeholders = ', '.join(['?' for _ in columns])
                values = list(record_data.values())
                
                query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                
                cursor.execute(query, values)
                conn.commit()
                
                inserted_id = cursor.lastrowid
                
                # Log the change
                self.log_change('INSERT', database_name, table_name, {
                    'record_id': inserted_id,
                    'data': record_data
                })
                
                return {
                    'success': True,
                    'message': f'Record added successfully to {database_name}.{table_name}',
                    'inserted_id': inserted_id
                }
                
        except Exception as e:
            error_msg = f"Error adding record to {database_name}.{table_name}: {e}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def update_record(self, database_name: str, table_name: str,
                     record_id: Any, record_data: Dict[str, Any],
                     id_column: str = 'id') -> Dict[str, Any]:
        """
        Update an existing record in any table
        """
        try:
            db_path = self.base_path / f"{database_name}.db"
            
            if not db_path.exists():
                return {'success': False, 'error': f'Database {database_name} not found'}
            
            with sqlite3.connect(db_path) as conn:
                # Build update query
                set_clauses = [f"{col} = ?" for col in record_data.keys()]
                values = list(record_data.values()) + [record_id]
                
                query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {id_column} = ?"
                
                cursor = conn.cursor()
                cursor.execute(query, values)
                conn.commit()
                
                affected_rows = cursor.rowcount
                
                # Log the change
                self.log_change('UPDATE', database_name, table_name, {
                    'record_id': record_id,
                    'data': record_data,
                    'affected_rows': affected_rows
                })
                
                return {
                    'success': True,
                    'message': f'Record updated successfully in {database_name}.{table_name}',
                    'affected_rows': affected_rows
                }
                
        except Exception as e:
            error_msg = f"Error updating record in {database_name}.{table_name}: {e}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def delete_record(self, database_name: str, table_name: str,
                     record_id: Any, id_column: str = 'id') -> Dict[str, Any]:
        """
        Delete a specific record from any table
        """
        try:
            db_path = self.base_path / f"{database_name}.db"
            
            if not db_path.exists():
                return {'success': False, 'error': f'Database {database_name} not found'}
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Get record before deletion for logging
                cursor.execute(f"SELECT * FROM {table_name} WHERE {id_column} = ?", (record_id,))
                deleted_record = cursor.fetchone()
                
                # Delete record
                cursor.execute(f"DELETE FROM {table_name} WHERE {id_column} = ?", (record_id,))
                conn.commit()
                
                affected_rows = cursor.rowcount
                
                # Log the change
                self.log_change('DELETE_RECORD', database_name, table_name, {
                    'record_id': record_id,
                    'deleted_record': dict(deleted_record) if deleted_record else None,
                    'affected_rows': affected_rows
                })
                
                return {
                    'success': True,
                    'message': f'Record deleted successfully from {database_name}.{table_name}',
                    'affected_rows': affected_rows
                }
                
        except Exception as e:
            error_msg = f"Error deleting record from {database_name}.{table_name}: {e}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def delete_column(self, database_name: str, table_name: str, 
                     column_name: str) -> Dict[str, Any]:
        """
        Delete a specific column from a table
        Note: SQLite doesn't support DROP COLUMN, so we recreate the table
        """
        try:
            db_path = self.base_path / f"{database_name}.db"
            
            if not db_path.exists():
                return {'success': False, 'error': f'Database {database_name} not found'}
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Get current table schema
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                # Filter out the column to delete
                remaining_columns = [col for col in columns if col[1] != column_name]
                
                if len(remaining_columns) == len(columns):
                    return {'success': False, 'error': f'Column {column_name} not found in table'}
                
                # Create new table schema
                column_definitions = []
                for col in remaining_columns:
                    definition = f"{col[1]} {col[2]}"
                    if col[3]:  # NOT NULL
                        definition += " NOT NULL"
                    if col[4] is not None:  # DEFAULT
                        definition += f" DEFAULT {col[4]}"
                    if col[5]:  # PRIMARY KEY
                        definition += " PRIMARY KEY"
                    column_definitions.append(definition)
                
                # Execute table recreation
                temp_table = f"{table_name}_temp"
                column_names = [col[1] for col in remaining_columns]
                
                # Create temporary table
                create_sql = f"CREATE TABLE {temp_table} ({', '.join(column_definitions)})"
                cursor.execute(create_sql)
                
                # Copy data (excluding the deleted column)
                insert_sql = f"INSERT INTO {temp_table} SELECT {', '.join(column_names)} FROM {table_name}"
                cursor.execute(insert_sql)
                
                # Drop original table and rename temp table
                cursor.execute(f"DROP TABLE {table_name}")
                cursor.execute(f"ALTER TABLE {temp_table} RENAME TO {table_name}")
                
                conn.commit()
                
                # Log the change
                self.log_change('DELETE_COLUMN', database_name, table_name, {
                    'column_name': column_name,
                    'remaining_columns': column_names
                })
                
                return {
                    'success': True,
                    'message': f'Column {column_name} deleted successfully from {database_name}.{table_name}'
                }
                
        except Exception as e:
            error_msg = f"Error deleting column from {database_name}.{table_name}: {e}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def move_table_between_databases(self, source_db: str, target_db: str, 
                                   table_name: str) -> Dict[str, Any]:
        """
        Move a table from one database to another
        """
        try:
            source_path = self.base_path / f"{source_db}.db"
            target_path = self.base_path / f"{target_db}.db"
            
            if not source_path.exists():
                return {'success': False, 'error': f'Source database {source_db} not found'}
            
            # Create target database if it doesn't exist
            if not target_path.exists():
                with sqlite3.connect(target_path) as conn:
                    pass  # Just create the file
            
            # Attach databases and copy table
            with sqlite3.connect(source_path) as conn:
                cursor = conn.cursor()
                
                # Attach target database
                cursor.execute(f"ATTACH DATABASE '{target_path}' AS target_db")
                
                # Get table schema
                cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                create_sql = cursor.fetchone()
                
                if not create_sql:
                    return {'success': False, 'error': f'Table {table_name} not found in source database'}
                
                # Create table in target database
                cursor.execute(create_sql[0].replace(f"CREATE TABLE {table_name}", 
                                                    f"CREATE TABLE target_db.{table_name}"))
                
                # Copy data
                cursor.execute(f"INSERT INTO target_db.{table_name} SELECT * FROM {table_name}")
                
                # Drop from source
                cursor.execute(f"DROP TABLE {table_name}")
                
                conn.commit()
                
                # Log the change
                self.log_change('MOVE_TABLE', source_db, table_name, {
                    'target_database': target_db,
                    'source_database': source_db
                })
                
                return {
                    'success': True,
                    'message': f'Table {table_name} moved successfully from {source_db} to {target_db}'
                }
                
        except Exception as e:
            error_msg = f"Error moving table {table_name} from {source_db} to {target_db}: {e}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def execute_custom_query(self, database_name: str, query: str) -> Dict[str, Any]:
        """
        Execute a custom SQL query on any database
        """
        try:
            db_path = self.base_path / f"{database_name}.db"
            
            if not db_path.exists():
                return {'success': False, 'error': f'Database {database_name} not found'}
            
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Determine if it's a SELECT query or modification query
                query_upper = query.upper().strip()
                is_select = query_upper.startswith('SELECT') or query_upper.startswith('WITH')
                
                cursor = conn.cursor()
                cursor.execute(query)
                
                if is_select:
                    rows = cursor.fetchall()
                    data = [dict(row) for row in rows]
                    columns = [description[0] for description in cursor.description] if rows else []
                    
                    result = {
                        'success': True,
                        'query_type': 'SELECT',
                        'data': data,
                        'row_count': len(data),
                        'columns': columns
                    }
                else:
                    conn.commit()
                    affected_rows = cursor.rowcount
                    
                    # Log modification queries
                    self.log_change('CUSTOM_QUERY', database_name, None, {
                        'query': query,
                        'affected_rows': affected_rows
                    })
                    
                    result = {
                        'success': True,
                        'query_type': 'MODIFICATION',
                        'affected_rows': affected_rows,
                        'message': f'Query executed successfully. {affected_rows} rows affected.'
                    }
                
                return result
                
        except Exception as e:
            error_msg = f"Error executing custom query on {database_name}: {e}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg, 'query': query}
    
    def refresh_all_database_info(self):
        """
        Refresh cached information for all databases
        """
        self.schema_cache.clear()
        self.metadata_cache.clear()
        
        databases = self.get_all_databases()
        
        for db_name, db_info in databases.items():
            self.schema_cache[db_name] = db_info['tables']
            self.metadata_cache[db_name] = {
                'size': db_info['size'],
                'modified': db_info['modified'],
                'table_count': len(db_info['tables'])
            }
        
        self.logger.info(f"Refreshed info for {len(databases)} databases")
    
    def get_change_log(self, since: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent database changes for AI system updates
        """
        changes = self.change_log
        
        if since:
            # Filter changes since a specific timestamp
            changes = [c for c in changes if c['timestamp'] >= since]
        
        return changes[-limit:] if limit else changes