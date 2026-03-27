// Debug User 1 wallet issue specifically
const { Pool } = require('pg');

const pool = new Pool({
    host: process.env.DB_HOST || 'aws-1-ap-northeast-1.pooler.supabase.com',
    port: process.env.DB_PORT || 5432,
    database: process.env.DB_NAME || 'postgres',
    user: process.env.DB_USER || 'postgres.nzvkyxpgsegkpewhyqlc',
    pool_mode: 'session',
    password: process.env.DB_PASSWORD || 'PantangMenyerah123!',
});

async function debugUser1Wallet() {
    console.log('🔍 Debug User 1 Wallet Issue');
    console.log('============================\n');

    const client = await pool.connect();
    try {
        // Step 1: Check User 1's transaction history
        console.log('1. Checking User 1 transaction history...');
        const transactionResult = await client.query(`
            SELECT th.id, th.order_id, th.midtrans_order_id, th.total_amount, 
                   th.discount_amount, th.status, th.created_at
            FROM transaction_histories th
            WHERE th.user_id = 1
            ORDER BY th.created_at DESC
        `);

        if (transactionResult.rows.length === 0) {
            console.log('📭 No transaction history found for User 1');
        } else {
            console.log(`📋 Found ${transactionResult.rows.length} transactions for User 1:`);
            let totalExpected = 0;
            transactionResult.rows.forEach((tx, index) => {
                const amount = parseFloat(tx.total_amount);
                totalExpected += amount;
                console.log(`   ${index + 1}. Order: ${tx.order_id || tx.midtrans_order_id}`);
                console.log(`      Amount: Rp ${amount.toLocaleString('id-ID')}`);
                console.log(`      Status: ${tx.status}`);
                console.log(`      Date: ${tx.created_at}`);
                console.log('      ---');
            });
            console.log(`💰 Total expected wallet balance: Rp ${totalExpected.toLocaleString('id-ID')}`);
        }

        // Step 2: Check User 1's orders table
        console.log('\n2. Checking User 1 orders...');
        const ordersResult = await client.query(`
            SELECT o.id, o.midtrans_order_id, o.total_amount, o.payment_status, 
                   o.created_at, s.store_name, s.user_id as store_owner_id
            FROM orders o
            LEFT JOIN stores s ON o.store_id = s.id
            WHERE s.user_id = 1 OR o.midtrans_order_id IN (
                SELECT midtrans_order_id FROM transaction_histories WHERE user_id = 1
            )
            ORDER BY o.created_at DESC
        `);

        if (ordersResult.rows.length === 0) {
            console.log('📭 No orders found for User 1');
        } else {
            console.log(`📦 Found ${ordersResult.rows.length} orders related to User 1:`);
            ordersResult.rows.forEach((order, index) => {
                console.log(`   ${index + 1}. Order: ${order.midtrans_order_id}`);
                console.log(`      Amount: Rp ${parseFloat(order.total_amount).toLocaleString('id-ID')}`);
                console.log(`      Payment Status: ${order.payment_status}`);
                console.log(`      Store Owner: ${order.store_owner_id}`);
                console.log(`      Store: ${order.store_name || 'Unknown'}`);
                console.log('      ---');
            });
        }

        // Step 3: Check User 1's wallet
        console.log('\n3. Checking User 1 wallet...');
        const walletResult = await client.query('SELECT * FROM wallets WHERE user_id = 1');

        if (walletResult.rows.length === 0) {
            console.log('❌ User 1 has no wallet record');
        } else {
            const wallet = walletResult.rows[0];
            console.log('💰 User 1 wallet:');
            console.log(`   Balance: Rp ${parseFloat(wallet.balance).toLocaleString('id-ID')}`);
            console.log(`   Updated: ${wallet.updated_at}`);
        }

        // Step 4: Check financial records for User 1
        console.log('\n4. Checking User 1 financial records...');
        const financialResult = await client.query(`
            SELECT type, amount, description, created_at, reference_id
            FROM financial_records 
            WHERE user_id = 1 
            ORDER BY created_at DESC
        `);

        if (financialResult.rows.length === 0) {
            console.log('📊 No financial records found for User 1');
        } else {
            console.log(`📊 Found ${financialResult.rows.length} financial records:`);
            financialResult.rows.forEach((record, index) => {
                console.log(`   ${index + 1}. ${record.type}: Rp ${parseFloat(record.amount).toLocaleString('id-ID')}`);
                console.log(`      Description: ${record.description}`);
                console.log(`      Date: ${record.created_at}`);
                console.log('      ---');
            });
        }

        // Step 5: Check activity logs for User 1
        console.log('\n5. Checking User 1 activity logs...');
        const activityResult = await client.query(`
            SELECT activity_type, amount, description, created_at
            FROM activity_logs 
            WHERE user_id = 1 
            ORDER BY created_at DESC
        `);

        if (activityResult.rows.length === 0) {
            console.log('📝 No activity logs found for User 1');
            console.log('🔍 This suggests payment callbacks did NOT process for User 1');
        } else {
            console.log(`📝 Found ${activityResult.rows.length} activity logs:`);
            activityResult.rows.forEach((activity, index) => {
                console.log(`   ${index + 1}. ${activity.activity_type}: Rp ${parseFloat(activity.amount).toLocaleString('id-ID')}`);
                console.log(`      Description: ${activity.description}`);
                console.log(`      Date: ${activity.created_at}`);
                console.log('      ---');
            });
        }

        // Step 6: Check if there's a mismatch between transaction_histories and orders
        console.log('\n6. Analyzing transaction vs order mismatch...');

        if (transactionResult.rows.length > 0) {
            console.log('🔍 Checking if transaction_histories orders exist in orders table...');

            for (const tx of transactionResult.rows) {
                const orderCheck = await client.query(
                    'SELECT id, payment_status FROM orders WHERE midtrans_order_id = $1',
                    [tx.order_id || tx.midtrans_order_id]
                );

                if (orderCheck.rows.length === 0) {
                    console.log(`❌ Transaction ${tx.order_id || tx.midtrans_order_id} NOT found in orders table`);
                    console.log('   This explains why payment callback didn\'t work!');
                } else {
                    console.log(`✅ Transaction ${tx.order_id || tx.midtrans_order_id} found in orders table`);
                    console.log(`   Payment status: ${orderCheck.rows[0].payment_status}`);
                }
            }
        }

        // Step 7: Manual wallet fix for User 1
        console.log('\n7. Calculating correct wallet balance for User 1...');

        if (transactionResult.rows.length > 0) {
            const totalAmount = transactionResult.rows
                .filter(tx => tx.status === 'completed')
                .reduce((sum, tx) => sum + parseFloat(tx.total_amount), 0);

            console.log(`💰 Total amount from completed transactions: Rp ${totalAmount.toLocaleString('id-ID')}`);

            if (totalAmount > 0) {
                console.log('\n8. Fixing User 1 wallet balance...');
                try {
                    await client.query('BEGIN');

                    // Update wallet balance
                    const updateResult = await client.query(
                        'UPDATE wallets SET balance = $1 WHERE user_id = 1 RETURNING balance',
                        [totalAmount]
                    );

                    if (updateResult.rows.length > 0) {
                        console.log(`✅ Updated User 1 wallet balance to: Rp ${parseFloat(updateResult.rows[0].balance).toLocaleString('id-ID')}`);

                        // Add financial records for the missing transactions
                        for (const tx of transactionResult.rows.filter(t => t.status === 'completed')) {
                            await client.query(
                                `INSERT INTO financial_records (user_id, type, amount, description, reference_id)
                                 VALUES ($1, 'income', $2, $3, $4)`,
                                [1, tx.total_amount, `Retroactive payment for transaction ${tx.order_id || tx.midtrans_order_id}`, tx.id]
                            );

                            await client.query(
                                `INSERT INTO activity_logs (user_id, activity_type, amount, description)
                                 VALUES ($1, 'payment', $2, $3)`,
                                [1, tx.total_amount, `Retroactive payment for transaction ${tx.order_id || tx.midtrans_order_id}`]
                            );
                        }

                        console.log('✅ Added missing financial records and activity logs');

                        await client.query('COMMIT');
                        console.log('✅ User 1 wallet fix completed successfully!');

                    } else {
                        console.log('❌ Failed to update User 1 wallet');
                        await client.query('ROLLBACK');
                    }

                } catch (error) {
                    await client.query('ROLLBACK');
                    console.error('❌ Wallet fix failed:', error.message);
                }
            }
        }

    } catch (error) {
        console.error('❌ Debug failed:', error.message);
    } finally {
        client.release();
    }
}

// Run the debug
if (require.main === module) {
    debugUser1Wallet().catch(console.error).finally(() => {
        pool.end();
    });
}

module.exports = { debugUser1Wallet };