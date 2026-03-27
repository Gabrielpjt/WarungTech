# WarungTech AI API Testing Guide

## 🚀 Quick Start

### 1. Start the AI Server
```bash
# Method 1: Using startup script
python start_ai_server.py

# Method 2: Direct execution
python AIEnhanced.py server

# Method 3: Using batch file (Windows)
start_ai_server.bat
```

### 2. Run API Tests
```bash
# Run all tests
python test_api_prompts.py

# Quick tests only (faster)
python test_api_prompts.py --quick

# Windows batch file
test_ai_api.bat
```

## 🔧 Configuration

### Environment Variables (.env file)
```env
# REQUIRED: OpenRouter API Key
OPENROUTER_API_KEY=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

# OPTIONAL: Infura Project ID for blockchain features
INFURA_PROJECT_ID=b8a323a7e8f142c5b07ed9808af1f1a6
```

### Test Configuration
Update these variables in `test_api_prompts.py`:
```python
AI_API_BASE = "http://localhost:5000"  # AI server endpoint
TEST_JWT_TOKEN = "your-jwt-token-here"  # Real JWT from mobile app
TEST_WALLET_ADDRESS = "0x742d35Cc..."   # Ethereum wallet address
```

## 📊 Test Categories

### 1. Basic Functionality
- ✅ Health check endpoint
- ✅ Basic chat without authentication
- ✅ API connectivity validation

### 2. Business Analysis (Requires JWT Token)
- 📊 Dashboard statistics
- 💰 Financial summary
- 📈 Revenue analysis
- 🏪 Store performance metrics

### 3. Investment Analysis
- 💎 Crypto portfolio analysis
- 📈 Market data integration
- 🎯 Investment recommendations
- ⚖️ Risk assessment

### 4. Blockchain Features (Requires Wallet Address)
- 🎫 Smart contract coupon analysis
- 🔗 Blockchain transaction data
- 💰 On-chain asset tracking

### 5. Advanced Features
- 🧠 Comprehensive business intelligence
- 📊 Multi-domain analysis
- 🎯 Strategic planning
- 🚀 Growth optimization

## 🎯 Test Scenarios

### Scenario 1: New User (No Auth)
```bash
python test_api_prompts.py --quick
```
Tests basic chat functionality and market data without authentication.

### Scenario 2: Business Owner (With JWT)
```bash
python test_api_prompts.py --token "eyJhbGc..."
```
Tests business analysis, financial planning, and investment features.

### Scenario 3: Crypto Investor (Full Auth)
```bash
python test_api_prompts.py --token "eyJhbGc..." --wallet "0x742d35..."
```
Tests all features including blockchain coupon analysis.

### Scenario 4: Production Testing
```bash
python test_api_prompts.py --endpoint "http://192.168.43.166:5000" --full-response
```
Tests against network-deployed AI server with verbose output.

## 📈 Performance Metrics

### Response Time Benchmarks
- ⚡ **Fast**: < 5 seconds
- ✅ **Good**: 5-15 seconds  
- ⚠️ **Slow**: 15-30 seconds
- ❌ **Timeout**: > 30 seconds

### Success Criteria
- All tests return HTTP 200
- AI responses are relevant and actionable
- Business data matches actual metrics
- Crypto recommendations are current
- Error messages are user-friendly

## 🔍 Debugging

### Common Issues

#### 1. Connection Refused
```
🔌 Connection failed - is the AI server running?
```
**Solution**: Start the AI server first using `python start_ai_server.py`

#### 2. Invalid JWT Token
```
❌ Authentication failed - invalid or expired token
```
**Solution**: Get a fresh JWT token from the mobile app login

#### 3. Missing API Keys
```
❌ ERROR: OPENROUTER_API_KEY not found
```
**Solution**: Add your OpenRouter API key to the `.env` file

#### 4. Slow Responses
```
⚠️ SLOW RESPONSE - Consider optimization
```
**Solution**: Check internet connection and API rate limits

### Debug Mode
```bash
# Show full AI responses
python test_api_prompts.py --full-response

# Test specific endpoint
python test_api_prompts.py --endpoint "http://127.0.0.1:5000"
```

## 📊 Test Results

### Automatic Logging
Test results are automatically saved to:
```
test_results_YYYYMMDD.json
```

### Result Analysis
```python
import json

# Load test results
with open('test_results_20260131.json', 'r') as f:
    results = json.load(f)

# Analyze performance
avg_response_time = sum(r['response_time'] for r in results) / len(results)
success_rate = sum(1 for r in results if r['success']) / len(results) * 100

print(f"Average Response Time: {avg_response_time:.2f}s")
print(f"Success Rate: {success_rate:.1f}%")
```

## 🚀 Integration Testing

### Mobile App Integration
1. Start AI server: `python start_ai_server.py`
2. Update mobile app `aiService.ts` with correct IP
3. Test chat functionality in mobile app
4. Verify responses match API test results

### Production Deployment
1. Deploy AI server to cloud/VPS
2. Update `AI_API_BASE` in test script
3. Run full test suite against production
4. Monitor performance and error rates

## 📋 Test Checklist

### Pre-Testing
- [ ] AI server is running
- [ ] `.env` file configured with API keys
- [ ] Test credentials updated
- [ ] Network connectivity verified

### During Testing
- [ ] All health checks pass
- [ ] Authentication tests work
- [ ] Business data is accurate
- [ ] Crypto data is current
- [ ] Response times acceptable

### Post-Testing
- [ ] Results saved and analyzed
- [ ] Performance metrics reviewed
- [ ] Issues documented and fixed
- [ ] Mobile app integration tested

## 🔗 Related Files

- `AIEnhanced.py` - Main AI implementation
- `start_ai_server.py` - Server startup script
- `test_api_prompts.py` - Test suite
- `.env` - Environment configuration
- `requirements.txt` - Python dependencies

## 💡 Tips & Best Practices

1. **Always test health endpoint first** to verify server status
2. **Use real JWT tokens** for accurate business data testing
3. **Test with different network conditions** to simulate mobile usage
4. **Monitor response times** and optimize slow queries
5. **Save test results** for performance tracking over time
6. **Test error scenarios** to ensure graceful failure handling

## 🆘 Support

If you encounter issues:

1. Check the AI server logs for errors
2. Verify API keys are correct and active
3. Test network connectivity to external APIs
4. Review test results JSON for patterns
5. Update dependencies if needed

For additional help, check the main project documentation or contact the development team.