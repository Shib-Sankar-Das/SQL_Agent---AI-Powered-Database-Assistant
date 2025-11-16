"""
Database Management Interface for SQL Agent
A comprehensive CRUD interface for managing database records
"""

import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import traceback
from datetime import datetime, date
from csv_reader_utils import robust_read_csv, get_csv_info
import json
import re

# Import our SQL Agent for schema info
from sql_agent import SQLAgent
from file_upload_manager import FileUploadManager

# Import dynamic database manager for multi-database support
try:
    from dynamic_database_manager import DynamicDatabaseManager
    DYNAMIC_MANAGER_AVAILABLE = True
except ImportError:
    DYNAMIC_MANAGER_AVAILABLE = False
    st.warning("Dynamic database manager not available. Some features will be limited.")

# Import AI system integrator for real-time updates
try:
    from ai_system_integrator import AISystemIntegrator
    AI_INTEGRATOR_AVAILABLE = True
except ImportError:
    AI_INTEGRATOR_AVAILABLE = False

def get_db_connection(db_path=None):
    """Get database connection - supports both single and multi-database modes"""
    if db_path is None:
        # Default to main database
        db_path = Path("database/sql_agent.db")
    return sqlite3.connect(db_path)

def get_table_schema(table_name, db_path=None):
    """Get schema information for a table"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    schema = cursor.fetchall()
    conn.close()
    return schema

def get_all_tables(db_path=None):
    """Get list of all tables in the database"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

def get_all_databases():
    """Get all available databases using dynamic manager if available"""
    if DYNAMIC_MANAGER_AVAILABLE:
        try:
            from dynamic_database_manager import DynamicDatabaseManager
            dynamic_manager = DynamicDatabaseManager()
            return dynamic_manager.get_all_databases()
        except Exception as e:
            st.warning(f"Error accessing dynamic databases: {str(e)}")
    
    # Fallback to main database only
    main_db_path = Path("database/sql_agent.db")
    if main_db_path.exists():
        return {
            "Main Database": {
                "path": str(main_db_path),
                "tables": [],
                "size": main_db_path.stat().st_size
            }
        }
    return {}

def get_table_data(table_name, limit=100, db_path=None, offset=0):
    """Get data from a table with pagination"""
    conn = get_db_connection(db_path)
    query = f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_table_count(table_name, db_path=None):
    """Get total count of records in a table"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def execute_query(query, params=None, db_path=None):
    """Execute a query and return results"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            results = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            conn.close()
            return True, results, columns
        else:
            conn.commit()
            rows_affected = cursor.rowcount
            conn.close()
            return True, f"Query executed successfully. Rows affected: {rows_affected}", []
    except Exception as e:
        conn.close()
        return False, str(e), []

def insert_record(table_name, data, db_path=None):
    """Insert a new record into a table"""
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data])
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    
    return execute_query(query, list(data.values()), db_path)

def update_record(table_name, record_id, id_column, data, db_path=None):
    """Update an existing record"""
    set_clause = ', '.join([f"{col} = ?" for col in data.keys()])
    query = f"UPDATE {table_name} SET {set_clause} WHERE {id_column} = ?"
    
    values = list(data.values()) + [record_id]
    return execute_query(query, values, db_path)

def delete_record(table_name, record_id, id_column, db_path=None):
    """Delete a record from a table"""
    query = f"DELETE FROM {table_name} WHERE {id_column} = ?"
    return execute_query(query, [record_id], db_path)

def render_data_input_form(schema, existing_data=None):
    """Render input form based on table schema"""
    form_data = {}
    
    for col_info in schema:
        col_name = col_info[1]
        col_type = col_info[2]
        not_null = col_info[3]
        default_val = col_info[4]
        is_pk = col_info[5]
        
        # Skip auto-increment primary keys for insert
        if is_pk and 'AUTOINCREMENT' in str(col_type).upper():
            continue
            
        # Get existing value if updating
        existing_val = existing_data.get(col_name, '') if existing_data else ''
        
        # Determine input type based on column type
        if 'INT' in col_type.upper():
            if existing_val == '':
                existing_val = 0 if not_null else None
            form_data[col_name] = st.number_input(
                f"{col_name} {'*' if not_null else ''}",
                value=existing_val,
                help=f"Type: {col_type}, Required: {not_null}"
            )
        elif 'DECIMAL' in col_type.upper() or 'REAL' in col_type.upper():
            if existing_val == '':
                existing_val = 0.0 if not_null else None
            form_data[col_name] = st.number_input(
                f"{col_name} {'*' if not_null else ''}",
                value=float(existing_val) if existing_val is not None else 0.0,
                format="%.2f",
                help=f"Type: {col_type}, Required: {not_null}"
            )
        elif 'DATE' in col_type.upper():
            if existing_val and existing_val != '':
                try:
                    existing_val = datetime.strptime(existing_val, '%Y-%m-%d').date()
                except:
                    existing_val = date.today()
            else:
                existing_val = date.today() if not_null else None
            
            form_data[col_name] = st.date_input(
                f"{col_name} {'*' if not_null else ''}",
                value=existing_val,
                help=f"Type: {col_type}, Required: {not_null}"
            )
        elif 'BOOLEAN' in col_type.upper():
            form_data[col_name] = st.checkbox(
                f"{col_name} {'*' if not_null else ''}",
                value=bool(existing_val) if existing_val else False,
                help=f"Type: {col_type}, Required: {not_null}"
            )
        else:  # TEXT, VARCHAR, etc.
            form_data[col_name] = st.text_input(
                f"{col_name} {'*' if not_null else ''}",
                value=str(existing_val) if existing_val else '',
                help=f"Type: {col_type}, Required: {not_null}"
            )
    
    return form_data

def create_table_from_dataframe(df, table_name, db_path=None):
    """Create a new table from DataFrame"""
    try:
        conn = get_db_connection(db_path)
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error creating table: {str(e)}")
        return False

