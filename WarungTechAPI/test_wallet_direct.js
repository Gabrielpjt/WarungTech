// Direct test of wallet update functionality
const { Pool } = require('pg');

const pool = new Pool({
    host: process.env.DB_HOST || 'aws-1-ap-northeast-1.pooler.supabase.com',
    port: process.env.DB_PORT || 5432,
    database: process.env.DB_NAME || 'postgres',
    user: process.env.DB_USER || 'postgres.nzvkyxpgsegkpewhyqlc',
    pool_mode: 'session',
    password: process.env.DB_PASSWORD || 'PantangMenyerah123!',
});

// Helper function to safely update wallet balance
const updateWalletBalance = async (client, userId, amount, description) => {
    try {
        console.log(`💰 Updating wallet for user ${userId}, adding ${amount}`);

        // Try to update existing wallet
        const walletUpdateResult = await client.query(
            `UPDATE wallets 
       SET balance = balance + $1, updated_at = CURRENT_TIMESTAMP
       WHERE user_id = $2
       RETURNING balance`,
            [amount, userId]
        );

        if (walletUpdateResult.rows.length === 0) {
            // Create wallet if it doesn't exist
            const newWalletResult = await client.query(
                'INSERT INTO wallets (user_id, balance) VALUES ($1, $2) RETURNING balance',
                [userId, amount]
            );
            console.log(`✅ Created new wallet for user ${userId} with balance ${amount}`);
            return newWalletResult.rows[0].balance;
        } else {
            const newBalance = walletUpdateResult.rows[0].balance;
            console.log(`✅ Updated wallet for user ${userId}, new balance: ${newBalance}`);
            return newBalance;
        }
    } catch (error) {
        console.error('Failed to update wallet:', error.message);
        throw error; // Re-throw wallet errors as they're critical
    }
};

async function testWalletDirect() {
    console.log('🔍 Direct Wallet Update Test');
    console.log('============================\n');

    const client = await pool.connect();
    try {
        await client.query('BEGIN');

        // Step 1: Find a user to test with
        console.log('1. Finding a test user...');
        const userResult = await client.query('SELECT id, email FROM users ORDER BY id DESC LIMIT 1');

        if (userResult.rows.length === 0) {
            console.log('❌ No users found in database');
            return;
        }

        const testUser = userResult.rows[0];
        console.log(`✅ Using user: ${testUser.email} (ID: ${testUser.id})`);

        // Step 2: Check current wallet balance
        console.log('\n2. Checking current wallet balance...');
        const walletResult = await client.query('SELECT balance FROM wallets WHERE user_id = $1', [testUser.id]);

        let currentBalance = 0;
        if (walletResult.rows.length > 0) {
            currentBalance = parseFloat(walletResult.rows[0].balance);
            console.log(`💰 Current balance: Rp ${currentBalance.toLocaleString('id-ID')}`);
        } else {
            console.log('💰 No wallet found, will create new one');
        }

        // Step 3: Test wallet update
        console.log('\n3. Testing wallet update...');
        const testAmount = 50000;

        try {
            const newBalance = await updateWalletBalance(
                client,
                testUser.id,
                testAmount,
                'Direct test payment'
            );

            console.log(`✅ Wallet update successful!`);
            console.log(`💰 New balance: Rp ${newBalance.toLocaleString('id-ID')}`);
            console.log(`💵 Amount added: Rp ${testAmount.toLocaleString('id-ID')}`);

            // Verify the update
            const verifyResult = await client.query('SELECT balance FROM wallets WHERE user_id = $1', [testUser.id]);
            if (verifyResult.rows.length > 0) {
                const verifiedBalance = parseFloat(verifyResult.rows[0].balance);
                console.log(`🔍 Verified balance: Rp ${verifiedBalance.toLocaleString('id-ID')}`);

                if (Math.abs(verifiedBalance - newBalance) < 0.01) {
                    console.log('✅ Balance verification successful!');
                } else {
                    console.log('❌ Balance verification failed!');
                }
            }

        } catch (error) {
            console.error('❌ Wallet update failed:', error.message);
        }

        // Step 4: Check wallet table structure
        console.log('\n4. Checking wallet table structure...');
        const tableInfoResult = await client.query(`
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'wallets' 
            ORDER BY ordinal_position
        `);

        console.log('📋 Wallet table columns:');
        tableInfoResult.rows.forEach(col => {
            console.log(`   - ${col.column_name}: ${col.data_type} (nullable: ${col.is_nullable})`);
        });

        // Step 5: Check all wallets
        console.log('\n5. Checking all wallets in database...');
        const allWalletsResult = await client.query('SELECT user_id, balance, created_at, updated_at FROM wallets ORDER BY user_id');

        if (allWalletsResult.rows.length === 0) {
            console.log('📭 No wallets found in database');
        } else {
            console.log('💼 All wallets:');
            allWalletsResult.rows.forEach(wallet => {
                console.log(`   User ${wallet.user_id}: Rp ${parseFloat(wallet.balance).toLocaleString('id-ID')} (updated: ${wallet.updated_at})`);
            });
        }

        await client.query('COMMIT');
        console.log('\n✅ Direct wallet test completed successfully!');

    } catch (error) {
        await client.query('ROLLBACK');
        console.error('❌ Direct wallet test failed:', error.message);
    } finally {
        client.release();
    }
}

// Run the test
if (require.main === module) {
    testWalletDirect().catch(console.error).finally(() => {
        pool.end();
    });
}

module.exports = { testWalletDirect };