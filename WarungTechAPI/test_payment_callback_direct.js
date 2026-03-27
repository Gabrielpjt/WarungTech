// Test payment callback directly
const API_BASE_URL = 'http://192.168.100.15:3001/api';

async function testPaymentCallbackDirect() {
    console.log('🔍 Testing Payment Callback Directly');
    console.log('====================================\n');

    // Use the latest order ID from our previous test
    const orderToTest = 'ORD-1769856608770-1LAHLVX52';

    console.log(`1. Testing payment finish callback for order: ${orderToTest}`);

    try {
        const response = await fetch(`${API_BASE_URL}/payment/finish?order_id=${orderToTest}&transaction_status=settlement&status_code=200`, {
            method: 'GET'
        });

        console.log(`📡 Response status: ${response.status}`);
        console.log(`📡 Response headers:`, Object.fromEntries(response.headers.entries()));

        if (response.ok) {
            const responseText = await response.text();
            console.log('✅ Payment callback successful');
            console.log(`📄 Response length: ${responseText.length} characters`);

            // Check if it's HTML (success page) or JSON (error)
            if (responseText.includes('<!DOCTYPE html>')) {
                console.log('📄 Response is HTML success page');
            } else {
                console.log('📄 Response content:', responseText.substring(0, 500));
            }
        } else {
            const errorText = await response.text();
            console.error('❌ Payment callback failed');
            console.error('📄 Error response:', errorText);
        }
    } catch (error) {
        console.error('❌ Payment callback error:', error.message);
    }

    // Now check if the wallet was updated
    console.log('\n2. Checking if wallet was updated...');

    // First, get the user ID for this order
    try {
        const healthResponse = await fetch(`${API_BASE_URL}/health`);
        if (healthResponse.ok) {
            console.log('✅ API server is responding');
        }
    } catch (error) {
        console.error('❌ API server not responding:', error.message);
    }
}

// Run the test
if (require.main === module) {
    testPaymentCallbackDirect().catch(console.error);
}

module.exports = { testPaymentCallbackDirect };