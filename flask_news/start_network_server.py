#!/usr/bin/env python3
"""
Enhanced startup script for the StudLyf Network Flask Backend
Includes environment validation and graceful startup
"""

import os
import sys
import json
import base64
from dotenv import load_dotenv

def validate_environment():
    """Validate required environment variables"""
    print("🔍 Validating environment configuration...")
    
    required_vars = {
        'MONGO_URI': 'MongoDB connection string',
        'FIREBASE_ADMIN_KEY': 'Firebase Admin SDK key (base64 encoded)'
    }
    
    missing_vars = []
    
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"  - {var}: {description}")
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(var)
        print("\n📝 Please create a .env file with the required variables.")
        print("💡 See NETWORK_SETUP.md for detailed instructions.")
        return False
    
    # Validate Firebase Admin Key format
    try:
        firebase_key = os.getenv('FIREBASE_ADMIN_KEY')
        decoded_key = base64.b64decode(firebase_key).decode('utf-8')
        json.loads(decoded_key)
        print("✅ Firebase Admin Key format is valid")
    except Exception as e:
        print(f"❌ Invalid Firebase Admin Key format: {e}")
        return False
    
    print("✅ Environment validation successful!")
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    print("📦 Checking dependencies...")
    
    required_packages = [
        'flask',
        'flask_cors',
        'pymongo',
        'firebase_admin',
        'python_dotenv',
        'apscheduler',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('_', '-'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n💡 Install missing packages with: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed!")
    return True

def main():
    """Main startup function"""
    print("🚀 Starting StudLyf Network Flask Backend...")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    print("🌟 All checks passed! Starting the Flask application...")
    print("-" * 60)
    
    # Import and run the Flask app
    try:
        from app import app, create_indexes, schedule_jobs, fetch_news, fetch_blogs, fetch_shorts, db
        
        # Initialize data and indexes
        print("📊 Initializing data and database indexes...")
        if db:
            create_indexes()
        
        # Fetch initial data
        print("📰 Fetching initial news, blogs, and shorts...")
        fetch_news()
        fetch_blogs()
        fetch_shorts()
        
        # Start background scheduler
        print("⏰ Starting background scheduler...")
        schedule_jobs()
        
        print("✅ Initialization complete!")
        print("🌐 Server starting on http://localhost:5001")
        print("📚 API Documentation available in NETWORK_SETUP.md")
        print("🧪 Test the API with: python test_network_api.py")
        print("-" * 60)
        
        # Run the Flask app
        app.run(debug=True, port=5001, host='0.0.0.0')
        
    except ImportError as e:
        print(f"❌ Failed to import Flask app: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

