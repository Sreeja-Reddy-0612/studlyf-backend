#!/usr/bin/env python3
"""
MongoDB Connection Test Script
This script helps diagnose MongoDB Atlas connection issues
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
import ssl

# Load environment variables
load_dotenv()

def test_mongodb_connection():
    """Test MongoDB connection with different configurations"""
    
    MONGO_URI = os.getenv("MONGO_URI")
    if not MONGO_URI:
        print("MONGO_URI not found in environment variables")
        print("Please set MONGO_URI in your .env file")
        return False
    
    print(f"Testing connection to: {MONGO_URI[:20]}...")
    
    # Test 1: Standard connection with SSL
    print("\nTest 1: Standard SSL connection")
    try:
        client = MongoClient(
            MONGO_URI,
            tls=True,
            tlsAllowInvalidCertificates=False,
            tlsAllowInvalidHostnames=False,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        client.admin.command('ping')
        print("Standard SSL connection successful!")
        client.close()
        return True
    except Exception as e:
        print(f"Standard SSL connection failed: {e}")
    
    # Test 2: Connection with relaxed SSL settings
    print("\nTest 2: Relaxed SSL connection")
    try:
        client = MongoClient(
            MONGO_URI,
            tls=True,
            tlsAllowInvalidCertificates=True,
            tlsAllowInvalidHostnames=True,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        client.admin.command('ping')
        print("Relaxed SSL connection successful!")
        client.close()
        return True
    except Exception as e:
        print(f"Relaxed SSL connection failed: {e}")
    
    # Test 3: Connection without SSL (for local MongoDB)
    print("\nTest 3: Non-SSL connection")
    try:
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        client.admin.command('ping')
        print("Non-SSL connection successful!")
        client.close()
        return True
    except Exception as e:
        print(f"Non-SSL connection failed: {e}")
    
    print("\nAll connection tests failed!")
    return False

def check_environment():
    """Check environment variables and system configuration"""
    print("Environment Check:")
    print(f"Python version: {os.sys.version}")
    print(f"SSL version: {ssl.OPENSSL_VERSION}")
    
    MONGO_URI = os.getenv("MONGO_URI")
    if MONGO_URI:
        print(f"MONGO_URI: {MONGO_URI[:50]}...")
        if "mongodb+srv://" in MONGO_URI:
            print("Using MongoDB Atlas (mongodb+srv://)")
        elif "mongodb://" in MONGO_URI:
            print("Using standard MongoDB connection")
        else:
            print("Invalid MongoDB URI format")
    else:
        print("MONGO_URI not set")

def provide_troubleshooting_tips():
    """Provide troubleshooting tips"""
    print("\nTroubleshooting Tips:")
    print("1. Ensure your MongoDB Atlas cluster is running")
    print("2. Check if your IP address is whitelisted in MongoDB Atlas")
    print("3. Verify your username and password in the connection string")
    print("4. Make sure your MongoDB Atlas cluster allows connections from your network")
    print("5. Try updating your MongoDB driver: pip install --upgrade pymongo")
    print("6. Check if your firewall is blocking the connection")
    print("7. For development, you can use the relaxed SSL settings")

if __name__ == "__main__":
    print("MongoDB Connection Test")
    print("=" * 50)
    
    check_environment()
    print("\n" + "=" * 50)
    
    success = test_mongodb_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("MongoDB connection test completed successfully!")
    else:
        provide_troubleshooting_tips()
