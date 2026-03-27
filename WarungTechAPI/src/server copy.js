// server.js - Backend untuk Midtrans Snap Integration (Fixed Callbacks)
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const midtransClient = require('midtrans-client');

const app = express();
const PORT = 3001;

// Middleware
app.use(cors({
  origin: '*',
  credentials: true
}));
app.use(express.json());

// Konfigurasi Midtrans Snap
const snap = new midtransClient.Snap({
  isProduction: process.env.MIDTRANS_IS_PRODUCTION === 'true',
  serverKey: process.env.MIDTRANS_SERVER_KEY,
  clientKey: process.env.MIDTRANS_CLIENT_KEY
});

console.log(`✅ Midtrans configured in ${snap.isProduction ? 'PRODUCTION' : 'SANDBOX'} mode`);

// Store untuk menyimpan status transaksi sementara
const transactionStore = new Map();

// Endpoint untuk membuat transaksi dan mendapatkan Snap Token
app.post('/api/tokenizer', async (req, res) => {
  try {
    const { orderId, amount, customerName, customerEmail, customerPhone, items, discount } = req.body;

    console.log('Received transaction request:', {
      orderId,
      amount,
      customerName,
      items: items?.length || 0,
      discount
    });

    // Validasi input
    if (!orderId || !amount || !customerName || !customerEmail || !items || items.length === 0) {
      return res.status(400).json({
        error: 'Missing required fields',
        message: 'orderId, amount, customerName, customerEmail, and items are required'
      });
    }

    // Format item_details untuk Midtrans
    const itemDetails = items.map(item => ({
      id: item.id,
      price: item.price,
      quantity: item.quantity,
      name: item.productName
    }));

    // Tambahkan diskon sebagai item jika ada
    if (discount && discount > 0) {
      itemDetails.push({
        id: 'DISCOUNT',
        price: -discount,
        quantity: 1,
        name: 'Diskon Kupon'
      });
    }

    // Parameter transaksi dengan callback URLs yang mengarah ke backend
    const parameter = {
      transaction_details: {
        order_id: orderId,
        gross_amount: amount
      },
      credit_card: {
        secure: true
      },
      customer_details: {
        first_name: customerName,
        email: customerEmail,
        phone: customerPhone
      },
      item_details: itemDetails,
      callbacks: {
        finish: `http://192.168.100.15:${PORT}/api/payment/finish?order_id=${orderId}`,
        error: `http://192.168.100.15:${PORT}/api/payment/error?order_id=${orderId}`,
        pending: `http://192.168.100.15:${PORT}/api/payment/pending?order_id=${orderId}`
      }
    };

    console.log('Creating Midtrans transaction with params:', JSON.stringify(parameter, null, 2));

    // Buat transaksi menggunakan Midtrans Snap API
    const transaction = await snap.createTransaction(parameter);

    console.log('Transaction created successfully:', {
      token: transaction.token?.substring(0, 20) + '...',
      redirect_url: transaction.redirect_url
    });

    // Return token dan redirect_url ke frontend
    res.json({
      success: true,
      token: transaction.token,
      redirect_url: transaction.redirect_url,
      order_id: orderId
    });

  } catch (error) {
    console.error('Error creating Midtrans transaction:', error);

    res.status(500).json({
      success: false,
      error: 'Failed to create transaction',
      message: error.message || 'Internal server error',
      details: error.ApiResponse?.error_messages || []
    });
  }
});

