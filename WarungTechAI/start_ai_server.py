#!/usr/bin/env python3
"""
WarungTech AI Server Startup Script
"""

import os
import sys
import subprocess

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'requests',
        'flask', 
        'flask_cors',
        'web3',
        'langchain_core',
        'langchain_openai',
        'langgraph'
    ]
    
    missing = []
    for package in required_packages:
        try:
            if package == 'flask_cors':
                __import__('flask_cors')
            elif package == 'langchain_core':
                __import__('langchain_core')
            elif package == 'langchain_openai':
                __import__('langchain_openai')
            else:
                __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("📦 Installing missing packages...")
        
        try:
            # Map package names for pip install
            pip_packages = []
            for pkg in missing:
                if pkg == 'langchain_core':
                    pip_packages.append('langchain-core')
                elif pkg == 'langchain_openai':
                    pip_packages.append('langchain-openai')
                elif pkg == 'flask_cors':
                    pip_packages.append('flask-cors')
                else:
                    pip_packages.append(pkg)
            
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + pip_packages)
            print("✅ Packages installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install packages: {e}")
            return False
    
    return True

def main():
    """Main startup function"""
    
    print("🚀 Starting WarungTech AI Assistant...")
    print("="*50)
    
    # Check configuration
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("📝 Please create .env file with your API keys")
        return False
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Import and run the AI server
    try:
        print("🤖 Loading AI Assistant...")
        
        # Set environment variables from .env
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        
        # Import the AI module
        from AIEnhanced import app, OPENROUTER_API_KEY, INFURA_PROJECT_ID
        
        print("✅ AI Assistant loaded successfully")
        print(f"🔑 OpenRouter: {'✅ Configured' if OPENROUTER_API_KEY else '❌ Missing'}")
        print(f"🌐 Infura: {'✅ Configured' if INFURA_PROJECT_ID else '⚠️ Optional'}")
        
        print("\n🌐 Starting Flask server...")
        print("📡 Server will be available at: http://localhost:5000")
        print("🔍 Health check: http://localhost:5000/health")
        print("💬 Chat endpoint: http://localhost:5000/chat")
        print("\n⏹️ Press Ctrl+C to stop the server")
        print("="*50)
        
        # Start the Flask server
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False  # Avoid double startup in debug mode
        )
        
    except ImportError as e:
        print(f"❌ Failed to import AI module: {e}")
        return False
    except KeyboardInterrupt:
        print("\n\n⏹️ Server stopped by user")
        return True
    except Exception as e:
        print(f"❌ Server error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Failed to start AI server")
        sys.exit(1)
    else:
        print("\n✅ AI server stopped gracefully")
        sys.exit(0)