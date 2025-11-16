import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class MultiDatabaseManager:
    def __init__(self, config_path: str = "database/db_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(exist_ok=True)
        self.databases = self._load_config()
        self._ensure_default_database()
    
    def _load_config(self) -> Dict[str, str]:
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    return config.get('databases', {})
            except Exception:
                return {}
        return {}
    
    def _save_config(self):
        try:
            config = {
                'databases': self.databases,
                'default_database': 'main'
            }
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass
    
    def _ensure_default_database(self):
        default_db_path = "database/sql_agent.db"
        
        if 'main' not in self.databases:
            self.databases['main'] = default_db_path
        
        self._discover_databases()
        
        db_path = Path(self.databases['main'])
        if not db_path.exists():
            db_path.parent.mkdir(exist_ok=True)
            conn = sqlite3.connect(db_path)
            conn.close()
            self._save_config()
    
    def _discover_databases(self):
        database_dir = Path("database")
        if not database_dir.exists():
            return
        
        for db_file in database_dir.glob("*.db"):
            db_path = str(db_file)
            
            if db_file.name == "sql_agent.db":
                db_name = "main"
            else:
                db_name = db_file.stem
            
            if db_name not in self.databases:
                self.databases[db_name] = db_path
    
    def get_databases(self) -> Dict[str, str]:
        return self.databases.copy()
    
    def get_database_path(self, name: str) -> Optional[str]:
        return self.databases.get(name)
    
    def execute_query_on_database(self, db_name: str, query: str) -> Dict[str, Any]:
        if db_name not in self.databases:
            return {"success": False, "error": "Database not found"}
        
        try:
            db_path = self.databases[db_name]
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                conn.close()
                
                return {
                    "success": True,
                    "data": results,
                    "columns": columns,
                    "row_count": len(results),
                    "database": db_name
                }
            else:
                conn.commit()
                rows_affected = cursor.rowcount
                conn.close()
                
                return {
                    "success": True,
                    "rows_affected": rows_affected,
                    "database": db_name
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "database": db_name
            }
    
    def refresh_database_info(self):
        """Refresh database information for all databases"""
        # Remove non-existent databases
        to_remove = []
        for db_name, db_path in self.databases.items():
            if not Path(db_path).exists() and db_name != 'main':
                to_remove.append(db_name)
        
        for db_name in to_remove:
            del self.databases[db_name]
        
        # Ensure main database exists
        self._ensure_default_database()
        self._save_config()
    
    def create_database_from_upload(self, name: str, upload_results: List[Dict]) -> str:
        """Create a new database from file upload results
        
        Args:
            name: Name for the new database
            upload_results: Results from file upload processing
            
        Returns:
            Path to the created database
        """
        # Create new database path
        db_path = f"database/{name}.db"
        db_full_path = Path(db_path)
        
        # If database already exists, add number suffix
        counter = 1
        while db_full_path.exists():
            db_path = f"database/{name}_{counter}.db"
            db_full_path = Path(db_path)
            counter += 1
        
        # Create directory
        db_full_path.parent.mkdir(exist_ok=True)
        
        # Add to configuration
        self.databases[name] = str(db_full_path)
        self._save_config()
        
        return str(db_full_path)
    
    def get_database_info(self, name: str) -> Dict[str, Any]:
        """Get detailed information about a database
        
        Args:
            name: Database name
            
        Returns:
            Database information dictionary
        """
        if name not in self.databases:
            return {"error": "Database not found"}
        
        try:
            db_path = self.databases[name]
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get total record count
            total_records = 0
            table_info = {}
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                total_records += count
                
                # Get column info
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                
                table_info[table] = {
                    "rows": count,
                    "columns": len(columns),
                    "column_details": [{"name": col[1], "type": col[2]} for col in columns]
                }
            
            conn.close()
            
            # Get file size
            file_size = Path(db_path).stat().st_size if Path(db_path).exists() else 0
            
            return {
                "name": name,
                "path": db_path,
                "tables": tables,
                "table_count": len(tables),
                "total_records": total_records,
                "file_size": file_size,
                "table_info": table_info
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_all_tables_across_databases(self) -> Dict[str, List[str]]:
        """Get all tables across all databases
        
        Returns:
            Dictionary of database_name -> list of tables
        """
        all_tables = {}
        
        for db_name in self.databases:
            try:
                db_path = self.databases[db_name]
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                tables = [row[0] for row in cursor.fetchall()]
                all_tables[db_name] = tables
                
                conn.close()
            except Exception as e:
                print(f"Error getting tables from {db_name}: {e}")
                all_tables[db_name] = []
        
        return all_tables
    
    def refresh_configuration(self):
        """Refresh the database configuration by scanning for new database files"""
        self._discover_databases()
        self._save_config()
    
    def get_schema_for_databases(self, db_names: List[str]) -> str:
        """Get combined schema information for multiple databases
        
        Args:
            db_names: List of database names
            
        Returns:
            Combined schema information string
        """
        schema_info = "MULTI-DATABASE SCHEMA:\n\n"
        
        for db_name in db_names:
            if db_name not in self.databases:
                continue
                
            try:
                db_path = self.databases[db_name]
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                schema_info += f"DATABASE: {db_name} ({db_path})\n"
                schema_info += "=" * 50 + "\n"
                
                # Get tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    schema_info += f"Table: {db_name}.{table}\n"
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    
                    for col in columns:
                        col_name, col_type, not_null, default, pk = col[1], col[2], col[3], col[4], col[5]
                        constraints = []
                        if pk:
                            constraints.append("PRIMARY KEY")
                        if not_null:
                            constraints.append("NOT NULL")
                        if default:
                            constraints.append(f"DEFAULT {default}")
                        
                        constraint_str = f" ({', '.join(constraints)})" if constraints else ""
                        schema_info += f"  - {col_name}: {col_type}{constraint_str}\n"
                    
                    # Get sample data (first 2 rows to keep it compact)
                    cursor.execute(f"SELECT * FROM {table} LIMIT 2")
                    sample_data = cursor.fetchall()
                    if sample_data:
                        schema_info += f"  Sample data: {sample_data}\n"
                    
                    schema_info += "\n"
                
                conn.close()
                schema_info += "\n"
                
            except Exception as e:
                schema_info += f"Error reading database {db_name}: {str(e)}\n\n"
        
        return schema_info
