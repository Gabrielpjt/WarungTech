// Test script to verify payment and wallet integration
const API_BASE_URL = 'http://192.168.100.15:3001/api';

async function testPaymentWalletIntegration() {
    console.log('🧪 Testing Payment and Wallet Integration');
    console.log('==========================================\n');

    let token = null;

    // Step 1: Login to get token
    console.log('1. Logging in...');
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
            console.log('✅ Login successful');
        } else {
            console.error('❌ Login failed');
            return;
        }
    } catch (error) {
        console.error('❌ Login error:', error.message);
        return;
    }

    // Step 2: Check initial wallet balance
    console.log('\n2. Checking initial wallet balance...');
    let initialBalance = 0;
    try {
        const walletResponse = await fetch(`${API_BASE_URL}/wallet`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (walletResponse.ok) {
            const walletData = await walletResponse.json();
            initialBalance = parseFloat(walletData.data.balance);
            console.log(`💰 Initial wallet balance: ${initialBalance}`);
        }
    } catch (error) {
        console.error('❌ Wallet check error:', error.message);
    }

    // Step 3: Create a transaction history (simulating completed payment)
    console.log('\n3. Creating completed transaction...');
    const testAmount = 50000;
    const orderId = `TEST-${Date.now()}`;

    try {
        const transactionResponse = await fetch(`${API_BASE_URL}/transaction-history`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                order_id: orderId,
                total_amount: testAmount,
                discount_amount: 5000,
                coupons_used: [{ code: 'TEST10', discount: 5000 }],
                payment_method: 'midtrans',
                items: [
                    { name: 'Test Product', price: 25000, quantity: 2 }
                ],
                status: 'completed'
            })
        });

        if (transactionResponse.ok) {
            const transactionData = await transactionResponse.json();
            console.log('✅ Transaction created successfully');
            console.log(`📄 Transaction ID: ${transactionData.data.id}`);
        } else {
            const errorData = await transactionResponse.json();
            console.error('❌ Transaction creation failed:', errorData.message);
        }
    } catch (error) {
        console.error('❌ Transaction creation error:', error.message);
    }

    // Step 4: Check wallet balance after transaction
    console.log('\n4. Checking wallet balance after transaction...');
    try {
        const walletResponse = await fetch(`${API_BASE_URL}/wallet`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (walletResponse.ok) {
            const walletData = await walletResponse.json();
            const newBalance = parseFloat(walletData.data.balance);
            const expectedBalance = initialBalance + testAmount;

            console.log(`💰 New wallet balance: ${newBalance}`);
            console.log(`📊 Expected balance: ${expectedBalance}`);
            console.log(`💵 Amount added: ${newBalance - initialBalance}`);

            if (Math.abs(newBalance - expectedBalance) < 0.01) {
                console.log('✅ Wallet balance updated correctly!');
            } else {
                console.log('❌ Wallet balance mismatch!');
            }
        }
    } catch (error) {
        console.error('❌ Final wallet check error:', error.message);
    }

    // Step 5: Test manual payment processing
    console.log('\n5. Testing manual payment processing...');
    const manualAmount = 25000;
    const manualOrderId = `MANUAL-${Date.now()}`;

    try {
        const manualResponse = await fetch(`${API_BASE_URL}/payment/process-manual`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                order_id: manualOrderId,
                amount: manualAmount,
                description: 'Manual test payment'
            })
        });

        if (manualResponse.ok) {
            const manualData = await manualResponse.json();
            console.log('✅ Manual payment processed successfully');
            console.log(`💰 New balance: ${manualData.data.new_balance}`);
        } else {
            const errorData = await manualResponse.json();
            console.error('❌ Manual payment failed:', errorData.message);
        }
    } catch (error) {
        console.error('❌ Manual payment error:', error.message);
    }

    // Step 6: Check dashboard stats
    console.log('\n6. Checking dashboard stats...');
    try {
        const statsResponse = await fetch(`${API_BASE_URL}/dashboard/stats`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (statsResponse.ok) {
            const statsData = await statsResponse.json();
            console.log('✅ Dashboard stats retrieved');
            console.log(`📊 Total transactions: ${statsData.data.total_transactions}`);
            console.log(`💰 Total revenue: ${statsData.data.total_revenue}`);
            console.log(`💼 Wallet balance: ${statsData.data.wallet_balance}`);
            console.log(`💸 Total savings: ${statsData.data.total_savings}`);
        }
    } catch (error) {
        console.error('❌ Dashboard stats error:', error.message);
    }

    // Step 7: Check recent activities
    console.log('\n7. Checking recent activities...');
    try {
        const activitiesResponse = await fetch(`${API_BASE_URL}/activities?limit=5`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (activitiesResponse.ok) {
            const activitiesData = await activitiesResponse.json();
            console.log('✅ Recent activities retrieved');
            activitiesData.data.forEach((activity, index) => {
                console.log(`   ${index + 1}. ${activity.activity_type}: ${activity.amount} - ${activity.description}`);
            });
        }
    } catch (error) {
        console.error('❌ Activities check error:', error.message);
    }

    console.log('\n🎉 Payment and wallet integration test completed!');
}

// Run the test
if (require.main === module) {
    testPaymentWalletIntegration().catch(console.error);
}

module.exports = { testPaymentWalletIntegration };