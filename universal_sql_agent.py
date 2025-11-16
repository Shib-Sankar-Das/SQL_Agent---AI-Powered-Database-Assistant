"""
Enhanced SQL Agent with External Database Support
Extends the existing SQL Agent to work with both SQLite and external databases
"""

import logging
from typing import Dict, List, Optional, Any
import traceback

# Import existing SQL Agent
from sql_agent import SQLAgent
from universal_database_adapter import UniversalDatabaseAdapter

logger = logging.getLogger(__name__)

class UniversalSQLAgent(SQLAgent):
    """
    Enhanced SQL Agent that can work with both local SQLite and external SQL databases
    Inherits from the original SQLAgent and extends it with external database support
    """
    
    def __init__(self, api_key: str = None, model: str = "gemini-1.5-pro"):
        # Initialize the base SQL Agent
        super().__init__(api_key, model)
        
        # Initialize universal database adapter
        self.db_adapter = UniversalDatabaseAdapter()
        
        # Override database information with universal adapter
        self.refresh_database_schemas()
        
        logger.info("UniversalSQLAgent initialized with external database support")
    
    def refresh_database_schemas(self):
        """Refresh database schemas from all available databases"""
        try:
            # Get all databases (SQLite + external)
            all_databases = self.db_adapter.get_all_databases()
            
            # Build comprehensive schema information
            self.database_schemas = {}
            self.database_info = {}
            
            for db_name, db_info in all_databases.items():
                try:
                    # Get detailed schema
                    schema_info = self.db_adapter.get_database_schema(db_name)
                    
                    # Store in format expected by SQL Agent
                    self.database_schemas[db_name] = schema_info
                    
                    # Store database info
                    self.database_info[db_name] = {
                        'type': db_info['type'],
                        'is_external': db_info.get('is_external', False),
                        'table_count': len(db_info['tables']),
                        'connection_info': db_info.get('connection_info')
                    }
                    
                except Exception as e:
                    logger.warning(f"Could not get schema for database {db_name}: {str(e)}")
            
            # Update the system prompt with new database information
            self.update_system_prompt()
            
            logger.info(f"Refreshed schemas for {len(self.database_schemas)} databases")
            
        except Exception as e:
            logger.error(f"Error refreshing database schemas: {str(e)}")
            # Fall back to original behavior
            super().__init__(self.api_key, self.model)
    
    def update_system_prompt(self):
        """Update the system prompt with information about all available databases"""
        try:
            # Build database information for prompt
            db_info_text = "Available Databases:\n"
            
            for db_name, db_info in self.database_info.items():
                db_type = db_info['type'].upper()
                is_external = " (External)" if db_info['is_external'] else " (Local SQLite)"
                table_count = db_info['table_count']
                
                db_info_text += f"\n- **{db_name}**: {db_type}{is_external} - {table_count} tables"
                
                # Add tables information
                if db_name in self.database_schemas:
                    tables = self.database_schemas[db_name].get('tables', [])
                    if tables:
                        for table in tables[:5]:  # Limit to first 5 tables
                            column_count = len(table.get('columns', []))
                            row_count = table.get('row_count', 'Unknown')
                            db_info_text += f"\n  - {table['name']}: {column_count} columns, {row_count} rows"
                        
                        if len(tables) > 5:
                            db_info_text += f"\n  - ... and {len(tables) - 5} more tables"
            
            # Add external database specific instructions
            external_db_instructions = """

EXTERNAL DATABASE SUPPORT:
- External databases are marked with 🌐 prefix
- Supported types: PostgreSQL, MySQL, SQL Server, SQLite
- Use appropriate SQL syntax for each database type
- PostgreSQL: Use $1, $2 for parameters
- MySQL: Use standard SQL syntax
- SQL Server: Use OFFSET...FETCH for pagination
- Always specify the database name when querying

QUERY EXECUTION:
- For external databases, queries are executed via SQLAlchemy
- Connection pooling and timeout handling are automatic
- Schema information is cached and refreshed automatically
- All CRUD operations work across database types

DATABASE SELECTION STRATEGY:
- Auto-detect best database based on query keywords
- Prefer databases with relevant table names
- Consider data recency and completeness
- Handle connection errors gracefully
"""
            
            # Update the system prompt
            self.system_prompt = f"""You are an intelligent SQL Agent that can work with multiple database systems including local SQLite databases and external SQL databases (PostgreSQL, MySQL, SQL Server, etc.).

{db_info_text}

{external_db_instructions}

Your capabilities include:
1. **Multi-Database Query Execution**: Execute queries on any available database
2. **Smart Database Selection**: Automatically choose the best database for each query
3. **Schema Awareness**: Understand table structures across all databases
4. **Syntax Adaptation**: Use appropriate SQL syntax for each database type
5. **Connection Management**: Handle external database connections seamlessly
6. **Error Recovery**: Gracefully handle connection issues and fallback strategies

When users ask questions:
1. Analyze which database(s) contain relevant data
2. Choose the most appropriate database
3. Generate syntactically correct SQL for the target database
4. Execute the query and format results clearly
5. Provide insights and explanations

Always be helpful, accurate, and provide clear explanations of your reasoning."""

            logger.info("System prompt updated with external database information")
            
        except Exception as e:
            logger.error(f"Error updating system prompt: {str(e)}")
    
    def auto_detect_database(self, user_query: str) -> str:
        """
        Enhanced database detection that considers external databases
        """
        try:
            # First try the original detection method
            detected_db = super().auto_detect_database(user_query)
            
            # If original method found a database, check if it exists in our universal adapter
            if detected_db and detected_db in self.database_schemas:
                return detected_db
            
            # Enhanced detection for external databases
            query_lower = user_query.lower()
            
            # Database-specific keywords with priorities - updated to match actual database names
            database_keywords = {
                'earthquake': ['earthquake', 'seismic', 'magnitude', 'depth', 'latitude', 'longitude', 'tremor', 'quake', 'richter', 'tsunami'],
                'cardict_arrest': ['cardiac', 'heart', 'arrest', 'cardiovascular', 'cardict', 'coronary', 'arrhythmia', 'ecg', 'ekg', 'cardiology'],
                'customer_churn_prediction': ['customer', 'churn', 'retention', 'prediction', 'subscription', 'cancel', 'loyalty', 'attrition', 'clients', 'users'],
                'crop_recommendation': ['crop', 'crops', 'farming', 'agriculture', 'recommendation', 'plant', 'grow', 'harvest', 'soil', 'fertilizer', 'rice', 'wheat'],
                'main': ['pcos', 'polycystic', 'ovary', 'hormone', 'insulin', 'fertility', 'sales', 'revenue', 'profit', 'employees', 'staff', 'hr']
            }
            
            # Score databases based on keyword matches
            database_scores = {}
            
            for db_name, db_info in self.database_info.items():
                score = 0
                
                # Check database name matches - handle actual database names
                db_name_lower = db_name.lower()
                
                # Map actual database names to keyword categories
                db_to_category_map = {
                    'earthquake': 'earthquake',
                    'cardict_arrest': 'cardict_arrest', 
                    'customer_churn_prediction': 'customer_churn_prediction',
                    'crop_recommendation': 'crop_recommendation',
                    'main': 'main'
                }
                
                # Check for direct matches and keyword matches
                for actual_db, category in db_to_category_map.items():
                    if actual_db in db_name_lower or db_name_lower == actual_db:
                        keywords = database_keywords.get(category, [])
                        for keyword in keywords:
                            if keyword in query_lower:
                                score += 3  # High score for name + keyword match
                
                # Check table name matches
                if db_name in self.database_schemas:
                    tables = self.database_schemas[db_name].get('tables', [])
                    for table in tables:
                        table_name_lower = table['name'].lower()
                        for keyword_category, keywords in database_keywords.items():
                            if keyword_category in table_name_lower:
                                for keyword in keywords:
                                    if keyword in query_lower:
                                        score += 2  # Medium score for table + keyword match
                        
                        # Direct table name mentions
                        if table['name'].lower() in query_lower:
                            score += 4  # Very high score for direct table mention
                
                # Prefer databases with more tables (more complete)
                score += db_info['table_count'] * 0.1
                
                # Slight preference for external databases if they have relevant data
                if db_info['is_external'] and score > 0:
                    score += 0.5
                
                database_scores[db_name] = score
            
            # Return the database with the highest score
            if database_scores:
                best_database = max(database_scores.items(), key=lambda x: x[1])
                if best_database[1] > 0:
                    logger.info(f"Auto-detected database: {best_database[0]} (score: {best_database[1]:.2f})")
                    return best_database[0]
            
            # If no good match, return the first available database
            if self.database_schemas:
                fallback_db = list(self.database_schemas.keys())[0]
                logger.info(f"Using fallback database: {fallback_db}")
                return fallback_db
            
            return "Main Database"  # Ultimate fallback
            
        except Exception as e:
            logger.error(f"Error in auto-detect database: {str(e)}")
            return "Main Database"
    
    def execute_query(self, query: str, database_name: str = None) -> Dict[str, Any]:
        """
        Enhanced query execution that works with external databases
        """
        try:
            # Auto-detect database if not specified
            if not database_name:
                database_name = self.auto_detect_database(query)
            
            logger.info(f"Executing query on {database_name}: {query[:100]}...")
            
            # Use universal database adapter to execute query
            result = self.db_adapter.execute_query(database_name, query)
            
            if result['success']:
                # Format the result in the expected format
                if result['query_type'] == 'SELECT':
                    formatted_data = []
                    if result['data']:
                        # Convert to the format expected by the original SQL Agent
                        for row in result['data']:
                            formatted_data.append(row)
                    
                    return {
                        'success': True,
                        'data': formatted_data,
                        'columns': result.get('columns', []),
                        'row_count': result.get('row_count', len(formatted_data)),
                        'database_used': database_name,
                        'query': query
                    }
                else:
                    return {
                        'success': True,
                        'message': result.get('message', 'Query executed successfully'),
                        'rows_affected': result.get('rows_affected', 0),
                        'database_used': database_name,
                        'query': query
                    }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'database_used': database_name,
                    'query': query
                }
                
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'database_used': database_name or 'Unknown',
                'query': query
            }
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about all available databases
        """
        try:
            info = {
                'total_databases': len(self.database_schemas),
                'local_databases': 0,
                'external_databases': 0,
                'total_tables': 0,
                'databases': {}
            }
            
            for db_name, db_info in self.database_info.items():
                info['total_tables'] += db_info['table_count']
                
                if db_info['is_external']:
                    info['external_databases'] += 1
                else:
                    info['local_databases'] += 1
                
                info['databases'][db_name] = {
                    'type': db_info['type'],
                    'is_external': db_info['is_external'],
                    'table_count': db_info['table_count'],
                    'tables': [table['name'] for table in self.database_schemas.get(db_name, {}).get('tables', [])]
                }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting database info: {str(e)}")
            return {'error': str(e)}
    
    def add_external_database(self, connection_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new external database connection
        """
        try:
            from external_database_manager import DatabaseConnection
            
            # Create connection object
            connection = DatabaseConnection(
                name=connection_config['name'],
                db_type=connection_config['db_type'],
                host=connection_config['host'],
                port=connection_config['port'],
                database=connection_config['database'],
                username=connection_config['username'],
                password=connection_config['password'],
                connection_string=connection_config.get('connection_string')
            )
            
            # Add connection
            success, message = self.db_adapter.add_external_connection(connection)
            
            if success:
                # Refresh schemas to include the new database
                self.refresh_database_schemas()
                
                return {
                    'success': True,
                    'message': message,
                    'connection_name': connection.name
                }
            else:
                return {
                    'success': False,
                    'error': message
                }
                
        except Exception as e:
            logger.error(f"Error adding external database: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def remove_external_database(self, connection_name: str) -> Dict[str, Any]:
        """
        Remove an external database connection
        """
        try:
            success, message = self.db_adapter.remove_external_connection(connection_name)
            
            if success:
                # Refresh schemas to remove the database
                self.refresh_database_schemas()
                
                return {
                    'success': True,
                    'message': message
                }
            else:
                return {
                    'success': False,
                    'error': message
                }
                
        except Exception as e:
            logger.error(f"Error removing external database: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_external_connection(self, connection_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test an external database connection without adding it
        """
        try:
            from external_database_manager import DatabaseConnection
            
            # Create temporary connection object
            connection = DatabaseConnection(
                name="test_connection",
                db_type=connection_config['db_type'],
                host=connection_config['host'],
                port=connection_config['port'],
                database=connection_config['database'],
                username=connection_config['username'],
                password=connection_config['password'],
                connection_string=connection_config.get('connection_string')
            )
            
            # Test connection
            success, message = self.db_adapter.test_external_connection(connection)
            
            return {
                'success': success,
                'message': message
            }
            
        except Exception as e:
            logger.error(f"Error testing external connection: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_external_connections(self) -> List[Dict[str, Any]]:
        """
        List all external database connections
        """
        try:
            connections = self.db_adapter.list_external_connections()
            return [
                {
                    'name': conn.name,
                    'db_type': conn.db_type,
                    'host': conn.host,
                    'port': conn.port,
                    'database': conn.database,
                    'username': conn.username,
                    'is_active': conn.is_active,
                    'test_status': conn.test_status,
                    'last_tested': conn.last_tested
                }
                for conn in connections
            ]
        except Exception as e:
            logger.error(f"Error listing external connections: {str(e)}")
            return []

# Example usage
if __name__ == "__main__":
    # Initialize the universal SQL agent
    agent = UniversalSQLAgent()
    
    # Get database information
    db_info = agent.get_database_info()
    print(f"Total databases: {db_info['total_databases']}")
    print(f"Local: {db_info['local_databases']}, External: {db_info['external_databases']}")
    print(f"Total tables: {db_info['total_tables']}")
    
    # Test a query
    result = agent.execute_query("SELECT COUNT(*) FROM customers")
    print(f"Query result: {result}")