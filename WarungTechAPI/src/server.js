// server.js - Complete Backend with All Features
require('dotenv').config({ path: require('path').join(__dirname, '../.env') });
const express = require('express');
const cors = require('cors');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const midtransClient = require('midtrans-client');
const { Pool } = require('pg');

const app = express();
const PORT = process.env.PORT || 3001;
const JWT_SECRET = process.env.JWT_SECRET || 'warungtech-secret-key-change-in-production';
const LOCAL_IP = process.env.LOCAL_IP || '192.168.100.15';

// ============================================
// ACTIVITY TYPE CONSTANTS
// ============================================
const ACTIVITY_TYPES = {
  PAYMENT: 'payment',
  TOPUP: 'topup',
  WITHDRAW: 'withdraw',
  INVEST_BUY: 'invest_buy',
  INVEST_SELL: 'invest_sell',
  TRANSACTION: 'transaction'
};

// ============================================
// DATABASE CONNECTION (Fixed: removed invalid pool_mode)
// ============================================
const pool = new Pool({
  host: process.env.DB_HOST || 'aws-1-ap-northeast-1.pooler.supabase.com',
  port: parseInt(process.env.DB_PORT) || 5432,
  database: process.env.DB_NAME || 'postgres',
  user: process.env.DB_USER || 'postgres.nzvkyxpgsegkpewhyqlc',
  password: process.env.DB_PASSWORD || 'PantangMenyerah123!',
  ssl: { rejectUnauthorized: false },
  connectionTimeoutMillis: 10000,
  idleTimeoutMillis: 30000,
  max: 10,
});

pool.on('connect', () => console.log('✅ Connected to PostgreSQL database'));
pool.on('error', (err) => console.error('❌ Database pool error:', err.message));

// ============================================
// HELPER FUNCTIONS
// ============================================
const logActivity = async (client, userId, activityType, amount, description) => {
  try {
    await client.query(
      `INSERT INTO activity_logs (user_id, activity_type, amount, description) VALUES ($1, $2, $3, $4)`,
      [userId, activityType, amount, description]
    );
  } catch (error) {
    console.error('Failed to log activity:', error.message);
  }
};

const updateWalletBalance = async (client, userId, amount, description) => {
  try {
    const result = await client.query(
      `INSERT INTO wallets (user_id, balance) VALUES ($1, $2)
       ON CONFLICT (user_id) DO UPDATE SET balance = wallets.balance + $2, updated_at = CURRENT_TIMESTAMP
       RETURNING balance`,
      [userId, amount]
    );
    console.log(`✅ Wallet updated for user ${userId}, new balance: ${result.rows[0].balance}`);
    return result.rows[0].balance;
  } catch (error) {
    // Fallback to UPDATE then INSERT
    const updateResult = await client.query(
      `UPDATE wallets SET balance = balance + $1 WHERE user_id = $2 RETURNING balance`,
      [amount, userId]
    );
    if (updateResult.rows.length === 0) {
      const insertResult = await client.query(
        `INSERT INTO wallets (user_id, balance) VALUES ($1, $2) RETURNING balance`,
        [userId, amount]
      );
      return insertResult.rows[0].balance;
    }
    return updateResult.rows[0].balance;
  }
};

// ============================================
// MIDDLEWARE
// ============================================
app.use(cors({ origin: '*', credentials: true }));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
  next();
});

// ============================================
// MIDTRANS CONFIGURATION
// ============================================
const snap = new midtransClient.Snap({
  isProduction: process.env.MIDTRANS_IS_PRODUCTION === 'true',
  serverKey: process.env.MIDTRANS_SERVER_KEY,
  clientKey: process.env.MIDTRANS_CLIENT_KEY
});
console.log(`✅ Midtrans configured in ${snap.isProduction ? 'PRODUCTION' : 'SANDBOX'} mode`);

const transactionStore = new Map();

// ============================================
// AUTH MIDDLEWARE
// ============================================
const authenticateToken = (req, res, next) => {
  const token = req.headers['authorization']?.split(' ')[1];
  if (!token) return res.status(401).json({ success: false, message: 'Access token required' });
  jwt.verify(token, JWT_SECRET, (err, user) => {
    if (err) return res.status(403).json({ success: false, message: 'Invalid or expired token' });
    req.user = user;
    next();
  });
};

// ============================================
// 1. AUTH ENDPOINTS
// ============================================
app.post('/api/auth/register', async (req, res) => {
  const client = await pool.connect();
  try {
    const { name, email, password, phone } = req.body;
    if (!name || !email || !password)
      return res.status(400).json({ success: false, message: 'Name, email, and password are required' });

    const existing = await client.query('SELECT id FROM users WHERE email = $1', [email]);
    if (existing.rows.length > 0)
      return res.status(409).json({ success: false, message: 'Email already registered' });

    const passwordHash = await bcrypt.hash(password, 10);
    await client.query('BEGIN');
    const userResult = await client.query(
      `INSERT INTO users (name, email, password_hash, phone) VALUES ($1, $2, $3, $4) RETURNING id, name, email, phone, created_at`,
      [name, email, passwordHash, phone]
    );
    const newUser = userResult.rows[0];
    await client.query('INSERT INTO wallets (user_id, balance) VALUES ($1, 0) ON CONFLICT (user_id) DO NOTHING', [newUser.id]);
    await client.query('COMMIT');

    const token = jwt.sign({ userId: newUser.id, email: newUser.email }, JWT_SECRET, { expiresIn: '7d' });
    res.status(201).json({ success: true, message: 'User registered successfully', data: { user: newUser, token } });
  } catch (error) {
    await client.query('ROLLBACK');
    console.error('Register error:', error.message);
    res.status(500).json({ success: false, message: 'Registration failed', error: error.message });
  } finally {
    client.release();
  }
});

