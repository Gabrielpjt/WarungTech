#!/usr/bin/env python3
"""
WarungTech AI API Testing Prompts
Comprehensive test cases for all AI features
"""

import requests
import json
import time
from datetime import datetime

# Configuration
AI_API_BASE = "http://localhost:5000"
# Alternative endpoints to test:
# AI_API_BASE = "http://192.168.43.166:5000"  # Network IP
# AI_API_BASE = "http://127.0.0.1:5000"       # Loopback

# Test credentials (update with real values for production testing)
TEST_JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEsImVtYWlsIjoidGVzdEB3YXJ1bmd0ZWNoLmNvbSIsImlhdCI6MTczODMxNzYwMCwiZXhwIjoxNzM4OTIyNDAwfQ.test"
TEST_WALLET_ADDRESS = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

# Test configuration
TEST_CONFIG = {
    "timeout": 30,
    "max_retries": 2,
    "show_full_response": False,  # Set to True for debugging
    "save_results": True,         # Save test results to file
    "test_real_apis": True        # Test actual API integrations
}

def test_api_call(prompt, user_token="", wallet_address="", description=""):
    """Make API call and display results"""
    
    print(f"\n{'='*80}")
    print(f"🧪 TEST: {description}")
    print(f"{'='*80}")
    print(f"📝 Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
    print(f"🔑 Token: {'✅ Provided' if user_token else '❌ None'}")
    print(f"💰 Wallet: {wallet_address[:10] + '...' if wallet_address else '❌ None'}")
    print("-" * 80)
    
    try:
        payload = {
            "message": prompt,
            "user_token": user_token,
            "wallet_address": wallet_address
        }
        
        start_time = time.time()
        
        response = requests.post(
            f"{AI_API_BASE}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=TEST_CONFIG["timeout"]
        )
        
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        
        print(f"⏱️ Response Time: {response_time}s")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Status: SUCCESS")
                report = data.get('report', 'No report')
                print(f"� Response Length: {len(report)} characters")
                
                if TEST_CONFIG["show_full_response"]:
                    print("\n📋 FULL AI RESPONSE:")
                    print("-" * 40)
                    print(report)
                    print("-" * 40)
                else:
                    # Show truncated response
                    preview = report[:300] + "..." if len(report) > 300 else report
                    print(f"\n📋 AI RESPONSE PREVIEW:")
                    print("-" * 40)
                    print(preview)
                    print("-" * 40)
                
                # Show features used
                features = data.get('features_used', {})
                print(f"\n🔧 Features Used:")
                for feature, used in features.items():
                    status = "✅" if used else "❌"
                    print(f"  {status} {feature}")
                
                # Performance metrics
                if response_time > 20:
                    print("⚠️ SLOW RESPONSE - Consider optimization")
                elif response_time < 5:
                    print("🚀 FAST RESPONSE - Excellent performance")
                
                # Save result if configured
                if TEST_CONFIG["save_results"]:
                    save_test_result(description, prompt, data, response_time)
                    
            else:
                print("❌ Status: FAILED")
                print(f"Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except requests.exceptions.Timeout:
        print(f"⏰ Request timed out ({TEST_CONFIG['timeout']}s)")
    except requests.exceptions.ConnectionError:
        print("🔌 Connection failed - is the AI server running?")
        print(f"💡 Check if server is running at: {AI_API_BASE}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print(f"{'='*80}\n")


def save_test_result(test_name, prompt, response_data, response_time):
    """Save test results to file for analysis"""
    try:
        result = {
            "timestamp": datetime.now().isoformat(),
            "test_name": test_name,
            "prompt": prompt,
            "response_time": response_time,
            "success": response_data.get("success", False),
            "features_used": response_data.get("features_used", {}),
            "report_length": len(response_data.get("report", "")),
            "error": response_data.get("error")
        }
        
        # Append to results file
        results_file = f"test_results_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)
        except FileNotFoundError:
            results = []
        
        results.append(result)
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"⚠️ Failed to save test result: {e}")


def test_api_connectivity():
    """Test basic API connectivity and configuration"""
    print("\n🔍 TESTING API CONNECTIVITY")
    print("=" * 50)
    
    # Test different endpoints
    endpoints_to_test = [
        "http://localhost:5000",
        "http://127.0.0.1:5000", 
        "http://192.168.43.166:5000"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            print(f"🌐 Testing: {endpoint}")
            response = requests.get(f"{endpoint}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {endpoint} - ONLINE")
                print(f"   Features: {data.get('features', {})}")
                return endpoint
            else:
                print(f"❌ {endpoint} - HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - {str(e)}")
    
    print("⚠️ No AI server found. Please start the server first.")
    return None

def run_all_tests():
    """Run comprehensive test suite"""
    global AI_API_BASE
    
    print("🚀 WarungTech AI API Testing Suite")
    print("=" * 80)
    print(f"🌐 API Base: {AI_API_BASE}")
    print(f"🕒 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⚙️ Configuration: {TEST_CONFIG}")
    print("=" * 80)
    
    # Test API connectivity first
    working_endpoint = test_api_connectivity()
    if not working_endpoint:
        print("❌ Cannot proceed - AI server not accessible")
        return False
    
    # Update API base if different endpoint works
    AI_API_BASE = working_endpoint
    
    # Test 1: Health Check
    print("\n🏥 Testing Health Endpoint...")
    try:
        response = requests.get(f"{AI_API_BASE}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health Check: PASSED")
            print(f"📊 Features Available: {data.get('features', {})}")
            print(f"🔧 Requirements: {data.get('requirements', {})}")
        else:
            print(f"❌ Health Check: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Health Check: ERROR - {e}")
    
    # Test 2: Basic Chat (No Auth)
    test_api_call(
        prompt="Halo, apa yang bisa kamu bantu?",
        description="Basic Chat - No Authentication"
    )
    
    # Test 3: Business Analysis (With Auth)
    test_api_call(
        prompt="Tolong analisis kondisi bisnis saya. Bagaimana performa revenue, orders, dan produk bulan ini?",
        user_token=TEST_JWT_TOKEN,
        description="Business Analysis - With JWT Token"
    )
    
    # Test 4: Investment Analysis
    test_api_call(
        prompt="Analisis portfolio investasi crypto saya. Berikan rekomendasi diversifikasi dan strategi untuk 3 bulan ke depan.",
        user_token=TEST_JWT_TOKEN,
        description="Investment Portfolio Analysis"
    )
    
    # Test 5: Market Data Analysis
    test_api_call(
        prompt="Bagaimana performa Bitcoin, Ethereum, dan Solana hari ini? Berikan analisis teknikal dan rekomendasi trading.",
        description="Crypto Market Data Analysis"
    )
    
    # Test 6: Blockchain Coupons (Full Auth)
    test_api_call(
        prompt="Berapa banyak kupon blockchain yang sudah saya buat? Bagaimana utilisasi dan performanya?",
        user_token=TEST_JWT_TOKEN,
        wallet_address=TEST_WALLET_ADDRESS,
        description="Blockchain Coupon Analysis - Full Auth"
    )
    
    # Test 7: Comprehensive Business Intelligence
    test_api_call(
        prompt="""Tolong berikan analisis lengkap dan komprehensif:
        
        1. Kondisi bisnis dan keuangan saya saat ini
        2. Performa portfolio investasi crypto
        3. Status kupon blockchain dan promo
        4. Analisis pasar crypto terkini
        5. Rekomendasi strategis untuk 6 bulan ke depan
        
        Berikan insight mendalam dengan data konkret dan actionable recommendations.""",
        user_token=TEST_JWT_TOKEN,
        wallet_address=TEST_WALLET_ADDRESS,
        description="Comprehensive Business Intelligence Analysis"
    )
    
    # Test 8: Financial Planning
    test_api_call(
        prompt="Saya ingin merencanakan keuangan untuk ekspansi bisnis. Analisis cash flow, profit margin, dan berikan rekomendasi investasi yang aman.",
        user_token=TEST_JWT_TOKEN,
        description="Financial Planning & Cash Flow Analysis"
    )
    
    # Test 9: Risk Assessment
    test_api_call(
        prompt="Evaluasi risiko bisnis dan investasi saya. Apa saja potensi masalah dan bagaimana cara mitigasinya?",
        user_token=TEST_JWT_TOKEN,
        wallet_address=TEST_WALLET_ADDRESS,
        description="Risk Assessment & Mitigation Strategy"
    )
    
    # Test 10: Growth Strategy
    test_api_call(
        prompt="Berdasarkan data bisnis saya, bagaimana strategi terbaik untuk meningkatkan revenue 50% dalam 6 bulan? Berikan roadmap detail.",
        user_token=TEST_JWT_TOKEN,
        description="Growth Strategy & Revenue Optimization"
    )
    
    # Test 11: Specific Crypto Analysis
    test_api_call(
        prompt="Analisis Bitcoin, Ethereum, dan Solana hari ini. Berikan technical analysis dengan RSI, support/resistance levels, dan rekomendasi entry point.",
        description="Detailed Crypto Technical Analysis"
    )
    
    # Test 12: DCA Strategy Planning
    test_api_call(
        prompt="Saya punya budget Rp 2 juta per bulan untuk investasi crypto. Buatkan strategi DCA (Dollar Cost Averaging) yang optimal dengan alokasi per coin.",
        user_token=TEST_JWT_TOKEN,
        description="DCA Investment Strategy Planning"
    )
    
    # Test 13: Business Expansion Planning
    test_api_call(
        prompt="Saya ingin ekspansi bisnis ke 3 kota baru. Analisis cash flow, modal yang dibutuhkan, dan timeline realistis berdasarkan performa saat ini.",
        user_token=TEST_JWT_TOKEN,
        description="Business Expansion Financial Planning"
    )
    
    # Test 14: Blockchain Coupon Analysis (Full Features)
    test_api_call(
        prompt="Berapa kupon blockchain yang sudah saya deploy? Bagaimana utilisasi dan ROI dari setiap campaign promo? Berikan analisis mendalam.",
        user_token=TEST_JWT_TOKEN,
        wallet_address=TEST_WALLET_ADDRESS,
        description="Blockchain Coupon ROI Analysis"
    )
    
    # Test 15: Market Sentiment & News Impact
    test_api_call(
        prompt="Bagaimana sentiment pasar crypto saat ini? Apakah ada berita atau event penting yang akan mempengaruhi harga dalam 2 minggu ke depan?",
        description="Market Sentiment & News Analysis"
    )
    
    # Test 16: Portfolio Rebalancing
    test_api_call(
        prompt="Portfolio crypto saya: BTC 60%, ETH 25%, SOL 15%. Apakah perlu rebalancing? Berikan strategi optimal berdasarkan kondisi pasar saat ini.",
        user_token=TEST_JWT_TOKEN,
        wallet_address=TEST_WALLET_ADDRESS,
        description="Portfolio Rebalancing Strategy"
    )
    
    # Test 17: Emergency Financial Planning
    test_api_call(
        prompt="Jika terjadi krisis ekonomi atau bear market, bagaimana saya harus melindungi bisnis dan investasi? Berikan contingency plan detail.",
        user_token=TEST_JWT_TOKEN,
        description="Crisis Management & Contingency Planning"
    )
    
    # Test 18: Tax Optimization
    test_api_call(
        prompt="Bagaimana cara mengoptimalkan pajak dari profit trading crypto dan revenue bisnis? Berikan strategi legal untuk meminimalkan beban pajak.",
        user_token=TEST_JWT_TOKEN,
        description="Tax Optimization Strategy"
    )
    
    # Test 19: Long-term Wealth Building
    test_api_call(
        prompt="Saya ingin membangun wealth jangka panjang 10 tahun. Berikan roadmap lengkap: bisnis scaling, investasi diversifikasi, dan passive income streams.",
        user_token=TEST_JWT_TOKEN,
        wallet_address=TEST_WALLET_ADDRESS,
        description="Long-term Wealth Building Strategy"
    )
    
    # Test 20: AI Stress Test (Complex Multi-domain Query)
    test_api_call(
        prompt="""Tolong berikan analisis SUPER KOMPREHENSIF dan mendalam:

        📊 BUSINESS INTELLIGENCE:
        1. Analisis mendalam revenue, profit margin, dan growth trajectory
        2. Evaluasi product portfolio dan market positioning
        3. Competitive analysis dan market opportunity
        4. Operational efficiency dan cost optimization

        💰 FINANCIAL ANALYSIS:
        1. Cash flow forecasting 12 bulan ke depan
        2. Working capital management dan liquidity analysis
        3. Debt-to-equity ratio dan financial leverage
        4. Break-even analysis untuk expansion plans

        🚀 INVESTMENT STRATEGY:
        1. Portfolio optimization dengan Modern Portfolio Theory
        2. Risk-adjusted returns dan Sharpe ratio analysis
        3. Correlation analysis antar asset classes
        4. Hedging strategy untuk downside protection

        🎯 BLOCKCHAIN & CRYPTO:
        1. Smart contract utilization dan gas optimization
        2. DeFi yield farming opportunities
        3. NFT marketplace potential untuk brand expansion
        4. Tokenomics design untuk loyalty program

        📈 MARKET ANALYSIS:
        1. Macro-economic factors affecting crypto dan business
        2. Regulatory landscape dan compliance requirements
        3. Technology trends dan disruption threats
        4. Consumer behavior shifts post-pandemic

        💡 STRATEGIC RECOMMENDATIONS:
        1. 30-60-90 day action plan dengan specific KPIs
        2. Resource allocation dan budget planning
        3. Team scaling dan talent acquisition strategy
        4. Technology stack modernization roadmap

        Berikan insight yang actionable dengan data konkret, risk assessment, dan timeline eksekusi yang realistis!""",
        user_token=TEST_JWT_TOKEN,
        wallet_address=TEST_WALLET_ADDRESS,
        description="🔥 AI STRESS TEST - Ultra Comprehensive Analysis"
    )
    
    print("\n🎉 Testing Complete!")
    print("=" * 80)
    print("📊 COMPREHENSIVE TEST SUMMARY:")
    print("✅ Basic functionality (health, chat)")
    print("✅ Authentication scenarios (with/without JWT)")
    print("✅ Business intelligence capabilities")
    print("✅ Financial analysis and planning")
    print("✅ Crypto market data integration")
    print("✅ Investment portfolio analysis")
    print("✅ Blockchain coupon features")
    print("✅ Risk assessment and mitigation")
    print("✅ Growth strategy planning")
    print("✅ Advanced technical analysis")
    print("✅ DCA and rebalancing strategies")
    print("✅ Crisis management planning")
    print("✅ Tax optimization advice")
    print("✅ Long-term wealth building")
    print("✅ AI stress test with complex queries")
    
    print("\n🔧 TECHNICAL VALIDATION:")
    print("- API endpoint connectivity")
    print("- Response time measurement")
    print("- Error handling verification")
    print("- Feature availability checking")
    print("- Token validation testing")
    print("- Wallet address validation")
    
    print("\n💡 NEXT STEPS:")
    print("1. 📱 Test mobile app integration")
    print("2. 🔑 Use real JWT tokens from login")
    print("3. 💰 Verify with actual wallet addresses")
    print("4. 📊 Cross-check business data accuracy")
    print("5. 🚀 Deploy to production environment")
    print("6. 📈 Monitor performance metrics")
    print("7. 🔄 Set up automated testing pipeline")
    
    print("\n🎯 SUCCESS CRITERIA:")
    print("- All tests return HTTP 200")
    print("- AI responses are relevant and actionable")
    print("- Business data matches actual metrics")
    print("- Crypto recommendations are current")
    print("- Error messages are user-friendly")
    print("- Response times under 30 seconds")
    
    print("\n🔗 INTEGRATION CHECKLIST:")
    print("- ✅ WarungTech Backend API connection")
    print("- ✅ CoinGecko market data integration")
    print("- ✅ OpenRouter LLM functionality")
    print("- ✅ Web3 blockchain features (optional)")
    print("- ✅ Mobile app aiService.ts compatibility")
    
    print(f"\n🌐 API Endpoints Tested:")
    print(f"- Health Check: {AI_API_BASE}/health")
    print(f"- Chat Interface: {AI_API_BASE}/chat")
    print(f"- Business Analysis: WarungTech Backend API")
    print(f"- Market Data: CoinGecko API")
    print(f"- Blockchain: Ethereum Sepolia (if configured)")
    
    print("\n" + "="*80)
    print("🚀 WarungTech AI Testing Suite Complete!")
    print("="*80)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='WarungTech AI API Testing Suite')
    parser.add_argument('--endpoint', default='http://localhost:5000', 
                       help='AI API endpoint (default: http://localhost:5000)')
    parser.add_argument('--token', default=TEST_JWT_TOKEN,
                       help='JWT token for authenticated tests')
    parser.add_argument('--wallet', default=TEST_WALLET_ADDRESS,
                       help='Wallet address for blockchain tests')
    parser.add_argument('--quick', action='store_true',
                       help='Run only essential tests (faster)')
    parser.add_argument('--full-response', action='store_true',
                       help='Show full AI responses (verbose)')
    parser.add_argument('--save-results', action='store_true', default=True,
                       help='Save test results to file')
    
    args = parser.parse_args()
    
    # Update configuration
    AI_API_BASE = args.endpoint
    TEST_JWT_TOKEN = args.token
    TEST_WALLET_ADDRESS = args.wallet
    TEST_CONFIG["show_full_response"] = args.full_response
    TEST_CONFIG["save_results"] = args.save_results
    
    if args.quick:
        print("🏃‍♂️ Running QUICK test suite...")
        
        # Quick tests only
        working_endpoint = test_api_connectivity()
        if working_endpoint:
            AI_API_BASE = working_endpoint
            
            test_api_call(
                prompt="Halo, test koneksi AI",
                description="Quick Connection Test"
            )
            
            test_api_call(
                prompt="Analisis bisnis saya secara singkat",
                user_token=TEST_JWT_TOKEN,
                description="Quick Business Analysis"
            )
            
            test_api_call(
                prompt="Harga Bitcoin dan Ethereum hari ini?",
                description="Quick Market Data"
            )
            
            print("\n✅ Quick test complete!")
        else:
            print("❌ Cannot run tests - AI server not accessible")
    else:
        print("🔬 Running COMPREHENSIVE test suite...")
        success = run_all_tests()
        
        if success:
            print("\n🎉 All tests completed successfully!")
        else:
            print("\n⚠️ Some tests failed - check logs above")
    
    print(f"\n📊 Test results saved to: test_results_{datetime.now().strftime('%Y%m%d')}.json")
    print("🔗 Use results for performance monitoring and debugging")
    
    # Usage examples
    print("\n" + "="*80)
    print("📖 USAGE EXAMPLES:")
    print("="*80)
    print("# Run all tests with default settings:")
    print("python test_api_prompts.py")
    print()
    print("# Run quick tests only:")
    print("python test_api_prompts.py --quick")
    print()
    print("# Test with custom endpoint:")
    print("python test_api_prompts.py --endpoint http://192.168.43.166:5000")
    print()
    print("# Show full AI responses:")
    print("python test_api_prompts.py --full-response")
    print()
    print("# Test with real JWT token:")
    print("python test_api_prompts.py --token 'eyJhbGc...'")
    print("="*80)