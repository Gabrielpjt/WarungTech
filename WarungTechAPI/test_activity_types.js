// Test script to verify activity types work correctly
const { Pool } = require('pg');

// Same constants as in server.js
const ACTIVITY_TYPES = {
    PAYMENT: 'payment',
    TOPUP: 'topup',
    WITHDRAW: 'withdraw',
    INVEST_BUY: 'invest_buy',
    INVEST_SELL: 'invest_sell',
    TRANSACTION: 'transaction'
};

// Helper function (same as in server.js)
const logActivity = async (client, userId, activityType, amount, description) => {
    try {
        await client.query(
            `INSERT INTO activity_logs (user_id, activity_type, amount, description)
       VALUES ($1, $2, $3, $4)`,
            [userId, activityType, amount, description]
        );
        console.log(`✅ Successfully logged activity: ${activityType}`);
        return true;
    } catch (error) {
        console.error(`❌ Failed to log activity ${activityType}:`, error.message);
        return false;
    }
};

async function testActivityTypes() {
    const pool = new Pool({
        host: process.env.DB_HOST || 'aws-1-ap-northeast-1.pooler.supabase.com',
        port: process.env.DB_PORT || 5432,
        database: process.env.DB_NAME || 'postgres',
        user: process.env.DB_USER || 'postgres.nzvkyxpgsegkpewhyqlc',
        pool_mode: 'session',
        password: process.env.DB_PASSWORD || 'PantangMenyerah123!',
    });

    const client = await pool.connect();

    try {
        console.log('🧪 Testing all activity types...\n');

        // Test user ID (use 1 or create a test user)
        const testUserId = 1;

        // Test each activity type
        const results = {};

        for (const [key, value] of Object.entries(ACTIVITY_TYPES)) {
            console.log(`Testing ${key} (${value})...`);
            const success = await logActivity(
                client,
                testUserId,
                value,
                100.00,
                `Test ${key} activity`
            );
            results[key] = success;
        }

        console.log('\n📊 Test Results:');
        console.log('================');

        let allPassed = true;
        for (const [key, success] of Object.entries(results)) {
            const status = success ? '✅ PASS' : '❌ FAIL';
            console.log(`${key}: ${status}`);
            if (!success) allPassed = false;
        }

        console.log('\n' + (allPassed ? '🎉 All tests passed!' : '⚠️  Some tests failed - check database enum constraints'));

        // Clean up test data
        await client.query(
            'DELETE FROM activity_logs WHERE user_id = $1 AND description LIKE $2',
            [testUserId, 'Test % activity']
        );
        console.log('🧹 Cleaned up test data');

    } catch (error) {
        console.error('❌ Test failed:', error.message);
    } finally {
        client.release();
        await pool.end();
    }
}

// Run tests
if (require.main === module) {
    testActivityTypes().catch(console.error);
}

module.exports = { ACTIVITY_TYPES, logActivity, testActivityTypes };