app.post('/api/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    if (!email || !password)
      return res.status(400).json({ success: false, message: 'Email and password are required' });

    const result = await pool.query('SELECT id, name, email, password_hash, phone FROM users WHERE email = $1', [email]);
    if (result.rows.length === 0)
      return res.status(401).json({ success: false, message: 'Invalid email or password' });

    const user = result.rows[0];
    const validPassword = await bcrypt.compare(password, user.password_hash);
    if (!validPassword)
      return res.status(401).json({ success: false, message: 'Invalid email or password' });

    const token = jwt.sign({ userId: user.id, email: user.email }, JWT_SECRET, { expiresIn: '7d' });
    res.json({ success: true, message: 'Login successful', data: { user: { id: user.id, name: user.name, email: user.email, phone: user.phone }, token } });
  } catch (error) {
    console.error('Login error:', error.message);
    res.status(500).json({ success: false, message: 'Login failed', error: error.message });
  }
});

app.get('/api/auth/profile', authenticateToken, async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT u.id, u.name, u.email, u.phone, u.created_at, COALESCE(w.balance, 0) as wallet_balance
       FROM users u LEFT JOIN wallets w ON u.id = w.user_id WHERE u.id = $1`,
      [req.user.userId]
    );
    if (result.rows.length === 0)
      return res.status(404).json({ success: false, message: 'User not found' });
    res.json({ success: true, data: result.rows[0] });
  } catch (error) {
    console.error('Get profile error:', error.message);
    res.status(500).json({ success: false, message: 'Failed to get profile', error: error.message });
  }
});

// ============================================
// 2. STORE ENDPOINTS
// ============================================
app.post('/api/stores', authenticateToken, async (req, res) => {
  try {
    const { store_name, description, address, logo_url } = req.body;
    if (!store_name) return res.status(400).json({ success: false, message: 'Store name is required' });
    const result = await pool.query(
      `INSERT INTO stores (user_id, store_name, description, address, logo_url) VALUES ($1, $2, $3, $4, $5) RETURNING *`,
      [req.user.userId, store_name, description, address, logo_url]
    );
    res.status(201).json({ success: true, message: 'Store created successfully', data: result.rows[0] });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Failed to create store', error: error.message });
  }
});

app.get('/api/stores', authenticateToken, async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM stores WHERE user_id = $1 ORDER BY created_at DESC', [req.user.userId]);
    res.json({ success: true, data: result.rows });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Failed to get stores', error: error.message });
  }
});

app.get('/api/stores/:id', authenticateToken, async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM stores WHERE id = $1 AND user_id = $2', [req.params.id, req.user.userId]);
    if (result.rows.length === 0) return res.status(404).json({ success: false, message: 'Store not found' });
    res.json({ success: true, data: result.rows[0] });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Failed to get store', error: error.message });
  }
});

app.put('/api/stores/:id', authenticateToken, async (req, res) => {
  try {
    const { store_name, description, address, logo_url } = req.body;
    const result = await pool.query(
      `UPDATE stores SET store_name = COALESCE($1, store_name), description = COALESCE($2, description),
       address = COALESCE($3, address), logo_url = COALESCE($4, logo_url), updated_at = CURRENT_TIMESTAMP
       WHERE id = $5 AND user_id = $6 RETURNING *`,
      [store_name, description, address, logo_url, req.params.id, req.user.userId]
    );
    if (result.rows.length === 0) return res.status(404).json({ success: false, message: 'Store not found' });
    res.json({ success: true, message: 'Store updated successfully', data: result.rows[0] });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Failed to update store', error: error.message });
  }
});

app.delete('/api/stores/:id', authenticateToken, async (req, res) => {
  try {
    const result = await pool.query('DELETE FROM stores WHERE id = $1 AND user_id = $2 RETURNING id', [req.params.id, req.user.userId]);
    if (result.rows.length === 0) return res.status(404).json({ success: false, message: 'Store not found' });
    res.json({ success: true, message: 'Store deleted successfully' });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Failed to delete store', error: error.message });
  }
});

// ============================================
// 3. PRODUCT ENDPOINTS
// ============================================
app.post('/api/products', authenticateToken, async (req, res) => {
  try {
    const { store_id, name, description, price, stock, is_active, image_url } = req.body;
    if (!store_id || !name || !price)
      return res.status(400).json({ success: false, message: 'Store ID, name, and price are required' });

    // Guard: reject oversized base64 image_url (>2MB string = ~1.5MB image)
    if (image_url && image_url.startsWith('data:') && image_url.length > 2_000_000) {
      return res.status(413).json({ success: false, message: 'Image too large. Please use a smaller image.' });
    }

    const storeCheck = await pool.query('SELECT id FROM stores WHERE id = $1 AND user_id = $2', [store_id, req.user.userId]);
    if (storeCheck.rows.length === 0) return res.status(403).json({ success: false, message: 'Store not found or access denied' });
    const result = await pool.query(
      `INSERT INTO products (store_id, name, description, price, stock, is_active, image_url) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *`,
      [store_id, name, description, price, stock || 0, is_active !== false, image_url ?? null]
    );
    res.status(201).json({ success: true, message: 'Product created successfully', data: result.rows[0] });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Failed to create product', error: error.message });
  }
});

app.get('/api/stores/:storeId/products', authenticateToken, async (req, res) => {
  try {
    const storeCheck = await pool.query('SELECT id FROM stores WHERE id = $1 AND user_id = $2', [req.params.storeId, req.user.userId]);
    if (storeCheck.rows.length === 0) return res.status(403).json({ success: false, message: 'Store not found or access denied' });
    const result = await pool.query('SELECT * FROM products WHERE store_id = $1 ORDER BY created_at DESC', [req.params.storeId]);
    res.json({ success: true, data: result.rows });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Failed to get products', error: error.message });
  }
});

app.put('/api/products/:id', authenticateToken, async (req, res) => {
  try {
    const { name, description, price, stock, is_active, image_url } = req.body;

    // Guard: reject oversized base64 image_url
    if (image_url && image_url.startsWith('data:') && image_url.length > 2_000_000) {
      return res.status(413).json({ success: false, message: 'Image too large. Please use a smaller image.' });
    }

    const ownerCheck = await pool.query(
      `SELECT p.id FROM products p JOIN stores s ON p.store_id = s.id WHERE p.id = $1 AND s.user_id = $2`,
      [req.params.id, req.user.userId]
    );
    if (ownerCheck.rows.length === 0) return res.status(403).json({ success: false, message: 'Product not found or access denied' });

    // Build dynamic update to allow explicit null for image_url
    const fields = [];
    const values = [];
    let idx = 1;
    if (name !== undefined) { fields.push(`name = $${idx++}`); values.push(name); }
    if (description !== undefined) { fields.push(`description = $${idx++}`); values.push(description); }
    if (price !== undefined) { fields.push(`price = $${idx++}`); values.push(price); }
    if (stock !== undefined) { fields.push(`stock = $${idx++}`); values.push(stock); }
    if (is_active !== undefined) { fields.push(`is_active = $${idx++}`); values.push(is_active); }
    if ('image_url' in req.body) { fields.push(`image_url = $${idx++}`); values.push(image_url); }
    fields.push(`updated_at = CURRENT_TIMESTAMP`);
    values.push(req.params.id);

    const result = await pool.query(
      `UPDATE products SET ${fields.join(', ')} WHERE id = $${idx} RETURNING *`,
      values
    );
    res.json({ success: true, message: 'Product updated successfully', data: result.rows[0] });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Failed to update product', error: error.message });
  }
});

app.delete('/api/products/:id', authenticateToken, async (req, res) => {
  try {
    const ownerCheck = await pool.query(
      `SELECT p.id FROM products p JOIN stores s ON p.store_id = s.id WHERE p.id = $1 AND s.user_id = $2`,
      [req.params.id, req.user.userId]
    );
    if (ownerCheck.rows.length === 0) return res.status(403).json({ success: false, message: 'Product not found or access denied' });
    await pool.query('DELETE FROM products WHERE id = $1', [req.params.id]);
    res.json({ success: true, message: 'Product deleted successfully' });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Failed to delete product', error: error.message });
  }
});

// AI image edit/generation for product images using Gemini
app.post('/api/products/ai-image-edit', authenticateToken, async (req, res) => {
  try {
    const { image, prompt } = req.body;
    if (!prompt) return res.status(400).json({ success: false, message: 'Prompt is required' });

    const geminiApiKey = process.env.GEMINI_API_KEY;
    if (!geminiApiKey) return res.status(500).json({ success: false, message: 'GEMINI_API_KEY not configured on server' });

    let requestBody;

    if (image) {
      // Image editing: send image as inline_data base64 with the prompt
      const base64Data = image.replace(/^data:image\/\w+;base64,/, '');
      const mimeMatch = image.match(/^data:(image\/\w+);base64,/);
      const mimeType = mimeMatch ? mimeMatch[1] : 'image/jpeg';

      requestBody = {
        contents: [{
          role: 'user',
          parts: [
            { text: prompt },
            { inline_data: { mime_type: mimeType, data: base64Data } }
          ]
        }],
        generationConfig: {
          temperature: 1,
          topP: 0.95,
          topK: 40,
          maxOutputTokens: 8192,
          responseModalities: ['IMAGE', 'TEXT']
        }
      };
    } else {
      // Text-to-image generation
      requestBody = {
        contents: [{
          role: 'user',
          parts: [{ text: prompt }]
        }],
        generationConfig: {
          responseModalities: ['IMAGE', 'TEXT']
        }
      };
    }

    const geminiResponse = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key=${geminiApiKey}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      }
    );

    const geminiData = await geminiResponse.json();

    if (!geminiResponse.ok) {
      console.error('Gemini error:', JSON.stringify(geminiData));
      return res.status(502).json({ success: false, message: geminiData.error?.message || 'Gemini request failed' });
    }

    // Extract image from response parts
    const parts = geminiData.candidates?.[0]?.content?.parts || [];
    const imagePart = parts.find(p => p.inlineData?.data);

    if (!imagePart) {
      console.error('Gemini no image in response:', JSON.stringify(geminiData).substring(0, 500));
      return res.status(502).json({ success: false, message: 'No image returned from Gemini' });
    }

    const b64 = imagePart.inlineData.data;
    const outMime = imagePart.inlineData.mimeType || 'image/png';
    res.json({ success: true, data: { image_url: `data:${outMime};base64,${b64}` } });
  } catch (error) {
    console.error('AI image edit error:', error.message);
    res.status(500).json({ success: false, message: 'Failed to process AI image edit', error: error.message });
  }
});

// ============================================
// 4. MIDTRANS PAYMENT ENDPOINTS
// ============================================
const buildCallbackUrls = (orderId) => ({
  finish: `http://${LOCAL_IP}:${PORT}/api/payment/finish?order_id=${orderId}`,
  error: `http://${LOCAL_IP}:${PORT}/api/payment/error?order_id=${orderId}`,
  pending: `http://${LOCAL_IP}:${PORT}/api/payment/pending?order_id=${orderId}`
});

