# ?? SQL Agent - AI-Powered Database Assistant

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini%20AI-4285F4?logo=google&logoColor=white)](https://ai.google.dev)
[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An AI-powered Natural Language to SQL application built with Google's Gemini 2.0 Flash and LangGraph. Query databases using plain English and get intelligent insights automatically.

## ?? Features

- ?? **Natural Language Processing**: Ask questions in plain English
- ?? **Automatic Error Recovery**: Self-correcting queries with intelligent retry
- ?? **Data Visualization**: Interactive charts and comprehensive analysis
- ?? **Geographic Intelligence**: Location-based querying with distance calculations
- ??? **Multiple Interfaces**: Web app, CLI, and Python API
- ?? **Dynamic Database Creation**: Upload CSV/Excel files to create tables instantly

## ?? Quick Start

### Prerequisites

- Python 3.8+
- Google AI API Key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- 4GB RAM recommended

### Installation

```bash
# Clone and install
git clone <repository-url>
cd sql-agent
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Initialize database
python database/init_db.py
```

### Launch Application

```bash
# Web Interface (Recommended)
streamlit run streamlit_app.py

# Command Line Interface
python cli_app.py

# Database Manager
streamlit run database_manager.py --server.port 8502
```

## ?? Usage

### Web Interface

Access at http://localhost:8501 for:
- Natural language database querying
- CRUD operations
- Data visualization
- Schema browsing
- CSV/JSON export

### CLI Commands

- help - Show available commands
- schema - Display database schema
- examples - View sample queries
- stats - Show database statistics
- Type any question in natural language

### Python API

```python
from sql_agent import SQLAgent

agent = SQLAgent()
response = agent.query("Show me all customers in New York")

print(response['formatted_data'])
print(response['explanation'])
```

## ?? Example Queries

- Show me all active customers
- What's our total revenue from subscriptions?
- Find customers within 50km of New York City
- Which offers are available in California?
- Show subscription renewal rates by offer type
- List expired subscriptions from this year

## ?? Database Schema

The application includes a sample database with:

- **Customers**: Customer profiles with geographic coordinates
- **Offers**: Subscription offers with location-based targeting
- **Subscriptions**: Subscription lifecycle and payment tracking
- **Views**: Pre-computed customer-offer availability analysis

## ?? Configuration

Edit .env file:

```env
# Required
GOOGLE_API_KEY=your_api_key_here

# Optional
DATABASE_PATH=database/sql_agent.db
MODEL_TEMPERATURE=0.1
MAX_RETRIES=2
DEBUG=True
```

## ?? Project Structure

```
sql-agent/
+-- sql_agent.py              # Core AI engine
+-- streamlit_app.py          # Web interface
+-- database_manager.py       # CRUD interface
+-- cli_app.py                # CLI interface
+-- requirements.txt          # Dependencies
+-- database/
¦   +-- init_db.py           # Database setup
¦   +-- schema.sql           # Database schema
¦   +-- sample_data.sql      # Sample data
+-- .env                      # Configuration
```

## ??? Troubleshooting

### API Key Issues
```bash
# Verify .env file exists and contains:
GOOGLE_API_KEY=your_actual_key
```

### Database Issues
```bash
# Reinitialize database
python database/init_db.py
```

### Package Issues
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

## ?? Dependencies

- google-generativeai>=0.8.0 - Gemini AI integration
- langgraph>=0.2.0 - Workflow orchestration
- streamlit>=1.30.0 - Web interface
- pandas>=2.0.0 - Data manipulation
- python-dotenv>=1.0.0 - Environment management

## ?? Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## ?? License

This project is licensed under the MIT License.

## ?? Acknowledgments

- **Google Gemini AI** - Advanced language understanding
- **LangGraph** - Workflow orchestration
- **Streamlit** - Web application framework
- **SQLite** - Embedded database

## ?? Support

For issues and questions:
- GitHub Issues: Report bugs and request features
- Documentation: Check project wiki and docs
- Community: Join discussions

---

**Start querying your database with natural language today!** ??
