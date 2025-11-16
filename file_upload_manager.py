"""
File Upload Manager for SQL Agent
Handles CSV and Excel file uploads to create dynamic databases
"""

import pandas as pd
import sqlite3
import streamlit as st
from pathlib import Path
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import io
from csv_reader_utils import robust_read_csv, get_csv_info


class FileUploadManager:
    """Handles file uploads and database creation from CSV/Excel files"""
    
    def __init__(self, db_path: str = "database/sql_agent.db"):
        """Initialize the FileUploadManager
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
    
    def set_target_database(self, db_path: str):
        """Set the target database for uploads
        
        Args:
            db_path: Path to the target database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
    
    def create_new_database(self, db_name: str) -> str:
        """Create a new database file
        
        Args:
            db_name: Name for the new database (without .db extension)
            
        Returns:
            Path to the created database file
        """
        # Sanitize database name
        db_name = re.sub(r'[^a-zA-Z0-9_-]', '_', db_name)
        db_name = re.sub(r'_+', '_', db_name).strip('_')
        
        if not db_name:
            db_name = f"database_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Ensure .db extension
        if not db_name.endswith('.db'):
            db_name += '.db'
        
        # Create database file path
        db_path = Path("database") / db_name
        db_path.parent.mkdir(exist_ok=True)
        
        # Create the database file
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE IF NOT EXISTS _metadata (created_at TEXT, description TEXT)")
        conn.execute("INSERT INTO _metadata VALUES (?, ?)", 
                    (datetime.now().isoformat(), f"Database created from file upload"))
        conn.commit()
        conn.close()
        
        return str(db_path)
    
    def create_database_with_files(self, db_name: str, uploaded_files: List) -> Tuple[str, List[Dict]]:
        """Create a new database and populate it with uploaded files
        
        Args:
            db_name: Name for the new database (without .db extension)
            uploaded_files: List of uploaded file objects
            
        Returns:
            Tuple of (database_path, upload_results)
        """
        # First create the database
        db_path = self.create_new_database(db_name)
        
        # Set it as the target
        self.set_target_database(db_path)
        
        # Process all uploaded files
        all_results = []
        
        for uploaded_file in uploaded_files:
            try:
                # Determine file type and process accordingly
                if uploaded_file.name.lower().endswith('.csv'):
                    results = self.process_csv_file(uploaded_file)
                    all_results.extend(results if isinstance(results, list) else [results])
                    
                elif uploaded_file.name.lower().endswith(('.xlsx', '.xls')):
                    results = self.process_excel_file(uploaded_file)
                    all_results.extend(results if isinstance(results, list) else [results])
                    
                else:
                    all_results.append({
                        'success': False,
                        'message': f'Unsupported file type: {uploaded_file.name}',
                        'file_name': uploaded_file.name,
                        'table_name': None,
                        'rows': 0,
                        'columns': 0
                    })
                    
            except Exception as e:
                all_results.append({
                    'success': False,
                    'message': f'Error processing {uploaded_file.name}: {str(e)}',
                    'file_name': uploaded_file.name,
                    'table_name': None,
                    'rows': 0,
                    'columns': 0
                })
        
        return db_path, all_results
    
    def get_available_databases(self) -> Dict[str, str]:
        """Get list of available databases
        
        Returns:
            Dictionary of database display name -> file path
        """
        database_dir = Path("database")
        if not database_dir.exists():
            return {}
        
        databases = {}
        for db_file in database_dir.glob("*.db"):
            # Use filename without extension as display name
            display_name = db_file.stem
            if display_name == "sql_agent":
                display_name = "Main Database"
            databases[display_name] = str(db_file)
        
        return databases
    
    def get_db_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def sanitize_table_name(self, name: str) -> str:
        """Sanitize table name to be SQL-safe
        
        Args:
            name: Original name (from file or sheet name)
            
        Returns:
            SQL-safe table name
        """
        # Remove file extension
        name = re.sub(r'\.[^.]+$', '', name)
        
        # Replace spaces and special characters with underscores
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        
        # Remove consecutive underscores
        name = re.sub(r'_+', '_', name)
        
        # Remove leading/trailing underscores
        name = name.strip('_')
        
        # Ensure it doesn't start with a number
        if name and name[0].isdigit():
            name = f"table_{name}"
        
        # Ensure it's not empty
        if not name:
            name = "unnamed_table"
        
        return name.lower()
    
    def get_unique_table_name(self, base_name: str) -> str:
        """Get a unique table name by appending numbers if needed
        
        Args:
            base_name: Base table name
            
        Returns:
            Unique table name
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Get existing table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0].lower() for row in cursor.fetchall()}
        conn.close()
        
        # If base name is unique, use it
        if base_name not in existing_tables:
            return base_name
        
        # Otherwise, append numbers until we find a unique name
        counter = 1
        while f"{base_name}_{counter}" in existing_tables:
            counter += 1
        
        return f"{base_name}_{counter}"
    
    def infer_column_type(self, series: pd.Series) -> str:
        """Infer SQL column type from pandas Series
        
        Args:
            series: Pandas Series to analyze
            
        Returns:
            SQL column type string
        """
        # Handle completely null columns
        if series.isnull().all():
            return "TEXT"
        
        # Drop null values for type inference
        non_null_series = series.dropna()
        
        if len(non_null_series) == 0:
            return "TEXT"
        
        # Check for boolean
        if non_null_series.dtype == 'bool':
            return "BOOLEAN"
        
        # Check for integer
        if pd.api.types.is_integer_dtype(non_null_series):
            return "INTEGER"
        
        # Check for float
        if pd.api.types.is_numeric_dtype(non_null_series):
            return "REAL"
        
        # Check for datetime
        if pd.api.types.is_datetime64_any_dtype(non_null_series):
            return "DATE"
        
        # Try to parse as datetime
        if non_null_series.dtype == 'object':
            sample = non_null_series.iloc[0] if len(non_null_series) > 0 else ""
            if isinstance(sample, str):
                # Try common date formats
                date_formats = [
                    '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', 
                    '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S'
                ]
                for fmt in date_formats:
                    try:
                        pd.to_datetime(non_null_series.iloc[:min(5, len(non_null_series))], format=fmt)
                        return "DATE"
                    except:
                        continue
        
        # Default to TEXT
        return "TEXT"
    
    def create_table_from_dataframe(self, df: pd.DataFrame, table_name: str, replace: bool = False) -> Tuple[bool, str]:
        """Create a table from a DataFrame
        
        Args:
            df: DataFrame to create table from
            table_name: Name of the table to create
            replace: Whether to replace existing table
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Validation checks
            if df is None:
                return False, "DataFrame is None"
            
            if df.empty:
                return False, "DataFrame is empty (no rows found)"
            
            if len(df.columns) == 0:
                return False, "DataFrame has no columns"
            
            # Check for completely empty DataFrame
            if df.isnull().all().all():
                return False, "DataFrame contains only null values"
            
            # Clean column names
            original_cols = df.columns.tolist()
            df.columns = [self.sanitize_table_name(str(col)) for col in df.columns]
            
            # Validate that we have valid column names after sanitization
            if not all(col.strip() for col in df.columns):
                return False, "Some columns have invalid names after sanitization"
            
            # Handle duplicate column names
            seen_cols = {}
            new_cols = []
            for col in df.columns:
                if col in seen_cols:
                    seen_cols[col] += 1
                    new_cols.append(f"{col}_{seen_cols[col]}")
                else:
                    seen_cols[col] = 0
                    new_cols.append(col)
            df.columns = new_cols
            
            # Check for reserved SQL keywords and prefix them
            reserved_keywords = {
                'select', 'from', 'where', 'insert', 'update', 'delete', 'create', 'drop', 
                'alter', 'table', 'index', 'view', 'grant', 'revoke', 'commit', 'rollback',
                'order', 'by', 'group', 'having', 'join', 'inner', 'left', 'right', 'outer',
                'union', 'intersect', 'except', 'case', 'when', 'then', 'else', 'end',
                'and', 'or', 'not', 'in', 'exists', 'between', 'like', 'is', 'null'
            }
            
            df.columns = [f"col_{col}" if col.lower() in reserved_keywords else col for col in df.columns]
            
            # Infer column types
            column_definitions = []
            for col in df.columns:
                col_type = self.infer_column_type(df[col])
                column_definitions.append(f"{col} {col_type}")
            
            # Create table
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Drop table if replacing
            if replace:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            
            # Create table SQL
            create_sql = f"""
            CREATE TABLE {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {', '.join(column_definitions)}
            )
            """
            
            cursor.execute(create_sql)
            
            # Insert data
            placeholders = ', '.join(['?' for _ in range(len(df.columns) + 1)])  # +1 for id column
            insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
            
            # Prepare data for insertion
            for _, row in df.iterrows():
                values: List[Any] = [None]  # Auto-increment id
                for col in df.columns:
                    value = row[col]
                    
                    # Handle different data types
                    if pd.isna(value):
                        values.append(None)
                    elif isinstance(value, (pd.Timestamp, datetime)):
                        values.append(value.strftime('%Y-%m-%d'))
                    else:
                        values.append(value)
                
                cursor.execute(insert_sql, values)
            
            conn.commit()
            conn.close()
            
            return True, f"Table '{table_name}' created successfully with {len(df)} records"
        
        except Exception as e:
            return False, f"Error creating table: {str(e)}"
    
    def process_csv_file(self, uploaded_file: Any, table_name_override: Optional[str] = None) -> List[Dict]:
        """Process a CSV file and create database table(s)
        
        Args:
            uploaded_file: Streamlit uploaded file object
            table_name_override: Optional custom table name
            
        Returns:
            List of results for each table created
        """
        results = []
        
        try:
            # Read CSV file using robust reader
            df = robust_read_csv(uploaded_file)
            
            if df is None:
                results.append({
                    'file_name': uploaded_file.name,
                    'sheet_name': None,
                    'table_name': None,
                    'success': False,
                    'message': 'Could not read CSV file - invalid format, encoding, or delimiter',
                    'rows': 0,
                    'columns': 0
                })
                return results
            
            # Determine table name
            if table_name_override:
                table_name = self.sanitize_table_name(table_name_override)
            else:
                table_name = self.sanitize_table_name(uploaded_file.name)
            
            # Ensure unique table name
            table_name = self.get_unique_table_name(table_name)
            
            # Create table
            success, message = self.create_table_from_dataframe(df, table_name)
            
            results.append({
                'file_name': uploaded_file.name,
                'sheet_name': None,
                'table_name': table_name,
                'success': success,
                'message': message,
                'rows': len(df) if success else 0,
                'columns': len(df.columns) if success else 0
            })
        
        except Exception as e:
            results.append({
                'file_name': uploaded_file.name,
                'sheet_name': None,
                'table_name': None,
                'success': False,
                'message': f"Error processing CSV: {str(e)}",
                'rows': 0,
                'columns': 0
            })
        
        return results
    
    def process_excel_file(self, uploaded_file: Any, table_name_override: Optional[str] = None) -> List[Dict]:
        """Process an Excel file and create database table(s) from each sheet
        
        Args:
            uploaded_file: Streamlit uploaded file object
            table_name_override: Optional custom base table name
            
        Returns:
            List of results for each sheet/table created
        """
        results = []
        
        try:
            # Read all sheets from Excel file
            excel_file = pd.ExcelFile(uploaded_file)
            sheet_names = excel_file.sheet_names
            
            for sheet_name in sheet_names:
                try:
                    # Read sheet data
                    df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
                    
                    # Determine table name
                    if table_name_override:
                        if len(sheet_names) == 1:
                            # Single sheet, use override name directly
                            table_name = self.sanitize_table_name(table_name_override)
                        else:
                            # Multiple sheets, append sheet name
                            base_name = self.sanitize_table_name(table_name_override)
                            sheet_suffix = self.sanitize_table_name(str(sheet_name))
                            table_name = f"{base_name}_{sheet_suffix}"
                    else:
                        # Use file name and sheet name
                        file_base = self.sanitize_table_name(uploaded_file.name)
                        sheet_suffix = self.sanitize_table_name(str(sheet_name))
                        table_name = f"{file_base}_{sheet_suffix}" if len(sheet_names) > 1 else file_base
                    
                    # Ensure unique table name
                    table_name = self.get_unique_table_name(table_name)
                    
                    # Create table
                    success, message = self.create_table_from_dataframe(df, table_name)
                    
                    results.append({
                        'file_name': uploaded_file.name,
                        'sheet_name': sheet_name,
                        'table_name': table_name,
                        'success': success,
                        'message': message,
                        'rows': len(df) if success else 0,
                        'columns': len(df.columns) if success else 0
                    })
                
                except Exception as e:
                    results.append({
                        'file_name': uploaded_file.name,
                        'sheet_name': sheet_name,
                        'table_name': None,
                        'success': False,
                        'message': f"Error processing sheet '{sheet_name}': {str(e)}",
                        'rows': 0,
                        'columns': 0
                    })
        
        except Exception as e:
            results.append({
                'file_name': uploaded_file.name,
                'sheet_name': None,
                'table_name': None,
                'success': False,
                'message': f"Error reading Excel file: {str(e)}",
                'rows': 0,
                'columns': 0
            })
        
        return results
    
    def process_uploaded_files(self, uploaded_files: List[Any], table_name_overrides: Optional[Dict[str, str]] = None) -> List[Dict]:
        """Process multiple uploaded files
        
        Args:
            uploaded_files: List of Streamlit uploaded file objects
            table_name_overrides: Optional dict mapping file names to custom table names
            
        Returns:
            List of results for all files processed
        """
        all_results = []
        table_name_overrides = table_name_overrides or {}
        
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            table_override = table_name_overrides.get(file_name)
            
            # Reset file pointer
            uploaded_file.seek(0)
            
            # Process based on file type
            if file_name.lower().endswith('.csv'):
                results = self.process_csv_file(uploaded_file, table_override)
            elif file_name.lower().endswith(('.xlsx', '.xls')):
                results = self.process_excel_file(uploaded_file, table_override)
            else:
                results = [{
                    'file_name': file_name,
                    'sheet_name': None,
                    'table_name': None,
                    'success': False,
                    'message': f"Unsupported file type: {file_name}",
                    'rows': 0,
                    'columns': 0
                }]
            
            all_results.extend(results)
        
        return all_results
    
    def get_database_tables(self) -> List[str]:
        """Get list of all tables in the database
        
        Returns:
            List of table names
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            return tables
        except Exception:
            return []
    
    def get_table_info(self, table_name: str) -> Dict:
        """Get information about a specific table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with table information
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            schema = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'name': table_name,
                'columns': len(schema),
                'rows': row_count,
                'schema': schema
            }
        except Exception as e:
            return {
                'name': table_name,
                'error': str(e)
            }