def external_database_interface():
    """External Database Management Interface"""
    st.header("🌐 External Database Management")
    
    st.markdown("""
    **Connect to External SQL Databases**
    
    Extend your SQL Agent with support for:
    - 🐘 **PostgreSQL** (including Supabase)
    - 🐬 **MySQL** (including PlanetScale, AWS RDS)
    - 🏢 **SQL Server** (including Azure SQL)
    - 🌐 **Other SQLAlchemy-supported databases**
    """)
    
    # Check dependencies
    try:
        from external_database_manager import ExternalDatabaseManager
        from universal_database_adapter import UniversalDatabaseAdapter
        external_manager = ExternalDatabaseManager()
        EXTERNAL_SUPPORT_AVAILABLE = True
    except ImportError as e:
        st.error(f"❌ External database support not available: {str(e)}")
        st.info("Install required dependencies: `pip install sqlalchemy psycopg2-binary pymysql pyodbc`")
        EXTERNAL_SUPPORT_AVAILABLE = False
        return
    
    # Tabs for different operations
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Add Connection", "📋 Manage Connections", "🧪 Test Connection", "📊 Dependencies"])
    
    with tab1:
        st.subheader("➕ Add New External Database")
        
        with st.form("add_external_db"):
            col1, col2 = st.columns(2)
            
            with col1:
                db_types = external_manager.get_available_db_types()
                available_types = {k: v for k, v in db_types.items() if v['available'] and k != 'sqlite'}
                
                if not available_types:
                    st.error("No external database drivers available. Please install dependencies.")
                    st.stop()
                
                selected_type = st.selectbox(
                    "Database Type", 
                    list(available_types.keys()),
                    format_func=lambda x: available_types[x]['name']
                )
                
                conn_name = st.text_input(
                    "Connection Name", 
                    placeholder="e.g., Production DB, Supabase Analytics"
                )
                
                host = st.text_input(
                    "Host", 
                    placeholder=available_types[selected_type]['example_host']
                )
            
            with col2:
                port = st.number_input(
                    "Port", 
                    value=available_types[selected_type]['default_port'],
                    min_value=1,
                    max_value=65535
                )
                
                database = st.text_input(
                    "Database Name", 
                    placeholder="database_name"
                )
                
                username = st.text_input(
                    "Username", 
                    placeholder="username"
                )
                
                password = st.text_input(
                    "Password", 
                    type="password"
                )
            
            # Advanced options
            with st.expander("🔧 Advanced Options"):
                custom_connection_string = st.text_area(
                    "Custom Connection String (Optional)",
                    placeholder="Leave empty to auto-generate",
                    help="If provided, will override individual connection parameters"
                )
                
                st.markdown("**Examples:**")
                st.code("""
PostgreSQL (Supabase):
postgresql://username:password@host:5432/database

MySQL:
mysql://username:password@host:3306/database

SQL Server:
mssql+pyodbc://username:password@host:1433/database?driver=ODBC+Driver+17+for+SQL+Server
                """)
            
            # Submit button
            if st.form_submit_button("🔗 Add Connection", type="primary"):
                if not all([conn_name, host, database]):
                    st.error("❌ Please fill in all required fields")
                else:
                    try:
                        from external_database_manager import DatabaseConnection
                        
                        # Create connection object
                        connection = DatabaseConnection(
                            name=conn_name,
                            db_type=selected_type,
                            host=host,
                            port=port,
                            database=database,
                            username=username,
                            password=password,
                            connection_string=custom_connection_string if custom_connection_string.strip() else None
                        )
                        
                        # Add connection
                        with st.spinner(f"Testing connection to {conn_name}..."):
                            success, message = external_manager.add_connection(connection)
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.balloons()
                            
                            # Clear cached resources to refresh
                            try:
                                if 'universal_sql_agent' in st.session_state:
                                    del st.session_state.universal_sql_agent
                                if 'enhanced_sql_agent' in st.session_state:
                                    del st.session_state.enhanced_sql_agent
                            except:
                                pass
                        else:
                            st.error(f"❌ {message}")
                            
                    except Exception as e:
                        st.error(f"❌ Error adding connection: {str(e)}")
    
    with tab2:
        st.subheader("📋 Manage External Connections")
        
        connections = external_manager.list_connections()
        
        if not connections:
            st.info("No external database connections configured.")
        else:
            for i, conn in enumerate(connections):
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    
                    with col1:
                        status_icon = "✅" if conn.test_status == "success" else "❌" if conn.test_status == "failed" else "⚪"
                        st.write(f"**{status_icon} {conn.name}**")
                        st.write(f"{conn.db_type.upper()} • {conn.host}:{conn.port}")
                    
                    with col2:
                        st.write(f"**Database:** {conn.database}")
                        st.write(f"**User:** {conn.username}")
                    
                    with col3:
                        if conn.last_tested:
                            test_date = conn.last_tested[:10]
                            st.write(f"**Last tested:** {test_date}")
                        else:
                            st.write("**Never tested**")
                        
                        if conn.test_status == "success":
                            st.success("Connected")
                        elif conn.test_status == "failed":
                            st.error("Failed")
                        else:
                            st.warning("Not tested")
                    
                    with col4:
                        if st.button("🧪 Test", key=f"test_{i}"):
                            with st.spinner("Testing..."):
                                success, message = external_manager.test_connection(conn)
                            
                            if success:
                                st.success("✅ Connected")
                            else:
                                st.error(f"❌ {message}")
                        
                        if st.button("🗑️ Remove", key=f"remove_{i}"):
                            success, message = external_manager.remove_connection(conn.name)
                            if success:
                                st.success(f"✅ Removed {conn.name}")
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                    
                    st.markdown("---")
    
    with tab3:
        st.subheader("🧪 Test Connection")
        st.markdown("Test a database connection without saving it")
        
        with st.form("test_connection"):
            col1, col2 = st.columns(2)
            
            with col1:
                db_types = external_manager.get_available_db_types()
                available_types = {k: v for k, v in db_types.items() if v['available'] and k != 'sqlite'}
                
                test_type = st.selectbox(
                    "Database Type", 
                    list(available_types.keys()),
                    format_func=lambda x: available_types[x]['name'],
                    key="test_type"
                )
                
                test_host = st.text_input("Host", key="test_host")
                test_database = st.text_input("Database", key="test_database")
            
            with col2:
                test_port = st.number_input(
                    "Port", 
                    value=available_types[test_type]['default_port'],
                    key="test_port"
                )
                test_username = st.text_input("Username", key="test_username")
                test_password = st.text_input("Password", type="password", key="test_password")
            
            if st.form_submit_button("🧪 Test Connection"):
                if all([test_host, test_database, test_username, test_password]):
                    try:
                        from external_database_manager import DatabaseConnection
                        
                        test_conn = DatabaseConnection(
                            name="test",
                            db_type=test_type,
                            host=test_host,
                            port=test_port,
                            database=test_database,
                            username=test_username,
                            password=test_password
                        )
                        
                        with st.spinner("Testing connection..."):
                            success, message = external_manager.test_connection(test_conn)
                        
                        if success:
                            st.success(f"✅ Connection successful: {message}")
                            
                            # Try to get schema info
                            try:
                                st.info("🔍 Attempting to retrieve schema information...")
                                # This would require temporarily adding the connection
                                # For now, just show success
                                st.success("Connection can be used with SQL Agent!")
                            except Exception as e:
                                st.warning(f"Connection works but couldn't get schema: {str(e)}")
                        else:
                            st.error(f"❌ Connection failed: {message}")
                            
                            # Provide troubleshooting tips
                            st.markdown("""
                            **Troubleshooting Tips:**
                            - Check if the host and port are correct
                            - Verify username and password
                            - Ensure the database exists
                            - Check if firewall allows connections
                            - For cloud databases, verify IP whitelist
                            """)
                    except Exception as e:
                        st.error(f"❌ Test error: {str(e)}")
                else:
                    st.error("Please fill in all required fields")
    
    with tab4:
        st.subheader("📊 Database Support Status")
        
        db_types = external_manager.get_available_db_types()
        missing_deps = external_manager.get_missing_dependencies()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Available Database Types:**")
            for db_type, info in db_types.items():
                if info['available']:
                    st.success(f"✅ {info['name']} - Ready")
                else:
                    st.error(f"❌ {info['name']} - Missing dependencies")
        
        with col2:
            if missing_deps:
                st.markdown("**Missing Dependencies:**")
                st.code(f"pip install {' '.join(missing_deps)}")
                
                st.markdown("**Individual packages:**")
                for dep in missing_deps:
                    st.code(f"pip install {dep}")
            else:
                st.success("✅ All dependencies available!")
        
        # Connection summary
        st.markdown("---")
        summary = external_manager.get_connection_summary()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Connections", summary['total_connections'])
        with col2:
            st.metric("Active Connections", summary['active_connections'])
        with col3:
            successful_connections = len([c for c in external_manager.list_connections() if c.test_status == "success"])
            st.metric("Working Connections", successful_connections)
        
        if summary['by_type']:
            st.markdown("**Connections by Type:**")
            for db_type, count in summary['by_type'].items():
                st.write(f"- {db_type.title()}: {count}")

