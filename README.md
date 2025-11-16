# 🤖 SQL Agent - AI-Powered Database Assistant

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini%20AI-4285F4?logo=google&logoColor=white)](https://ai.google.dev)
[![LangGraph](https://img.shields.io/badge/LangChain-LangGraph-1C3C3C?logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An advanced Natural Language to SQL application that revolutionizes database interactions through cutting-edge AI. Built with Google''s Gemini 2.0 Flash and LangGraph for intelligent query orchestration, automated error recovery, and comprehensive data analysis.

## 🌟 Project Overview

SQL Agent is a sophisticated database interaction system that bridges the gap between natural language and SQL queries. It enables users to query complex databases using plain English, automatically generating optimized SQL queries, executing them safely, and providing intelligent insights about the results.

### ✨ Key Features

- 🚀 **Enhanced Multi-Database Support**: Automatic detection for various database types
- 📊 **Table Migration Feature**: Complete CRUD interface with table migration between databases
- 🔧 **Improved Auto-Detection**: Seamless database selection with all available databases
- 📈 **Advanced Analytics**: AI-powered insights and business intelligence generation
- 🎯 **Geographic Intelligence**: Sophisticated location-based querying with Haversine distance calculations

### 🎯 Core Philosophy

- **Accessibility**: Make database querying accessible to non-technical users through natural language
- **Intelligence**: Leverage cutting-edge AI for smart query generation and comprehensive data analysis
- **Reliability**: Robust error handling, automatic query optimization, and intelligent retry mechanisms
- **Flexibility**: Multiple interfaces (Web, CLI, API) for different use cases and user preferences
- **Extensibility**: Modular architecture supporting custom databases, AI models, and UI components

## ✨ Advanced Features

### 🧠 AI-Powered Query Intelligence

- **Natural Language Processing**: Advanced understanding of complex business questions
- **Context-Aware Generation**: Leverages database schema for accurate query construction
- **Intelligent Query Optimization**: Automatically optimizes queries for performance
- **Business Logic Understanding**: Interprets relationships and business rules

### 🔄 Robust Error Handling

- **Automatic Retry Mechanism**: Self-correcting queries with error context learning
- **Progressive Enhancement**: Improves query accuracy through iterative refinement
- **Graceful Degradation**: Handles edge cases and provides meaningful error messages
- **SQL Injection Prevention**: Safe query execution with parameterized statements

### 📊 Comprehensive Data Analysis

- **AI-Powered Insights**: Goes beyond raw data to provide business intelligence
- **Pattern Recognition**: Identifies trends and anomalies in query results
- **Automated Explanations**: Translates technical results into business language
- **Recommendation Engine**: Suggests follow-up queries and actionable insights

### 🌍 Geographic Intelligence

- **Location-Based Queries**: Advanced geographic query capabilities
- **Distance Calculations**: Haversine formula for precise distance-based filtering
- **Multi-Level Targeting**: City, state, region, and radius-based data filtering
- **Coordinate System Support**: Full latitude/longitude coordinate processing

### 🖥️ Multi-Interface Architecture

- **Streamlit Web App**: Beautiful, interactive web interface with real-time visualizations
- **Command Line Interface**: Developer-friendly CLI for testing and automation
- **Database Manager**: Comprehensive CRUD interface for data administration
- **🆕 Dynamic Database Creation**: Upload CSV/Excel files to create tables instantly
- **Python API**: Programmatic access for integration with existing systems

### 📈 Advanced Visualization

- **Dynamic Chart Generation**: Automatic visualization based on data types
- **Interactive Dashboards**: Real-time data exploration capabilities
- **Export Functionality**: CSV, JSON, and chart export options
- **Responsive Design**: Mobile-friendly interface with adaptive layouts

## 🚀 Quick Start Guide

### Prerequisites

- **Python 3.8+**: Modern Python environment with pip package manager
- **Google AI API Key**: Free Gemini API access from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **4GB RAM**: Recommended for optimal performance
- **Internet Connection**: Required for AI API calls

### Installation Steps

```bash
# 1. Clone the Repository
git clone https://github.com/Shib-Sankar-Das/SQL_Agent---AI-Powered-Database-Assistant.git
cd SQL_Agent---AI-Powered-Database-Assistant

# 2. Install Dependencies
pip install -r requirements.txt

# 3. Set up Environment Variables
# Create a .env file and add your Google API key
echo GOOGLE_API_KEY=your_api_key_here > .env

# 4. Initialize Database
python database/init_db.py
```

### API Key Setup

1. **Get Gemini API Key**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Sign in with your Google account
   - Click "Create API Key"
   - Copy the generated key

2. **Configure Environment**
   - Add your Gemini API key to the `.env` file
   - Format: `GOOGLE_API_KEY=your_actual_key_here_without_quotes`

## 🎯 Usage Options

### Option 1: Streamlit Web Interface (Recommended)

Launch the comprehensive web application:

```bash
streamlit run streamlit_app.py
```

**Features Available:**
- �� **Query Interface**: Natural language database querying with AI explanations
- 🗃️ **Database Manager**: Complete CRUD operations interface
- 📊 **Data Visualization**: Interactive charts and graphs
- 📋 **Schema Browser**: Explore database structure and relationships
- 💾 **Export Options**: Download results as CSV or JSON

**Access Points:**
- Main Interface: `http://localhost:8501`
- Database Manager: `http://localhost:8502` (if launched separately)

### Option 2: Command Line Interface

Interactive CLI for developers and power users:

```bash
python cli_app.py
```

**CLI Commands Available:**
- `help` - Display all available commands and their descriptions
- `schema` - Show the complete database schema with table structures
- `examples` - View sample questions and query patterns for reference
- `stats` - Display real-time database statistics and metrics
- `clear` - Clear the terminal screen for better visibility
- `quit/exit` - Safely exit the application
- Type any question in plain English for immediate processing

### Option 3: Database Management Interface

Dedicated CRUD interface for data administration:

```bash
streamlit run database_manager.py --server.port 8502
```

**Management Features:**
- 📋 **Browse Tables**: Paginated data viewing with search
- ➕ **Add Records**: Form-based data entry with validation
- ✏️ **Edit Records**: In-place editing with constraints
- 🗑️ **Delete Records**: Safe deletion with confirmation
- 📊 **Table Statistics**: Real-time metrics and analysis
- 🔍 **Custom SQL**: Execute custom queries safely
- 🆕 **📤 File Upload**: Create dynamic tables from CSV/Excel files

**🚀 NEW: Dynamic Database Creation**

The SQL Agent now supports instant table creation from your data files:
- **📊 CSV Support**: Upload CSV files to create individual tables
- **📈 Excel Support**: Each sheet becomes a separate table automatically
- **🔄 Multiple Files**: Process multiple files simultaneously
- **🧠 Smart Processing**: Automatic data type detection and column naming
- **✅ Validation**: Comprehensive error handling and data validation
- **🎯 Custom Naming**: Optional custom table name prefixes

### Option 4: Python API Integration

Programmatic access for applications:

```python
from sql_agent import SQLAgent

# Initialize agent
agent = SQLAgent()

# Execute natural language query
response = agent.query("Show me all active customers")

# Access results
print(response['sql_query'])        # Generated SQL
print(response['formatted_data'])   # Query results
print(response['explanation'])      # AI insights

# Get database schema
schema = agent.get_schema_info()
print(schema)
```

## 💡 Example Queries & Use Cases

### 🏢 Business Intelligence Queries

**Customer Analytics:**
- "Show me all active customers"
- "How many customers registered each month this year?"
- "Find customers in New York with active subscriptions"
- "Which customers have multiple subscriptions?"
- "Show customer lifetime value by state"
- "List customers who haven''t been active in 30 days"

**Revenue Analysis:**
- "What''s our total revenue from active subscriptions?"
- "Show revenue breakdown by subscription type"
- "Calculate monthly recurring revenue trends"
- "Which offers generate the most revenue?"
- "Compare revenue by geographic region"
- "Show average revenue per user by customer segment"

### 🌍 Geographic Intelligence Queries

**Location-Based Analysis:**
- "Show me all customers within 50km of New York City"
- "Which offers are available in California?"
- "Find the closest customers to our Los Angeles office"
- "Show subscription rates by state"
- "List location-specific offers and their performance"
- "Map customer distribution across the United States"

**Market Penetration:**
- "Which cities have the highest customer concentration?"
- "Show states with no active subscriptions"
- "Find underserved markets with growth potential"
- "Compare urban vs rural subscription patterns"

### 📊 Subscription Management Queries

**Lifecycle Analysis:**
- "Show all expired subscriptions from this year"
- "Which customers recently cancelled their subscriptions?"
- "Find subscriptions expiring in the next 30 days"
- "Show subscription renewal rates by offer type"
- "List customers eligible for upgrade offers"

**Performance Metrics:**
- "What''s our monthly churn rate?"
- "Show subscription duration statistics"
- "Calculate customer acquisition cost trends"
- "Which offers have the highest retention rates?"

### 🎯 Offer Optimization Queries

**Pricing Analysis:**
- "What are the top 5 most expensive offers?"
- "Show price sensitivity by customer segment"
- "Compare offer performance by price range"
- "Which offers are underperforming?"
- "Find optimal pricing for new customer segments"

**Availability Assessment:**
- "List all California-exclusive offers"
- "Show offers with no active subscriptions"
- "Which offers are location-restricted?"
- "Find offers available nationwide"

## 📊 Database Architecture & Schema

### 🏗️ Database Design Overview

The SQL Agent uses a sophisticated SQLite database designed for complex business analytics, geographic intelligence, and subscription management. The schema supports advanced querying patterns including location-based searches, temporal analysis, and multi-dimensional business intelligence.

### 📋 Core Tables Structure

#### 🧑‍🤝‍🧑 Customers Table

**Purpose**: Central customer repository with comprehensive profile and location data

**Key Columns:**
- `customer_id` - Primary key with auto-increment
- `first_name`, `last_name` - Customer names
- `email` - Unique identifier
- `phone` - Contact information
- `registration_date` - Account creation date
- `city`, `state`, `country` - Location information
- `postal_code` - Address detail
- `latitude`, `longitude` - Geographic coordinates for location-based queries
- `is_active` - Account status flag
- `created_at` - Audit timestamp

**Key Features:**
- Geographic Intelligence with precise lat/lng coordinates
- Email uniqueness constraints
- Audit trail with timestamps
- Soft deletion support

#### 🎯 Offers Table

**Purpose**: Subscription offers with advanced location targeting and pricing strategies

**Key Columns:**
- `offer_id` - Primary key
- `offer_name` - Descriptive name
- `description` - Detailed benefits
- `price` - Monetary value
- `duration_months` - Subscription length
- `available_cities` - Comma-separated eligible cities
- `available_states` - Comma-separated eligible states
- `is_location_specific` - Geographic restriction flag
- `max_distance_km` - Radius-based availability
- `offer_center_latitude`, `offer_center_longitude` - Geographic center
- `is_active` - Offer status
- `created_at` - Audit timestamp

**Advanced Features:**
- Multi-level targeting (city, state, country, radius)
- Distance-based availability using Haversine formula
- Flexible pricing models
- Location-specific and nationwide offer support

#### �� Subscriptions Table

**Purpose**: Subscription lifecycle management with financial tracking

**Key Columns:**
- `subscription_id` - Primary key
- `customer_id` - Foreign key to customers
- `offer_id` - Foreign key to offers
- `start_date` - Subscription activation
- `end_date` - Expiration date
- `status` - Current status (active/expired/cancelled)
- `payment_amount` - Actual payment received
- `created_at` - Audit timestamp

**Business Logic:**
- Complete subscription status tracking
- Payment history and revenue calculation
- Referential integrity with foreign keys
- Temporal analysis support

### 🚀 Performance Optimizations

**Strategic Indexing:**
- Email index for customer lookups
- Location index (latitude, longitude) for geographic queries
- Subscription status index for analytics
- Date range index for temporal analysis
- Location-specific offers index

**Advanced Views:**
- `customer_available_offers` - Pre-computed offer availability based on complex location logic
- Implements Haversine formula for distance calculations
- Processes comma-separated city/state lists
- Applies business rules for offer eligibility

## 🏗️ Technical Architecture

### 🧠 AI-Powered Query Engine

The SQL Agent employs a sophisticated multi-layered architecture combining advanced AI reasoning with robust database management.

#### Core AI Components

**1. Gemini 2.0 Flash Integration**
- Optimized configuration for consistent SQL generation
- Low temperature settings for reliable query generation
- Context-aware processing with database schema

**2. LangGraph Workflow Orchestration**

**Process Flow:**
1. **User Query Input** → Natural language questions received and validated
2. **Query Generation** → Gemini AI processes input with database schema context
3. **Query Execution** → Generated SQL safely executed against SQLite database
4. **Error Check** → Intelligent error detection with automatic retry capability
5. **AI Analysis** → Results analyzed for patterns and business insights
6. **Final Response** → Comprehensive response with explanation and recommendations

**Error Recovery Mechanism:**
- Automatic error detection
- Context enhancement with error information
- Maximum of two retry attempts
- Progressive learning from failures

### 🔄 Intelligent Workflow Process

#### Phase 1: Schema-Aware Query Generation
- Dynamic schema injection into AI prompt
- Comprehensive rules for SQLite compatibility
- Geographic handling for lat/lng calculations
- Business context integration
- Safety validation

#### Phase 2: Safe Query Execution
- Parameterized execution to prevent SQL injection
- Automatic data type detection
- Pandas DataFrame conversion for analysis
- Comprehensive error capture
- Resource management and cleanup

#### Phase 3: Intelligent Error Recovery
- Error classification and categorization
- Intelligent retry decision making
- Context enhancement for each retry
- Learning from error patterns
- Maximum retry limit prevention

#### Phase 4: AI-Powered Result Analysis
- Business intelligence generation
- Pattern and anomaly detection
- Actionable insights and recommendations
- User-friendly explanations
- Context integration

### 🛡️ Security & Safety Framework

**SQL Injection Prevention:**
- Parameterized queries for all inputs
- Query validation and safety checks
- Read-only enforcement by default
- Error sanitization

**Data Privacy & Access Control:**
- Local database storage
- Environment variable API key protection
- Optional audit logging
- Resource usage monitoring

### 🚀 Performance Optimization

**Caching Strategies:**
- Singleton pattern for agent instances
- Schema information caching
- Connection pool management
- Result caching for frequent queries

**Query Optimization:**
- Strategic database indexing
- Result pagination
- Efficient memory management
- Optimized database connections

## 🔧 Configuration & Customization

### 🌍 Environment Variables

Create a `.env` file in the project root:

```env
# Required Configuration
GOOGLE_API_KEY=your_gemini_api_key

# Optional Database Configuration
DATABASE_PATH=database/sql_agent.db
BACKUP_PATH=database/backups/

# AI Model Configuration
MODEL_NAME=gemini-2.0-flash-exp
MODEL_TEMPERATURE=0.1
MAX_RETRIES=2
QUERY_TIMEOUT=30

# Application Configuration
DEBUG=True
LOG_LEVEL=INFO
MAX_RESULT_ROWS=1000
ENABLE_CACHE=True

# Security Settings
ALLOW_SCHEMA_MODIFICATION=False
ENABLE_AUDIT_LOG=True
SAFE_MODE=True

# Performance Tuning
CONNECTION_POOL_SIZE=5
QUERY_CACHE_SIZE=100
RESULT_CACHE_TTL=300

# UI Configuration
DEFAULT_PAGE_SIZE=50
ENABLE_CHARTS=True
CHART_MAX_POINTS=500
```

## 📁 Project Structure

```
SQL_Agent/
├── sql_agent.py              # Core AI engine with LangGraph workflow
├── streamlit_app.py          # Primary web interface
├── database_manager.py       # CRUD operations interface
├── cli_app.py                # Command line interface
├── requirements.txt          # Python dependencies
├── setup.py                  # Package installation script
├── .env                      # Environment configuration
├── database/
│   ├── init_db.py           # Database initialization
│   ├── schema.sql           # Database schema definition
│   ├── sample_data.sql      # Sample data for testing
│   └── sql_agent.db         # SQLite database (generated)
├── __pycache__/             # Python cache files
└── README.md                # This file
```

## 🛠️ Troubleshooting

### Common Issues & Solutions

#### 1. API Key Configuration Issues

**Error**: `ValueError: Please set GOOGLE_API_KEY in your .env file`

**Solutions:**
- Verify `.env` file exists in project root
- Check format: `GOOGLE_API_KEY=your_key` (no quotes, no spaces)
- Ensure API key is valid and active
- Restart the application

#### 2. Database Connection Problems

**Error**: `FileNotFoundError: Database not found`

**Solutions:**
```bash
# Reinitialize database
python database/init_db.py

# Verify database file exists
ls database/sql_agent.db
```

#### 3. Package Installation Errors

**Error**: `No module named 'langgraph'`

**Solutions:**
```bash
# Update pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Install individually if needed
pip install google-generativeai>=0.8.0
pip install langgraph>=0.2.0
pip install streamlit>=1.30.0
```

#### 4. Streamlit Interface Problems

**Error**: Web interface not loading

**Solutions:**
```bash
# Check port availability
netstat -ano | findstr :8501

# Run on different port
streamlit run streamlit_app.py --server.port 8502

# Clear cache
streamlit cache clear
```

## 📦 Dependencies

**Core AI & ML Libraries:**
- `google-generativeai>=0.8.0` - Gemini AI integration
- `langgraph>=0.2.0` - Workflow orchestration
- `langchain>=0.3.0` - AI framework
- `langchain-google-genai>=2.0.0` - Google AI connectors

**Web & Data Libraries:**
- `streamlit>=1.30.0` - Web interface framework
- `pandas>=2.0.0` - Data manipulation
- `python-dotenv>=1.0.0` - Environment management
- `typing-extensions>=4.0.0` - Type system support

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Update documentation
7. Submit a pull request with detailed description

## 📝 License

This project is licensed under the MIT License.

```
MIT License

Copyright (c) 2024 SQL Agent Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Acknowledgments

### Technology Partners

- **Google Gemini AI** - Advanced language understanding and query generation
- **LangGraph** - Workflow orchestration and state management
- **Streamlit** - Rapid web application development
- **SQLite** - Reliable embedded database

### Inspiration & Research

- NL2SQL research and methodologies
- Human-Computer Interaction design principles
- Database query optimization techniques
- AI ethics and responsible AI development

## 📞 Support & Contact

### Getting Help

**Documentation Resources:**
- README.md - Comprehensive setup guide
- QUICKSTART.md - Fast setup instructions
- PROJECT_SUMMARY.md - Executive overview
- DATABASE_MANAGEMENT.md - Admin guide

**Community Support:**
- **GitHub Issues** - Report bugs and request features
- **GitHub Discussions** - Ask questions and share experiences
- **Wiki Pages** - Community-contributed guides

---

## 🚀 Get Started Today!

**Transform your database experience with AI-powered natural language querying!**

```bash
# Quick start in 3 steps
git clone https://github.com/Shib-Sankar-Das/SQL_Agent---AI-Powered-Database-Assistant.git
pip install -r requirements.txt
streamlit run streamlit_app.py
```

**Experience the power of conversational database querying!**

*Ask questions in natural language and let AI handle the SQL complexity for you!* 🚀

---

**Happy Querying! 🎉**
