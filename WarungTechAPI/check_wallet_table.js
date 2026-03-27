// Check wallet table directly
const { Pool } = require('pg');

const pool = new Pool({
    host: process.env.DB_HOST || 'aws-1-ap-northeast-1.pooler.supabase.com',
    port: process.env.DB_PORT || 5432,
    database: process.env.DB_NAME || 'postgres',
    user: process.env.DB_USER || 'postgres.nzvkyxpgsegkpewhyqlc',
    pool_mode: 'session',
    password: process.env.DB_PASSWORD || 'PantangMenyerah123!',
});

async function checkWalletTable() {
    console.log('🔍 Checking Wallet Table');
    console.log('========================\n');

    const client = await pool.connect();
    try {
        // Check all wallets
        console.log('1. Checking all wallets...');
        const allWalletsResult = await client.query('SELECT * FROM wallets ORDER BY user_id');

        if (allWalletsResult.rows.length === 0) {
            console.log('📭 No wallets found in database');
        } else {
            console.log('💼 All wallets:');
            allWalletsResult.rows.forEach(wallet => {
                console.log(`   User ${wallet.user_id}: Rp ${parseFloat(wallet.balance).toLocaleString('id-ID')} (ID: ${wallet.id})`);
            });
        }

        // Check if user 8 has a wallet
        console.log('\n2. Checking specifically for user 8...');
        const user8WalletResult = await client.query('SELECT * FROM wallets WHERE user_id = 8');

        if (user8WalletResult.rows.length === 0) {
            console.log('❌ User 8 has no wallet record');
            console.log('🔍 This explains why the UPDATE query returns 0 rows');
            console.log('💡 The updateWalletBalance function should create a new wallet');
        } else {
            console.log('✅ User 8 wallet found:');
            const wallet = user8WalletResult.rows[0];
            console.log(`   Balance: Rp ${parseFloat(wallet.balance).toLocaleString('id-ID')}`);
            console.log(`   Wallet ID: ${wallet.id}`);
        }

        // Test creating a wallet for user 8
        console.log('\n3. Testing wallet creation for user 8...');
        try {
            await client.query('BEGIN');

            // Try to create wallet
            const createResult = await client.query(
                'INSERT INTO wallets (user_id, balance) VALUES ($1, $2) RETURNING *',
                [8, 100000]
            );

            console.log('✅ Wallet creation successful:');
            console.log(`   New wallet ID: ${createResult.rows[0].id}`);
            console.log(`   Balance: Rp ${parseFloat(createResult.rows[0].balance).toLocaleString('id-ID')}`);

            await client.query('ROLLBACK'); // Don't actually save it
            console.log('🔄 Transaction rolled back (test only)');

        } catch (error) {
            await client.query('ROLLBACK');
            console.error('❌ Wallet creation failed:', error.message);
        }

        // Check wallet table structure
        console.log('\n4. Checking wallet table structure...');
        const tableInfoResult = await client.query(`
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'wallets' 
            ORDER BY ordinal_position
        `);

        console.log('📋 Wallet table columns:');
        tableInfoResult.rows.forEach(col => {
            console.log(`   - ${col.column_name}: ${col.data_type} (nullable: ${col.is_nullable}, default: ${col.column_default})`);
        });

    } catch (error) {
        console.error('❌ Check failed:', error.message);
    } finally {
        client.release();
    }
}

// Run the check
if (require.main === module) {
    checkWalletTable().catch(console.error).finally(() => {
        pool.end();
    });
}

module.exports = { checkWalletTable };