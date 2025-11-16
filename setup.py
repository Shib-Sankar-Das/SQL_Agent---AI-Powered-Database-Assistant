"""
Setup script for SQL Agent
Helps users set up the environment and get started quickly
"""

import os
import subprocess
import sys
from pathlib import Path

def print_banner():
    """Print setup banner"""
    print("=" * 60)
    print("🚀 SQL Agent Setup Script")
    print("=" * 60)
    print("This script will help you set up the SQL Agent environment")
    print("=" * 60)

def check_python_version():
    """Check if Python version is compatible"""
    print("\n🔄 Checking Python version...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("   Please install Python 3.8 or higher")
        return False

def install_packages():
    """Install required packages"""
    print("\n🔄 Installing required packages...")
    
    try:
        # Check if requirements.txt exists
        if not Path("requirements.txt").exists():
            print("❌ requirements.txt not found")
            return False
        
        # Install packages
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Packages installed successfully")
            return True
        else:
            print(f"❌ Package installation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error installing packages: {e}")
        return False

def setup_environment():
    """Set up environment file"""
    print("\n🔄 Setting up environment configuration...")
    
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        
        # Check if API key is configured
        with open(env_file, 'r') as f:
            content = f.read()
            if "your_gemini_api_key_here" in content:
                print("⚠️  Please update your API key in .env file")
                return False
            elif "GOOGLE_API_KEY=" in content:
                print("✅ API key appears to be configured")
                return True
    else:
        print("📝 Creating .env file...")
        
        env_content = """# Add your Google API key here
GOOGLE_API_KEY=your_gemini_api_key_here

# Database configuration
DATABASE_PATH=database/sql_agent.db

# Optional: Set debug mode
DEBUG=True"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("✅ .env file created")
        print("⚠️  Please add your Gemini API key to .env file")
        return False

def setup_database():
    """Initialize the database"""
    print("\n🔄 Setting up database...")
    
    try:
        # Check if database files exist
        db_dir = Path("database")
        if not db_dir.exists():
            print("❌ Database directory not found")
            return False
        
        required_files = ["init_db.py", "schema.sql", "sample_data.sql"]
        for file in required_files:
            if not (db_dir / file).exists():
                print(f"❌ Required file not found: database/{file}")
                return False
        
        # Initialize database
        sys.path.insert(0, str(db_dir))
        from init_db import init_database
        
        success = init_database()
        if success:
            print("✅ Database initialized successfully")
            return True
        else:
            print("❌ Database initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False

def get_api_key():
    """Guide user to get API key"""
    print("\n🔑 Getting Gemini API Key")
    print("-" * 30)
    print("To use the SQL Agent, you need a Google Gemini API key.")
    print("\nFollow these steps:")
    print("1. Go to: https://makersuite.google.com/app/apikey")
    print("2. Sign in with your Google account")
    print("3. Click 'Create API Key'")
    print("4. Copy the generated key")
    print("5. Add it to your .env file")
    
    api_key = input("\n📝 Paste your API key here (or press Enter to skip): ").strip()
    
    if api_key:
        # Update .env file
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, 'r') as f:
                content = f.read()
            
            # Replace placeholder with actual key
            content = content.replace("your_gemini_api_key_here", api_key)
            
            with open(env_file, 'w') as f:
                f.write(content)
            
            print("✅ API key saved to .env file")
            return True
        else:
            print("❌ .env file not found")
            return False
    else:
        print("⚠️  Skipping API key setup - you can add it later")
        return False

def run_test():
    """Run the test script"""
    print("\n🧪 Running tests...")
    
    try:
        result = subprocess.run([sys.executable, "test_agent.py"], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def show_next_steps():
    """Show what to do next"""
    print("\n🎯 Next Steps")
    print("-" * 30)
    print("Your SQL Agent is ready! Here's how to use it:")
    print("\n1. 🌐 Web Interface (Recommended):")
    print("   streamlit run streamlit_app.py")
    print("   Then open http://localhost:8501 in your browser")
    
    print("\n2. 💻 Command Line Interface:")
    print("   python cli_app.py")
    
    print("\n3. 🐍 Python API:")
    print("   from sql_agent import SQLAgent")
    print("   agent = SQLAgent()")
    print("   response = agent.query('Show me all customers')")
    
    print("\n4. 🧪 Run Tests:")
    print("   python test_agent.py")
    
    print("\n💡 Example Questions:")
    print("   - Show me all active customers")
    print("   - What are the top 5 most expensive offers?")
    print("   - How many customers are in California?")
    print("   - Show me revenue by subscription status")

def main():
    """Main setup script"""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        return
    
    # Install packages
    if not install_packages():
        print("\n❌ Setup failed at package installation")
        return
    
    # Setup environment
    env_ok = setup_environment()
    
    # Setup database
    if not setup_database():
        print("\n❌ Setup failed at database initialization")
        return
    
    # Get API key if not configured
    if not env_ok:
        api_key_ok = get_api_key()
    else:
        api_key_ok = True
    
    # Run tests
    print("\n" + "=" * 60)
    
    if api_key_ok:
        test_ok = run_test()
        if test_ok:
            print("🎉 Setup completed successfully!")
            show_next_steps()
        else:
            print("⚠️  Setup completed with some issues - check test output above")
            show_next_steps()
    else:
        print("⚠️  Setup completed but API key needs to be configured")
        print("   Add your Gemini API key to .env file, then run: python test_agent.py")
        show_next_steps()

if __name__ == "__main__":
    main()