// Old endpoint - backward compatibility
app.post('/api/tokenizer', async (req, res) => {
  try {
    const { orderId, amount, customerName, customerEmail, customerPhone, items, discount } = req.body;
    if (!orderId || !amount || !customerName || !customerEmail || !items?.length)
      return res.status(400).json({ error: 'Missing required fields' });

    const itemDetails = items.map(item => ({ id: item.id, price: item.price, quantity: item.quantity, name: item.productName }));
    if (discount > 0) itemDetails.push({ id: 'DISCOUNT', price: -discount, quantity: 1, name: 'Diskon Kupon' });

    const transaction = await snap.createTransaction({
      transaction_details: { order_id: orderId, gross_amount: amount },
      credit_card: { secure: true },
      customer_details: { first_name: customerName, email: customerEmail, phone: customerPhone },
      item_details: itemDetails,
      callbacks: buildCallbackUrls(orderId)
    });

    transactionStore.set(orderId, { amount, customerName, createdAt: new Date(), status: 'pending' });
    res.json({ success: true, token: transaction.token, redirect_url: transaction.redirect_url, order_id: orderId });
  } catch (error) {
    console.error('Tokenizer error:', error.message);
    res.status(500).json({ success: false, error: 'Failed to create transaction', message: error.message });
  }
});

