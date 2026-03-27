#!/usr/bin/env node
/**
 * Test Business Analysis API with Sample Data
 * Creates sample data and tests the business analysis endpoints
 */

const https = require('https');
const http = require('http');

const API_CONFIG = {
    BASE_URL: 'http://localhost:3002/api',
    TEST_EMAIL: 'test@warungtech.com',
    TEST_PASSWORD: 'password123',
    TIMEOUT: 15000
};

let authToken = null;

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
                        data: parsed
                    });
                } catch (e) {
                    resolve({
                        statusCode: res.statusCode,
                        data: responseData
                    });
                }
            });
        });

        req.on('error', reject);
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

async function login() {
    console.log('🔐 Logging in...');
    const response = await makeRequest('POST', '/auth/login', {
        email: API_CONFIG.TEST_EMAIL,
        password: API_CONFIG.TEST_PASSWORD
    });

    if (response.statusCode === 200 && response.data.success) {
        authToken = response.data.data.token;
        console.log('✅ Login successful');
        return true;
    }

    console.log('❌ Login failed');
    return false;
}

async function createSampleStore() {
    console.log('\n🏪 Creating sample store...');
    const response = await makeRequest('POST', '/stores', {
        store_name: 'Warung Makan Sederhana',
        description: 'Warung makan tradisional dengan cita rasa autentik',
        address: 'Jl. Malioboro No. 123, Yogyakarta'
    }, authToken);

    if (response.statusCode === 201 && response.data.success) {
        console.log('✅ Store created:', response.data.data.store_name);
        return response.data.data.id;
    }

    console.log('⚠️ Store creation failed or store already exists');
    return null;
}

async function createSampleProducts(storeId) {
    if (!storeId) return;

    console.log('\n📦 Creating sample products...');

    const products = [
        {
            name: 'Nasi Gudeg Special',
            description: 'Nasi gudeg dengan ayam dan telur',
            price: 25000,
            stock: 50
        },
        {
            name: 'Soto Ayam',
            description: 'Soto ayam dengan kuah bening',
            price: 20000,
            stock: 30
        },
        {
            name: 'Es Teh Manis',
            description: 'Es teh manis segar',
            price: 5000,
            stock: 100
        }
    ];

    for (const product of products) {
        const response = await makeRequest('POST', '/products', {
            store_id: storeId,
            ...product
        }, authToken);

        if (response.statusCode === 201) {
            console.log(`✅ Product created: ${product.name}`);
        }
    }
}

async function topUpWallet() {
    console.log('\n💰 Adding wallet balance...');
    const response = await makeRequest('POST', '/wallet/topup', {
        amount: 5000000 // 5 million IDR
    }, authToken);

    if (response.statusCode === 200) {
        console.log('✅ Wallet topped up: Rp 5,000,000');
    }
}

async function createSampleInvestment() {
    console.log('\n📈 Creating sample investment...');
    const response = await makeRequest('POST', '/investments', {
        wallet_address: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
        amount: 1000000, // 1 million IDR
        asset: 'BTC'
    }, authToken);

    if (response.statusCode === 201) {
        console.log('✅ Investment created: BTC 1,000,000 IDR');
    }
}

async function testBusinessAnalysis() {
    console.log('\n📊 Testing Business Analysis with data...');
    const response = await makeRequest('GET', '/business/analysis', null, authToken);

    if (response.statusCode === 200 && response.data.success) {
        const data = response.data.data;
        console.log('✅ Business Analysis Results:');
        console.log(`   📊 Condition: ${data.business_overview.condition} (Score: ${data.business_overview.condition_score})`);
        console.log(`   🏪 Stores: ${data.business_overview.total_stores}`);
        console.log(`   📦 Products: ${data.business_overview.total_products}`);
        console.log(`   💰 Revenue: Rp ${data.business_overview.total_revenue.toLocaleString()}`);
        console.log(`   💼 Wallet: Rp ${data.financial_health.wallet_balance.toLocaleString()}`);
        console.log(`   📈 Investments: ${data.financial_health.active_investments} (Rp ${data.financial_health.total_invested.toLocaleString()})`);

        if (data.recommendations.length > 0) {
            console.log('   💡 Recommendations:');
            data.recommendations.forEach(rec => console.log(`      - ${rec}`));
        }
    }
}

async function testMidtransBalance() {
    console.log('\n💳 Testing Midtrans Balance...');
    const response = await makeRequest('GET', '/midtrans/balance', null, authToken);

    if (response.statusCode === 200 && response.data.success) {
        const data = response.data.data;
        console.log('✅ Midtrans Balance Results:');
        console.log(`   💳 Processed: Rp ${data.account_summary.total_processed_amount.toLocaleString()}`);
        console.log(`   💸 Fees: Rp ${data.account_summary.estimated_midtrans_fees.toLocaleString()}`);
        console.log(`   📈 Success Rate: ${data.account_summary.success_rate_percentage}%`);
        console.log(`   🔄 Transactions: ${data.account_summary.total_transactions}`);
    }
}

async function runTestWithData() {
    console.log('🧪 WarungTech Business Analysis - Test with Sample Data');
    console.log('='.repeat(70));

    try {
        // Step 1: Login
        const loginSuccess = await login();
        if (!loginSuccess) return;

        // Step 2: Create sample data
        const storeId = await createSampleStore();
        await createSampleProducts(storeId);
        await topUpWallet();
        await createSampleInvestment();

        // Step 3: Test business analysis endpoints
        await testBusinessAnalysis();
        await testMidtransBalance();

        console.log('\n🎉 Test completed successfully!');
        console.log('\n💡 The business analysis now shows:');
        console.log('   - Store and product data');
        console.log('   - Wallet balance information');
        console.log('   - Investment portfolio');
        console.log('   - Business condition scoring');
        console.log('   - Actionable recommendations');

    } catch (error) {
        console.error('❌ Test failed:', error.message);
    }
}

runTestWithData();