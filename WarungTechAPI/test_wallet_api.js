// Test wallet API directly
const API_BASE_URL = 'http://192.168.100.15:3001/api';

async function testWalletAPI() {
    console.log('🔍 Testing Wallet API');
    console.log('=====================\n');

    // Login as user 8 (the user we know has Rp 100,000 in wallet)
    console.log('1. Finding user 8 credentials...');

    // We need to find user 8's email from our previous test
    // Let's try to login with the latest test user
    const testEmail = 'test1769856606786@wartech.com'; // User 8 from our test
    const testPassword = 'password123';
    let token = null;

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
            console.log(`👤 User ID from token: ${loginData.data?.user?.id || 'unknown'}`);
        } else {
            const errorData = await loginResponse.json();
            console.error('❌ Login failed:', errorData.message);
            return;
        }
    } catch (error) {
        console.error('❌ Login error:', error.message);
        return;
    }

    // Test wallet API
    console.log('\n2. Testing wallet API...');
    try {
        const walletResponse = await fetch(`${API_BASE_URL}/wallet`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (walletResponse.ok) {
            const walletData = await walletResponse.json();
            console.log('✅ Wallet API successful');
            console.log('💰 Wallet data:', walletData.data);
            console.log(`💰 Balance: Rp ${parseFloat(walletData.data.balance).toLocaleString('id-ID')}`);
            console.log(`👤 User ID: ${walletData.data.user_id}`);
        } else {
            const errorData = await walletResponse.json();
            console.error('❌ Wallet API failed:', errorData.message);
        }
    } catch (error) {
        console.error('❌ Wallet API error:', error.message);
    }

    // Test dashboard stats API
    console.log('\n3. Testing dashboard stats API...');
    try {
        const statsResponse = await fetch(`${API_BASE_URL}/dashboard/stats`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (statsResponse.ok) {
            const statsData = await statsResponse.json();
            console.log('✅ Dashboard stats successful');
            console.log(`💰 Wallet balance from stats: Rp ${(statsData.data.wallet_balance || 0).toLocaleString('id-ID')}`);
            console.log(`💰 Total revenue: Rp ${(statsData.data.total_revenue || 0).toLocaleString('id-ID')}`);
            console.log(`📊 Total transactions: ${statsData.data.total_transactions || 0}`);
        } else {
            const errorData = await statsResponse.json();
            console.error('❌ Dashboard stats failed:', errorData.message);
        }
    } catch (error) {
        console.error('❌ Dashboard stats error:', error.message);
    }
}

// Run the test
if (require.main === module) {
    testWalletAPI().catch(console.error);
}

module.exports = { testWalletAPI };