// Old endpoint - backward compatibility
app.post('/api/transaction/create', async (req, res) => {
  try {
    const { orderId, amount, customerName, customerEmail, customerPhone, items, discount = 0 } = req.body;
    if (!orderId || !amount || !customerName || !customerEmail || !items?.length)
      return res.status(400).json({ success: false, message: 'Invalid transaction data' });

    const itemDetails = items.map(item => ({ id: item.id, name: item.productName, price: item.price, quantity: item.quantity }));
    if (discount > 0) itemDetails.push({ id: 'DISCOUNT', name: 'Diskon', price: -discount, quantity: 1 });

    const transaction = await snap.createTransaction({
      transaction_details: { order_id: orderId, gross_amount: amount },
      customer_details: { first_name: customerName, email: customerEmail, phone: customerPhone },
      item_details: itemDetails,
      credit_card: { secure: true },
      callbacks: buildCallbackUrls(orderId)
    });

    transactionStore.set(orderId, { amount, customerName, createdAt: new Date(), status: 'pending' });
    res.status(201).json({ success: true, message: 'Transaction created', data: { orderId, snapToken: transaction.token, redirectUrl: transaction.redirect_url } });
  } catch (error) {
    console.error('Create transaction error:', error.message);
    res.status(500).json({ success: false, message: 'Failed to create transaction', error: error.message });
  }
});

