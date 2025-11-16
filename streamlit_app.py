"""
Streamlit Web Interface for SQL Agent with Database Management
A user-friendly web interface for the SQL Agent powered by Gemini and LangGraph
"""

import streamlit as st
import pandas as pd
import json
import sqlite3
from pathlib import Path
import traceback
import os
import subprocess
import sys

# Import our SQL Agent
from sql_agent import SQLAgent
from enhanced_sql_agent import EnhancedSQLAgent
from multi_database_manager import MultiDatabaseManager

def get_dynamic_database_stats():
    """Get dynamic statistics about all databases and tables"""
    stats = {
        'total_databases': 0,
        'total_tables': 0,
        'total_records': 0,
        'database_details': [],
        'recent_tables': []
    }
    
    try:
        multi_db_manager = MultiDatabaseManager()
        # Always refresh to get latest database configurations
        multi_db_manager.refresh_configuration()
        db_paths = multi_db_manager.get_databases()
        
        stats['total_databases'] = len(db_paths)
        
        for db_name, db_path_str in db_paths.items():
            db_path = Path(db_path_str)
            if db_path.exists():
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Get all tables in this database
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                    tables = cursor.fetchall()
                    table_names = [table[0] for table in tables]
                    
                    db_record_count = 0
                    table_details = []
                    
                    for table_name in table_names:
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                            table_count = cursor.fetchone()[0]
                            db_record_count += table_count
                            
                            table_details.append({
                                'name': table_name,
                                'records': table_count,
                                'database': db_name
                            })
                            
                            # Add to recent tables (for dynamic examples)
                            stats['recent_tables'].append({
                                'name': table_name,
                                'database': db_name,
                                'records': table_count
                            })
                        except:
                            continue
                    
                    stats['total_tables'] += len(table_names)
                    stats['total_records'] += db_record_count
                    
                    # Get database file size
                    db_size = db_path.stat().st_size / (1024 * 1024)  # MB
                    
                    stats['database_details'].append({
                        'name': db_name,
                        'tables': len(table_names),
                        'records': db_record_count,
                        'size_mb': round(db_size, 2),
                        'table_details': table_details
                    })
                    
                    conn.close()
                except Exception as e:
                    continue
                    
    except Exception as e:
        st.error(f"Error loading database statistics: {str(e)}")
    
    return stats

def generate_dynamic_example_questions(stats):
    """Generate example questions based on current database content"""
    questions = []
    
    if not stats['recent_tables']:
        # Fallback to generic questions if no tables found
        return [
            "Show me the database schema",
            "How many tables are in the database?",
            "What data is available to query?"
        ]
    
    # Get unique table names
    table_names = list(set([table['name'] for table in stats['recent_tables'][:10]]))
    
    # Generate questions based on actual tables
    for table_name in table_names[:5]:  # Limit to 5 tables
        table_info = next((t for t in stats['recent_tables'] if t['name'] == table_name), None)
        if table_info:
            questions.extend([
                f"Show me all data from {table_name}",
                f"How many records are in {table_name}?",
                f"What columns are available in {table_name}?"
            ])
    
    # Add some cross-table questions if multiple tables exist
    if len(table_names) > 1:
        questions.extend([
            f"Compare data between {table_names[0]} and {table_names[1] if len(table_names) > 1 else table_names[0]}",
            "Show me relationships between tables",
            "What are the most populated tables?"
        ])
    
    # Add database-level questions
    if stats['total_databases'] > 1:
        questions.extend([
            "Show me data from all databases",
            "Compare statistics across databases",
            "Which database has the most data?"
        ])
    
    return questions[:10]  # Limit to 10 questions