// Endpoint untuk melakukan transaksi (create payment)
app.post('/api/transaction/create', async (req, res) => {
  try {
    const {
      orderId,
      amount,
      customerName,
      customerEmail,
      customerPhone,
      items,
      discount = 0
    } = req.body;

    console.log('=== CREATE TRANSACTION REQUEST ===');
    console.log('Order ID:', orderId);
    console.log('Amount:', amount);
    console.log('Items:', items?.length || 0);

    // Validasi input
    if (!orderId || !amount || !customerName || !customerEmail || !items || items.length === 0) {
      return res.status(400).json({
        success: false,
        message: 'Invalid transaction data'
      });
    }

    // Mapping item_details
    const itemDetails = items.map(item => ({
      id: item.id,
      name: item.productName,
      price: item.price,
      quantity: item.quantity
    }));

    // Tambahkan diskon jika ada
    if (discount > 0) {
      itemDetails.push({
        id: 'DISCOUNT',
        name: 'Diskon',
        price: -discount,
        quantity: 1
      });
    }

    // Payload Midtrans dengan callback URLs yang benar
    const parameter = {
      transaction_details: {
        order_id: orderId,
        gross_amount: amount
      },
      customer_details: {
        first_name: customerName,
        email: customerEmail,
        phone: customerPhone
      },
      item_details: itemDetails,
      credit_card: {
        secure: true
      },
      callbacks: {
        finish: `http://192.168.100.15:${PORT}/api/payment/finish?order_id=${orderId}`,
        error: `http://192.168.100.15:${PORT}/api/payment/error?order_id=${orderId}`,
        pending: `http://192.168.100.15:${PORT}/api/payment/pending?order_id=${orderId}`
      }
    };

    console.log('Creating transaction with callbacks:', parameter.callbacks);

    // Create transaction ke Midtrans
    const transaction = await snap.createTransaction(parameter);

    console.log('✅ Transaction created successfully');
    console.log('Snap Token:', transaction.token?.substring(0, 20) + '...');

    // Simpan info transaksi sementara
    transactionStore.set(orderId, {
      amount,
      customerName,
      createdAt: new Date(),
      status: 'pending'
    });

    return res.status(201).json({
      success: true,
      message: 'Transaction created',
      data: {
        orderId,
        snapToken: transaction.token,
        redirectUrl: transaction.redirect_url
      }
    });

  } catch (error) {
    console.error('❌ Create transaction error:', error);

    return res.status(500).json({
      success: false,
      message: 'Failed to create transaction',
      error: error.message
    });
  }
});

// ============================================
// CALLBACK ENDPOINTS - Menangani redirect dari Midtrans
// ============================================

// Callback: Payment Finished (Success)
app.get('/api/payment/finish', async (req, res) => {
  const { order_id, transaction_status, status_code } = req.query;

  console.log('🎉 Payment FINISH callback received');
  console.log('Order ID:', order_id);
  console.log('Transaction Status:', transaction_status);
  console.log('Status Code:', status_code);

  // Update status di store
  if (order_id && transactionStore.has(order_id)) {
    const txData = transactionStore.get(order_id);
    txData.status = 'success';
    txData.completedAt = new Date();
    transactionStore.set(order_id, txData);
  }

  // Return HTML yang akan di-detect oleh WebView
  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Payment Success</title>
      <style>
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 100vh;
          margin: 0;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .container {
          background: white;
          padding: 40px;
          border-radius: 20px;
          box-shadow: 0 20px 60px rgba(0,0,0,0.3);
          text-align: center;
          max-width: 400px;
        }
        .success-icon {
          width: 80px;
          height: 80px;
          background: #10B981;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto 20px;
        }
        .checkmark {
          width: 40px;
          height: 40px;
          border: 4px solid white;
          border-radius: 50%;
          position: relative;
        }
        .checkmark:after {
          content: '';
          position: absolute;
          left: 8px;
          top: 12px;
          width: 10px;
          height: 18px;
          border: solid white;
          border-width: 0 4px 4px 0;
          transform: rotate(45deg);
        }
        h1 {
          color: #10B981;
          margin: 0 0 10px 0;
          font-size: 28px;
        }
        p {
          color: #6B7280;
          margin: 10px 0;
          font-size: 16px;
        }
        .order-id {
          background: #F3F4F6;
          padding: 10px;
          border-radius: 8px;
          font-family: monospace;
          margin: 20px 0;
          color: #374151;
        }
        .loading {
          margin-top: 20px;
          color: #9CA3AF;
          font-size: 14px;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="success-icon">
          <div class="checkmark"></div>
        </div>
        <h1>Pembayaran Berhasil!</h1>
        <p>Terima kasih atas pembayaran Anda</p>
        ${order_id ? `<div class="order-id">Order ID: ${order_id}</div>` : ''}
        <p class="loading">Mengarahkan kembali ke aplikasi...</p>
      </div>
      <script>
        // Kirim message ke React Native WebView
        setTimeout(() => {
          if (window.ReactNativeWebView) {
            window.ReactNativeWebView.postMessage(JSON.stringify({
              type: 'payment_complete',
              status: 'settlement',
              orderId: '${order_id}',
              transactionStatus: '${transaction_status}',
              statusCode: '${status_code}'
            }));
          }
        }, 1500);
      </script>
    </body>
    </html>
  `);
});

// Callback: Payment Error
app.get('/api/payment/error', (req, res) => {
  const { order_id, transaction_status, status_code } = req.query;

  console.log('❌ Payment ERROR callback received');
  console.log('Order ID:', order_id);
  console.log('Transaction Status:', transaction_status);
  console.log('Status Code:', status_code);

  // Update status di store
  if (order_id && transactionStore.has(order_id)) {
    const txData = transactionStore.get(order_id);
    txData.status = 'error';
    txData.errorAt = new Date();
    transactionStore.set(order_id, txData);
  }

  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Payment Error</title>
      <style>
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 100vh;
          margin: 0;
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        .container {
          background: white;
          padding: 40px;
          border-radius: 20px;
          box-shadow: 0 20px 60px rgba(0,0,0,0.3);
          text-align: center;
          max-width: 400px;
        }
        .error-icon {
          width: 80px;
          height: 80px;
          background: #EF4444;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto 20px;
        }
        .cross {
          width: 40px;
          height: 40px;
          position: relative;
        }
        .cross:before, .cross:after {
          content: '';
          position: absolute;
          width: 4px;
          height: 40px;
          background: white;
          left: 18px;
        }
        .cross:before {
          transform: rotate(45deg);
        }
        .cross:after {
          transform: rotate(-45deg);
        }
        h1 {
          color: #EF4444;
          margin: 0 0 10px 0;
          font-size: 28px;
        }
        p {
          color: #6B7280;
          margin: 10px 0;
          font-size: 16px;
        }
        .order-id {
          background: #FEE2E2;
          padding: 10px;
          border-radius: 8px;
          font-family: monospace;
          margin: 20px 0;
          color: #991B1B;
        }
        .loading {
          margin-top: 20px;
          color: #9CA3AF;
          font-size: 14px;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="error-icon">
          <div class="cross"></div>
        </div>
        <h1>Pembayaran Gagal</h1>
        <p>Terjadi kesalahan saat memproses pembayaran</p>
        ${order_id ? `<div class="order-id">Order ID: ${order_id}</div>` : ''}
        <p class="loading">Mengarahkan kembali ke aplikasi...</p>
      </div>
      <script>
        setTimeout(() => {
          if (window.ReactNativeWebView) {
            window.ReactNativeWebView.postMessage(JSON.stringify({
              type: 'payment_complete',
              status: 'error',
              orderId: '${order_id}',
              transactionStatus: '${transaction_status}',
              statusCode: '${status_code}'
            }));
          }
        }, 1500);
      </script>
    </body>
    </html>
  `);
});

