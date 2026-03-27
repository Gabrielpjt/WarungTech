// Debug payment callback issue
const { Pool } = require('pg');

const pool = new Pool({
    host: process.env.DB_HOST || 'aws-1-ap-northeast-1.pooler.supabase.com',
    port: process.env.DB_PORT || 5432,
    database: process.env.DB_NAME || 'postgres',
    user: process.env.DB_USER || 'postgres.nzvkyxpgsegkpewhyqlc',
    pool_mode: 'session',
    password: process.env.DB_PASSWORD || 'PantangMenyerah123!',
});

async function debugPaymentCallback() {
    console.log('🔍 Debug Payment Callback Issue');
    console.log('===============================\n');

    const client = await pool.connect();
    try {
        // Step 1: Check recent orders
        console.log('1. Checking recent orders...');
        const ordersResult = await client.query(`
            SELECT o.id, o.midtrans_order_id, o.total_amount, o.payment_status, 
                   s.user_id, s.store_name, o.created_at
            FROM orders o
            JOIN stores s ON o.store_id = s.id
            ORDER BY o.created_at DESC
            LIMIT 5
        `);

        if (ordersResult.rows.length === 0) {
            console.log('📭 No orders found in database');
            return;
        }

        console.log('📦 Recent orders:');
        ordersResult.rows.forEach(order => {
            console.log(`   Order ID: ${order.midtrans_order_id}`);
            console.log(`   Amount: Rp ${parseFloat(order.total_amount).toLocaleString('id-ID')}`);
            console.log(`   Status: ${order.payment_status}`);
            console.log(`   User ID: ${order.user_id}`);
            console.log(`   Store: ${order.store_name}`);
            console.log(`   Created: ${order.created_at}`);
            console.log('   ---');
        });

        // Step 2: Test the exact query used in payment callback
        const latestOrder = ordersResult.rows[0];
        console.log(`\n2. Testing payment callback query for order: ${latestOrder.midtrans_order_id}`);

        const callbackQueryResult = await client.query(
            `SELECT o.id, o.total_amount, s.user_id, s.store_name
             FROM orders o
             JOIN stores s ON o.store_id = s.id
             WHERE o.midtrans_order_id = $1`,
            [latestOrder.midtrans_order_id]
        );

        if (callbackQueryResult.rows.length === 0) {
            console.log('❌ Payment callback query returned no results!');
            console.log('   This explains why wallet is not updated');
        } else {
            const order = callbackQueryResult.rows[0];
            console.log('✅ Payment callback query successful:');
            console.log(`   Order ID: ${order.id}`);
            console.log(`   Amount: Rp ${parseFloat(order.total_amount).toLocaleString('id-ID')}`);
            console.log(`   User ID: ${order.user_id}`);
            console.log(`   Store: ${order.store_name}`);
        }

        // Step 3: Check wallet for the user
        console.log(`\n3. Checking wallet for user ${latestOrder.user_id}...`);
        const walletResult = await client.query('SELECT balance FROM wallets WHERE user_id = $1', [latestOrder.user_id]);

        if (walletResult.rows.length === 0) {
            console.log('💰 No wallet found for this user');
        } else {
            const balance = parseFloat(walletResult.rows[0].balance);
            console.log(`💰 Current wallet balance: Rp ${balance.toLocaleString('id-ID')}`);
        }

        // Step 4: Check financial records
        console.log(`\n4. Checking financial records for user ${latestOrder.user_id}...`);
        const financialResult = await client.query(
            'SELECT type, amount, description, created_at FROM financial_records WHERE user_id = $1 ORDER BY created_at DESC LIMIT 5',
            [latestOrder.user_id]
        );

        if (financialResult.rows.length === 0) {
            console.log('📊 No financial records found for this user');
        } else {
            console.log('📊 Recent financial records:');
            financialResult.rows.forEach(record => {
                console.log(`   ${record.type}: Rp ${parseFloat(record.amount).toLocaleString('id-ID')} - ${record.description}`);
            });
        }

        // Step 5: Check activity logs
        console.log(`\n5. Checking activity logs for user ${latestOrder.user_id}...`);
        const activityResult = await client.query(
            'SELECT activity_type, amount, description, created_at FROM activity_logs WHERE user_id = $1 ORDER BY created_at DESC LIMIT 5',
            [latestOrder.user_id]
        );

        if (activityResult.rows.length === 0) {
            console.log('📝 No activity logs found for this user');
        } else {
            console.log('📝 Recent activity logs:');
            activityResult.rows.forEach(activity => {
                console.log(`   ${activity.activity_type}: Rp ${parseFloat(activity.amount).toLocaleString('id-ID')} - ${activity.description}`);
            });
        }

        // Step 6: Simulate the payment callback manually
        console.log(`\n6. Manually simulating payment callback for order: ${latestOrder.midtrans_order_id}`);

        try {
            await client.query('BEGIN');

            // Update order status
            const updateResult = await client.query(
                `UPDATE orders 
                 SET payment_status = 'paid', updated_at = CURRENT_TIMESTAMP
                 WHERE midtrans_order_id = $1`,
                [latestOrder.midtrans_order_id]
            );
            console.log(`✅ Updated order status (${updateResult.rowCount} rows affected)`);

            // Get order details
            const orderResult = await client.query(
                `SELECT o.id, o.total_amount, s.user_id, s.store_name
                 FROM orders o
                 JOIN stores s ON o.store_id = s.id
                 WHERE o.midtrans_order_id = $1`,
                [latestOrder.midtrans_order_id]
            );

            if (orderResult.rows.length > 0) {
                const order = orderResult.rows[0];
                console.log(`💰 Processing payment for user ${order.user_id}, amount: ${order.total_amount}`);

                // Update wallet balance
                const walletUpdateResult = await client.query(
                    `UPDATE wallets 
                     SET balance = balance + $1, updated_at = CURRENT_TIMESTAMP
                     WHERE user_id = $2
                     RETURNING balance`,
                    [order.total_amount, order.user_id]
                );

                if (walletUpdateResult.rows.length === 0) {
                    // Create wallet if it doesn't exist
                    const newWalletResult = await client.query(
                        'INSERT INTO wallets (user_id, balance) VALUES ($1, $2) RETURNING balance',
                        [order.user_id, order.total_amount]
                    );
                    console.log(`✅ Created new wallet with balance: Rp ${parseFloat(newWalletResult.rows[0].balance).toLocaleString('id-ID')}`);
                } else {
                    const newBalance = walletUpdateResult.rows[0].balance;
                    console.log(`✅ Updated wallet, new balance: Rp ${parseFloat(newBalance).toLocaleString('id-ID')}`);
                }

                // Record financial record
                await client.query(
                    `INSERT INTO financial_records (user_id, type, amount, description, reference_id)
                     VALUES ($1, 'income', $2, $3, $4)`,
                    [order.user_id, order.total_amount, `Payment received for order ${latestOrder.midtrans_order_id} from ${order.store_name}`, order.id]
                );
                console.log('✅ Financial record created');

                // Log activity
                await client.query(
                    `INSERT INTO activity_logs (user_id, activity_type, amount, description)
                     VALUES ($1, $2, $3, $4)`,
                    [order.user_id, 'payment', order.total_amount, `Payment received for order ${latestOrder.midtrans_order_id} - Added to wallet`]
                );
                console.log('✅ Activity logged');

            } else {
                console.log('❌ Order not found in callback query');
            }

            await client.query('COMMIT');
            console.log('✅ Manual payment callback simulation completed');

        } catch (error) {
            await client.query('ROLLBACK');
            console.error('❌ Manual payment callback failed:', error.message);
        }

    } catch (error) {
        console.error('❌ Debug failed:', error.message);
    } finally {
        client.release();
    }
}

// Run the debug
if (require.main === module) {
    debugPaymentCallback().catch(console.error).finally(() => {
        pool.end();
    });
}

module.exports = { debugPaymentCallback };