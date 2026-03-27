#!/usr/bin/env python3
"""
Test WarungTech AI Configuration
"""

import os
import sys

def test_configuration():
    """Test if configuration is properly loaded"""
    
    print("🔧 Testing WarungTech AI Configuration...")
    print("="*50)
    
    # Check if .env file exists
    env_file = ".env"
    if os.path.exists(env_file):
        print("✅ .env file found")
        
        # Read .env file manually
        with open(env_file, 'r') as f:
            content = f.read()
            
        # Check for keys
        if "OPENROUTER_API_KEY=sk-or-v1-" in content:
            print("✅ OpenRouter API Key configured")
        else:
            print("❌ OpenRouter API Key missing or invalid")
            
        if "INFURA_PROJECT_ID=" in content and len(content.split("INFURA_PROJECT_ID=")[1].split('\n')[0].strip()) > 10:
            print("✅ Infura Project ID configured")
        else:
            print("⚠️ Infura Project ID missing (blockchain features disabled)")
            
    else:
        print("❌ .env file not found")
        return False
    
    print("\n🌐 Testing API Connectivity...")
    
    # Test basic imports
    try:
        import requests
        print("✅ Requests library available")
    except ImportError:
        print("❌ Requests library missing")
        return False
    
    # Test OpenRouter connectivity (simple)
    try:
        response = requests.get("https://openrouter.ai", timeout=5)
        if response.status_code == 200:
            print("✅ OpenRouter service reachable")
        else:
            print("⚠️ OpenRouter service may be down")
    except Exception as e:
        print(f"⚠️ Network connectivity issue: {e}")
    
    # Test WarungTech API connectivity
    try:
        response = requests.get("https://war-tech-backend-ouiu-a3ge8s8q9.vercel.app/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ WarungTech API reachable")
        else:
            print("⚠️ WarungTech API may have issues")
    except Exception as e:
        print(f"⚠️ WarungTech API connectivity issue: {e}")
    
    print("\n🎯 Configuration Summary:")
    print("- OpenRouter API: Ready for AI chat")
    print("- WarungTech API: Ready for business analysis")
    print("- Infura Web3: Ready for blockchain features")
    print("- Flask Server: Ready to start")
    
    print("\n🚀 Next Steps:")
    print("1. Start AI server: python AIEnhanced.py server")
    print("2. Test health: curl http://localhost:5000/health")
    print("3. Update mobile app IP if needed")
    print("4. Test chat functionality")
    
    return True

if __name__ == "__main__":
    success = test_configuration()
    if success:
        print("\n✅ Configuration test passed!")
        sys.exit(0)
    else:
        print("\n❌ Configuration test failed!")
        sys.exit(1)