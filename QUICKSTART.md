# 🚀 SQL Agent Quick Start Guide

*Get up and running with AI-powered database queries in under 5 minutes!*

## 📋 Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation) 
- [Configuration](#configuration)
- [First Query](#first-query)
- [Interface Options](#interface-options)
- [Common Issues](#common-issues)
- [Next Steps](#next-steps)

## Step 1: Get Your Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account  
3. Click "Create API Key"
4. Copy the generated key

## Step 2: Configure Environment

1. Open the `.env` file in this folder
2. Replace `your_gemini_api_key_here` with your actual API key:
   ```
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Run the SQL Agent

### Option A: Web Interface (Recommended)
```bash
streamlit run streamlit_app.py
```
Then open http://localhost:8501 in your browser

### Option B: Command Line
```bash
python cli_app.py
```

### Option C: Run Setup Script
```bash
python setup.py
```

## 🎯 Example Questions to Try

- "Show me all active customers"
- "What are the top 5 most expensive offers?" 
- "How many customers are in California?"
- "Show me revenue by subscription status"
- "Which customers have active subscriptions?"

## 🛠️ Troubleshooting

- **Import errors**: Run `pip install -r requirements.txt`
- **API key error**: Make sure you added your Gemini API key to `.env`
- **Database error**: The database should be automatically created
- **Test everything**: Run `python test_agent.py`

## 📁 What You Have

- ✅ SQLite database with sample data (customers, offers, subscriptions)
- ✅ AI-powered SQL agent using Gemini 2.0 Flash  
- ✅ LangGraph workflow for intelligent query processing
- ✅ Beautiful web interface with Streamlit
- ✅ Command line interface for quick queries
- ✅ Python API for integration

**You're all set! 🎉**