// New order endpoint with database
app.post('/api/orders/create', authenticateToken, async (req, res) => {
  const client = await pool.connect();
  try {
    const { store_id, items, customer_name, customer_email, customer_phone, discount = 0 } = req.body;
    if (!store_id || !items?.length)
      return res.status(400).json({ success: false, message: 'Store ID and items are required' });

    const storeCheck = await client.query('SELECT id FROM stores WHERE id = $1 AND user_id = $2', [store_id, req.user.userId]);
    if (storeCheck.rows.length === 0) return res.status(403).json({ success: false, message: 'Store not found or access denied' });

    await client.query('BEGIN');
    let totalAmount = 0;
    const orderItems = [];

    for (const item of items) {
      const productResult = await client.query('SELECT id, name, price, stock FROM products WHERE id = $1 AND store_id = $2', [item.product_id, store_id]);
      if (productResult.rows.length === 0) throw new Error(`Product ${item.product_id} not found`);
      const product = productResult.rows[0];
      if (product.stock < item.quantity) throw new Error(`Insufficient stock for ${product.name}`);
      totalAmount += product.price * item.quantity;
      orderItems.push({ product_id: product.id, quantity: item.quantity, price: product.price, productName: product.name });
      await client.query('UPDATE products SET stock = stock - $1 WHERE id = $2', [item.quantity, product.id]);
    }

    totalAmount -= discount;
    const orderId = `ORD-${Date.now()}-${Math.random().toString(36).substr(2, 9).toUpperCase()}`;
    const orderResult = await client.query(
      `INSERT INTO orders (store_id, total_amount, payment_status, midtrans_order_id) VALUES ($1, $2, 'pending', $3) RETURNING *`,
      [store_id, totalAmount, orderId]
    );
    const order = orderResult.rows[0];

    for (const item of orderItems) {
      await client.query('INSERT INTO order_items (order_id, product_id, quantity, price) VALUES ($1, $2, $3, $4)', [order.id, item.product_id, item.quantity, item.price]);
    }

    const itemDetails = orderItems.map(i => ({ id: i.product_id, price: i.price, quantity: i.quantity, name: i.productName }));
    if (discount > 0) itemDetails.push({ id: 'DISCOUNT', price: -discount, quantity: 1, name: 'Discount' });

    const transaction = await snap.createTransaction({
      transaction_details: { order_id: orderId, gross_amount: totalAmount },
      credit_card: { secure: true },
      customer_details: { first_name: customer_name || 'Customer', email: customer_email || 'customer@example.com', phone: customer_phone || '08123456789' },
      item_details: itemDetails,
      callbacks: buildCallbackUrls(orderId)
    });

    await client.query('COMMIT');
    res.status(201).json({ success: true, message: 'Order created successfully', data: { order_id: order.id, midtrans_order_id: orderId, total_amount: totalAmount, snap_token: transaction.token, redirect_url: transaction.redirect_url } });
  } catch (error) {
    await client.query('ROLLBACK');
    console.error('Create order error:', error.message);
    res.status(500).json({ success: false, message: 'Failed to create order', error: error.message });
  } finally {
    client.release();
  }
});

app.get('/api/stores/:storeId/orders', authenticateToken, async (req, res) => {
  try {
    const storeCheck = await pool.query('SELECT id FROM stores WHERE id = $1 AND user_id = $2', [req.params.storeId, req.user.userId]);
    if (storeCheck.rows.length === 0) return res.status(403).json({ success: false, message: 'Store not found or access denied' });
    const result = await pool.query(
      `SELECT o.*, COUNT(oi.id) as total_items FROM orders o LEFT JOIN order_items oi ON o.id = oi.order_id WHERE o.store_id = $1 GROUP BY o.id ORDER BY o.created_at DESC`,
      [req.params.storeId]
    );
    res.json({ success: true, data: result.rows });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Failed to get orders', error: error.message });
  }
});

// ============================================
// 5. PAYMENT CALLBACKS
// ============================================
const paymentSuccessHtml = (orderId) => `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Payment Success</title>
<style>body{font-family:sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:linear-gradient(135deg,#667eea,#764ba2)}.container{background:white;padding:40px;border-radius:20px;text-align:center;max-width:400px}h1{color:#10B981}.order-id{background:#F3F4F6;padding:10px;border-radius:8px;font-family:monospace;margin:20px 0}</style></head>
<body><div class="container"><h1>✅ Pembayaran Berhasil!</h1><p>Terima kasih atas pembayaran Anda</p>${orderId ? `<div class="order-id">Order ID: ${orderId}</div>` : ''}<p>Mengarahkan kembali ke aplikasi...</p></div>
<script>setTimeout(()=>{if(window.ReactNativeWebView){window.ReactNativeWebView.postMessage(JSON.stringify({type:'payment_complete',status:'settlement',orderId:'${orderId}'}));}},1500);</script></body></html>`;

const paymentErrorHtml = (orderId) => `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Payment Error</title>
<style>body{font-family:sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:linear-gradient(135deg,#f093fb,#f5576c)}.container{background:white;padding:40px;border-radius:20px;text-align:center;max-width:400px}h1{color:#EF4444}</style></head>
<body><div class="container"><h1>❌ Pembayaran Gagal</h1><p>Terjadi kesalahan saat memproses pembayaran</p>${orderId ? `<p>Order ID: ${orderId}</p>` : ''}</div>
<script>setTimeout(()=>{if(window.ReactNativeWebView){window.ReactNativeWebView.postMessage(JSON.stringify({type:'payment_complete',status:'error',orderId:'${orderId}'}));}},1500);</script></body></html>`;

const paymentPendingHtml = (orderId) => `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Payment Pending</title>
<style>body{font-family:sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:linear-gradient(135deg,#f6d365,#fda085)}.container{background:white;padding:40px;border-radius:20px;text-align:center;max-width:400px}h1{color:#F59E0B}</style></head>
<body><div class="container"><h1>⏳ Pembayaran Tertunda</h1><p>Pembayaran Anda sedang diproses</p>${orderId ? `<p>Order ID: ${orderId}</p>` : ''}</div>
<script>setTimeout(()=>{if(window.ReactNativeWebView){window.ReactNativeWebView.postMessage(JSON.stringify({type:'payment_complete',status:'pending',orderId:'${orderId}'}));}},1500);</script></body></html>`;

