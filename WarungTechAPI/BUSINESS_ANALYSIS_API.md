# 🏢 Business Analysis & Midtrans Balance API Documentation

## Overview
New API endpoints for comprehensive business condition analysis and Midtrans balance tracking, designed to provide detailed insights for the WarungTech AI chatbot and mobile app dashboard.

## 🔐 Authentication
All endpoints require JWT token in Authorization header:
```
Authorization: Bearer <jwt_token>
```

## 📊 Business Analysis Endpoints

### 1. Get Business Condition Analysis
**Endpoint:** `GET /api/business/analysis`

**Description:** Provides comprehensive business health analysis including performance metrics, financial health, and actionable recommendations.

**Response Example:**
```json
{
  "success": true,
  "data": {
    "business_overview": {
      "condition": "good",
      "condition_score": 75,
      "total_stores": 2,
      "total_products": 15,
      "total_orders": 45,
      "total_revenue": 15750000,
      "avg_order_value": 350000
    },
    "performance_metrics": {
      "order_success_rate": 87.5,
      "recent_orders_30d": 12,
      "recent_revenue_30d": 4200000,
      "revenue_growth_rate": 26.67,
      "paid_orders": 39,
      "pending_orders": 3,
      "failed_orders": 3
    },
    "financial_health": {
      "wallet_balance": 2500000,
      "total_invested": 5000000,
      "active_investments": 3,
      "total_income": 15750000,
      "total_expense": 2100000,
      "total_gains": 750000,
      "net_profit": 13650000
    },
    "top_products": [
      {
        "name": "Nasi Gudeg Special",
        "price": 25000,
        "total_sold": 85,
        "total_revenue": 2125000
      }
    ],
    "recommendations": [
      "Tingkatkan conversion rate dengan optimasi checkout process",
      "Pertahankan cash reserve minimal 10% dari total revenue"
    ],
    "analysis_timestamp": "2026-01-31T05:00:00.000Z"
  }
}
```

**Business Condition Scoring:**
- **Excellent (80-100):** Established business with strong metrics
- **Good (60-79):** Growing business with solid foundation  
- **Fair (40-59):** Developing business with potential
- **Developing (0-39):** Early stage business needing improvement

**Scoring Criteria:**
- Has stores: +20 points
- 5+ products: +20 points  
- 10+ orders: +20 points
- 1M+ revenue: +20 points
- 80%+ success rate: +20 points

### 2. Get Midtrans Balance & Transaction Summary
**Endpoint:** `GET /api/midtrans/balance`

**Description:** Provides detailed Midtrans account summary including processed amounts, fees, and transaction analytics.

**Response Example:**
```json
{
  "success": true,
  "data": {
    "account_summary": {
      "total_processed_amount": 15750000,
      "estimated_midtrans_fees": 456750,
      "estimated_net_amount": 15293250,
      "total_transactions": 45,
      "successful_transactions": 39,
      "pending_transactions": 3,
      "failed_transactions": 3,
      "success_rate_percentage": 86.67
    },
    "financial_metrics": {
      "pending_amount": 1050000,
      "daily_average_revenue": 525000,
      "last_transaction_date": "2026-01-30T14:30:00.000Z",
      "estimated_monthly_fees": 342000
    },
    "recent_transactions": [
      {
        "order_id": "ORD-1738317600-ABC123",
        "amount": 275000,
        "status": "paid",
        "store_name": "Warung Makan Sederhana",
        "created_at": "2026-01-30T14:30:00.000Z"
      }
    ],
    "midtrans_info": {
      "environment": "sandbox",
      "fee_structure": {
        "percentage_fee": "2.9%",
        "fixed_fee": "Rp 2,000",
        "description": "Estimated fees based on Midtrans standard rates"
      }
    },
    "balance_timestamp": "2026-01-31T05:00:00.000Z"
  }
}
```

**Fee Calculation:**
- **Percentage Fee:** 2.9% of transaction amount
- **Fixed Fee:** Rp 2,000 per successful transaction
- **Total Fee:** (Amount × 0.029) + 2,000

### 3. Get Transaction Analytics
**Endpoint:** `GET /api/analytics/transactions`

**Query Parameters:**
- `period` (optional): `7d`, `30d`, `90d`, `1y` (default: `30d`)

**Description:** Provides detailed transaction trends and analytics for specified time period.

**Response Example:**
```json
{
  "success": true,
  "data": {
    "period": "30d",
    "daily_trends": [
      {
        "date": "2026-01-30",
        "total_transactions": 3,
        "daily_revenue": 825000,
        "successful_transactions": 3
      }
    ],
    "payment_methods": [
      {
        "method": "midtrans",
        "transaction_count": 45,
        "total_amount": 15750000
      }
    ],
    "store_performance": [
      {
        "store_name": "Warung Makan Sederhana",
        "total_orders": 28,
        "store_revenue": 9800000,
        "avg_order_value": 350000
      }
    ],
    "analysis_timestamp": "2026-01-31T05:00:00.000Z"
  }
}
```

