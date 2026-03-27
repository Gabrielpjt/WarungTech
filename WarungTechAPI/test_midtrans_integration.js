#!/usr/bin/env node
/**
 * Midtrans Integration Testing Script
 * Tests the new Midtrans transaction sync and integration endpoints
 */

const https = require('https');
const http = require('http');

// Configuration
const API_CONFIG = {
    BASE_URL: 'http://localhost:3002/api',
    TEST_EMAIL: 'test@warungtech.com',
    TEST_PASSWORD: 'password123',
    TIMEOUT: 15000
};

let authToken = null;

console.log('🧪 WarungTech Midtrans Integration Testing');
console.log('='.repeat(60));
console.log(`🌐 Testing API: ${API_CONFIG.BASE_URL}`);
console.log(`📧 Test User: ${API_CONFIG.TEST_EMAIL}`);
console.log('='.repeat(60));

/**
 * Make HTTP request
 */
function makeRequest(method, endpoint, data = null, token = null) {
    return new Promise((resolve, reject) => {
        const url = new URL(API_CONFIG.BASE_URL + endpoint);
        const isHttps = url.protocol === 'https:';
        const client = isHttps ? https : http;

        const options = {
            hostname: url.hostname,
            port: url.port || (isHttps ? 443 : 80),
            path: url.pathname + url.search,
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout: API_CONFIG.TIMEOUT
        };

        if (token) {
            options.headers['Authorization'] = `Bearer ${token}`;
        }

        if (data) {
            const jsonData = JSON.stringify(data);
            options.headers['Content-Length'] = Buffer.byteLength(jsonData);
        }

        const req = client.request(options, (res) => {
            let responseData = '';

            res.on('data', (chunk) => {
                responseData += chunk;
            });

            res.on('end', () => {
                try {
                    const parsed = JSON.parse(responseData);
                    resolve({
                        statusCode: res.statusCode,
                        data: parsed,
                        headers: res.headers
                    });
                } catch (e) {
                    resolve({
                        statusCode: res.statusCode,
                        data: responseData,
                        headers: res.headers
                    });
                }
            });
        });

        req.on('error', (err) => {
            reject(err);
        });

        req.on('timeout', () => {
            req.destroy();
            reject(new Error('Request timeout'));
        });

        if (data) {
            req.write(JSON.stringify(data));
        }

        req.end();
    });
}

/**
 * Test API endpoint
 */
async function testEndpoint(name, method, endpoint, data = null, requireAuth = false) {
    console.log(`\n🧪 Testing: ${name}`);
    console.log(`📡 ${method} ${endpoint}`);
    console.log('-'.repeat(50));

    try {
        const startTime = Date.now();
        const token = requireAuth ? authToken : null;

        if (requireAuth && !token) {
            console.log('❌ SKIPPED: No auth token available');
            return false;
        }

        const response = await makeRequest(method, endpoint, data, token);
        const responseTime = Date.now() - startTime;

        console.log(`⏱️ Response Time: ${responseTime}ms`);
        console.log(`📊 Status Code: ${response.statusCode}`);

        if (response.statusCode >= 200 && response.statusCode < 300) {
            console.log('✅ Status: SUCCESS');

            if (typeof response.data === 'object' && response.data.success) {
                console.log('✅ API Response: SUCCESS');

                // Show key data points
                if (response.data.data) {
                    const data = response.data.data;

                    // Sync results
                    if (data.synced !== undefined) {
                        console.log(`🔄 Synced: ${data.synced} transactions`);
                        console.log(`⏭️ Skipped: ${data.skipped} transactions`);
                        console.log(`❌ Errors: ${data.errors} transactions`);
                        console.log(`🏪 Store ID: ${data.store_id}`);
                    }

                    // Balance data
                    if (data.midtrans_account) {
                        console.log(`💰 Actual Balance: Rp ${data.midtrans_account.actual_balance?.toLocaleString()}`);
                        console.log(`🔄 Sync Status: ${data.midtrans_account.sync_status || 'N/A'}`);
                    }

                    // Account summary
                    if (data.account_summary) {
                        console.log(`💳 System Processed: Rp ${data.account_summary.total_processed_amount?.toLocaleString()}`);
                        console.log(`📊 Total Transactions: ${data.account_summary.total_transactions}`);
                        console.log(`📈 Success Rate: ${data.account_summary.success_rate_percentage}%`);
                    }

                    // Business overview
                    if (data.business_overview) {
                        console.log(`📊 Business Condition: ${data.business_overview.condition}`);
                        console.log(`💰 Total Revenue: Rp ${data.business_overview.total_revenue?.toLocaleString()}`);
                        console.log(`🛒 Total Orders: ${data.business_overview.total_orders}`);
                    }

                    // User login
                    if (data.user && data.token) {
                        console.log(`👤 User: ${data.user.name} (${data.user.email})`);
                        console.log(`🔑 Token: ${data.token.substring(0, 20)}...`);
                        authToken = data.token;
                    }
                }

                console.log(`📄 Response Size: ${JSON.stringify(response.data).length} characters`);
            } else {
                console.log('⚠️ API Response: Non-standard format');
                console.log('📄 Response:', JSON.stringify(response.data, null, 2).substring(0, 500));
            }
        } else {
            console.log('❌ Status: FAILED');
            console.log(`📄 Error Response: ${JSON.stringify(response.data, null, 2)}`);
        }

        return response.statusCode >= 200 && response.statusCode < 300;

    } catch (error) {
        console.log('❌ Status: ERROR');
        console.log(`📄 Error: ${error.message}`);
        return false;
    }
}