app.get('/api/payment/finish', async (req, res) => {
  const { order_id } = req.query;
  console.log('🎉 Payment FINISH callback:', order_id);
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    await client.query(`UPDATE orders SET payment_status = 'paid' WHERE midtrans_order_id = $1`, [order_id]);
    const orderResult = await client.query(
      `SELECT o.id, o.total_amount, s.user_id, s.store_name FROM orders o JOIN stores s ON o.store_id = s.id WHERE o.midtrans_order_id = $1`,
      [order_id]
    );
    if (orderResult.rows.length > 0) {
      const order = orderResult.rows[0];
      await updateWalletBalance(client, order.user_id, order.total_amount, `Payment for order ${order_id}`);
      await client.query(`INSERT INTO financial_records (user_id, type, amount, description, reference_id) VALUES ($1, 'income', $2, $3, $4)`,
        [order.user_id, order.total_amount, `Payment received for order ${order_id}`, order.id]);
      await logActivity(client, order.user_id, ACTIVITY_TYPES.PAYMENT, order.total_amount, `Payment received for order ${order_id}`);
    }
    if (transactionStore.has(order_id)) transactionStore.get(order_id).status = 'success';
    await client.query('COMMIT');
    console.log(`✅ Payment finish processed for ${order_id}`);
  } catch (error) {
    await client.query('ROLLBACK');
    console.error('❌ Payment finish error:', error.message);
  } finally {
    client.release();
  }
  res.send(paymentSuccessHtml(order_id));
});

app.get('/api/payment/error', async (req, res) => {
  const { order_id } = req.query;
  console.log('❌ Payment ERROR callback:', order_id);
  try {
    await pool.query(`UPDATE orders SET payment_status = 'failed' WHERE midtrans_order_id = $1`, [order_id]);
    if (transactionStore.has(order_id)) transactionStore.get(order_id).status = 'error';
  } catch (error) {
    console.error('Error updating payment status:', error.message);
  }
  res.send(paymentErrorHtml(order_id));
});

app.get('/api/payment/pending', (req, res) => {
  const { order_id } = req.query;
  console.log('⏳ Payment PENDING callback:', order_id);
  if (transactionStore.has(order_id)) transactionStore.get(order_id).status = 'pending';
  res.send(paymentPendingHtml(order_id));
});

app.post('/api/notification', async (req, res) => {
  const client = await pool.connect();
  try {
    const statusResponse = await snap.transaction.notification(req.body);
    const { order_id, transaction_status, fraud_status } = statusResponse;
    console.log(`📬 Notification: ${order_id} - ${transaction_status}`);

    await client.query('BEGIN');
    let paymentStatus = 'pending';
    if (transaction_status === 'capture' || transaction_status === 'settlement') paymentStatus = 'paid';
    else if (['deny', 'expire', 'cancel'].includes(transaction_status)) paymentStatus = 'failed';

    await client.query('UPDATE orders SET payment_status = $1 WHERE midtrans_order_id = $2', [paymentStatus, order_id]);

    if (paymentStatus === 'paid') {
      const orderResult = await client.query(
        `SELECT o.id, o.total_amount, s.user_id FROM orders o JOIN stores s ON o.store_id = s.id WHERE o.midtrans_order_id = $1`,
        [order_id]
      );
      if (orderResult.rows.length > 0) {
        const order = orderResult.rows[0];
        await updateWalletBalance(client, order.user_id, order.total_amount, `Payment settled for order ${order_id}`);
        await logActivity(client, order.user_id, ACTIVITY_TYPES.PAYMENT, order.total_amount, `Payment settled for order ${order_id}`);
      }
    }
    await client.query('COMMIT');
    res.status(200).json({ status: 'ok' });
  } catch (error) {
    await client.query('ROLLBACK');
    console.error('Notification error:', error.message);
    res.status(500).json({ error: 'Failed to process notification' });
  } finally {
    client.release();
  }
});

app.get('/api/transaction/:orderId', async (req, res) => {
  try {
    const statusResponse = await snap.transaction.status(req.params.orderId);
    res.json({ success: true, data: statusResponse });
  } catch (error) {
    res.status(500).json({ success: false, error: 'Failed to check transaction status', message: error.message });
  }
});

// ============================================
// 6. WALLET ENDPOINTS
// ============================================
app.get('/api/wallet', authenticateToken, async (req, res) => {
  try {
    let result = await pool.query('SELECT * FROM wallets WHERE user_id = $1', [req.user.userId]);
    if (result.rows.length === 0) {
      result = await pool.query('INSERT INTO wallets (user_id, balance) VALUES ($1, 0) ON CONFLICT (user_id) DO UPDATE SET balance = wallets.balance RETURNING *', [req.user.userId]);
    }
    res.json({ success: true, data: result.rows[0] });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Failed to get wallet', error: error.message });
  }
});

