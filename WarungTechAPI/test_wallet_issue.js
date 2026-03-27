// Test script to debug wallet issue
const API_BASE_URL = 'http://192.168.100.15:3001/api';

async function debugWalletIssue() {
    console.log('🔍 Debugging E-Wallet Issue');
    console.log('============================\n');

    // Step 1: Register a new user first
    console.log('1. Registering new test user...');
    const testEmail = `test${Date.now()}@wartech.com`;
    const testPassword = 'password123';
    let token = null;

    try {
        const registerResponse = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: 'Test User',
                email: testEmail,
                password: testPassword
            })
        });

        if (registerResponse.ok) {
            const registerData = await registerResponse.json();
            console.log('✅ User registered successfully');
            console.log(`📧 Email: ${testEmail}`);
        } else {
            const errorData = await registerResponse.json();
            console.error('❌ Registration failed:', errorData.message);
            return;
        }
    } catch (error) {
        console.error('❌ Registration error:', error.message);
        return;
    }

    // Step 2: Login with the new user
    console.log('\n2. Logging in with new user...');
    try {
        const loginResponse = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: testEmail,
                password: testPassword
            })
        });

        if (loginResponse.ok) {
            const loginData = await loginResponse.json();
            token = loginData.data?.token;
            console.log('✅ Login successful');
            console.log(`🔑 Token: ${token ? 'Received' : 'Missing'}`);
        } else {
            const errorData = await loginResponse.json();
            console.error('❌ Login failed:', errorData.message);
            return;
        }
    } catch (error) {
        console.error('❌ Login error:', error.message);
        return;
    }

    // Step 3: Check initial wallet balance
    console.log('\n3. Checking initial wallet balance...');
    let initialBalance = 0;
    try {
        const walletResponse = await fetch(`${API_BASE_URL}/wallet`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (walletResponse.ok) {
            const walletData = await walletResponse.json();
            initialBalance = parseFloat(walletData.data.balance);
            console.log(`💰 Initial wallet balance: Rp ${initialBalance.toLocaleString('id-ID')}`);
        } else {
            const errorData = await walletResponse.json();
            console.error('❌ Wallet check failed:', errorData.message);
        }
    } catch (error) {
        console.error('❌ Wallet check error:', error.message);
    }

    // Step 4: Create a store first (required for orders)
    console.log('\n4. Creating a test store...');
    const testAmount = 100000; // Rp 100,000
    let storeId = null;
    try {
        const storeResponse = await fetch(`${API_BASE_URL}/stores`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                store_name: 'Test Store',
                description: 'Test store for wallet testing',
                address: 'Test Address'
            })
        });

        if (storeResponse.ok) {
            const storeData = await storeResponse.json();
            storeId = storeData.data.id;
            console.log('✅ Store created successfully');
            console.log(`🏪 Store ID: ${storeId}`);
        } else {
            const errorData = await storeResponse.json();
            console.error('❌ Store creation failed:', errorData.message);
            return;
        }
    } catch (error) {
        console.error('❌ Store creation error:', error.message);
        return;
    }

    // Step 5: Create a product first
    console.log('\n5. Creating a test product...');
    let productId = null;

    try {
        const productResponse = await fetch(`${API_BASE_URL}/products`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                store_id: storeId,
                name: 'Test Product',
                description: 'Test product for wallet testing',
                price: testAmount,
                stock: 10,
                is_active: true
            })
        });

        if (productResponse.ok) {
            const productData = await productResponse.json();
            productId = productData.data.id;
            console.log('✅ Product created successfully');
            console.log(`📦 Product ID: ${productId}`);
        } else {
            const errorData = await productResponse.json();
            console.error('❌ Product creation failed:', errorData.message);
            return;
        }
    } catch (error) {
        console.error('❌ Product creation error:', error.message);
        return;
    }

    // Step 6: Create an order
    console.log('\n6. Creating a test order...');
    let orderId = null;

    try {
        const orderResponse = await fetch(`${API_BASE_URL}/orders/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                store_id: storeId,
                items: [
                    {
                        product_id: productId,
                        quantity: 1
                    }
                ],
                customer_name: 'Test Customer',
                customer_email: testEmail,
                customer_phone: '081234567890'
            })
        });

        if (orderResponse.ok) {
            const orderData = await orderResponse.json();
            orderId = orderData.data.midtrans_order_id;
            console.log('✅ Order created successfully');
            console.log(`📦 Order ID: ${orderId}`);
            console.log(`💰 Order Amount: Rp ${testAmount.toLocaleString('id-ID')}`);
        } else {
            const errorData = await orderResponse.json();
            console.error('❌ Order creation failed:', errorData.message);
            return;
        }
    } catch (error) {
        console.error('❌ Order creation error:', error.message);
        return;
    }

    // Step 7: Simulate payment success callback
    console.log('\n7. Simulating payment success...');
    try {
        const callbackResponse = await fetch(`${API_BASE_URL}/payment/finish?order_id=${orderId}&transaction_status=settlement&status_code=200`, {
            method: 'GET'
        });

        if (callbackResponse.ok) {
            console.log('✅ Payment callback processed');
        } else {
            console.error('❌ Payment callback failed');
        }
    } catch (error) {
        console.error('❌ Payment callback error:', error.message);
    }

    // Step 8: Check wallet balance after payment
    console.log('\n8. Checking wallet balance after payment...');
    try {
        const walletResponse = await fetch(`${API_BASE_URL}/wallet`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (walletResponse.ok) {
            const walletData = await walletResponse.json();
            const newBalance = parseFloat(walletData.data.balance);
            const expectedBalance = initialBalance + testAmount;
            const actualIncrease = newBalance - initialBalance;

            console.log(`💰 Previous balance: Rp ${initialBalance.toLocaleString('id-ID')}`);
            console.log(`💰 Current balance: Rp ${newBalance.toLocaleString('id-ID')}`);
            console.log(`📊 Expected balance: Rp ${expectedBalance.toLocaleString('id-ID')}`);
            console.log(`💵 Actual increase: Rp ${actualIncrease.toLocaleString('id-ID')}`);

            if (Math.abs(newBalance - expectedBalance) < 0.01) {
                console.log('✅ SUCCESS: Wallet balance updated correctly!');
            } else {
                console.log('❌ ISSUE: Wallet balance not updated as expected!');

                if (actualIncrease === 0) {
                    console.log('🔍 DIAGNOSIS: No money was added to wallet');
                    console.log('   - Check if payment callback is working');
                    console.log('   - Check if updateWalletBalance function is called');
                    console.log('   - Check database wallet table');
                } else if (actualIncrease !== testAmount) {
                    console.log('🔍 DIAGNOSIS: Wrong amount added to wallet');
                    console.log('   - Check if correct amount is passed to updateWalletBalance');
                }
            }
        } else {
            const errorData = await walletResponse.json();
            console.error('❌ Final wallet check failed:', errorData.message);
        }
    } catch (error) {
        console.error('❌ Final wallet check error:', error.message);
    }

    // Step 9: Check dashboard stats to see if they reflect the changes
    console.log('\n9. Checking dashboard stats...');
    try {
        const statsResponse = await fetch(`${API_BASE_URL}/dashboard/stats`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (statsResponse.ok) {
            const statsData = await statsResponse.json();
            console.log('✅ Dashboard stats retrieved');
            console.log(`📊 Total transactions: ${statsData.data.total_transactions}`);
            console.log(`💰 Total revenue: Rp ${statsData.data.total_revenue?.toLocaleString('id-ID') || 0}`);
            console.log(`💼 Wallet balance: Rp ${statsData.data.wallet_balance?.toLocaleString('id-ID') || 0}`);
            console.log(`🏪 Total stores: ${statsData.data.total_stores}`);
        } else {
            const errorData = await statsResponse.json();
            console.error('❌ Dashboard stats failed:', errorData.message);
        }
    } catch (error) {
        console.error('❌ Dashboard stats error:', error.message);
    }

    console.log('\n🎯 Wallet Issue Debug Test Completed!');
    console.log('=====================================');
}

// Run the test
if (require.main === module) {
    debugWalletIssue().catch(console.error);
}

module.exports = { debugWalletIssue };