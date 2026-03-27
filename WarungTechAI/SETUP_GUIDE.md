# 🚀 WarungTech AI Assistant - Setup Guide

## 📋 Overview

The WarungTech AI Assistant provides intelligent business analysis, investment recommendations, and blockchain coupon management for the WarungTech ecosystem.

## 🔑 Required API Keys

### 1. OpenRouter API Key (REQUIRED)
**Purpose**: Powers the AI chat functionality and business analysis

**How to get**:
1. Go to [https://openrouter.ai/keys](https://openrouter.ai/keys)
2. Create account (free)
3. Click "Create Key"
4. Copy the key (starts with `sk-or-v1-`)

**Cost**: Pay-per-use (~$0.001-0.01 per request), free tier available

### 2. Infura Project ID (OPTIONAL)
**Purpose**: Enables blockchain coupon features and Web3 integration

**How to get**:
1. Go to [https://infura.io/register](https://infura.io/register)
2. Create free account
3. Create new project → Select "Ethereum"
4. Copy Project ID from dashboard

**Cost**: Free tier (100,000 requests/day)

## 🛠️ Installation

### 1. Install Python Dependencies
```bash
cd WarungTechAI
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
# Copy example file
cp .env.example .env

# Edit .env file and add your keys
nano .env
```

Add your keys to `.env`:
```env
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
INFURA_PROJECT_ID=your-infura-project-id-here
```

### 3. Test Installation
```bash
# Test basic functionality
python AIEnhanced_Fixed.py

# Or start API server
python AIEnhanced_Fixed.py server
```

## 🌐 API Endpoints

### Start Server
```bash
python AIEnhanced_Fixed.py server
```

Server runs on: `http://localhost:5000`

### Available Endpoints

#### 1. Chat Endpoint
```bash
POST /chat
Content-Type: application/json

{
  "message": "Analisis bisnis saya dan berikan rekomendasi",
  "user_token": "eyJhbGc...",
  "wallet_address": "0x742d35Cc..."
}
```

#### 2. Health Check
```bash
GET /health
```

## 📱 Mobile App Integration

### Update AI Service Configuration
In `WarTechUIRevision1/services/aiService.ts`:

```typescript
const AI_API_CONFIG = {
    BASE_URL: 'http://192.168.43.166:5000',  // Your AI server IP
    TIMEOUT: 15000,
    MAX_RETRIES: 1,
};
```

### Test Integration
1. Start AI server: `python AIEnhanced_Fixed.py server`
2. Run mobile app: `cd WarTechUIRevision1 && npm start`
3. Test chat functionality in the app

## 🔧 Features Available

### With OpenRouter API Key Only:
- ✅ Business analysis from WarungTech API
- ✅ Financial summary and recommendations  
- ✅ Investment portfolio analysis
- ✅ Real-time crypto market data
- ✅ AI-powered business insights
- ❌ Blockchain coupon features (disabled)

### With Both API Keys:
- ✅ All above features
- ✅ Smart contract coupon statistics
- ✅ Blockchain promo management
- ✅ Web3 wallet integration

## 🧪 Testing

### Test Business Analysis
```python
from AIEnhanced_Fixed import run_agent

# Test with JWT token from mobile app
result = run_agent(
    query="Analisis kondisi bisnis saya",
    user_token="eyJhbGc...",  # Real JWT token
    wallet_address="0x742d35Cc..."  # Optional
)

print(result)
```

### Test API Endpoint
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Bagaimana performa investasi crypto saya?",
    "user_token": "eyJhbGc...",
    "wallet_address": "0x742d35Cc..."
  }'
```

## 🔍 Troubleshooting

### Common Issues

#### 1. "OPENROUTER_API_KEY not found"
- Check `.env` file exists in `WarungTechAI/` directory
- Verify key format starts with `sk-or-v1-`
- Ensure no extra spaces or quotes

#### 2. "Web3 initialization failed"
- This is normal if INFURA_PROJECT_ID is not set
- Blockchain features will be disabled
- Business analysis still works

#### 3. "Cannot connect to WarungTech API"
- Check internet connection
- Verify WarungTech backend is running
- Check JWT token is valid

#### 4. Import errors
- Run `pip install -r requirements.txt`
- Check Python version (3.8+ recommended)

### Debug Mode
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with debug
result = run_agent("test query", debug=True)
```

## 📊 Usage Examples

### 1. Business Analysis
```python
run_agent(
    query="Berapa revenue bulan ini dan bagaimana trendnya?",
    user_token="your_jwt_token"
)
```

### 2. Investment Recommendations
```python
run_agent(
    query="Analisis portfolio crypto saya dan berikan rekomendasi diversifikasi",
    user_token="your_jwt_token"
)
```

### 3. Blockchain Coupons (if Web3 enabled)
```python
run_agent(
    query="Berapa kupon blockchain yang sudah saya buat?",
    user_token="your_jwt_token",
    wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
)
```

### 4. Comprehensive Analysis
```python
run_agent(
    query="""Tolong analisis lengkap:
    1. Kondisi bisnis dan revenue
    2. Performa investasi
    3. Rekomendasi strategi 3 bulan ke depan
    """,
    user_token="your_jwt_token",
    wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
)
```

## 🔒 Security Best Practices

1. **Never commit `.env` file** - Already in `.gitignore`
2. **Rotate API keys periodically**
3. **Monitor usage** on OpenRouter/Infura dashboards
4. **Use HTTPS** in production
5. **Validate JWT tokens** before processing

## 📈 Monitoring & Analytics

### Check API Usage
- OpenRouter: [https://openrouter.ai/activity](https://openrouter.ai/activity)
- Infura: [https://infura.io/dashboard](https://infura.io/dashboard)

### Performance Metrics
- Response time: ~2-5 seconds typical
- Token usage: ~1000-3000 tokens per request
- Success rate: Monitor via health endpoint

## 🚀 Production Deployment

### Environment Variables for Production
```env
OPENROUTER_API_KEY=sk-or-v1-production-key
INFURA_PROJECT_ID=production-project-id
FLASK_ENV=production
FLASK_DEBUG=False
```

### Docker Deployment (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "AIEnhanced_Fixed.py", "server"]
```

## 📞 Support

### Getting Help
1. Check this setup guide
2. Review error messages carefully
3. Test with minimal examples
4. Check API provider status pages

### Common Solutions
- **API errors**: Check keys and quotas
- **Connection issues**: Verify network and URLs
- **Import errors**: Reinstall dependencies
- **Token errors**: Get fresh JWT from mobile app

---

## ✅ Quick Start Checklist

- [ ] Install Python dependencies (`pip install -r requirements.txt`)
- [ ] Get OpenRouter API key from [openrouter.ai](https://openrouter.ai/keys)
- [ ] Create `.env` file with your API key
- [ ] Test basic functionality (`python AIEnhanced_Fixed.py`)
- [ ] Start API server (`python AIEnhanced_Fixed.py server`)
- [ ] Test health endpoint (`curl http://localhost:5000/health`)
- [ ] Update mobile app AI service URL
- [ ] Test end-to-end integration

**Your WarungTech AI Assistant is ready! 🎉**