// Callback: Payment Pending
app.get('/api/payment/pending', (req, res) => {
  const { order_id, transaction_status, status_code } = req.query;

  console.log('⏳ Payment PENDING callback received');
  console.log('Order ID:', order_id);
  console.log('Transaction Status:', transaction_status);
  console.log('Status Code:', status_code);

  // Update status di store
  if (order_id && transactionStore.has(order_id)) {
    const txData = transactionStore.get(order_id);
    txData.status = 'pending';
    txData.pendingAt = new Date();
    transactionStore.set(order_id, txData);
  }

  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Payment Pending</title>
      <style>
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 100vh;
          margin: 0;
          background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
        }
        .container {
          background: white;
          padding: 40px;
          border-radius: 20px;
          box-shadow: 0 20px 60px rgba(0,0,0,0.3);
          text-align: center;
          max-width: 400px;
        }
        .pending-icon {
          width: 80px;
          height: 80px;
          background: #F59E0B;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto 20px;
        }
        .clock {
          width: 40px;
          height: 40px;
          border: 4px solid white;
          border-radius: 50%;
          position: relative;
        }
        .clock:before {
          content: '';
          position: absolute;
          width: 2px;
          height: 12px;
          background: white;
          left: 17px;
          top: 8px;
        }
        .clock:after {
          content: '';
          position: absolute;
          width: 8px;
          height: 2px;
          background: white;
          left: 17px;
          top: 17px;
        }
        h1 {
          color: #F59E0B;
          margin: 0 0 10px 0;
          font-size: 28px;
        }
        p {
          color: #6B7280;
          margin: 10px 0;
          font-size: 16px;
        }
        .order-id {
          background: #FEF3C7;
          padding: 10px;
          border-radius: 8px;
          font-family: monospace;
          margin: 20px 0;
          color: #92400E;
        }
        .loading {
          margin-top: 20px;
          color: #9CA3AF;
          font-size: 14px;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="pending-icon">
          <div class="clock"></div>
        </div>
        <h1>Pembayaran Tertunda</h1>
        <p>Pembayaran Anda sedang diproses</p>
        ${order_id ? `<div class="order-id">Order ID: ${order_id}</div>` : ''}
        <p class="loading">Mengarahkan kembali ke aplikasi...</p>
      </div>
      <script>
        setTimeout(() => {
          if (window.ReactNativeWebView) {
            window.ReactNativeWebView.postMessage(JSON.stringify({
              type: 'payment_complete',
              status: 'pending',
              orderId: '${order_id}',
              transactionStatus: '${transaction_status}',
              statusCode: '${status_code}'
            }));
          }
        }, 1500);
      </script>
    </body>
    </html>
  `);
});

// Endpoint untuk notifikasi callback dari Midtrans
app.post('/api/notification', async (req, res) => {
  try {
    const notification = req.body;
    console.log('📬 Received notification from Midtrans:', notification);

    // Verifikasi signature notification
    const statusResponse = await snap.transaction.notification(notification);

    const orderId = statusResponse.order_id;
    const transactionStatus = statusResponse.transaction_status;
    const fraudStatus = statusResponse.fraud_status;

    console.log(`Transaction notification: Order ID: ${orderId}, Status: ${transactionStatus}, Fraud: ${fraudStatus}`);

    // Update status di store
    if (transactionStore.has(orderId)) {
      const txData = transactionStore.get(orderId);
      txData.status = transactionStatus;
      txData.notifiedAt = new Date();
      transactionStore.set(orderId, txData);
    }

    // Handle status transaksi
    if (transactionStatus === 'capture') {
      if (fraudStatus === 'accept') {
        console.log(`✅ Transaction ${orderId} captured and accepted`);
      }
    } else if (transactionStatus === 'settlement') {
      console.log(`✅ Transaction ${orderId} settled`);
    } else if (transactionStatus === 'pending') {
      console.log(`⏳ Transaction ${orderId} is pending`);
    } else if (transactionStatus === 'deny') {
      console.log(`❌ Transaction ${orderId} denied`);
    } else if (transactionStatus === 'expire') {
      console.log(`⏰ Transaction ${orderId} expired`);
    } else if (transactionStatus === 'cancel') {
      console.log(`🚫 Transaction ${orderId} cancelled`);
    }

    res.status(200).json({ status: 'ok' });
  } catch (error) {
    console.error('Error handling notification:', error);
    res.status(500).json({ error: 'Failed to process notification' });
  }
});

// Endpoint untuk cek status transaksi
app.get('/api/transaction/:orderId', async (req, res) => {
  try {
    const { orderId } = req.params;

    // Cek di store lokal dulu
    if (transactionStore.has(orderId)) {
      const localData = transactionStore.get(orderId);
      console.log(`📊 Local transaction data for ${orderId}:`, localData);
    }

    // Query ke Midtrans untuk data real-time
    const statusResponse = await snap.transaction.status(orderId);

    res.json({
      success: true,
      data: statusResponse
    });
  } catch (error) {
    console.error('Error checking transaction status:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to check transaction status',
      message: error.message
    });
  }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    message: 'Midtrans Snap API server is running',
    timestamp: new Date().toISOString(),
    activeTransactions: transactionStore.size
  });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`
╔══════════════════════════════════════════════╗
║   Midtrans Snap API Server (Fixed Callbacks) ║
║   Running on: http://192.168.100.15:${PORT}   ║
║                                              ║
║   Main Endpoints:                            ║
║   POST /api/transaction/create               ║
║   POST /api/tokenizer                        ║
║                                              ║
║   Callback Endpoints:                        ║
║   GET  /api/payment/finish                   ║
║   GET  /api/payment/error                    ║
║   GET  /api/payment/pending                  ║
║                                              ║
║   Other Endpoints:                           ║
║   POST /api/notification                     ║
║   GET  /api/transaction/:orderId             ║
║   GET  /api/health                           ║
╚══════════════════════════════════════════════╝
  `);

  console.log('\n✅ Callback URLs are configured correctly');
  console.log('📱 WebView will automatically detect payment completion');
  console.log('\n⚠️  For Production:');
  console.log('1. Change isProduction to true');
  console.log('2. Update server keys');
  console.log('3. Use HTTPS for callback URLs\n');
});

module.exports = app;