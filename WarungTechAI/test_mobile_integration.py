#!/usr/bin/env python3
"""
Mobile App Integration Test
Tests the exact same endpoints and data format used by the mobile app
"""

import requests
import json
import time
from datetime import datetime

# Mobile app configuration (matches aiService.ts)
MOBILE_CONFIG = {
    "AI_API_BASE": "http://192.168.43.166:5000",  # Network IP for mobile testing
    "TIMEOUT": 15,
    "USER_ID": "mobile_user",
    "TEST_MESSAGES": [
        "Halo, apa yang bisa kamu bantu?",
        "Bagaimana kondisi bisnis saya hari ini?",
        "Analisis portfolio crypto saya",
        "Berikan rekomendasi investasi untuk pemula",
        "Bagaimana cara meningkatkan revenue toko online?"
    ]
}

def test_mobile_chat_format():
    """Test chat endpoint with mobile app format"""
    
    print("📱 MOBILE APP INTEGRATION TEST")
    print("=" * 60)
    print(f"🌐 Testing endpoint: {MOBILE_CONFIG['AI_API_BASE']}")
    print(f"👤 User ID: {MOBILE_CONFIG['USER_ID']}")
    print("=" * 60)
    
    for i, message in enumerate(MOBILE_CONFIG["TEST_MESSAGES"], 1):
        print(f"\n🧪 Test {i}/5: {message[:50]}...")
        
        try:
            # Exact payload format from mobile app
            payload = {
                "message": message.strip(),
                "user_id": MOBILE_CONFIG["USER_ID"],
                "conversation_id": None  # New conversation
            }
            
            start_time = time.time()
            
            response = requests.post(
                f"{MOBILE_CONFIG['AI_API_BASE']}/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=MOBILE_CONFIG["TIMEOUT"]
            )
            
            response_time = round(time.time() - start_time, 2)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    print(f"✅ Success ({response_time}s)")
                    
                    # Validate mobile app expected format
                    report = data.get("report", "")
                    features = data.get("features_used", {})
                    
                    print(f"   📄 Response: {len(report)} chars")
                    print(f"   🔧 Features: {sum(1 for f in features.values() if f)}/{len(features)}")
                    
                    # Test mobile app formatting
                    mobile_formatted = format_for_mobile(data, i)
                    print(f"   📱 Mobile format: {mobile_formatted['type']} message")
                    
                else:
                    print(f"❌ AI Error: {data.get('error', 'Unknown')}")
            else:
                print(f"❌ HTTP {response.status_code}: {response.text[:100]}")
                
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout ({MOBILE_CONFIG['TIMEOUT']}s)")
        except requests.exceptions.ConnectionError:
            print("🔌 Connection failed - check AI server")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n{'=' * 60}")
    print("📱 Mobile integration test complete!")


def format_for_mobile(ai_response, message_id):
    """Format AI response for mobile app (matches aiService.ts)"""
    
    if not ai_response.get("success") or not ai_response.get("data"):
        return {
            "id": message_id,
            "type": "ai",
            "text": "❌ Maaf, terjadi kesalahan saat memproses permintaan Anda.",
            "subText": ai_response.get("error", "Silakan coba lagi dalam beberapa saat."),
            "time": datetime.now().strftime("%H:%M"),
            "showActions": True
        }
    
    # Simulate mobile app formatting logic
    data = ai_response.get("data", {})
    report = data.get("report", "")
    
    # Extract key info for mobile display
    has_card = False
    sub_text = ""
    
    # Check for business data
    if "revenue" in report.lower() or "omzet" in report.lower():
        sub_text = "💰 Analisis bisnis dan keuangan tersedia"
        has_card = True
    
    # Check for crypto data
    if "bitcoin" in report.lower() or "crypto" in report.lower():
        sub_text = "📈 Analisis pasar crypto dan rekomendasi investasi"
        has_card = True
    
    return {
        "id": message_id,
        "type": "ai",
        "text": report[:200] + "..." if len(report) > 200 else report,
        "subText": sub_text,
        "hasCard": has_card,
        "time": datetime.now().strftime("%H:%M"),
        "showActions": True,
        "metadata": {
            "fullReport": report,
            "features": ai_response.get("features_used", {}),
            "timestamp": ai_response.get("timestamp")
        }
    }


def test_health_endpoint():
    """Test health endpoint for mobile app"""
    
    print("\n🏥 HEALTH CHECK TEST")
    print("-" * 30)
    
    try:
        response = requests.get(
            f"{MOBILE_CONFIG['AI_API_BASE']}/health",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check: PASSED")
            print(f"   Status: {data.get('status')}")
            print(f"   Features: {data.get('features', {})}")
            print(f"   Requirements: {data.get('requirements', {})}")
            return True
        else:
            print(f"❌ Health check failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


def test_error_scenarios():
    """Test error handling for mobile app"""
    
    print("\n🚨 ERROR HANDLING TEST")
    print("-" * 30)
    
    # Test empty message
    try:
        response = requests.post(
            f"{MOBILE_CONFIG['AI_API_BASE']}/chat",
            json={"message": "", "user_id": "test"},
            timeout=5
        )
        
        if response.status_code == 400:
            print("✅ Empty message handling: PASSED")
        else:
            print(f"⚠️ Empty message: Got {response.status_code}, expected 400")
            
    except Exception as e:
        print(f"❌ Empty message test error: {e}")
    
    # Test invalid JSON
    try:
        response = requests.post(
            f"{MOBILE_CONFIG['AI_API_BASE']}/chat",
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code >= 400:
            print("✅ Invalid JSON handling: PASSED")
        else:
            print(f"⚠️ Invalid JSON: Got {response.status_code}, expected 4xx")
            
    except Exception as e:
        print(f"❌ Invalid JSON test error: {e}")


if __name__ == "__main__":
    print("🚀 WarungTech Mobile Integration Test Suite")
    print("=" * 60)
    
    # Test health first
    if test_health_endpoint():
        # Run mobile chat tests
        test_mobile_chat_format()
        
        # Test error scenarios
        test_error_scenarios()
        
        print("\n✅ Mobile integration testing complete!")
        print("\n💡 Next steps:")
        print("1. Update mobile app aiService.ts with working endpoint")
        print("2. Test actual mobile app chat functionality")
        print("3. Verify response formatting matches expectations")
        
    else:
        print("\n❌ Cannot proceed - AI server not accessible")
        print("💡 Start the AI server first:")
        print("   python start_ai_server.py")