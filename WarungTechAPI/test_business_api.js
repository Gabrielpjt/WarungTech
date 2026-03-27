#!/usr/bin/env node
/**
 * Business Analysis API Testing Script
 * Tests the new business analysis and Midtrans balance endpoints
 */

const https = require('https');
const http = require('http');

// Configuration
const API_CONFIG = {
    // Local development API
    BASE_URL: 'http://localhost:3002/api',

    // Production API (commented out for development testing)
    // BASE_URL: 'https://war-tech-backend-ouiu-a3ge8s8q9.vercel.app/api',

    // Test credentials
    TEST_EMAIL: 'test@warungtech.com',
    TEST_PASSWORD: 'password123',

    TIMEOUT: 15000
};

let authToken = null;

console.log('🧪 WarungTech Business Analysis API Testing');
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

                    // Business analysis data
                    if (data.business_overview) {
                        console.log(`📊 Business Condition: ${data.business_overview.condition}`);
                        console.log(`💰 Total Revenue: Rp ${data.business_overview.total_revenue?.toLocaleString()}`);
                        console.log(`🏪 Total Stores: ${data.business_overview.total_stores}`);
                        console.log(`📦 Total Products: ${data.business_overview.total_products}`);
                    }

                    // Midtrans balance data
                    if (data.account_summary) {
                        console.log(`💳 Processed Amount: Rp ${data.account_summary.total_processed_amount?.toLocaleString()}`);
                        console.log(`💸 Estimated Fees: Rp ${data.account_summary.estimated_midtrans_fees?.toLocaleString()}`);
                        console.log(`📈 Success Rate: ${data.account_summary.success_rate_percentage}%`);
                    }

                    // Dashboard stats
                    if (data.total_revenue !== undefined) {
                        console.log(`💰 Dashboard Revenue: Rp ${data.total_revenue?.toLocaleString()}`);
                        console.log(`🛒 Total Orders: ${data.total_orders}`);
                        console.log(`💼 Wallet Balance: Rp ${data.wallet_balance?.toLocaleString()}`);
                    }

                    // User profile
                    if (data.user && data.token) {
                        console.log(`👤 User: ${data.user.name} (${data.user.email})`);
                        console.log(`🔑 Token: ${data.token.substring(0, 20)}...`);
                        authToken = data.token; // Store for subsequent requests
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
 * Run all tests
 */
async function runAllTests() {
    console.log('\n🚀 Starting API Test Suite...\n');

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

    // Test 2: User Login (to get auth token)
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

    // Test 3: Dashboard Stats (requires auth)
    results.total++;
    const dashboardResult = await testEndpoint(
        'Dashboard Statistics',
        'GET',
        '/dashboard/stats',
        null,
        true
    );
    if (dashboardResult) results.passed++; else results.failed++;

    // Test 4: Business Analysis (NEW - requires auth)
    results.total++;
    const businessResult = await testEndpoint(
        'Business Analysis',
        'GET',
        '/business/analysis',
        null,
        true
    );
    if (businessResult) results.passed++; else results.failed++;

    // Test 5: Midtrans Balance (NEW - requires auth)
    results.total++;
    const midtransResult = await testEndpoint(
        'Midtrans Balance',
        'GET',
        '/midtrans/balance',
        null,
        true
    );
    if (midtransResult) results.passed++; else results.failed++;

    // Test 6: Transaction Analytics (NEW - requires auth)
    results.total++;
    const analyticsResult = await testEndpoint(
        'Transaction Analytics (30d)',
        'GET',
        '/analytics/transactions?period=30d',
        null,
        true
    );
    if (analyticsResult) results.passed++; else results.failed++;

    // Test 7: Financial Summary (requires auth)
    results.total++;
    const financialResult = await testEndpoint(
        'Financial Summary',
        'GET',
        '/financial/summary',
        null,
        true
    );
    if (financialResult) results.passed++; else results.failed++;

    // Test 8: User Stores (requires auth)
    results.total++;
    const storesResult = await testEndpoint(
        'User Stores',
        'GET',
        '/stores',
        null,
        true
    );
    if (storesResult) results.passed++; else results.failed++;

    // Test 9: User Investments (requires auth)
    results.total++;
    const investmentsResult = await testEndpoint(
        'User Investments',
        'GET',
        '/investments',
        null,
        true
    );
    if (investmentsResult) results.passed++; else results.failed++;

    // Test 10: Wallet Balance (requires auth)
    results.total++;
    const walletResult = await testEndpoint(
        'Wallet Balance',
        'GET',
        '/wallet',
        null,
        true
    );
    if (walletResult) results.passed++; else results.failed++;

    // Test Results Summary
    console.log('\n' + '='.repeat(60));
    console.log('📊 TEST RESULTS SUMMARY');
    console.log('='.repeat(60));
    console.log(`✅ Passed: ${results.passed}/${results.total}`);
    console.log(`❌ Failed: ${results.failed}/${results.total}`);
    console.log(`📈 Success Rate: ${((results.passed / results.total) * 100).toFixed(1)}%`);

    if (results.passed === results.total) {
        console.log('\n🎉 ALL TESTS PASSED! API is working perfectly.');
    } else if (results.passed > 0) {
        console.log('\n⚠️ SOME TESTS FAILED. Check the errors above.');
    } else {
        console.log('\n❌ ALL TESTS FAILED. API may be down or misconfigured.');
    }

    console.log('\n💡 Next Steps:');
    console.log('1. 🤖 Test AI chatbot integration with these endpoints');
    console.log('2. 📱 Update mobile app to use business analysis data');
    console.log('3. 📊 Verify dashboard displays new metrics correctly');
    console.log('4. 🔄 Test with real user data and transactions');

    console.log('\n🔗 API Documentation:');
    console.log('- Business Analysis: GET /api/business/analysis');
    console.log('- Midtrans Balance: GET /api/midtrans/balance');
    console.log('- Transaction Analytics: GET /api/analytics/transactions');

    console.log('\n' + '='.repeat(60));
}

// Run tests
runAllTests().catch(console.error);