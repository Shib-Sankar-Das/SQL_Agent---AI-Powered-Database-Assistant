"""
Enhanced SQL Agent with Multi-Database Support
Extends the original SQL Agent to work with multiple databases and table selection
"""

from sql_agent import SQLAgent
from multi_database_manager import MultiDatabaseManager
from typing import Dict, List, Any, Optional
import sqlite3
from pathlib import Path


class EnhancedSQLAgent(SQLAgent):
    """Enhanced SQL Agent with multi-database and table selection support"""
    
    def __init__(self, db_manager_or_path=None):
        """Initialize the Enhanced SQL Agent
        
        Args:
            db_manager_or_path: Either a MultiDatabaseManager instance or a path to the primary SQLite database (optional)
        """
        # Handle different input types
        if isinstance(db_manager_or_path, MultiDatabaseManager):
            self.multi_db_manager = db_manager_or_path
            db_path = self.multi_db_manager.get_database_path('main')
        elif isinstance(db_manager_or_path, str):
            self.multi_db_manager = MultiDatabaseManager()
            db_path = db_manager_or_path
        else:
            # Default initialization
            self.multi_db_manager = MultiDatabaseManager()
            db_path = self.multi_db_manager.get_database_path('main')
        
        # Ensure db_path is not None
        if db_path is None:
            raise ValueError("Could not determine database path. Please ensure databases are available.")
        
        # Initialize parent SQL Agent
        super().__init__(db_path)
        
        # Track current database context
        self.current_databases = ['main']
        self.current_tables = []
    
    def refresh_all_schemas(self):
        """Refresh schema information for all databases"""
        self.multi_db_manager.refresh_database_info()
        self.refresh_schema()
    
    def auto_detect_databases(self, question: str) -> List[str]:
        """Automatically detect which databases to query based on keywords in the question
        
        Args:
            question: Natural language question
            
        Returns:
            List of database names that likely contain relevant data
        """
        question_lower = question.lower()
        detected_databases = []
        
        # Get available databases dynamically
        available_dbs = self.multi_db_manager.get_databases()
        
        # Keyword patterns for database detection
        database_keywords = {}
        
        # Add keywords for each available database based on actual content and names
        if 'earthquake' in available_dbs:
            database_keywords['earthquake'] = ['earthquake', 'seismic', 'magnitude', 'tsunami', 'geological', 'tremor', 'quake', 'disaster', 'natural disaster', 'richter']
        
        if 'Crop_recommendation' in available_dbs:
            database_keywords['Crop_recommendation'] = ['crop', 'crops', 'farming', 'agriculture', 'recommendation', 'plant', 'grow', 'harvest', 'soil', 'fertilizer', 'irrigation', 'seeds', 'yield', 'rice', 'wheat', 'corn', 'barley']
        
        if 'Customer_Churn_prediction' in available_dbs:
            database_keywords['Customer_Churn_prediction'] = ['customer', 'churn', 'retention', 'prediction', 'subscription', 'cancel', 'loyalty', 'attrition', 'clients', 'users', 'subscribers']
        
        if 'Cardict_Arrest' in available_dbs:
            database_keywords['Cardict_Arrest'] = ['cardiac', 'heart', 'arrest', 'cardiovascular', 'medical', 'cardiact', 'cardict', 'heart attack', 'coronary', 'arrhythmia', 'cardiology', 'ecg', 'ekg']
        
        if 'main' in available_dbs:
            database_keywords['main'] = [
                # PCOS related
                'pcos', 'patient', 'health', 'syndrome', 'ovarian', 'hormone', 'polycystic', 'infertility',
                # Sales and business related
                'sales', 'revenue', 'profit', 'orders', 'products', 'company', 'business', 'offers',
                # Employee related
                'employees', 'staff', 'workers', 'human resources', 'hr'
            ]
        
        # Check for keyword matches
        for db_name, keywords in database_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                # Verify database exists
                if db_name in available_dbs:
                    detected_databases.append(db_name)
        
        # If no specific database detected, return main as default
        if not detected_databases:
            detected_databases = ['main']
            
        return detected_databases
    
    def set_database_context(self, database_names: List[str]):
        """Set the current database context for queries
        
        Args:
            database_names: List of database names to include in context
        """
        # Validate database names
        available_dbs = self.multi_db_manager.get_databases()
        valid_db_names = [db for db in database_names if db in available_dbs]
        
        if valid_db_names:
            self.current_databases = valid_db_names
            
            # If only one database, update the agent's primary database
            if len(valid_db_names) == 1:
                db_path = self.multi_db_manager.get_database_path(valid_db_names[0])
                if db_path and Path(db_path).exists():
                    self.db_path = Path(db_path)
                    self.refresh_schema()
        else:
            # Fallback to main database
            self.current_databases = ['main']
    
    def set_table_context(self, table_names: List[str]):
        """Set the current table context for queries
        
        Args:
            table_names: List of table names to focus on
        """
        self.current_tables = table_names
    
    def get_available_databases(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available databases
        
        Returns:
            Dictionary with database information
        """
        databases_info = {}
        databases = self.multi_db_manager.get_databases()
        
        for db_name in databases:
            info = self.multi_db_manager.get_database_info(db_name)
            databases_info[db_name] = info
        
        return databases_info
    
    def get_available_tables(self, database_name: Optional[str] = None) -> List[str]:
        """Get available tables from a specific database or all databases
        
        Args:
            database_name: Specific database name, or None for all
            
        Returns:
            List of table names
        """
        if database_name:
            if database_name in self.multi_db_manager.get_databases():
                db_info = self.multi_db_manager.get_database_info(database_name)
                return db_info.get('tables', [])
            return []
        else:
            # Get tables from all databases
            all_tables = self.multi_db_manager.get_all_tables_across_databases()
            tables = []
            for db_name, db_tables in all_tables.items():
                # Add database prefix to table names for clarity
                tables.extend([f"{db_name}.{table}" for table in db_tables])
            return tables
    
    def get_tables_by_database(self) -> Dict[str, List[str]]:
        """Get tables organized by database
        
        Returns:
            Dictionary of database_name -> list of tables
        """
        return self.multi_db_manager.get_all_tables_across_databases()
    
    def query_enhanced(self, question: str, selected_databases: Optional[List[str]] = None, 
                      selected_tables: Optional[List[str]] = None) -> Dict[str, Any]:
        """Enhanced query method with database and table selection
        
        Args:
            question: Natural language question
            selected_databases: List of databases to query (optional)
            selected_tables: List of tables to focus on (optional)
            
        Returns:
            Query results dictionary
        """
        # Store original context
        original_databases = self.current_databases.copy()
        original_tables = self.current_tables.copy()
        original_db_path = self.db_path
        original_schema = self.schema_info
        
        try:
            # Set context if provided, otherwise auto-detect
            if selected_databases:
                self.set_database_context(selected_databases)
            else:
                # Auto-detect databases based on question keywords
                auto_detected = self.auto_detect_databases(question)
                self.set_database_context(auto_detected)
            
            if selected_tables:
                self.set_table_context(selected_tables)
            
            # Store the query result
            query_result = None
            
            # Handle multi-database queries
            if len(self.current_databases) > 1:
                query_result = self._query_multi_database(question, self.current_databases, selected_tables)
            
            # Single database query
            elif len(self.current_databases) == 1:
                # Set the database context
                db_name = self.current_databases[0]
                db_path = self.multi_db_manager.get_database_path(db_name)
                
                if db_path and Path(db_path).exists():
                    self.db_path = Path(db_path)
                    self.refresh_schema()
                    
                    # Add database context to query result
                    context_info = f"Using database: {db_name} ({db_path})"
                    
                    # Use table filtering if tables are selected
                    if self.current_tables:
                        query_result = self.query_with_table_filter(question, self.current_tables)
                    else:
                        query_result = self.query(question)
                        
                    # Add context information to the result
                    if query_result and isinstance(query_result, dict):
                        query_result['database_used'] = db_name
                        query_result['database_path'] = db_path
                        if 'explanation' in query_result:
                            query_result['explanation'] = f"{context_info}\n\n{query_result['explanation']}"
                else:
                    query_result = {
                        "success": False,
                        "error": f"Database '{db_name}' not found or inaccessible",
                        "sql_query": "",
                        "explanation": f"The specified database '{db_name}' could not be accessed."
                    }
            
            else:
                # No database context, use default
                query_result = self.query(question)
            
            # Restore original context AFTER query execution
            self.current_databases = original_databases
            self.current_tables = original_tables
            self.db_path = original_db_path
            self.schema_info = original_schema
            
            # Return the result
            return query_result
                
        except Exception as e:
            # Restore original context in case of exception
            self.current_databases = original_databases
            self.current_tables = original_tables
            self.db_path = original_db_path
            self.schema_info = original_schema
            
            return {
                "success": False,
                "error": str(e),
                "sql_query": "",
                "explanation": f"Error executing query: {str(e)}"
            }
    
    def _query_multi_database(self, question: str, database_names: List[str], 
                            selected_tables: Optional[List[str]] = None) -> Dict[str, Any]:
        """Handle queries across multiple databases
        
        Args:
            question: Natural language question
            database_names: List of database names
            selected_tables: Optional table filter
            
        Returns:
            Query results dictionary
        """
        try:
            # Get combined schema for selected databases
            combined_schema = self.multi_db_manager.get_schema_for_databases(database_names)
            
            # Temporarily replace schema
            original_schema = self.schema_info
            self.schema_info = combined_schema
            
            # Add multi-database context to the question
            db_context = f"Available databases: {', '.join(database_names)}. "
            if selected_tables:
                table_context = f"Focus on these tables: {', '.join(selected_tables)}. "
            else:
                table_context = ""
            
            enhanced_question = f"{db_context}{table_context}{question}"
            
            # Note: For true multi-database queries, you might need to implement
            # database attachment or federation. For now, we'll use the first database
            # and inform the user about the limitation
            
            result = self.query(enhanced_question)
            
            # Add multi-database context to explanation
            if result.get("success"):
                result["explanation"] += f"\n\nNote: This query was executed against the '{database_names[0]}' database. " \
                                       f"For queries across multiple databases ({', '.join(database_names)}), " \
                                       f"consider using ATTACH DATABASE statements in custom SQL."
            
            # Restore schema
            self.schema_info = original_schema
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql_query": "",
                "explanation": f"Error executing multi-database query: {str(e)}"
            }
    
    def add_database_from_upload(self, name: str, upload_results: List[Dict]) -> bool:
        """Add a new database from file upload results
        
        Args:
            name: Name for the new database
            upload_results: Upload processing results
            
        Returns:
            Success status
        """
        try:
            # Create the database path
            db_path = self.multi_db_manager.create_database_from_upload(name, upload_results)
            
            # Refresh manager info
            self.multi_db_manager.refresh_database_info()
            
            return True
        except Exception as e:
            print(f"Error adding database from upload: {e}")
            return False
    
    def get_database_summary(self) -> Dict[str, Any]:
        """Get a summary of all databases and their contents
        
        Returns:
            Summary dictionary
        """
        databases_info = self.get_available_databases()
        
        total_databases = len(databases_info)
        total_tables = 0
        total_records = 0
        
        for db_info in databases_info.values():
            if 'table_count' in db_info:
                total_tables += db_info['table_count']
            if 'total_records' in db_info:
                total_records += db_info['total_records']
        
        return {
            "total_databases": total_databases,
            "total_tables": total_tables,
            "total_records": total_records,
            "databases": databases_info,
            "current_context": {
                "databases": self.current_databases,
                "tables": self.current_tables
            }
        }
    
    def execute_custom_query_on_database(self, db_name: str, query: str) -> Dict[str, Any]:
        """Execute a custom SQL query on a specific database
        
        Args:
            db_name: Target database name
            query: SQL query to execute
            
        Returns:
            Query results
        """
        return self.multi_db_manager.execute_query_on_database(db_name, query)