app.post('/api/wallet/topup', authenticateToken, async (req, res) => {
  const client = await pool.connect();
  try {
    const { amount } = req.body;
    if (!amount || amount <= 0) return res.status(400).json({ success: false, message: 'Invalid amount' });
    await client.query('BEGIN');
    const result = await client.query(
      `UPDATE wallets SET balance = balance + $1, updated_at = CURRENT_TIMESTAMP WHERE user_id = $2 RETURNING *`,
      [amount, req.user.userId]
    );
    await logActivity(client, req.user.userId, ACTIVITY_TYPES.TOPUP, amount, 'Wallet top-up');
    await client.query('COMMIT');
    res.json({ success: true, message: 'Wallet topped up successfully', data: result.rows[0] });
  } catch (error) {
    await client.query('ROLLBACK');
    res.status(500).json({ success: false, message: 'Failed to top up wallet', error: error.message });
  } finally {
    client.release();
  }
});

app.post('/api/wallet/withdraw', authenticateToken, async (req, res) => {
  const client = await pool.connect();
  try {
    const { amount } = req.body;
    if (!amount || amount <= 0) return res.status(400).json({ success: false, message: 'Invalid amount' });
    const walletCheck = await client.query('SELECT balance FROM wallets WHERE user_id = $1', [req.user.userId]);
    if (walletCheck.rows.length === 0 || walletCheck.rows[0].balance < amount)
      return res.status(400).json({ success: false, message: 'Insufficient balance' });
    await client.query('BEGIN');
    const result = await client.query(
      `UPDATE wallets SET balance = balance - $1, updated_at = CURRENT_TIMESTAMP WHERE user_id = $2 RETURNING *`,
      [amount, req.user.userId]
    );
    await logActivity(client, req.user.userId, ACTIVITY_TYPES.WITHDRAW, amount, 'Wallet withdrawal');
    await client.query('COMMIT');
    res.json({ success: true, message: 'Withdrawal successful', data: result.rows[0] });
  } catch (error) {
    await client.query('ROLLBACK');
    res.status(500).json({ success: false, message: 'Failed to withdraw', error: error.message });
  } finally {
    client.release();
  }
});

// ============================================
// 7. TRANSACTION HISTORY ENDPOINTS
// ============================================
app.post('/api/transaction-history', authenticateToken, async (req, res) => {
  const client = await pool.connect();
  try {
    const { order_id, midtrans_order_id, total_amount, discount_amount = 0, coupons_used = [], payment_method = 'midtrans', items = [], status = 'completed' } = req.body;
    if (!order_id || !total_amount) return res.status(400).json({ success: false, message: 'Order ID and total amount are required' });

    await client.query('BEGIN');
    const historyResult = await client.query(
      `INSERT INTO transaction_histories (user_id, order_id, midtrans_order_id, total_amount, discount_amount, payment_method, coupons_used, items_data, status, created_at)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, CURRENT_TIMESTAMP) RETURNING *`,
      [req.user.userId, order_id, midtrans_order_id, total_amount, discount_amount, payment_method, JSON.stringify(coupons_used), JSON.stringify(items), status]
    );

    if (status === 'completed') {
      await updateWalletBalance(client, req.user.userId, total_amount, `Transaction completed: ${order_id}`);
      await logActivity(client, req.user.userId, ACTIVITY_TYPES.PAYMENT, total_amount, `Transaction ${order_id} completed`);
    }
    await client.query('COMMIT');
    res.status(201).json({ success: true, message: 'Transaction history recorded successfully', data: historyResult.rows[0] });
  } catch (error) {
    await client.query('ROLLBACK');
    console.error('Create transaction history error:', error.message);
    res.status(500).json({ success: false, message: 'Failed to record transaction history', error: error.message });
  } finally {
    client.release();
  }
});

app.get('/api/transaction-history', authenticateToken, async (req, res) => {
  try {
    const { limit = 20, offset = 0, status } = req.query;
    let query = `SELECT th.*, COUNT(*) OVER() as total_count FROM transaction_histories th WHERE th.user_id = $1`;
    const params = [req.user.userId];
    if (status) { query += ` AND th.status = $2`; params.push(status); }
    query += ` ORDER BY th.created_at DESC LIMIT $${params.length + 1} OFFSET $${params.length + 2}`;
    params.push(limit, offset);
    const result = await pool.query(query, params);
    const transactions = result.rows.map(row => ({
      ...row,
      coupons_used: typeof row.coupons_used === 'string' ? JSON.parse(row.coupons_used) : (row.coupons_used || []),
      items_data: typeof row.items_data === 'string' ? JSON.parse(row.items_data) : (row.items_data || [])
    }));
    res.json({ success: true, data: { transactions, pagination: { total: result.rows.length > 0 ? parseInt(result.rows[0].total_count) : 0, limit: parseInt(limit), offset: parseInt(offset) } } });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Failed to get transaction history', error: error.message });
  }
});

