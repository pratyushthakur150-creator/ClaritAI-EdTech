#!/usr/bin/env python3
"""
Setup and Test Script for Rate Limiting System

This script installs dependencies, tests Redis connection,
and validates the rate limiting system.
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "-r", "requirements.txt"
        ])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

def test_redis_connection():
    """Test Redis connection"""
    print("Testing Redis connection...")
    
    try:
        import redis
        
        client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        
        client.ping()
        print("✓ Redis connection successful")
        
        # Test basic operations
        client.set("test_key", "test_value", ex=60)
        value = client.get("test_key")
        client.delete("test_key")
        
        print("✓ Redis operations working")
        return True
        
    except ImportError:
        print("✗ Redis library not installed")
        return False
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        print("Make sure Redis server is running on localhost:6379")
        return False

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("Testing rate limiting system...")
    
    try:
        import asyncio
        from app.core.rate_limiter import RateLimiter, SubscriptionTier
        import redis
        
        # Create Redis client
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        
        # Create rate limiter
        rate_limiter = RateLimiter(redis_client)
        
        async def test_basic_rate_limiting():
            # Test basic functionality
            allowed, info = await rate_limiter.check_rate_limit(
                tenant_id="test-tenant",
                tier=SubscriptionTier.STARTER,
                endpoint="/api/v1/test"
            )
            
            return allowed and info['limit'] > 0
        
        result = asyncio.run(test_basic_rate_limiting())
        
        if result:
            print("✓ Rate limiting system working")
            
            # Clean up test data
            keys = redis_client.keys("rate_limit:test-tenant*")
            if keys:
                redis_client.delete(*keys)
            
            return True
        else:
            print("✗ Rate limiting test failed")
            return False
            
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Rate limiting test failed: {e}")
        return False

def test_fastapi_integration():
    """Test FastAPI integration"""
    print("Testing FastAPI integration...")
    
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # Test health endpoint (should be exempt)
        response = client.get("/health")
        if response.status_code != 200:
            print("✗ Health endpoint failed")
            return False
        
        print("✓ FastAPI integration working")
        return True
        
    except ImportError as e:
        print(f"✗ FastAPI import error: {e}")
        return False
    except Exception as e:
        print(f"✗ FastAPI integration test failed: {e}")
        return False

def main():
    """Main setup and test function"""
    print("Ravian Backend API - Rate Limiting Setup & Test")
    print("=" * 60)
    
    success = True
    
    # Install dependencies
    if not install_dependencies():
        success = False
    
    print()
    
    # Test Redis connection
    if not test_redis_connection():
        success = False
        print("\nTo install and start Redis:")
        print("  - Windows: Download from https://redis.io/download")
        print("  - macOS: brew install redis && brew services start redis")  
        print("  - Ubuntu: sudo apt-get install redis-server")
        print("  - Docker: docker run -d -p 6379:6379 redis:alpine")
    
    print()
    
    # Test rate limiting
    if success and not test_rate_limiting():
        success = False
    
    print()
    
    # Test FastAPI integration
    if success and not test_fastapi_integration():
        success = False
    
    print()
    print("=" * 60)
    
    if success:
        print("✓ All tests passed! Rate limiting system is ready.")
        print()
        print("Next steps:")
        print("1. Start Redis server if not already running")
        print("2. Update JWT_SECRET_KEY in .env file")
        print("3. Start the API server: python main.py")
        print("4. Test rate limiting: python rate_limiting_examples.py")
        print("5. Check API docs: http://localhost:8000/docs")
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        print()
        print("Common issues:")
        print("- Redis server not running")
        print("- Missing dependencies")
        print("- Configuration errors")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