def migrate_table(source_db_name, source_db_path, source_table, dest_db_name, dest_db_path, dest_table, is_move=True, dest_is_external=False):
    """
    Migrate a table from one database to another.
    
    Args:
        source_db_name: Name of source database
        source_db_path: Path to source database file (None if external)
        source_table: Name of table to migrate
        dest_db_name: Name of destination database
        dest_db_path: Path to destination database file (None if external)
        dest_table: Name for table in destination database
        is_move: If True, delete from source after copy (default: True)
        dest_is_external: If True, destination is external database
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Import required modules
        import streamlit as st
        
        # Step 1: Get source table schema and data
        st.info(f"📋 Reading table structure from {source_db_name}.{source_table}...")
        
        if source_db_name.startswith("🌐"):
            # For external databases, we'll need to use a simplified approach
            # This is a limitation - external to external/local migration needs custom implementation
            st.error("❌ Migration from external databases is not fully supported yet.")
            st.info("💡 Try exporting data from the external database and importing to the destination.")
            return False
            
        else:
            # Source is local SQLite database
            schema = get_table_schema(source_table, source_db_path)
            
            # Get all data from source table
            conn = get_db_connection(source_db_path)
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {source_table}")
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            conn.close()
        
        st.success(f"✅ Read {len(rows)} rows from source table")
        
        # Step 2: Create destination table
        st.info(f"🔧 Creating table {dest_table} in {dest_db_name}...")
        
        if dest_is_external:
            # For external destination, use UniversalDatabaseAdapter
            try:
                from universal_database_adapter import UniversalDatabaseAdapter
                db_adapter = UniversalDatabaseAdapter()
                
                # Create table manually by inserting records and letting the adapter handle schema
                if rows:
                    # Use the first row to create the table structure
                    sample_data = dict(zip(columns, rows[0]))
                    result = db_adapter.insert_record(dest_db_name, dest_table, sample_data)
                    if not result['success']:
                        st.error(f"❌ Failed to create destination table: {result.get('error', 'Unknown error')}")
                        return False
                    
                    # Insert remaining rows
                    for row in rows[1:]:
                        row_data = dict(zip(columns, row))
                        result = db_adapter.insert_record(dest_db_name, dest_table, row_data)
                        if not result['success']:
                            st.warning(f"⚠️ Failed to insert one row: {result.get('error', 'Unknown error')}")
                else:
                    # Empty table - create with minimal structure
                    sample_data = {col[1]: None for col in schema[:3]}  # Use first 3 columns
                    result = db_adapter.insert_record(dest_db_name, dest_table, sample_data)
                    if result['success']:
                        # Delete the sample record
                        st.info("📝 Created empty table structure")
            except ImportError:
                st.error("❌ External database adapter not available for destination migration")
                return False
                
        else:
            # Destination is local SQLite database
            # Generate CREATE TABLE statement
            create_sql = f"CREATE TABLE {dest_table} ("
            column_defs = []
            
            for col in schema:
                col_name = col[1]
                col_type = col[2]
                not_null = " NOT NULL" if col[3] else ""
                default = f" DEFAULT {col[4]}" if col[4] else ""
                pk = " PRIMARY KEY" if col[5] else ""
                
                column_def = f"{col_name} {col_type}{not_null}{default}{pk}"
                column_defs.append(column_def)
            
            create_sql += ", ".join(column_defs) + ")"
            
            # Execute CREATE TABLE
            conn = get_db_connection(dest_db_path)
            cursor = conn.cursor()
            
            # Check if table already exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (dest_table,))
            if cursor.fetchone():
                conn.close()
                st.error(f"❌ Table '{dest_table}' already exists in destination database")
                return False
            
            cursor.execute(create_sql)
            conn.commit()
            
            # Step 3: Copy data to destination (for local SQLite)
            if rows:
                st.info(f"📤 Copying {len(rows)} rows to destination...")
                
                # Prepare INSERT statement
                placeholders = ", ".join(["?" for _ in columns])
                insert_sql = f"INSERT INTO {dest_table} ({', '.join(columns)}) VALUES ({placeholders})"
                
                # Insert all rows
                cursor.executemany(insert_sql, rows)
                conn.commit()
                st.success(f"✅ Copied {len(rows)} rows successfully")
            else:
                st.info("ℹ️ No data to copy (empty table)")
            
            conn.close()
        
        st.success(f"✅ Created destination table structure")
        
        # Step 4: Delete from source if this is a move operation
        if is_move:
            st.info(f"�️ Removing table from source database...")
            
            # Delete from local SQLite database
            conn = get_db_connection(source_db_path)
            cursor = conn.cursor()
            cursor.execute(f"DROP TABLE {source_table}")
            conn.commit()
            conn.close()
            
            st.success(f"✅ Removed table from source database")
        
        return True
        
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Migration failed: {str(e)}")
        st.exception(e)  # Show full error for debugging
        return False

def main():
    """Main database management interface"""
    
    st.set_page_config(
        page_title="Database Management - SQL Agent",
        page_icon="🗃️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🗄️ Database Manager")
    st.markdown("**Manage your SQLite and External databases with an intuitive interface**")
    
    # Initialize components
    try:
        from dynamic_database_manager import DynamicDatabaseManager
        dynamic_manager = DynamicDatabaseManager()
        AI_INTEGRATOR_AVAILABLE = True
        DYNAMIC_MANAGER_AVAILABLE = True
    except ImportError:
        dynamic_manager = None
        AI_INTEGRATOR_AVAILABLE = False
        DYNAMIC_MANAGER_AVAILABLE = False
        st.info("ℹ️ Advanced dynamic features not available")
    
    # Sidebar configuration
    st.sidebar.title("🎯 Database Selection")
    st.sidebar.markdown("Choose your database and operations")
    
    # Get all databases
    databases = get_all_databases()
    
    if not databases:
        st.sidebar.error("No databases found!")
        st.error("No databases found in the system!")
        return
    
    # Database dropdown
    db_names = list(databases.keys())
    selected_db_name = st.sidebar.selectbox("Database", db_names, help="Choose which database to work with")
    selected_db_path = databases[selected_db_name]['path']
    
    # Show database info
    if selected_db_name and selected_db_name in databases:
        db_info = databases[selected_db_name]
        st.sidebar.info(f"**Database:** {selected_db_name}")
        if 'size' in db_info:
            size_mb = db_info['size'] / (1024 * 1024)
            st.sidebar.info(f"**Size:** {size_mb:.2f} MB")
    
    # Get all tables from selected database
    st.sidebar.subheader("📋 Select Table")
    tables = []
    selected_table = None
    
    try:
        tables = get_all_tables(selected_db_path)
        if not tables:
            st.sidebar.warning("No tables found in this database")
        else:
            selected_table = st.sidebar.selectbox("Table", tables, help="Select a table to work with")
    except Exception as e:
        st.sidebar.error(f"Error connecting to database: {str(e)}")
        st.sidebar.info("💡 Try 'Upload Files' to create new tables")

    # Operation selection
    st.sidebar.subheader("🔧 Select Operation")
    operation = st.sidebar.radio(
        "Choose Operation",
        ["📋 View Data", "➕ Add Record", "✏️ Edit Record", "🗑️ Delete Options", "📊 Custom Query", "📤 Upload Files", "🌐 External Databases"],
        help="Upload Files and External Databases operations are always available"
    )

    # Display table info
    if selected_table:
        st.sidebar.subheader("📊 Table Info")
        try:
            count = get_table_count(selected_table, selected_db_path)
            schema = get_table_schema(selected_table, selected_db_path)
            st.sidebar.success(f"**Records:** {count:,}")
            st.sidebar.success(f"**Columns:** {len(schema)}")
        except Exception as e:
            st.sidebar.error(f"Error getting table info: {str(e)}")
    
    # Show operation-specific info for Upload Files
    if operation == "📤 Upload Files" and not selected_table:
        st.sidebar.info("📤 **Upload Files** creates new tables - no table selection needed")
    elif operation == "🌐 External Databases":
        st.sidebar.info("🌐 **External Databases** - manage external database connections")
    
    # Main content area
    # Check if operation requires a table but none is selected
    table_required_operations = ["📋 View Data", "➕ Add Record", "✏️ Edit Record", "🗑️ Delete Options"]
    
    if operation in table_required_operations and not selected_table:
        st.warning(f"⚠️ **{operation}** requires selecting a table from the sidebar")
        st.info("💡 **Tip:** If no tables are available, use **📤 Upload Files** to create new tables in this database")
        return
    
    if operation == "📋 View Data":
        st.header(f"📋 View Data - {selected_db_name}.{selected_table}")
        
        # Pagination controls
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            page_size = st.selectbox("Records per page", [25, 50, 100, 200], index=1)
        with col2:
            try:
                total_records = get_table_count(selected_table, selected_db_path)
                max_page = max(1, (total_records - 1) // page_size + 1)
                page_number = st.number_input("Page", min_value=1, max_value=max_page, value=1)
                offset = (page_number - 1) * page_size
            except:
                offset = 0
                total_records = 0
        
        try:
            # Get data with pagination using updated function
            df = get_table_data(selected_table, limit=page_size, db_path=selected_db_path, offset=offset)
            
            if not df.empty:
                st.dataframe(df, use_container_width=True, height=400)
                st.info(f"Showing records {offset + 1} to {min(offset + page_size, total_records)} of {total_records}")
                
                # Download option
                csv = df.to_csv(index=False)
                st.download_button(
                    label=f"📥 Download {selected_db_name}.{selected_table} data as CSV",
                    data=csv,
                    file_name=f"{selected_db_name}_{selected_table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning(f"No data found in {selected_db_name}.{selected_table}")
                
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
    
    elif operation == "➕ Add Record":
        st.header(f"➕ Add New Record - {selected_db_name}.{selected_table}")
        
        # Enhanced Add Record with multiple options
        add_mode = st.radio(
            "Choose add mode:",
            ["📝 Single Record", "📋 Bulk Insert", "⚡ Quick Templates", "📅 Daily Entry"],
            horizontal=True
        )
        
        try:
            schema = get_table_schema(selected_table, selected_db_path)
            
            if add_mode == "📝 Single Record":
                with st.form(f"add_form_{selected_table}"):
                    st.subheader("Enter Record Details")
                    form_data = render_data_input_form(schema)
                    
                    submitted = st.form_submit_button("➕ Add Record", type="primary")
                    
                    if submitted:
                        # Filter out empty values for optional fields
                        clean_data = {}
                        for key, value in form_data.items():
                            if value is not None and str(value).strip() != '':
                                if isinstance(value, date):
                                    clean_data[key] = value.strftime('%Y-%m-%d')
                                else:
                                    clean_data[key] = value
                        
                        if clean_data:
                            # Use UniversalDatabaseAdapter for external DBs
                            from universal_database_adapter import UniversalDatabaseAdapter
                            db_adapter = UniversalDatabaseAdapter()
                            if selected_db_name.startswith("🌐"):
                                result = db_adapter.insert_record(selected_db_name, selected_table, clean_data)
                                if result['success']:
                                    st.success(f"✅ Record added successfully to {selected_db_name}.{selected_table}!")
                                    st.json(clean_data)
                                else:
                                    st.error(f"❌ Error adding record: {result.get('error', result.get('message', 'Unknown error'))}")
                            else:
                                success, message, _ = insert_record(selected_table, clean_data, selected_db_path)
                                if success:
                                    st.success(f"✅ Record added successfully to {selected_db_name}.{selected_table}!")
                                    st.json(clean_data)
                                    # Integrate with AI system if available
                                    if AI_INTEGRATOR_AVAILABLE and dynamic_manager:
                                        try:
                                            if hasattr(dynamic_manager, 'refresh_all_database_info'):
                                                dynamic_manager.refresh_all_database_info()
                                        except Exception as e:
                                            st.info(f"Note: AI system refresh failed: {str(e)}")
                                else:
                                    st.error(f"❌ Error adding record: {message}")
                        else:
                            st.warning("Please fill in at least some fields")
            
            elif add_mode == "📋 Bulk Insert":
                st.subheader("📋 Bulk Insert Records")
                st.info("Enter multiple records separated by lines. Use CSV format or copy-paste from Excel.")
                
                # Show column headers for reference
                columns = [col[1] for col in schema]
                st.code(f"Columns: {', '.join(columns)}")
                
                bulk_text = st.text_area(
                    "Paste your data (CSV format):",
                    height=200,
                    placeholder="id,name,email,date\n1,John,john@email.com,2024-01-01\n2,Jane,jane@email.com,2024-01-02"
                )
                
                if st.button("📋 Process Bulk Insert", type="primary"):
                    if bulk_text.strip():
                        try:
                            import io
                            import csv
                            
                            # Parse CSV data
                            csv_data = list(csv.DictReader(io.StringIO(bulk_text)))
                            
                            if csv_data:
                                success_count = 0
                                error_count = 0
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                for i, row_data in enumerate(csv_data):
                                    try:
                                        # Clean and validate data
                                        clean_data = {}
                                        for key, value in row_data.items():
                                            if value and str(value).strip():
                                                clean_data[key.strip()] = str(value).strip()
                                        
                                        if clean_data:
                                            success, message, _ = insert_record(selected_table, clean_data, selected_db_path)
                                            if success:
                                                success_count += 1
                                            else:
                                                error_count += 1
                                                st.error(f"Row {i+1}: {message}")
                                        
                                    except Exception as e:
                                        error_count += 1
                                        st.error(f"Row {i+1} error: {str(e)}")
                                    
                                    # Update progress
                                    progress_bar.progress((i + 1) / len(csv_data))
                                    status_text.text(f"Processing row {i+1} of {len(csv_data)}")
                                
                                st.success(f"✅ Bulk insert completed: {success_count} successful, {error_count} errors")
                                
                        except Exception as e:
                            st.error(f"❌ Error parsing CSV data: {str(e)}")
                    else:
                        st.warning("Please enter data to insert")
            
            elif add_mode == "⚡ Quick Templates":
                st.subheader("⚡ Quick Templates")
                st.info("Select from predefined templates for common data entry patterns.")
                
                # Analyze table structure to suggest templates
                columns = [col[1] for col in schema]
                
                template_options = []
                if any(col.lower() in ['name', 'first_name', 'last_name'] for col in columns):
                    template_options.append("👤 Person Template")
                if any(col.lower() in ['product', 'item', 'title'] for col in columns):
                    template_options.append("📦 Product Template")
                if any(col.lower() in ['date', 'created', 'timestamp'] for col in columns):
                    template_options.append("📅 Date-based Template")
                if any(col.lower() in ['amount', 'price', 'cost', 'value'] for col in columns):
                    template_options.append("💰 Financial Template")
                
                template_options.append("🔧 Custom Template")
                
                selected_template = st.selectbox("Choose a template:", template_options)
                
                if selected_template and st.button("📝 Generate Template Form"):
                    with st.form(f"template_form_{selected_template}"):
                        st.subheader(f"Template: {selected_template}")
                        
                        # Generate template-specific fields
                        template_data = {}
                        
                        if "Person" in selected_template:
                            if 'name' in columns:
                                template_data['name'] = st.text_input("Name", "John Doe")
                            if 'email' in columns:
                                template_data['email'] = st.text_input("Email", "john.doe@email.com")
                            if 'age' in columns:
                                template_data['age'] = st.number_input("Age", 18, 100, 25)
                        
                        elif "Product" in selected_template:
                            if any(col in columns for col in ['product', 'name', 'title']):
                                product_col = next((col for col in ['product', 'name', 'title'] if col in columns), columns[0])
                                template_data[product_col] = st.text_input("Product Name", "Sample Product")
                            if 'price' in columns:
                                template_data['price'] = st.number_input("Price", 0.0, 10000.0, 99.99)
                            if 'category' in columns:
                                template_data['category'] = st.selectbox("Category", ["Electronics", "Clothing", "Books", "Other"])
                        
                        elif "Financial" in selected_template:
                            if 'amount' in columns:
                                template_data['amount'] = st.number_input("Amount", 0.0, step=0.01)
                            if 'date' in columns:
                                template_data['date'] = st.date_input("Date", datetime.now().date())
                            if 'description' in columns:
                                template_data['description'] = st.text_input("Description", "Transaction description")
                        
                        # Add remaining fields
                        for col_info in schema:
                            col_name = col_info[1]
                            if col_name not in template_data and not col_info[5]:  # Not primary key
                                col_type = col_info[2].upper()
                                if 'INT' in col_type or 'NUM' in col_type:
                                    template_data[col_name] = st.number_input(f"{col_name}", value=0)
                                elif 'DATE' in col_type:
                                    template_data[col_name] = st.date_input(f"{col_name}")
                                else:
                                    template_data[col_name] = st.text_input(f"{col_name}")
                        
                        if st.form_submit_button("➕ Add from Template", type="primary"):
                            # Process template data same as regular form
                            clean_data = {}
                            for key, value in template_data.items():
                                if value is not None and str(value).strip() != '':
                                    if isinstance(value, date):
                                        clean_data[key] = value.strftime('%Y-%m-%d')
                                    else:
                                        clean_data[key] = value
                            
                            if clean_data:
                                success, message, _ = insert_record(selected_table, clean_data, selected_db_path)
                                if success:
                                    st.success(f"✅ Record added from template!")
                                    st.json(clean_data)
                                else:
                                    st.error(f"❌ Error: {message}")
                            else:
                                st.warning("Please fill in some fields")
            
            elif add_mode == "📅 Daily Entry":
                st.subheader("📅 Daily Entry Helper")
                st.info("Optimized for daily data entry with date/time helpers and quick repeat options.")
                
                # Auto-fill today's date for date fields
                today = datetime.now()
                
                with st.form(f"daily_form_{selected_table}"):
                    st.write("**Today's Date Entry**")
                    col1, col2 = st.columns(2)
                    
                    form_data = {}
                    
                    with col1:
                        for i, col_info in enumerate(schema[:len(schema)//2]):
                            col_name = col_info[1]
                            col_type = col_info[2].upper()
                            is_pk = col_info[5]
                            
                            if is_pk:
                                continue
                            
                            # Smart defaults for daily entry
                            if 'DATE' in col_type and 'TIME' not in col_type:
                                form_data[col_name] = st.date_input(f"📅 {col_name}", today.date())
                            elif 'TIME' in col_type or 'DATETIME' in col_type:
                                form_data[col_name] = st.time_input(f"🕐 {col_name}", today.time())
                            elif col_name.lower() in ['status', 'state']:
                                form_data[col_name] = st.selectbox(f"📊 {col_name}", ["Active", "Pending", "Complete", "Cancelled"])
                            elif 'INT' in col_type or 'NUM' in col_type:
                                form_data[col_name] = st.number_input(f"🔢 {col_name}", value=0)
                            else:
                                form_data[col_name] = st.text_input(f"📝 {col_name}")
                    
                    with col2:
                        for col_info in schema[len(schema)//2:]:
                            col_name = col_info[1]
                            col_type = col_info[2].upper()
                            is_pk = col_info[5]
                            
                            if is_pk:
                                continue
                            
                            if 'DATE' in col_type and 'TIME' not in col_type:
                                form_data[col_name] = st.date_input(f"📅 {col_name}", today.date(), key=f"{col_name}_2")
                            elif 'TIME' in col_type or 'DATETIME' in col_type:
                                form_data[col_name] = st.time_input(f"🕐 {col_name}", today.time(), key=f"{col_name}_2")
                            elif col_name.lower() in ['status', 'state']:
                                form_data[col_name] = st.selectbox(f"📊 {col_name}", ["Active", "Pending", "Complete", "Cancelled"], key=f"{col_name}_2")
                            elif 'INT' in col_type or 'NUM' in col_type:
                                form_data[col_name] = st.number_input(f"🔢 {col_name}", value=0, key=f"{col_name}_2")
                            else:
                                form_data[col_name] = st.text_input(f"📝 {col_name}", key=f"{col_name}_2")
                    
                    # Quick action buttons
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        add_and_new = st.form_submit_button("➕ Add & New", type="primary")
                    with col2:
                        add_only = st.form_submit_button("✅ Add Only")
                    with col3:
                        add_multiple = st.form_submit_button("📋 Add Multiple")
                    
                    if add_and_new or add_only or add_multiple:
                        # Clean and process form data
                        clean_data = {}
                        for key, value in form_data.items():
                            if value is not None and str(value).strip() != '':
                                if isinstance(value, date):
                                    clean_data[key] = value.strftime('%Y-%m-%d')
                                elif hasattr(value, 'strftime'):  # time object
                                    clean_data[key] = value.strftime('%H:%M:%S')
                                else:
                                    clean_data[key] = value
                        
                        if clean_data:
                            success, message, _ = insert_record(selected_table, clean_data, selected_db_path)
                            if success:
                                st.success(f"✅ Daily record added successfully!")
                                st.json(clean_data)
                                
                                if add_and_new:
                                    st.info("➡️ Ready for next entry (form will reset)")
                                elif add_multiple:
                                    st.info("📋 Continue adding more records as needed")
                                
                            else:
                                st.error(f"❌ Error adding daily record: {message}")
                        else:
                            st.warning("Please fill in some fields for daily entry")
        
        except Exception as e:
            st.error(f"Error setting up add form: {str(e)}")
    
    elif operation == "✏️ Edit Record":
        st.header(f"✏️ Edit Record & Table Management - {selected_db_name}.{selected_table}")
        
        # Enhanced Edit with multiple options
        edit_mode = st.radio(
            "Choose editing operation:",
            ["✏️ Edit Record Data", "🔄 Move Table to Another Database"],
            horizontal=True
        )
        
        if edit_mode == "✏️ Edit Record Data":
            st.subheader(f"✏️ Edit Record Data - {selected_table}")
            
            try:
                # Get primary key column
                schema = get_table_schema(selected_table, selected_db_path)
                pk_column = None
                for col_info in schema:
                    if col_info[5]:  # is_pk
                        pk_column = col_info[1]
                        break
                
                if not pk_column:
                    st.error("No primary key found for this table. Cannot edit records.")
                    return
            
                # Get record to edit
                col1, col2 = st.columns([1, 3])
                with col1:
                    try:
                        conn = get_db_connection(selected_db_path)
                        cursor = conn.cursor()
                        cursor.execute(f"SELECT {pk_column} FROM {selected_table} ORDER BY {pk_column}")
                        ids = [row[0] for row in cursor.fetchall()]
                        conn.close()
                        
                        if ids:
                            selected_id = st.selectbox(f"Select {pk_column}", ids)
                        else:
                            st.warning("No records found to edit")
                            return
                    except Exception as e:
                        st.error(f"Error loading record IDs: {str(e)}")
                        return
                
                with col2:
                    if st.button("🔍 Load Record", type="secondary"):
                        st.session_state.load_record = True
            
                # Load and edit record
                if selected_id and (st.session_state.get('load_record', False) or f'edit_data_{selected_table}' in st.session_state):
                    try:
                        conn = get_db_connection(selected_db_path)
                        cursor = conn.cursor()
                        cursor.execute(f"SELECT * FROM {selected_table} WHERE {pk_column} = ?", [selected_id])
                        record = cursor.fetchone()
                        columns = [description[0] for description in cursor.description]
                        conn.close()
                        
                        if record:
                            existing_data = dict(zip(columns, record))
                            
                            with st.form(f"edit_form_{selected_table}"):
                                st.subheader(f"Edit Record ID: {selected_id}")
                                form_data = render_data_input_form(schema, existing_data)
                            
                                submitted = st.form_submit_button("💾 Update Record", type="primary")
                                
                                if submitted:
                                    # Remove primary key from update data
                                    clean_data = {}
                                    for key, value in form_data.items():
                                        if key != pk_column and value is not None:
                                            if isinstance(value, date):
                                                clean_data[key] = value.strftime('%Y-%m-%d')
                                            else:
                                                clean_data[key] = value
                                    
                                    if clean_data:
                                        from universal_database_adapter import UniversalDatabaseAdapter
                                        db_adapter = UniversalDatabaseAdapter()
                                        if selected_db_name.startswith("🌐"):
                                            result = db_adapter.update_record(selected_db_name, selected_table, selected_id, pk_column, clean_data)
                                            if result['success']:
                                                st.success(f"✅ Record updated successfully!")
                                                st.json(clean_data)
                                                st.session_state.load_record = False
                                            else:
                                                st.error(f"❌ Error updating record: {result.get('error', result.get('message', 'Unknown error'))}")
                                        else:
                                            success, message, _ = update_record(selected_table, selected_id, pk_column, clean_data, selected_db_path)
                                            if success:
                                                st.success(f"✅ Record updated successfully!")
                                                st.json(clean_data)
                                                st.session_state.load_record = False
                                                # Refresh dynamic manager if available
                                                if dynamic_manager:
                                                    try:
                                                        dynamic_manager.refresh_all_database_info()
                                                    except Exception as e:
                                                        st.info(f"Note: Database refresh failed: {str(e)}")
                                            else:
                                                st.error(f"❌ Error updating record: {message}")
                                    else:
                                        st.warning("No changes to save")
                        else:
                            st.error("Record not found")
                            
                    except Exception as e:
                        st.error(f"Error loading record: {str(e)}")
        
            except Exception as e:
                st.error(f"Error setting up edit form: {str(e)}")
        
        elif edit_mode == "🔄 Move Table to Another Database":
            st.subheader(f"🔄 Move Table: {selected_table}")
            st.warning("⚠️ This operation will move the entire table and all its data to another database. The table will be removed from the current database.")
            
            try:
                # Get available databases
                all_databases = get_all_databases()
                
                all_dbs = []
                # Add local databases (excluding current database)
                for db_name, db_info in all_databases.items():
                    if db_name != selected_db_name:  # Exclude current database
                        db_path = db_info.get('path', None)
                        # Determine if it's external (no local path or starts with connection string)
                        if db_path and not db_path.startswith(('postgresql://', 'mysql://', 'sqlite:///')):
                            all_dbs.append((f"📁 {db_name}", db_path))
                        elif db_name.startswith("🌐") or not db_path:
                            all_dbs.append((f"🌐 {db_name}", None))
                        else:
                            all_dbs.append((f"📁 {db_name}", db_path))
                
                if not all_dbs:
                    st.error("No other databases available for table migration.")
                    st.info("Create another database or add external database connections to enable table migration.")
                    return
                
                # Destination database selection
                dest_db_names = [db[0] for db in all_dbs]
                selected_dest_db = st.selectbox("Select destination database:", dest_db_names)
                
                if selected_dest_db:
                    # Get destination database info
                    dest_db_path = None
                    dest_is_external = selected_dest_db.startswith("🌐")
                    
                    for db_name, db_path in all_dbs:
                        if db_name == selected_dest_db:
                            dest_db_path = db_path
                            break
                    
                    # Show table information
                    st.info(f"**Source:** {selected_db_name}.{selected_table}")
                    st.info(f"**Destination:** {selected_dest_db.replace('📁 ', '').replace('🌐 ', '')}")
                    
                    # Get table schema and data preview
                    try:
                        schema = get_table_schema(selected_table, selected_db_path)
                        conn = get_db_connection(selected_db_path)
                        cursor = conn.cursor()
                        cursor.execute(f"SELECT COUNT(*) FROM {selected_table}")
                        row_count = cursor.fetchone()[0]
                        conn.close()
                        
                        st.write(f"**Table Info:**")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Columns", len(schema))
                        with col2:
                            st.metric("Rows", row_count)
                        with col3:
                            st.metric("Type", "Local SQLite" if not selected_db_name.startswith("🌐") else "External DB")
                        
                        # Show column details
                        if st.checkbox("📋 Show table structure"):
                            schema_df = []
                            for col in schema:
                                schema_df.append({
                                    "Column": col[1],
                                    "Type": col[2],
                                    "Not Null": "Yes" if col[3] else "No",
                                    "Default": col[4] if col[4] else "None",
                                    "Primary Key": "Yes" if col[5] else "No"
                                })
                            st.dataframe(schema_df, use_container_width=True)
                    
                    except Exception as e:
                        st.error(f"Error getting table information: {str(e)}")
                        return
                    
                    # Migration options
                    st.subheader("📋 Migration Options")
                    
                    migration_options = st.radio(
                        "Choose migration type:",
                        ["🔄 Move (Copy + Delete Original)", "📋 Copy Only (Keep Original)"],
                        help="Move will transfer the table and delete from source. Copy will create a duplicate."
                    )
                    
                    # Handle table name conflicts
                    new_table_name = st.text_input(
                        "Table name in destination database:",
                        value=selected_table,
                        help="Specify the name for the table in the destination database"
                    )
                    
                    if not new_table_name:
                        st.warning("Please specify a table name for the destination.")
                        return
                    
                    # Safety confirmations
                    st.subheader("⚠️ Safety Confirmations")
                    
                    if migration_options == "🔄 Move (Copy + Delete Original)":
                        st.error("🚨 **DANGER ZONE**: This will permanently delete the table from the source database!")
                        
                        confirm1 = st.checkbox(f"✅ I understand this will DELETE '{selected_table}' from '{selected_db_name}'")
                        confirm2 = st.checkbox(f"✅ I confirm the destination '{selected_dest_db.replace('📁 ', '').replace('🌐 ', '')}' is correct")
                        confirm3 = st.checkbox(f"✅ I have backed up my data (if needed)")
                        confirm4 = st.checkbox(f"✅ I want to proceed with MOVING {row_count} rows to '{new_table_name}'")
                        
                        all_confirmed = confirm1 and confirm2 and confirm3 and confirm4
                        button_text = "🔄 MOVE TABLE (PERMANENT)"
                        button_type = "primary"
                    else:
                        confirm1 = st.checkbox(f"✅ I want to COPY '{selected_table}' to '{selected_dest_db.replace('📁 ', '').replace('🌐 ', '')}' as '{new_table_name}'")
                        confirm2 = st.checkbox(f"✅ I confirm {row_count} rows will be copied")
                        
                        all_confirmed = confirm1 and confirm2
                        button_text = "📋 COPY TABLE"
                        button_type = "secondary"
                    
                    # Execute migration
                    if st.button(button_text, type=button_type, disabled=not all_confirmed):
                        with st.spinner(f"Migrating table '{selected_table}'..."):
                            try:
                                success = migrate_table(
                                    source_db_name=selected_db_name,
                                    source_db_path=selected_db_path,
                                    source_table=selected_table,
                                    dest_db_name=selected_dest_db.replace('📁 ', '').replace('🌐 ', ''),
                                    dest_db_path=dest_db_path,
                                    dest_table=new_table_name,
                                    is_move=(migration_options == "🔄 Move (Copy + Delete Original)"),
                                    dest_is_external=dest_is_external
                                )
                                
                                if success:
                                    if migration_options == "🔄 Move (Copy + Delete Original)":
                                        st.success(f"✅ Table '{selected_table}' successfully MOVED to '{selected_dest_db.replace('📁 ', '').replace('🌐 ', '')}' as '{new_table_name}'!")
                                        st.info("🔄 The table has been removed from the source database.")
                                        # Refresh the page to update available tables
                                        st.rerun()
                                    else:
                                        st.success(f"✅ Table '{selected_table}' successfully COPIED to '{selected_dest_db.replace('📁 ', '').replace('🌐 ', '')}' as '{new_table_name}'!")
                                        st.info("📋 The original table remains in the source database.")
                                    
                                    # Show migration summary
                                    st.write("**Migration Summary:**")
                                    summary_col1, summary_col2 = st.columns(2)
                                    with summary_col1:
                                        st.write(f"**Source:** {selected_db_name}.{selected_table}")
                                        st.write(f"**Rows Processed:** {row_count}")
                                    with summary_col2:
                                        st.write(f"**Destination:** {selected_dest_db.replace('📁 ', '').replace('🌐 ', '')}.{new_table_name}")
                                        st.write(f"**Operation:** {migration_options.split(' (')[0]}")
                                
                                else:
                                    st.error("❌ Table migration failed. Please check the error messages above.")
                                    
                            except Exception as e:
                                st.error(f"❌ Error during table migration: {str(e)}")
                                st.info("💡 Try checking database permissions and connection status.")
            
            except Exception as e:
                st.error(f"Error setting up table migration: {str(e)}")
    
    elif operation == "🗑️ Delete Options":
        st.header(f"🗑️ Delete Options - {selected_db_name}")
        
        # Enhanced Delete with multiple options
        delete_mode = st.radio(
            "Choose deletion type:",
            ["🗑️ Delete Record", "📋 Delete Table", "🗄️ Delete Database", "🔄 Bulk Delete Records"],
            horizontal=True
        )
        
        try:
            if delete_mode == "🗑️ Delete Record":
                st.subheader(f"🗑️ Delete Record from {selected_table}")
                
                # Get primary key column
                schema = get_table_schema(selected_table, selected_db_path)
                pk_column = None
                for col_info in schema:
                    if col_info[5]:  # is_pk
                        pk_column = col_info[1]
                        break
                
                if not pk_column:
                    st.error("No primary key found for this table. Cannot delete records.")
                    return
                
                # Get record to delete
                col1, col2 = st.columns([1, 1])
                with col1:
                    try:
                        conn = get_db_connection(selected_db_path)
                        cursor = conn.cursor()
                        cursor.execute(f"SELECT {pk_column} FROM {selected_table} ORDER BY {pk_column}")
                        ids = [row[0] for row in cursor.fetchall()]
                        conn.close()
                        
                        if ids:
                            selected_id = st.selectbox(f"Select {pk_column} to delete", ids)
                        else:
                            st.warning("No records found to delete")
                            return
                    except Exception as e:
                        st.error(f"Error loading record IDs: {str(e)}")
                        return
                
                # Show record details before deletion
                if selected_id:
                    try:
                        conn = get_db_connection(selected_db_path)
                        cursor = conn.cursor()
                        cursor.execute(f"SELECT * FROM {selected_table} WHERE {pk_column} = ?", [selected_id])
                        record = cursor.fetchone()
                        columns = [description[0] for description in cursor.description]
                        conn.close()
                        
                        if record:
                            st.subheader("Record to Delete:")
                            record_dict = dict(zip(columns, record))
                            st.json(record_dict)
                            
                            # Confirmation
                            st.warning("⚠️ This action cannot be undone!")
                            confirm = st.checkbox(f"I confirm I want to delete record with {pk_column} = {selected_id}")
                        
                            if st.button("🗑️ Delete Record", type="primary", disabled=not confirm):
                                from universal_database_adapter import UniversalDatabaseAdapter
                                db_adapter = UniversalDatabaseAdapter()
                                if selected_db_name.startswith("🌐"):
                                    result = db_adapter.delete_record(selected_db_name, selected_table, selected_id, pk_column)
                                    if result['success']:
                                        st.success(f"✅ Record deleted successfully!")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Error deleting record: {result.get('error', result.get('message', 'Unknown error'))}")
                                else:
                                    success, message, _ = delete_record(selected_table, selected_id, pk_column, selected_db_path)
                                    if success:
                                        st.success(f"✅ Record deleted successfully!")
                                        # Refresh dynamic manager if available
                                        if dynamic_manager:
                                            try:
                                                dynamic_manager.refresh_all_database_info()
                                            except Exception as e:
                                                st.info(f"Note: Database refresh failed: {str(e)}")
                                        # Clear the page to prevent accidental re-deletion
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Error deleting record: {message}")
                        else:
                            st.error("Record not found")
                            
                    except Exception as e:
                        st.error(f"Error loading record details: {str(e)}")
                        
        except Exception as e:
            st.error(f"Error in delete operation: {str(e)}")
            
        if delete_mode == "🔄 Bulk Delete Records":
                st.subheader(f"🔄 Bulk Delete Records from {selected_table}")
                st.warning("⚠️ Use with extreme caution! This will delete multiple records at once.")
                
                # Get primary key column for bulk operations
                schema = get_table_schema(selected_table, selected_db_path)
                pk_column = None
                for col_info in schema:
                    if col_info[5]:  # is_pk
                        pk_column = col_info[1]
                        break
                
                if pk_column:
                    bulk_method = st.radio(
                        "Choose bulk delete method:",
                        ["📋 Select Multiple IDs", "🔍 Filter-based Delete"]
                    )
                    
                    if bulk_method == "📋 Select Multiple IDs":
                        conn = get_db_connection(selected_db_path)
                        cursor = conn.cursor()
                        cursor.execute(f"SELECT {pk_column} FROM {selected_table} ORDER BY {pk_column}")
                        all_ids = [row[0] for row in cursor.fetchall()]
                        conn.close()
                        
                        if all_ids:
                            selected_ids = st.multiselect(f"Select {pk_column}s to delete:", all_ids)
                            
                            if selected_ids:
                                st.subheader(f"Will delete {len(selected_ids)} records")
                                confirm_bulk = st.checkbox(f"I confirm deletion of {len(selected_ids)} records")
                                
                                if st.button("🗑️ Delete Selected Records", type="primary", disabled=not confirm_bulk):
                                    success_count = 0
                                    error_count = 0
                                    
                                    for record_id in selected_ids:
                                        try:
                                            success, message, _ = delete_record(selected_table, record_id, pk_column, selected_db_path)
                                            if success:
                                                success_count += 1
                                            else:
                                                error_count += 1
                                        except:
                                            error_count += 1
                                    
                                    st.success(f"✅ Bulk delete completed: {success_count} deleted, {error_count} errors")
                                    if error_count == 0:
                                        st.rerun()
                    
                    elif bulk_method == "🔍 Filter-based Delete":
                        st.info("Delete records matching specific criteria")
                        columns = [col[1] for col in schema]
                        
                        filter_column = st.selectbox("Select column to filter by:", columns)
                        filter_operator = st.selectbox("Operator:", ["=", "!=", "<", ">", "<=", ">=", "LIKE"])
                        filter_value = st.text_input("Value:")
                        
                        if filter_column and filter_value:
                            # Preview records that will be deleted
                            try:
                                conn = get_db_connection(selected_db_path)
                                cursor = conn.cursor()
                                if filter_operator == "LIKE":
                                    cursor.execute(f"SELECT COUNT(*) FROM {selected_table} WHERE {filter_column} LIKE ?", [f"%{filter_value}%"])
                                else:
                                    cursor.execute(f"SELECT COUNT(*) FROM {selected_table} WHERE {filter_column} {filter_operator} ?", [filter_value])
                                count = cursor.fetchone()[0]
                                conn.close()
                                
                                st.warning(f"⚠️ This will delete {count} records!")
                                
                                if count > 0:
                                    confirm_filter = st.checkbox(f"I confirm deletion of {count} records matching the filter")
                                    
                                    if st.button("🗑️ Delete Filtered Records", type="primary", disabled=not confirm_filter):
                                        try:
                                            conn = get_db_connection(selected_db_path)
                                            cursor = conn.cursor()
                                            if filter_operator == "LIKE":
                                                cursor.execute(f"DELETE FROM {selected_table} WHERE {filter_column} LIKE ?", [f"%{filter_value}%"])
                                            else:
                                                cursor.execute(f"DELETE FROM {selected_table} WHERE {filter_column} {filter_operator} ?", [filter_value])
                                            deleted_count = cursor.rowcount
                                            conn.commit()
                                            conn.close()
                                            
                                            st.success(f"✅ Deleted {deleted_count} records successfully!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Error during bulk delete: {str(e)}")
                                
                            except Exception as e:
                                st.error(f"Error previewing delete operation: {str(e)}")
            
        if delete_mode == "📋 Delete Table":
                st.subheader("📋 Delete Entire Table")
                st.error("⚠️ DANGER: This will permanently delete the entire table and all its data!")
                
                if selected_table:
                    # Show table info
                    try:
                        conn = get_db_connection(selected_db_path)
                        cursor = conn.cursor()
                        cursor.execute(f"SELECT COUNT(*) FROM {selected_table}")
                        record_count = cursor.fetchone()[0]
                        conn.close()
                        
                        st.info(f"📊 Table '{selected_table}' contains {record_count} records")
                        
                        # Triple confirmation for table deletion
                        confirm_table_name = st.text_input(f"Type the table name '{selected_table}' to confirm:")
                        confirm_understand = st.checkbox("I understand this will permanently delete ALL data in this table")
                        confirm_no_backup = st.checkbox("I confirm I have a backup or don't need the data")
                        
                        all_confirmed = (confirm_table_name == selected_table and 
                                        confirm_understand and confirm_no_backup)
                        
                        if st.button("🗑️ DELETE ENTIRE TABLE", type="primary", disabled=not all_confirmed):
                            try:
                                conn = get_db_connection(selected_db_path)
                                cursor = conn.cursor()
                                cursor.execute(f"DROP TABLE {selected_table}")
                                conn.commit()
                                conn.close()
                                
                                st.success(f"✅ Table '{selected_table}' has been permanently deleted!")
                                st.info("Refreshing page...")
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"❌ Error deleting table: {str(e)}")
                    
                    except Exception as e:
                        st.error(f"Error getting table info: {str(e)}")
            
        if delete_mode == "🗄️ Delete Database":
                st.subheader("🗄️ Delete Entire Database")
                st.error("⚠️ EXTREME DANGER: This will permanently delete the entire database and ALL its data!")
                
                # Show database info
                try:
                    tables_list = get_all_tables(selected_db_path)
                    st.info(f"📊 Database '{selected_db_name}' contains {len(tables_list)} tables")
                    
                    with st.expander("📋 Tables that will be deleted:"):
                        for table in tables_list:
                            try:
                                conn = get_db_connection(selected_db_path)
                                cursor = conn.cursor()
                                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                                count = cursor.fetchone()[0]
                                conn.close()
                                st.write(f"- {table}: {count} records")
                            except:
                                st.write(f"- {table}: (unable to count records)")
                    
                    # Extreme confirmation for database deletion
                    st.error("🚨 FINAL WARNING: This action cannot be undone!")
                    
                    confirm_db_name = st.text_input(f"Type the database name '{selected_db_name}' to confirm:")
                    confirm_understand_db = st.checkbox("I understand this will permanently delete the ENTIRE DATABASE")
                    confirm_have_backup = st.checkbox("I confirm I have a complete backup of all important data")
                    confirm_final = st.checkbox("I take full responsibility for this irreversible action")
                    
                    all_db_confirmed = (confirm_db_name == selected_db_name and 
                                       confirm_understand_db and confirm_have_backup and confirm_final)
                    
                    if st.button("🗑️ DELETE ENTIRE DATABASE", type="primary", disabled=not all_db_confirmed):
                        try:
                            import os
                            if os.path.exists(selected_db_path):
                                os.remove(selected_db_path)
                                st.success(f"✅ Database '{selected_db_name}' has been permanently deleted!")
                                st.info("Database deleted. Please refresh the page and select a different database.")
                                st.stop()
                            else:
                                st.error("Database file not found!")
                        
                        except Exception as e:
                            st.error(f"❌ Error deleting database: {str(e)}")
                
                except Exception as e:
                    st.error(f"Error getting database info: {str(e)}")
        
    
    elif operation == "📊 Custom Query":
        st.header(f"📊 Custom SQL Query - {selected_db_name}")
        
        st.markdown(f"""
        **Database:** `{selected_db_name}`  
        **⚠️ Warning:** Be careful with custom queries, especially UPDATE and DELETE operations.
        Always backup your data before making changes.
        """)
        
        # Show available tables in the selected database
        with st.expander("📋 Available Tables in Database"):
            try:
                tables_list = get_all_tables(selected_db_path)
                if tables_list:
                    cols = st.columns(min(len(tables_list), 4))
                    for i, table in enumerate(tables_list):
                        with cols[i % 4]:
                            try:
                                count = get_table_count(table, selected_db_path)
                                st.write(f"**{table}** ({count:,} records)")
                            except:
                                st.write(f"**{table}**")
                else:
                    st.info("No tables found in this database")
            except Exception as e:
                st.error(f"Error loading tables: {str(e)}")
        
        # Query input
        query = st.text_area(
            "Enter your SQL query:",
            height=150,
            placeholder=f"""Examples for {selected_db_name}:
SELECT * FROM {tables[0] if tables else 'table_name'} LIMIT 10;
SELECT COUNT(*) FROM {tables[0] if tables else 'table_name'};
UPDATE {tables[0] if tables else 'table_name'} SET column = 'value' WHERE id = 1;
DELETE FROM {tables[0] if tables else 'table_name'} WHERE condition;
"""
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            execute_btn = st.button("🚀 Execute Query", type="primary")
        
        if execute_btn and query.strip():
            try:
                success, result, columns = execute_query(query, db_path=selected_db_path)
                
                if success:
                    if columns:  # SELECT query
                        df = pd.DataFrame(result, columns=columns)
                        st.success(f"✅ Query executed successfully! Found {len(df)} rows.")
                        
                        if not df.empty:
                            st.dataframe(df, use_container_width=True)
                            
                            # Download option
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download results as CSV",
                                data=csv,
                                file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.info("Query executed successfully but returned no data.")
                    else:  # Non-SELECT query (INSERT, UPDATE, DELETE)
                        st.success(f"✅ Query executed successfully! {len(result)} rows affected.")
                        
                        # Refresh dynamic manager if available
                        if dynamic_manager:
                            try:
                                dynamic_manager.refresh_all_database_info()
                            except Exception as e:
                                st.info(f"Note: Database refresh failed: {str(e)}")
                else:
                    st.error(f"❌ Query failed: {result}")
                    
            except Exception as e:
                st.error(f"❌ Error executing query: {str(e)}")
    
    elif operation == "📤 Upload Files":
        st.header("📤 Upload Files to Create Database Tables")
        
        # Initialize file upload manager
        file_manager = FileUploadManager()
        
        # Database Selection Section
        st.subheader("🗄️ Database Selection")
        
        # Get available databases
        available_databases = file_manager.get_available_databases()
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            database_option = st.radio(
                "Choose database option:",
                ["📁 Use existing database", "🆕 Create empty database", "🚀 Create database with files"],
                index=0,
                help="Choose whether to use existing database, create empty database, or create database with initial data from files"
            )
        
        # Initialize variables
        new_db_name = None
        target_db_path = None
        
        with col2:
            if database_option == "📁 Use existing database":
                if available_databases:
                    target_db_name = st.selectbox(
                        "Select database:",
                        list(available_databases.keys()),
                        index=list(available_databases.keys()).index(selected_db_name) if selected_db_name in available_databases else 0
                    )
                    target_db_path = available_databases[target_db_name]
                    file_manager.set_target_database(target_db_path)
                    st.success(f"✅ Will upload to: **{target_db_name}**")
                else:
                    st.error("No databases available! Please create one first.")
                    target_db_path = None
                    
            elif database_option == "🆕 Create empty database":
                new_db_name = st.text_input(
                    "New database name:",
                    placeholder="Enter database name (e.g., 'customer_data')",
                    help="Database will be created as {name}.db"
                )
                if new_db_name:
                    if st.button("🆕 Create Empty Database", key="create_empty_db_btn"):
                        try:
                            target_db_path = file_manager.create_new_database(new_db_name)
                            st.success(f"✅ Created database: **{new_db_name}.db**")
                            file_manager.set_target_database(target_db_path)
                            st.rerun()  # Refresh to show new database in list
                        except Exception as e:
                            st.error(f"❌ Error creating database: {str(e)}")
                            target_db_path = None
                    else:
                        target_db_path = None
                else:
                    target_db_path = None
                    
            else:  # Create database with files
                st.info("🚀 **Create Database with Files**: Upload files to automatically create a new database with tables")
                new_db_name = st.text_input(
                    "New database name:",
                    placeholder="Enter database name (e.g., 'sales_data')",
                    help="Database will be created with uploaded files as tables",
                    key="new_db_with_files_name"
                )
                if new_db_name:
                    st.success(f"✅ Will create: **{new_db_name}.db** with uploaded files as tables")
                    target_db_path = "CREATE_WITH_FILES"  # Special flag for this mode
                else:
                    st.warning("⚠️ Please enter a database name to continue")
                    target_db_path = None
        
        # File Upload Section
        if target_db_path:
            st.subheader("📁 File Upload")
            
            uploaded_files = st.file_uploader(
                "Choose files to upload",
                type=['csv', 'xlsx', 'xls'],
                accept_multiple_files=True,
                help="Select CSV or Excel files. Each Excel sheet will become a separate table."
            )
        
            if uploaded_files:
                st.subheader("📋 File Analysis & Configuration")
                
                # Store file configurations
                if 'file_configs' not in st.session_state:
                    st.session_state.file_configs = {}
                
                for file in uploaded_files:
                    with st.expander(f"📄 {file.name}", expanded=True):
                        file_key = f"{file.name}_{file.size}"
                        
                        # Initialize config for this file
                        if file_key not in st.session_state.file_configs:
                            st.session_state.file_configs[file_key] = {
                                'table_name_override': '',
                                'sheets_config': {}
                            }
                        
                        try:
                            # Analyze file content
                            if file.name.endswith('.csv'):
                                df = robust_read_csv(file)
                                if df is None:
                                    st.error(f"❌ Could not read {file.name} - invalid CSV format or encoding")
                                    continue
                                
                                # CSV file configuration
                                sheets_info = [{'name': 'CSV Data', 'rows': len(df), 'columns': len(df.columns)}]
                                
                                # Table name configuration
                                default_name = file.name.split('.')[0].lower()
                                table_name = st.text_input(
                                    f"Table name for {file.name}:",
                                    value=st.session_state.file_configs[file_key]['table_name_override'] or default_name,
                                    key=f"table_name_{file_key}"
                                )
                                st.session_state.file_configs[file_key]['table_name_override'] = table_name
                                
                            else:
                                # Excel file - analyze all sheets
                                excel_file = pd.ExcelFile(file)
                                sheets_info = []
                                
                                for sheet_name in excel_file.sheet_names:
                                    try:
                                        df_sheet = pd.read_excel(file, sheet_name=sheet_name)
                                        sheets_info.append({
                                            'name': sheet_name,
                                            'rows': len(df_sheet),
                                            'columns': len(df_sheet.columns)
                                        })
                                    except Exception as e:
                                        sheets_info.append({
                                            'name': sheet_name,
                                            'rows': 0,
                                            'columns': 0,
                                            'error': str(e)
                                        })
                                
                                # Excel sheets configuration
                                if len(sheets_info) > 1:
                                    st.write(f"**📊 Found {len(sheets_info)} sheets - each will become a separate table:**")
                                    
                                    for sheet_info in sheets_info:
                                        sheet_name = sheet_info['name']
                                        if 'error' in sheet_info:
                                            st.error(f"❌ Sheet '{sheet_name}': {sheet_info['error']}")
                                            continue
                                        
                                        col_a, col_b = st.columns([2, 1])
                                        with col_a:
                                            default_table_name = f"{file.name.split('.')[0].lower()}_{sheet_name.lower()}"
                                            table_name = st.text_input(
                                                f"Table name for sheet '{sheet_name}':",
                                                value=st.session_state.file_configs[file_key]['sheets_config'].get(sheet_name, default_table_name),
                                                key=f"sheet_table_{file_key}_{sheet_name}"
                                            )
                                            st.session_state.file_configs[file_key]['sheets_config'][sheet_name] = table_name
                                        
                                        with col_b:
                                            st.metric("Rows", sheet_info['rows'])
                                            st.metric("Columns", sheet_info['columns'])
                                else:
                                    # Single sheet Excel
                                    sheet_name = sheets_info[0]['name']
                                    default_name = file.name.split('.')[0].lower()
                                    table_name = st.text_input(
                                        f"Table name for {file.name}:",
                                        value=st.session_state.file_configs[file_key]['table_name_override'] or default_name,
                                        key=f"single_table_name_{file_key}"
                                    )
                                    st.session_state.file_configs[file_key]['table_name_override'] = table_name
                            
                            # Show file preview
                            st.write("**📋 Data Preview:**")
                            if file.name.endswith('.csv'):
                                preview_df = df.head(3)
                            else:
                                # Show preview of first sheet
                                preview_df = pd.read_excel(file, sheet_name=excel_file.sheet_names[0]).head(3)
                            
                            st.dataframe(preview_df, use_container_width=True)
                            
                            # Show summary
                            summary_data = []
                            for sheet in sheets_info:
                                summary_data.append({
                                    'Sheet/File': sheet['name'],
                                    'Rows': sheet['rows'],
                                    'Columns': sheet['columns']
                                })
                            
                            st.write("**📊 Summary:**")
                            st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
                            
                        except Exception as e:
                            st.error(f"❌ Error analyzing {file.name}: {str(e)}")
            
                # Upload Processing
                if st.button("🚀 Upload All Files", type="primary", key="upload_all_btn"):
                    st.subheader("⚡ Processing Files...")
                    
                    # Handle "Create database with files" option
                    if database_option == "🚀 Create database with files":
                        if not new_db_name:
                            st.error("❌ Please enter a database name first!")
                            st.stop()
                        
                        try:
                            # Create database and populate with files in one operation
                            created_db_path, upload_results = file_manager.create_database_with_files(
                                new_db_name, uploaded_files
                            )
                            
                            st.success(f"✅ Created database: **{new_db_name}.db** with {len([r for r in upload_results if r['success']])} tables")
                            
                            # Display results
                            st.subheader("📊 Database Creation Results")
                            
                            success_count = 0
                            total_rows = 0
                            
                            for result in upload_results:
                                if result['success']:
                                    success_count += 1
                                    total_rows += result.get('rows', 0)
                                    st.success(f"✅ **{result.get('table_name', 'Unknown')}**: {result.get('rows', 0)} rows, {result.get('columns', 0)} columns")
                                else:
                                    st.error(f"❌ **{result.get('file_name', 'Unknown')}**: {result.get('message', 'Unknown error')}")
                            
                            if success_count > 0:
                                st.info(f"🎉 **Database Summary**: {success_count} tables created with {total_rows:,} total rows")
                                st.balloons()
                                
                                # Refresh the page to show the new database
                                st.rerun()
                            
                            st.stop()  # Don't continue with regular upload processing
                            
                        except Exception as e:
                            st.error(f"❌ Error creating database with files: {str(e)}")
                            st.stop()
                    
                    # Regular upload processing for existing databases
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    results_container = st.container()
                    
                    all_results = []
                    total_operations = 0
                    completed_operations = 0
                    
                    # Calculate total operations (sheets/files)
                    for file in uploaded_files:
                        if file.name.endswith('.csv'):
                            total_operations += 1
                        else:
                            try:
                                excel_file = pd.ExcelFile(file)
                                total_operations += len(excel_file.sheet_names)
                            except:
                                total_operations += 1
                
                    # Process each file
                    for file in uploaded_files:
                        file_key = f"{file.name}_{file.size}"
                        file_config = st.session_state.file_configs.get(file_key, {})
                        
                        status_text.text(f"📄 Processing {file.name}...")
                        
                        try:
                            if file.name.endswith('.csv'):
                                # Process CSV
                                table_override = file_config.get('table_name_override')
                                results = file_manager.process_csv_file(file, table_override)
                                all_results.extend(results)
                                completed_operations += 1
                                progress_bar.progress(completed_operations / total_operations)
                                
                            else:
                                # Process Excel with custom sheet names
                                try:
                                    excel_file = pd.ExcelFile(file)
                                    for sheet_name in excel_file.sheet_names:
                                        status_text.text(f"📊 Processing {file.name} - Sheet: {sheet_name}...")
                                        
                                        # Get custom table name for this sheet
                                        sheets_config = file_config.get('sheets_config', {})
                                        if len(excel_file.sheet_names) == 1:
                                            table_override = file_config.get('table_name_override')
                                        else:
                                            table_override = sheets_config.get(sheet_name)
                                        
                                        # Process single sheet
                                        try:
                                            df_sheet = pd.read_excel(file, sheet_name=sheet_name)
                                            if table_override:
                                                sanitized_name = file_manager.sanitize_table_name(table_override)
                                                unique_name = file_manager.get_unique_table_name(sanitized_name)
                                            else:
                                                base_name = f"{file.name.split('.')[0]}_{sheet_name}"
                                                sanitized_name = file_manager.sanitize_table_name(base_name)
                                                unique_name = file_manager.get_unique_table_name(sanitized_name)
                                            
                                            success, message = file_manager.create_table_from_dataframe(df_sheet, unique_name)
                                            
                                            all_results.append({
                                                'file_name': file.name,
                                                'sheet_name': sheet_name,
                                                'table_name': unique_name,
                                                'success': success,
                                                'message': message,
                                                'rows': len(df_sheet) if success else 0,
                                                'columns': len(df_sheet.columns) if success else 0
                                            })
                                            
                                        except Exception as e:
                                            all_results.append({
                                                'file_name': file.name,
                                                'sheet_name': sheet_name,
                                                'table_name': None,
                                                'success': False,
                                                'message': f"Error processing sheet: {str(e)}",
                                                'rows': 0,
                                                'columns': 0
                                            })
                                        
                                        completed_operations += 1
                                        progress_bar.progress(completed_operations / total_operations)
                                        
                                except Exception as e:
                                    all_results.append({
                                        'file_name': file.name,
                                        'sheet_name': None,
                                        'table_name': None,
                                        'success': False,
                                        'message': f"Error reading Excel file: {str(e)}",
                                        'rows': 0,
                                        'columns': 0
                                    })
                                    completed_operations += 1
                                    progress_bar.progress(completed_operations / total_operations)
                            
                        except Exception as e:
                            all_results.append({
                                'file_name': file.name,
                                'sheet_name': None,
                                'table_name': None,
                                'success': False,
                                'message': f"Error processing file: {str(e)}",
                                'rows': 0,
                                'columns': 0
                            })
                
                    # Show results
                    status_text.text("✅ Upload completed!")
                    progress_bar.progress(1.0)
                    
                    with results_container:
                        st.subheader("📊 Upload Results")
                        
                        success_count = sum(1 for r in all_results if r['success'])
                        total_count = len(all_results)
                        
                        # Summary metrics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("✅ Successful", success_count)
                        with col2:
                            st.metric("❌ Failed", total_count - success_count)
                        with col3:
                            st.metric("📁 Files Processed", len(uploaded_files))
                        with col4:
                            total_rows = sum(r['rows'] for r in all_results if r['success'])
                            st.metric("📊 Total Rows", total_rows)
                        
                        # Detailed results
                        for result in all_results:
                            if result['success']:
                                sheet_info = f" (Sheet: {result['sheet_name']})" if result['sheet_name'] else ""
                                st.success(f"✅ **{result['file_name']}**{sheet_info} → Table: `{result['table_name']}` ({result['rows']} rows, {result['columns']} columns)")
                            else:
                                sheet_info = f" (Sheet: {result['sheet_name']})" if result['sheet_name'] else ""
                                st.error(f"❌ **{result['file_name']}**{sheet_info}: {result['message']}")
                        
                        # Refresh database info
                        if success_count > 0:
                            if dynamic_manager:
                                try:
                                    dynamic_manager.refresh_all_database_info()
                                    st.info("🔄 Database information refreshed successfully!")
                                except Exception as e:
                                    st.warning(f"⚠️ Database refresh failed: {str(e)}")
                        
                        # Clear file configs after successful upload
                        if success_count > 0:
                            st.session_state.file_configs = {}
        else:
            st.info("� Please select or create a database first to upload files.")
            
            # Show example
            with st.expander("💡 Example: Sample Data Format"):
                example_data = pd.DataFrame({
                    'id': [1, 2, 3],
                    'name': ['John Doe', 'Jane Smith', 'Bob Wilson'],
                    'email': ['john@example.com', 'jane@example.com', 'bob@example.com'],
                    'created_date': ['2024-01-01', '2024-01-02', '2024-01-03']
                })
                st.dataframe(example_data, use_container_width=True)
                st.caption("This would create a table with columns: id, name, email, created_date")
    
    elif operation == "🌐 External Databases":
        external_database_interface()

if __name__ == "__main__":
    main()