# Page configuration
st.set_page_config(
    page_title="SQL Agent - Powered by Gemini & LangGraph",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Multi-page navigation
def main():
    # Sidebar navigation
    st.sidebar.title("🤖 SQL Agent Suite")
    st.sidebar.markdown("---")
    
    page = st.sidebar.selectbox(
        "🧭 Choose a page:",
        ["🔍 Query Interface", "🗃️ Database Manager"],
        help="Select between querying the database or managing the data directly"
    )
    
    # Page routing
    if page == "🔍 Query Interface":
        query_interface()
    elif page == "🗃️ Database Manager":
        database_manager_launcher()

def database_manager_launcher():
    """Load the database management interface launcher"""
    
    # Custom CSS
    st.markdown("""
    <style>
        .launcher-header {
            background: linear-gradient(90deg, #2E8B57 0%, #228B22 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
        }
        .feature-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            border: 1px solid #e0e6ed;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="launcher-header">
        <h1>🗃️ Enhanced Database Management</h1>
        <p>Dynamic Multi-Database CRUD operations with AI integration</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Features overview
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🔍 Dynamic Multi-Database Operations</h3>
            <ul>
                <li>📋 View data from ANY database/table</li>
                <li>🔍 Advanced filtering and pagination</li>
                <li>📊 Real-time schema detection</li>
                <li>📥 Export data to CSV from any source</li>
                <li>🔄 Automatic database discovery</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>✏️ Complete CRUD + AI Integration</h3>
            <ul>
                <li>➕ Add records to any database/table</li>
                <li>✏️ Edit records + move tables between DBs</li>
                <li>🗑️ Delete records/columns/tables/databases</li>
                <li>📊 Execute custom SQL on any database</li>
                <li>🤖 Real-time AI system updates</li>
                <li>🚀 Future-proof for new databases</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 🚀 Launch Enhanced Database Manager")
    
    st.markdown("""
    **Enhanced Database Management Interface - Now with Dynamic Multi-Database Support:**
    
    🆕 **INTEGRATED DYNAMIC FEATURES** - All in one enhanced interface:
    - 🗃️ **Multi-Database Support**: Work with all available databases seamlessly
    - 📋 **View Data**: Browse any database, any table with advanced pagination
    - ➕ **Add Records**: Insert data into any table in any database  
    - ✏️ **Edit Records**: Update records across all databases
    - 🗑️ **Delete Records**: Safe deletion with confirmation across all databases
    - 📊 **Custom Queries**: Execute SQL on any selected database with table hints
    - 📤 **File Upload**: Create new databases from CSV/Excel files
    - 🔄 **AI Integration**: Real-time updates and automatic schema detection
    - 🚀 **Future-Ready**: Automatically discovers and supports new databases
    
    **All features are now integrated into a single, powerful interface!**
    """)
    
    # Single Launch Button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("�️ Launch Enhanced Database Manager", type="primary", use_container_width=True):
            try:
                # Launch enhanced database manager on different port
                subprocess.Popen([
                    sys.executable, "-m", "streamlit", "run", "database_manager.py",
                    "--server.port", "8504",
                    "--server.headless", "false"
                ])
                st.success("🎉 Enhanced Database Manager launched successfully!")
                st.markdown("**[🔗 Open Enhanced Database Manager](http://localhost:8504)**", unsafe_allow_html=True)
                st.balloons()
            except Exception as e:
                st.error(f"Error launching Enhanced Database Manager: {str(e)}")
                st.info("Please try the manual launch option below.")
    
    # Manual Launch Instructions
    st.markdown("---")
    st.markdown("### 💻 Manual Launch Option")
    st.markdown("**Copy and run this command in your terminal:**")
    st.code("streamlit run database_manager.py --server.port 8504", language="bash")
    st.info("💡 This will open the Enhanced Database Manager on port 8504 with full dynamic features")
    
    # Quick database stats
    st.markdown("---")
    st.markdown("### 📊 Quick Database Overview")
    
    try:
        db_path = Path("database/sql_agent.db")
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get table information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📋 Total Tables", len(tables))
            
            if 'customers' in tables:
                cursor.execute("SELECT COUNT(*) FROM customers")
                customers_count = cursor.fetchone()[0]
                with col2:
                    st.metric("👥 Customers", customers_count)
            
            if 'subscriptions' in tables:
                cursor.execute("SELECT COUNT(*) FROM subscriptions WHERE status = 'active'")
                active_subs = cursor.fetchone()[0]
                with col3:
                    st.metric("✅ Active Subscriptions", active_subs)
            
            # Table details
            st.markdown("#### 📋 Available Tables")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                st.markdown(f"- **{table}**: {count} records")
            
            conn.close()
            
    except Exception as e:
        st.error(f"Error loading database stats: {str(e)}")

def query_interface():
    """Query interface page"""
    
    # Custom CSS for better styling
    st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
    }
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .query-box {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e0e6ed;
        margin: 1rem 0;
    }
    .result-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .error-box {
        background: #f8d7da;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e0e6ed;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

    def initialize_agent():
        """Initialize the Enhanced SQL Agent with fresh configuration"""
        try:
            # Create new agent instance (not cached)
            agent = EnhancedSQLAgent()
            # Always refresh to get latest database configurations
            agent.refresh_all_schemas()
            return agent, None
        except Exception as e:
            return None, str(e)

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 SQL Agent</h1>
        <p>Powered by Gemini AI & LangGraph | Ask questions about your database in natural language</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize agent
    agent, error = initialize_agent()
    
    if error:
        st.error(f"❌ Failed to initialize SQL Agent: {error}")
        st.info("💡 Make sure your database exists and API key is configured in .env file")
        return
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Database and Table Selection
        if agent is not None:
            st.subheader("�️ Database & Table Selection")
            
            # Get available databases and tables
            databases_info = agent.get_available_databases()
            tables_by_db = agent.get_tables_by_database()
            
            # Database selection
            available_databases = list(databases_info.keys())
            if available_databases:
                st.markdown("**Select Databases (Optional):**")
                selected_databases = st.multiselect(
                    "Choose databases to query",
                    options=available_databases,
                    default=None,
                    help="Leave empty to use all databases, or select specific ones to focus your queries"
                )
                
                # Table selection based on selected databases
                if selected_databases:
                    # Get tables from selected databases only
                    relevant_tables = []
                    for db_name in selected_databases:
                        if db_name in tables_by_db:
                            for table in tables_by_db[db_name]:
                                relevant_tables.append(f"{db_name}.{table}")
                else:
                    # Get all tables from all databases
                    relevant_tables = []
                    for db_name, tables in tables_by_db.items():
                        for table in tables:
                            relevant_tables.append(f"{db_name}.{table}")
                
                # Table selection
                if relevant_tables:
                    st.markdown("**Select Tables (Optional):**")
                    selected_tables = st.multiselect(
                        "Choose specific tables to focus on",
                        options=relevant_tables,
                        default=None,
                        help="Leave empty to use all tables, or select specific ones to focus your queries"
                    )
                    
                    # Store selections in session state for use in queries
                    st.session_state.selected_databases = selected_databases
                    st.session_state.selected_tables = [t.split('.')[1] if '.' in t else t for t in (selected_tables or [])]
                else:
                    st.info("No tables found in selected databases")
                    st.session_state.selected_databases = []
                    st.session_state.selected_tables = []
            
            # Database overview
            with st.expander("📊 Database Overview", expanded=False):
                for db_name, db_info in databases_info.items():
                    if 'error' not in db_info:
                        st.markdown(f"**{db_name}** ({db_info.get('table_count', 0)} tables, {db_info.get('total_records', 0):,} records)")
                        if 'tables' in db_info:
                            for table in db_info['tables']:
                                table_info = db_info.get('table_info', {}).get(table, {})
                                rows = table_info.get('rows', 0)
                                cols = table_info.get('columns', 0)
                                st.markdown(f"  - {table}: {rows:,} rows, {cols} columns")
                    else:
                        st.error(f"**{db_name}**: {db_info['error']}")
        
        # Database info
        st.subheader("📊 Database Schema")
        with st.expander("View Current Schema", expanded=False):
            if agent is not None:
                # Show schema for selected databases or current context
                if hasattr(st.session_state, 'selected_databases') and st.session_state.selected_databases:
                    multi_db_manager = MultiDatabaseManager()
                    schema_info = multi_db_manager.get_schema_for_databases(st.session_state.selected_databases)
                else:
                    schema_info = agent.get_schema_info()
                st.text(schema_info)
            else:
                st.error("❌ SQL Agent is not available. Cannot display schema info.")
        
        # Dynamic example queries based on current database content
        st.subheader("💡 Dynamic Example Questions")
        
        # Get current database stats for dynamic examples
        try:
            current_stats = get_dynamic_database_stats()
            example_questions = generate_dynamic_example_questions(current_stats)
            
            if example_questions:
                st.caption(f"📊 Based on {current_stats['total_tables']} tables across {current_stats['total_databases']} database(s)")
                
                for i, question in enumerate(example_questions[:8], 1):  # Show max 8 questions
                    if st.button(f"{i}. {question}", key=f"example_{i}"):
                        st.session_state.selected_question = question
            else:
                st.info("💡 Upload some data files to see dynamic example questions!")
        except Exception as e:
            st.warning("Unable to generate dynamic examples. Using fallback questions.")
            fallback_questions = [
                "Show me the database schema",
                "How many tables are available?",
                "What data can I query?"
            ]
            for i, question in enumerate(fallback_questions, 1):
                if st.button(f"{i}. {question}", key=f"fallback_{i}"):
                    st.session_state.selected_question = question
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Ask Your Question")
        
        # Question input
        default_question = st.session_state.get('selected_question', '')
        user_question = st.text_area(
            "Enter your question about the database:",
            value=default_question,
            height=100,
            placeholder="e.g., Show me all customers in California with active subscriptions"
        )
        
        # Query button
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        
        with col_btn1:
            query_button = st.button("🚀 Ask Agent", type="primary", use_container_width=True)
        
        with col_btn2:
            clear_button = st.button("🗑️ Clear", use_container_width=True)
        
        if clear_button:
            st.session_state.selected_question = ''
            # Clear stored results
            if 'query_results' in st.session_state:
                del st.session_state.query_results
            st.rerun()
    
    with col2:
        st.header("📈 Dynamic Database Stats")
        
        # Display dynamic database statistics
        try:
            dynamic_stats = get_dynamic_database_stats()
            
            if dynamic_stats['total_databases'] > 0:
                # Overall metrics
                st.metric("🗃️ Total Databases", dynamic_stats['total_databases'])
                st.metric("📋 Total Tables", dynamic_stats['total_tables'])
                st.metric("📊 Total Records", f"{dynamic_stats['total_records']:,}")
                
                # Database breakdown
                if dynamic_stats['database_details']:
                    st.markdown("---")
                    st.subheader("📊 Database Breakdown")
                    
                    for db_detail in dynamic_stats['database_details'][:3]:  # Show top 3 databases
                        with st.expander(f"🗃️ {db_detail['name']} ({db_detail['tables']} tables)", expanded=False):
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("Records", f"{db_detail['records']:,}")
                            with col_b:
                                st.metric("Size", f"{db_detail['size_mb']} MB")
                            
                            # Show top tables in this database
                            if db_detail['table_details']:
                                st.caption("📋 Largest Tables:")
                                sorted_tables = sorted(db_detail['table_details'], key=lambda x: x['records'], reverse=True)
                                for table in sorted_tables[:3]:
                                    st.text(f"  • {table['name']}: {table['records']:,} records")
                
                # Show most populated tables across all databases
                if dynamic_stats['recent_tables']:
                    st.markdown("---")
                    st.subheader("� Top Tables")
                    sorted_tables = sorted(dynamic_stats['recent_tables'], key=lambda x: x['records'], reverse=True)
                    
                    for i, table in enumerate(sorted_tables[:5], 1):
                        db_name = table['database'].replace('.db', '')
                        st.text(f"{i}. {table['name']} ({db_name}): {table['records']:,} records")
            else:
                st.info("� No databases found. Upload some data files to see statistics!")
                st.markdown("""
                **Get started:**
                1. Go to "Database Management"
                2. Upload CSV or Excel files
                3. Return here to see dynamic stats
                """)
                
        except Exception as e:
            st.error(f"Error loading dynamic stats: {str(e)}")
            # Fallback to basic info
            try:
                db_path = Path("database/sql_agent.db")
                if db_path.exists():
                    st.metric("🗃️ Main Database", "Available")
                else:
                    st.warning("No main database found")
            except:
                pass
    
    # Process query
    if query_button and user_question and user_question.strip():
        if agent is None:
            st.error("❌ SQL Agent is not available. Please check your configuration.")
        else:
            with st.spinner("🤖 AI Agent is working on your question..."):
                try:
                    # Get selected databases and tables from session state
                    selected_databases = getattr(st.session_state, 'selected_databases', [])
                    selected_tables = getattr(st.session_state, 'selected_tables', [])
                    
                    # Always use enhanced query method (now with automatic database detection)
                    response = agent.query_enhanced(
                        user_question, 
                        selected_databases=selected_databases if selected_databases else None,
                        selected_tables=selected_tables if selected_tables else None
                    )
                    
                    # Add context info to the response
                    context_info = []
                    if selected_databases:
                        context_info.append(f"Databases: {', '.join(selected_databases)}")
                    if selected_tables:
                        context_info.append(f"Tables: {', '.join(selected_tables)}")
                    
                    if context_info:
                        response['context'] = " | ".join(context_info)
                    
                    # Store results in session state
                    st.session_state.query_results = {
                        'query': user_question,
                        'response': response,
                        'selected_databases': selected_databases,
                        'selected_tables': selected_tables
                    }
                    
                    st.success("✅ Query completed!")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.session_state.query_results = None
    
    elif query_button and user_question and not user_question.strip():
        st.warning("⚠️ Please enter a question first!")
    
    # Display stored results from session state
    if 'query_results' in st.session_state and st.session_state.query_results:
        stored_data = st.session_state.query_results
        response = stored_data['response']
        original_query = stored_data['query']
        selected_databases = stored_data.get('selected_databases', [])
        selected_tables = stored_data.get('selected_tables', [])
        
        # Show query context if databases or tables were selected
        if selected_databases or selected_tables:
            st.header("🎯 Query Context")
            col1, col2 = st.columns(2)
            
            with col1:
                if selected_databases:
                    st.markdown("**Selected Databases:**")
                    for db in selected_databases:
                        st.markdown(f"  - 🗃️ {db}")
                else:
                    st.markdown("**Using:** All available databases")
            
            with col2:
                if selected_tables:
                    st.markdown("**Selected Tables:**")
                    for table in selected_tables:
                        st.markdown(f"  - 📋 {table}")
                else:
                    st.markdown("**Using:** All available tables")
        
        st.header("🔍 Generated SQL Query")
        st.code(response['sql_query'], language='sql')
        
        # Display results
        if response['success']:
            st.header("📊 Query Results")
            
            # Show data table if available
            if 'formatted_data' in response and response['formatted_data']:
                df = pd.DataFrame(response['formatted_data'])
                
                # Display data summary
                col_summary1, col_summary2, col_summary3 = st.columns(3)
                with col_summary1:
                    st.metric("📊 Total Rows", len(df))
                with col_summary2:
                    st.metric("📋 Columns", len(df.columns))
                with col_summary3:
                    if len(df) > 0 and df.select_dtypes(include=['number']).shape[1] > 0:
                        numeric_cols = df.select_dtypes(include=['number']).columns
                        st.metric("🔢 Numeric Columns", len(numeric_cols))
                
                # Display the data table
                st.dataframe(df, use_container_width=True, height=400)
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name=f"query_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
                # Optional Data Visualization
                numeric_columns = df.select_dtypes(include=['number']).columns
                if len(numeric_columns) > 0:
                    st.header("📈 Data Visualization (Optional)")
                    
                    # Add button to show/hide visualization
                    show_viz = st.button("� Show Data Visualization", key="show_viz_btn")
                    
                    if show_viz or st.session_state.get('show_visualization', False):
                        st.session_state.show_visualization = True
                        
                        chart_type = st.selectbox(
                            "Choose chart type:",
                            ["Bar Chart", "Line Chart", "Area Chart", "Histogram"],
                            key="chart_type_select"
                        )
                        
                        if len(numeric_columns) >= 1:
                            if chart_type == "Bar Chart" and len(df) <= 50:
                                if len(df.columns) >= 2:
                                    x_col = st.selectbox("X-axis:", df.columns, key="x_axis_select")
                                    y_col = st.selectbox("Y-axis:", numeric_columns, key="y_axis_select")
                                    if x_col and y_col:
                                        st.bar_chart(df.set_index(x_col)[y_col])
                            
                            elif chart_type == "Line Chart" and len(numeric_columns) >= 1:
                                selected_cols = st.multiselect(
                                    "Select columns for line chart:", 
                                    numeric_columns, 
                                    default=list(numeric_columns[:3]),
                                    key="line_cols_select"
                                )
                                if selected_cols:
                                    st.line_chart(df[selected_cols])
                            
                            elif chart_type == "Area Chart" and len(numeric_columns) >= 1:
                                selected_cols = st.multiselect(
                                    "Select columns for area chart:", 
                                    numeric_columns, 
                                    default=list(numeric_columns[:3]),
                                    key="area_cols_select"
                                )
                                if selected_cols:
                                    st.area_chart(df[selected_cols])
                            
                            elif chart_type == "Histogram":
                                col_hist = st.selectbox("Column for histogram:", numeric_columns, key="hist_col_select")
                                if col_hist:
                                    st.bar_chart(df[col_hist].value_counts())
                        
                        # Button to hide visualization
                        if st.button("🔽 Hide Visualization", key="hide_viz_btn"):
                            st.session_state.show_visualization = False
                            st.rerun()
            
            else:
                # Non-SELECT query result
                query_result = response.get('query_result', {})
                if 'message' in query_result:
                    st.success(query_result['message'])
                if 'rows_affected' in query_result:
                    st.info(f"Rows affected: {query_result['rows_affected']}")
        
        else:
            # Display error
            st.header("❌ Query Error")
            error_msg = response.get('error', 'Unknown error occurred')
            st.error(f"The query failed with the following error: {error_msg}")
        
        # AI Explanation
        st.header("🧠 AI Explanation")
        st.markdown(response['explanation'])
        
        # Show raw response in expander for debugging
        with st.expander("🔧 Raw Response (Debug Info)", expanded=False):
            st.json(response, expanded=False)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>🤖 SQL Agent powered by <strong>Gemini AI</strong> & <strong>LangGraph</strong></p>
        <p>Built with ❤️ using Streamlit | Ask questions in natural language and get SQL insights!</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