## 🤖 AI Chatbot Integration

### Business Analysis Usage
```javascript
// Example usage in AI chatbot
const businessAnalysis = await fetch('/api/business/analysis', {
  headers: { 'Authorization': `Bearer ${userToken}` }
});

const data = await businessAnalysis.json();

// Generate AI response based on business condition
if (data.data.business_overview.condition === 'excellent') {
  response = "Bisnis Anda dalam kondisi sangat baik! Revenue mencapai " + 
             formatCurrency(data.data.business_overview.total_revenue);
} else {
  response = "Bisnis Anda berkembang dengan " + 
             data.data.performance_metrics.order_success_rate + "% success rate";
}
```

### Midtrans Balance Usage
```javascript
// Check Midtrans balance for payment insights
const midtransData = await fetch('/api/midtrans/balance', {
  headers: { 'Authorization': `Bearer ${userToken}` }
});

const balance = await midtransData.json();

// AI can provide payment insights
const netAmount = balance.data.account_summary.estimated_net_amount;
const fees = balance.data.account_summary.estimated_midtrans_fees;

response = `Saldo bersih Midtrans: ${formatCurrency(netAmount)}. ` +
           `Total fee: ${formatCurrency(fees)} (${fees/netAmount*100}% dari revenue)`;
```

## 📱 Mobile App Integration

### Dashboard Cards
```typescript
// Business condition card
interface BusinessCondition {
  condition: 'excellent' | 'good' | 'fair' | 'developing';
  score: number;
  revenue: number;
  orders: number;
}

// Midtrans balance card  
interface MidtransBalance {
  totalProcessed: number;
  estimatedFees: number;
  netAmount: number;
  successRate: number;
}
```

### Usage Examples
```typescript
// Fetch business analysis for dashboard
const fetchBusinessAnalysis = async () => {
  const response = await apiService.get('/business/analysis');
  setBusinessData(response.data);
};

// Display business condition
const getConditionColor = (condition: string) => {
  switch(condition) {
    case 'excellent': return '#10B981'; // Green
    case 'good': return '#3B82F6';      // Blue  
    case 'fair': return '#F59E0B';      // Yellow
    default: return '#EF4444';          // Red
  }
};
```

## 🔍 Error Handling

### Common Error Responses
```json
{
  "success": false,
  "message": "Failed to analyze business condition",
  "error": "Database connection error"
}
```

### HTTP Status Codes
- **200:** Success
- **401:** Unauthorized (invalid/missing JWT token)
- **403:** Forbidden (access denied)
- **500:** Internal server error

## 📊 Data Insights

### Business Health Indicators
1. **Revenue Growth:** Month-over-month revenue increase
2. **Order Success Rate:** Percentage of paid vs total orders
3. **Average Order Value:** Revenue per successful transaction
4. **Product Diversity:** Number of active products
5. **Cash Flow:** Wallet balance vs expenses ratio

### Midtrans Metrics
1. **Processing Volume:** Total amount processed through Midtrans
2. **Fee Efficiency:** Fee percentage vs industry standards
3. **Transaction Success:** Payment completion rates
4. **Settlement Speed:** Time from payment to settlement
5. **Revenue Impact:** Net amount after fees

## 🚀 Performance Optimization

### Caching Strategy
- Business analysis: Cache for 1 hour
- Midtrans balance: Cache for 30 minutes  
- Transaction analytics: Cache for 15 minutes

### Database Optimization
- Indexed queries on user_id and created_at
- Aggregated calculations for better performance
- Pagination for large datasets

## 🔒 Security Considerations

### Data Privacy
- User data isolated by JWT token validation
- No sensitive Midtrans credentials exposed
- Estimated fees only (not actual account access)

### Rate Limiting
- 100 requests per hour per user for analysis endpoints
- 500 requests per hour for transaction analytics
- Exponential backoff for failed requests

## 📈 Future Enhancements

### Planned Features
1. **Real-time Midtrans API Integration:** Direct balance checking
2. **Predictive Analytics:** Revenue forecasting
3. **Competitor Benchmarking:** Industry comparison
4. **Automated Alerts:** Performance threshold notifications
5. **Export Capabilities:** PDF/Excel report generation

### AI Integration Roadmap
1. **Smart Recommendations:** ML-based business advice
2. **Anomaly Detection:** Unusual transaction patterns
3. **Customer Segmentation:** Revenue source analysis
4. **Seasonal Trends:** Time-based performance insights
5. **Risk Assessment:** Business stability scoring

---

## 🎯 Summary

These new endpoints provide comprehensive business intelligence for the WarungTech ecosystem:

- **Business Analysis:** Complete health assessment with actionable insights
- **Midtrans Integration:** Payment processing analytics and fee tracking  
- **Transaction Analytics:** Detailed performance trends and comparisons

Perfect for AI chatbot responses and mobile app dashboard displays! 🚀