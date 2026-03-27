#!/usr/bin/env python3
"""
Debug test to isolate the import issue
"""

import sys
import traceback

print("🔍 Debug Test - Isolating Import Issue")
print("=" * 50)

try:
    print("1. Testing basic imports...")
    import os
    import json
    import requests
    from datetime import datetime
    print("✅ Basic imports successful")
    
    print("2. Testing LangChain imports...")
    from langchain_core.tools import tool
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
    from langchain_openai import ChatOpenAI
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolNode
    print("✅ LangChain imports successful")
    
    print("3. Testing Web3 import...")
    from web3 import Web3
    print("✅ Web3 import successful")
    
    print("4. Testing dotenv import...")
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Dotenv import successful")
    
    print("5. Testing AIEnhanced import...")
    import AIEnhanced
    print("✅ AIEnhanced import successful")
    
    print("6. Testing agent creation...")
    agent = AIEnhanced.build_agent()
    print("✅ Agent creation successful")
    
    print("7. Testing simple agent run...")
    result = AIEnhanced.run_agent("Hello, test message")
    print(f"✅ Agent run result: {result.get('success', False)}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n🔍 Full traceback:")
    traceback.print_exc()