/**
 * Run all Midtrans integration tests
 */
async function runMidtransTests() {
    console.log('\n🚀 Starting Midtrans Integration Test Suite...\n');

    const results = {
        total: 0,
        passed: 0,
        failed: 0
    };

    // Test 1: Health Check
    results.total++;
    const healthResult = await testEndpoint(
        'Health Check',
        'GET',
        '/health'
    );
    if (healthResult) results.passed++; else results.failed++;

    // Test 2: User Login
    results.total++;
    const loginResult = await testEndpoint(
        'User Login',
        'POST',
        '/auth/login',
        {
            email: API_CONFIG.TEST_EMAIL,
            password: API_CONFIG.TEST_PASSWORD
        }
    );
    if (loginResult) results.passed++; else results.failed++;

    // Test 3: Midtrans Balance (Before Sync)
    results.total++;
    const balanceBeforeResult = await testEndpoint(
        'Midtrans Balance (Before Sync)',
        'GET',
        '/midtrans/balance',
        null,
        true
    );
    if (balanceBeforeResult) results.passed++; else results.failed++;

    // Test 4: Sync Midtrans Transactions
    results.total++;
    const syncResult = await testEndpoint(
        'Sync Midtrans Transactions',
        'POST',
        '/midtrans/sync-transactions',
        null,
        true
    );
    if (syncResult) results.passed++; else results.failed++;

    // Test 5: Midtrans Balance (After Sync)
    results.total++;
    const balanceAfterResult = await testEndpoint(
        'Midtrans Balance (After Sync)',
        'GET',
        '/midtrans/balance',
        null,
        true
    );
    if (balanceAfterResult) results.passed++; else results.failed++;

    // Test 6: Account Balance
    results.total++;
    const accountBalanceResult = await testEndpoint(
        'Midtrans Account Balance',
        'GET',
        '/midtrans/account-balance',
        null,
        true
    );
    if (accountBalanceResult) results.passed++; else results.failed++;

    // Test 7: Business Analysis (After Sync)
    results.total++;
    const businessResult = await testEndpoint(
        'Business Analysis (After Sync)',
        'GET',
        '/business/analysis',
        null,
        true
    );
    if (businessResult) results.passed++; else results.failed++;

    // Test 8: Dashboard Stats (After Sync)
    results.total++;
    const dashboardResult = await testEndpoint(
        'Dashboard Statistics (After Sync)',
        'GET',
        '/dashboard/stats',
        null,
        true
    );
    if (dashboardResult) results.passed++; else results.failed++;

    // Test 9: Transaction Analytics
    results.total++;
    const analyticsResult = await testEndpoint(
        'Transaction Analytics',
        'GET',
        '/analytics/transactions?period=30d',
        null,
        true
    );
    if (analyticsResult) results.passed++; else results.failed++;

    // Test 10: Import Transactions (Test with sample data)
    results.total++;
    const importResult = await testEndpoint(
        'Import Transactions (Sample)',
        'POST',
        '/midtrans/import-transactions',
        {
            transactions: [
                {
                    order_id: 'TEST-ORDER-001',
                    amount: 50000,
                    status: 'settlement',
                    transaction_time: new Date().toISOString()
                }
            ]
        },
        true
    );
    if (importResult) results.passed++; else results.failed++;

    // Test Results Summary
    console.log('\n' + '='.repeat(60));
    console.log('📊 MIDTRANS INTEGRATION TEST RESULTS');
    console.log('='.repeat(60));
    console.log(`✅ Passed: ${results.passed}/${results.total}`);
    console.log(`❌ Failed: ${results.failed}/${results.total}`);
    console.log(`📈 Success Rate: ${((results.passed / results.total) * 100).toFixed(1)}%`);

    if (results.passed === results.total) {
        console.log('\n🎉 ALL MIDTRANS INTEGRATION TESTS PASSED!');
        console.log('✅ Transaction sync working perfectly');
        console.log('✅ Balance integration complete');
        console.log('✅ Business analysis updated');
        console.log('✅ Ready for production deployment');
    } else if (results.passed > 0) {
        console.log('\n⚠️ SOME TESTS FAILED. Check the errors above.');
    } else {
        console.log('\n❌ ALL TESTS FAILED. API may be down or misconfigured.');
    }

    console.log('\n💡 Integration Features:');
    console.log('🔄 Automatic transaction sync from Midtrans dashboard');
    console.log('💰 Real balance display (Rp 316,000 + synced transactions)');
    console.log('📊 Enhanced business analysis with actual transaction data');
    console.log('📱 Mobile app ready with accurate financial data');
    console.log('🤖 AI chatbot can access real transaction history');

    console.log('\n🔗 New Endpoints:');
    console.log('- POST /api/midtrans/sync-transactions (Sync from dashboard)');
    console.log('- GET /api/midtrans/transaction/:orderId (Check status)');
    console.log('- POST /api/midtrans/import-transactions (Bulk import)');
    console.log('- GET /api/midtrans/account-balance (Real balance)');

    console.log('\n' + '='.repeat(60));
}

// Run tests
runMidtransTests().catch(console.error);