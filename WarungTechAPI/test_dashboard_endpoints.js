// Test script to verify dashboard endpoints work correctly
const API_BASE_URL = 'http://192.168.100.15:3001/api';

async function testDashboardEndpoints() {
    console.log('🧪 Testing Dashboard Endpoints');
    console.log('================================\n');

    // Test health endpoint (no auth required)
    console.log('1. Testing Health Endpoint');
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        console.log('✅ Health:', data.message);
    } catch (error) {
        console.error('❌ Health failed:', error.message);
        return; // Stop if basic connectivity fails
    }

    // Test endpoints that require authentication
    console.log('\n2. Testing Authentication');

    // Try to register a test user first
    try {
        const registerResponse = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: 'Test User',
                email: 'test@wartech.com',
                password: 'password123',
                phone: '08123456789'
            })
        });

        if (registerResponse.status === 409) {
            console.log('ℹ️ User already exists, proceeding with login...');
        } else if (registerResponse.ok) {
            console.log('✅ User registered successfully');
        }
    } catch (error) {
        console.log('ℹ️ Registration skipped:', error.message);
    }

    // Login to get token
    let token = null;
    try {
        const loginResponse = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: 'test@wartech.com',
                password: 'password123'
            })
        });

        if (loginResponse.ok) {
            const loginData = await loginResponse.json();
            token = loginData.data?.token;
            console.log('✅ Login successful, token obtained');
        } else {
            const errorData = await loginResponse.json();
            console.error('❌ Login failed:', errorData.message);
            return;
        }
    } catch (error) {
        console.error('❌ Login error:', error.message);
        return;
    }

    if (!token) {
        console.error('❌ No token available, cannot test authenticated endpoints');
        return;
    }

    // Test dashboard stats endpoint
    console.log('\n3. Testing Dashboard Stats');
    try {
        const statsResponse = await fetch(`${API_BASE_URL}/dashboard/stats`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (statsResponse.ok) {
            const statsData = await statsResponse.json();
            console.log('✅ Dashboard stats retrieved successfully');
            console.log('📊 Stats summary:');
            console.log(`   - Total Stores: ${statsData.data.total_stores}`);
            console.log(`   - Total Products: ${statsData.data.total_products}`);
            console.log(`   - Total Orders: ${statsData.data.total_orders}`);
            console.log(`   - Total Revenue: ${statsData.data.total_revenue}`);
            console.log(`   - Wallet Balance: ${statsData.data.wallet_balance}`);
            console.log(`   - Recent Transactions: ${statsData.data.recent_transactions.length}`);
        } else {
            const errorData = await statsResponse.json();
            console.error('❌ Dashboard stats failed:', errorData.message);
        }
    } catch (error) {
        console.error('❌ Dashboard stats error:', error.message);
    }

    // Test transaction history endpoint
    console.log('\n4. Testing Transaction History');
    try {
        const historyResponse = await fetch(`${API_BASE_URL}/transaction-history?limit=10`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (historyResponse.ok) {
            const historyData = await historyResponse.json();
            console.log('✅ Transaction history retrieved successfully');
            console.log(`📋 Found ${historyData.data.transactions.length} transactions`);

            if (historyData.data.transactions.length > 0) {
                const firstTx = historyData.data.transactions[0];
                console.log('📄 Sample transaction:');
                console.log(`   - Order ID: ${firstTx.order_id}`);
                console.log(`   - Amount: ${firstTx.total_amount}`);
                console.log(`   - Status: ${firstTx.status}`);
                console.log(`   - Coupons: ${firstTx.coupons_used?.length || 0}`);
            }
        } else {
            const errorData = await historyResponse.json();
            console.error('❌ Transaction history failed:', errorData.message);
        }
    } catch (error) {
        console.error('❌ Transaction history error:', error.message);
    }

    // Test wallet endpoint
    console.log('\n5. Testing Wallet');
    try {
        const walletResponse = await fetch(`${API_BASE_URL}/wallet`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (walletResponse.ok) {
            const walletData = await walletResponse.json();
            console.log('✅ Wallet retrieved successfully');
            console.log(`💰 Balance: ${walletData.data.balance}`);
        } else {
            const errorData = await walletResponse.json();
            console.error('❌ Wallet failed:', errorData.message);
        }
    } catch (error) {
        console.error('❌ Wallet error:', error.message);
    }

    console.log('\n🎉 Dashboard endpoint testing completed!');
}

// Run the test
if (require.main === module) {
    testDashboardEndpoints().catch(console.error);
}

module.exports = { testDashboardEndpoints };