// ============================================
// 8. FINANCIAL & ACTIVITY ENDPOINTS
// ============================================
app.get('/api/financial/summary', authenticateToken, async (req, res) => {
  try {
    const result = await pool.query(`SELECT type, SUM(amount) as total_amount, COUNT(*) as count FROM financial_records WHERE user_id = $1 GROUP BY type`, [req.user.userId]);
    const summary = { income: 0, expense: 0, investment: 0, gain: 0 };
    result.rows.forEach(row => { summary[row.type] = parseFloat(row.total_amount); });
    const walletResult = await pool.query('SELECT COALESCE(balance, 0) as balance FROM wallets WHERE user_id = $1', [req.user.userId]);
    summary.wallet_balance = parseFloat(walletResult.rows[0]?.balance || 0);
    summary.net_balance = summary.income - summary.expense + summary.gain;
    res.json({ success: true, data: summary });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Failed to get financial summary', error: error.message });
  }
});

app.get('/api/financial/records', authenticateToken, async (req, res) => {
  try {
    const { type, limit = 50, offset = 0 } = req.query;
    let query = 'SELECT * FROM financial_records WHERE user_id = $1';
    const params = [req.user.userId];
    if (type) { query += ' AND type = $2'; params.push(type); }
    query += ` ORDER BY created_at DESC LIMIT $${params.length + 1} OFFSET $${params.length + 2}`;
    params.push(limit, offset);
    const result = await pool.query(query, params);
    res.json({ success: true, data: result.rows });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Failed to get financial records', error: error.message });
  }
});

app.get('/api/activities', authenticateToken, async (req, res) => {
  try {
    const { activity_type, limit = 50, offset = 0 } = req.query;
    let query = 'SELECT * FROM activity_logs WHERE user_id = $1';
    const params = [req.user.userId];
    if (activity_type) { query += ' AND activity_type = $2'; params.push(activity_type); }
    query += ` ORDER BY created_at DESC LIMIT $${params.length + 1} OFFSET $${params.length + 2}`;
    params.push(limit, offset);
    const result = await pool.query(query, params);
    res.json({ success: true, data: result.rows });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Failed to get activities', error: error.message });
  }
});

// ============================================
// 9. DASHBOARD STATS
// ============================================
app.get('/api/dashboard/stats', authenticateToken, async (req, res) => {
  try {
    const [stores, products, orders, txHistory, wallet, investments] = await Promise.all([
      pool.query('SELECT COUNT(*) as total FROM stores WHERE user_id = $1', [req.user.userId]),
      pool.query(`SELECT COUNT(*) as total FROM products p JOIN stores s ON p.store_id = s.id WHERE s.user_id = $1`, [req.user.userId]),
      pool.query(`SELECT COUNT(*) as total_orders, SUM(CASE WHEN payment_status = 'paid' THEN total_amount ELSE 0 END) as total_revenue FROM orders o JOIN stores s ON o.store_id = s.id WHERE s.user_id = $1`, [req.user.userId]),
      pool.query(`SELECT COUNT(*) as total_transactions, SUM(total_amount) as total_transaction_amount, SUM(discount_amount) as total_savings FROM transaction_histories WHERE user_id = $1 AND status = 'completed'`, [req.user.userId]),
      pool.query('SELECT COALESCE(balance, 0) as balance FROM wallets WHERE user_id = $1', [req.user.userId]),
      pool.query(`SELECT COUNT(*) as total, SUM(amount) as total_invested FROM investments WHERE user_id = $1 AND status = 'active'`, [req.user.userId])
    ]);

    res.json({
      success: true,
      data: {
        total_stores: parseInt(stores.rows[0].total),
        total_products: parseInt(products.rows[0].total),
        total_orders: parseInt(orders.rows[0].total_orders),
        total_revenue: parseFloat(orders.rows[0].total_revenue || 0),
        total_transactions: parseInt(txHistory.rows[0].total_transactions || 0),
        total_transaction_amount: parseFloat(txHistory.rows[0].total_transaction_amount || 0),
        total_savings: parseFloat(txHistory.rows[0].total_savings || 0),
        wallet_balance: parseFloat(wallet.rows[0]?.balance || 0),
        active_investments: parseInt(investments.rows[0].total),
        total_invested: parseFloat(investments.rows[0].total_invested || 0)
      }
    });
  } catch (error) {
    console.error('Dashboard stats error:', error.message);
    res.status(500).json({ success: false, message: 'Failed to get dashboard statistics', error: error.message });
  }
});

// ============================================
// 10. HEALTH CHECK
// ============================================
app.get('/api/health', async (req, res) => {
  let dbStatus = 'disconnected';
  try {
    await pool.query('SELECT 1');
    dbStatus = 'connected';
  } catch (e) {
    dbStatus = 'error: ' + e.message;
  }
  res.json({
    status: 'ok',
    message: 'Store Management API is running',
    timestamp: new Date().toISOString(),
    services: { database: dbStatus, midtrans: snap.isProduction ? 'production' : 'sandbox' },
    activeTransactions: transactionStore.size
  });
});

// Global error handler
app.use((err, req, res, next) => {
  console.error('Global error:', err.message);
  res.status(500).json({ success: false, message: 'Internal server error', error: err.message });
});

// ============================================
// START SERVER
// ============================================
app.listen(PORT, '0.0.0.0', () => {
  console.log(`\n✅ WarungTech API running on http://0.0.0.0:${PORT}`);
  console.log(`✅ Health check: http://localhost:${PORT}/api/health`);
  console.log(`✅ Local IP: http://${LOCAL_IP}:${PORT}/api/health\n`);
});

module.exports = app;
