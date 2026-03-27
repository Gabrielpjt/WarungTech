# 🚀 WarungTech AI - Quick Start Guide

## ✅ Configuration Complete

Your API keys have been configured:
- ✅ **OpenRouter API Key**: Configured and ready
- ✅ **Infura Project ID**: Configured for blockchain features
- ✅ **WarungTech API**: Connected to production backend

## 🏃‍♂️ Quick Start (3 Steps)

### Step 1: Start AI Server
```bash
cd WarungTechAI
python start_ai_server.py
```

### Step 2: Test Server
Open browser: http://localhost:5000/health

Expected response:
```json
{
  "status": "ok",
  "message": "WarungTech AI Assistant is running",
  "features": {
    "business_analysis": true,
    "market_data": true,
    "blockchain_coupons": true
  }
}
```

### Step 3: Test Mobile Integration
```bash
cd WarTechUIRevision1
npm start
```

## 🧪 Test Chat Functionality

### Via API (curl)
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Halo, tolong analisis bisnis saya",
    "user_token": "eyJhbGc...",
    "wallet_address": "0x742d35Cc..."
  }'
```

### Via Mobile App
1. Open WarungTech mobile app
2. Go to Home tab
3. Use the chat feature
4. Ask: "Analisis kondisi bisnis saya"

## 🔧 Features Available

### ✅ Business Analysis
- Revenue and profit analysis
- Order volume tracking
- Product performance metrics
- Financial health assessment
- Growth recommendations

### ✅ Investment Analysis
- Crypto portfolio analysis
- Diversification scoring
- Risk assessment
- Market data integration
- Rebalancing recommendations

### ✅ Blockchain Coupons
- Smart contract coupon statistics
- Active coupon management
- Utilization rate analysis
- WhatsApp sharing integration

### ✅ Market Data
- Real-time crypto prices
- 24h change tracking
- Market sentiment analysis
- Multi-coin support (BTC, ETH, SOL, BNB, etc.)

## 📱 Mobile App Integration

The mobile app is already configured to connect to your AI server at:
`http://192.168.43.166:5000`

### If Connection Issues:
1. **Check IP Address**: Update in `WarTechUIRevision1/services/aiService.ts`
2. **Check Network**: Ensure both devices on same WiFi
3. **Check Firewall**: Allow port 5000 in Windows Firewall
4. **Try Alternatives**:
   - `http://localhost:5000` (same machine)
   - `http://10.0.2.2:5000` (Android emulator)

## 🎯 Example Queries

### Business Analysis
```
"Bagaimana performa bisnis saya bulan ini?"
"Berapa revenue dan profit margin saya?"
"Produk mana yang paling laris?"
```

### Investment Analysis
```
"Analisis portfolio crypto saya"
"Berikan rekomendasi diversifikasi"
"Bagaimana performa investasi BTC dan ETH?"
```

### Comprehensive Analysis
```
"Tolong analisis lengkap bisnis dan investasi saya"
"Berikan rekomendasi strategi untuk 3 bulan ke depan"
"Bagaimana kondisi keuangan dan cash flow saya?"
```

### Blockchain Coupons
```
"Berapa kupon blockchain yang sudah saya buat?"
"Kupon mana yang masih aktif dan bisa dibagikan?"
"Bagaimana utilisasi kupon promo saya?"
```

## 🔍 Troubleshooting

### Server Won't Start
```bash
# Check configuration
python test_config.py

# Install missing dependencies
pip install requests flask flask-cors

# Try manual start
python AIEnhanced.py server
```

### Mobile App Can't Connect
1. **Check server is running**: `curl http://localhost:5000/health`
2. **Check IP address**: Update in aiService.ts if needed
3. **Check network**: Both devices same WiFi
4. **Check logs**: Look at server console for connection attempts

### API Errors
- **401 Unauthorized**: Check JWT token from mobile app login
- **500 Server Error**: Check server logs for details
- **Timeout**: Increase timeout in aiService.ts

## 📊 Expected Performance

### Response Times
- Simple queries: 2-3 seconds
- Business analysis: 3-5 seconds
- Complex analysis: 5-8 seconds
- Market data: 1-2 seconds

### Token Usage (OpenRouter)
- Basic query: ~1,000 tokens (~$0.001-0.01)
- Complex analysis: ~3,000 tokens (~$0.003-0.03)
- Daily usage: ~$0.10-1.00 typical

## 🎉 Success Indicators

Your AI is working correctly if:

1. ✅ Server starts without errors
2. ✅ Health endpoint returns 200 OK
3. ✅ Mobile app connects successfully
4. ✅ Chat responses are relevant and detailed
5. ✅ Business data is fetched from WarungTech API
6. ✅ Market data is current and accurate

## 🚀 Next Steps

### Immediate
1. Test all features with real data
2. Try different query types
3. Check response quality and accuracy

### Advanced
1. Monitor API usage and costs
2. Add custom business rules
3. Integrate with additional data sources
4. Deploy to cloud for production use

---

## 🆘 Need Help?

### Quick Fixes
- **Restart server**: `Ctrl+C` then `python start_ai_server.py`
- **Clear cache**: Restart mobile app
- **Check logs**: Look at server console output
- **Test config**: `python test_config.py`

### Common Solutions
- **Connection refused**: Check IP address and firewall
- **Invalid token**: Login again in mobile app
- **Slow responses**: Check internet connection
- **Empty responses**: Verify API keys are correct

**Your WarungTech AI Assistant is ready! 🎉**