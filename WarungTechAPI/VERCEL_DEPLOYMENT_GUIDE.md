# 🚀 WarungTech API - Vercel Deployment Guide

## Overview
Complete guide to deploy the WarungTech API to Vercel with all features including store management, payments, investments, and AI integration.

## 📋 Prerequisites

### 1. Vercel Account
- Sign up at [vercel.com](https://vercel.com)
- Install Vercel CLI: `npm i -g vercel`

### 2. Database Setup (Supabase)
- Create account at [supabase.com](https://supabase.com)
- Create new project
- Get connection details from Settings > Database

### 3. Midtrans Account
- Sign up at [midtrans.com](https://midtrans.com)
- Get Server Key and Client Key from dashboard
- Use Sandbox for testing, Production for live

## 🔧 Deployment Steps

### Step 1: Prepare Project Structure
```
WarungTechAPI/
├── src/
│   ├── server.js          # Main server file
│   ├── package.json       # Dependencies
│   ├── vercel.json        # Vercel configuration
│   ├── .env.example       # Environment template
│   └── .env               # Your environment variables (don't commit)
```

### Step 2: Configure Environment Variables

Create `.env` file in `src/` directory:
```bash
# Copy from .env.example and fill with your values
cp .env.example .env
```

Required variables:
```env
# Database (Supabase)
DB_HOST=your-supabase-host
DB_PASSWORD=your-db-password
DB_USER=your-db-user

# JWT Secret (generate strong key)
JWT_SECRET=your-super-secret-jwt-key-min-32-characters

# Midtrans
MIDTRANS_SERVER_KEY=Mid-server-xxxxx
MIDTRANS_CLIENT_KEY=Mid-client-xxxxx

# Production URLs
API_BASE_URL=https://your-app.vercel.app
```

### Step 3: Database Schema Setup

Run these SQL commands in Supabase SQL Editor:

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stores table
CREATE TABLE stores (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    store_name VARCHAR(255) NOT NULL,
    description TEXT,
    address TEXT,
    logo_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(12,2) NOT NULL,
    stock INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
    total_amount DECIMAL(12,2) NOT NULL,
    payment_status VARCHAR(50) DEFAULT 'pending',
    midtrans_order_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items table
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    price DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Wallets table
CREATE TABLE wallets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    balance DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Investments table
CREATE TABLE investments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    wallet_address VARCHAR(255),
    amount DECIMAL(15,2) NOT NULL,
    asset VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    sold_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Financial records table
CREATE TABLE financial_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- income, expense, investment, gain
    amount DECIMAL(15,2) NOT NULL,
    description TEXT,
    reference_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activity logs table
CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    activity_type VARCHAR(100) NOT NULL,
    amount DECIMAL(15,2),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chatbot histories table
CREATE TABLE chatbot_histories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    command VARCHAR(255) NOT NULL,
    input_text TEXT,
    response_text TEXT,
    action_result VARCHAR(50),
    related_entity VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_stores_user_id ON stores(user_id);
CREATE INDEX idx_products_store_id ON products(store_id);
CREATE INDEX idx_orders_store_id ON orders(store_id);
CREATE INDEX idx_orders_midtrans_id ON orders(midtrans_order_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_wallets_user_id ON wallets(user_id);
CREATE INDEX idx_investments_user_id ON investments(user_id);
CREATE INDEX idx_financial_records_user_id ON financial_records(user_id);
CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX idx_chatbot_histories_user_id ON chatbot_histories(user_id);
```

### Step 4: Deploy to Vercel

#### Option A: Using Vercel CLI
```bash
# Navigate to src directory
cd WarungTechAPI/src

# Login to Vercel
vercel login

# Deploy
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name: warungtech-api
# - Directory: ./
# - Override settings? No
```

#### Option B: Using Vercel Dashboard
1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import from Git repository
4. Select `WarungTechAPI/src` as root directory
5. Configure environment variables
6. Deploy

### Step 5: Configure Environment Variables in Vercel

In Vercel Dashboard > Project > Settings > Environment Variables:

```
DB_HOST = aws-1-ap-northeast-1.pooler.supabase.com
DB_PORT = 5432
DB_NAME = postgres
DB_USER = postgres.nzvkyxpgsegkpewhyqlc
DB_PASSWORD = your-actual-password
JWT_SECRET = your-actual-jwt-secret-min-32-chars
MIDTRANS_SERVER_KEY = Mid-server-your-actual-key
MIDTRANS_CLIENT_KEY = Mid-client-your-actual-key
NODE_ENV = production
```

### Step 6: Update Mobile App Configuration

Update your mobile app's API configuration:

```typescript
// WarTechUIRevision1/config/api.ts
const API_CONFIG = {
    BASE_URL: 'https://your-vercel-app.vercel.app/api',  // Update this
    TIMEOUT: 15000,
    MAX_RETRIES: 3,
};
```

## 🧪 Testing Deployment

### 1. Health Check
```bash
curl https://your-vercel-app.vercel.app/api/health
```

Expected response:
```json
{
  "status": "ok",
  "message": "Store Management API is running",
  "services": {
    "database": "connected",
    "midtrans": "sandbox"
  }
}
```

### 2. Test Authentication
```bash
# Register test user
curl -X POST https://your-vercel-app.vercel.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "password123",
    "phone": "08123456789"
  }'
```

### 3. Test Payment (Old API)
```bash
curl -X POST https://your-vercel-app.vercel.app/api/tokenizer \
  -H "Content-Type: application/json" \
  -d '{
    "orderId": "TEST-001",
    "amount": 25000,
    "customerName": "Test Customer",
    "customerEmail": "test@example.com",
    "items": [
      {
        "id": "1",
        "productName": "Test Product",
        "price": 25000,
        "quantity": 1
      }
    ]
  }'
```

## 📱 Mobile App Integration

Update these files in your mobile app:

### 1. API Configuration
```typescript
// config/api.ts
export const API_CONFIG = {
    BASE_URL: 'https://warungtech-api.vercel.app/api',
    TIMEOUT: 15000,
    MAX_RETRIES: 3,
};
```

### 2. Payment Callbacks
Update callback URLs in payment integration:
```typescript
const callbacks = {
    finish: 'https://warungtech-api.vercel.app/api/payment/finish',
    error: 'https://warungtech-api.vercel.app/api/payment/error',
    pending: 'https://warungtech-api.vercel.app/api/payment/pending'
};
```

## 🔒 Security Considerations

### 1. Environment Variables
- Never commit `.env` files
- Use strong JWT secrets (min 32 characters)
- Rotate secrets regularly

### 2. Database Security
- Enable Row Level Security (RLS) in Supabase
- Use connection pooling
- Regular backups

### 3. API Security
- Rate limiting (consider Vercel Pro for advanced features)
- Input validation
- CORS configuration
- HTTPS only

## 🚀 Production Checklist

- [ ] Database schema created
- [ ] Environment variables configured
- [ ] SSL certificates (automatic with Vercel)
- [ ] Custom domain configured (optional)
- [ ] Monitoring setup
- [ ] Error tracking (Sentry integration)
- [ ] Performance monitoring
- [ ] Backup strategy
- [ ] Rate limiting
- [ ] Security headers

## 📊 Monitoring & Maintenance

### 1. Vercel Analytics
- Enable in Vercel Dashboard
- Monitor function execution times
- Track error rates

### 2. Database Monitoring
- Supabase Dashboard
- Query performance
- Connection limits

### 3. Logs
```bash
# View deployment logs
vercel logs your-deployment-url

# Real-time logs
vercel logs --follow
```

## 🆘 Troubleshooting

### Common Issues:

1. **Database Connection Failed**
   - Check Supabase connection string
   - Verify IP allowlist (Vercel IPs)
   - Check environment variables

2. **Midtrans Integration Issues**
   - Verify server/client keys
   - Check callback URLs
   - Test in sandbox first

3. **CORS Errors**
   - Update CORS configuration
   - Check allowed origins
   - Verify headers

4. **Function Timeout**
   - Optimize database queries
   - Use connection pooling
   - Consider upgrading Vercel plan

### Support Resources:
- [Vercel Documentation](https://vercel.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Midtrans Documentation](https://docs.midtrans.com)

## 🎉 Success!

Your WarungTech API is now deployed and ready for production use with:

✅ Complete store management system
✅ Secure payment processing with Midtrans
✅ User authentication and authorization
✅ Investment and wallet management
✅ AI chatbot integration ready
✅ Scalable serverless architecture
✅ Production-grade security

**API Base URL**: `https://your-vercel-app.vercel.app/api`

Update your mobile app configuration and start using the deployed API!