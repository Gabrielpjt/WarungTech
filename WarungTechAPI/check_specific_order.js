// Check specific order issue
const { Pool } = require('pg');

const pool = new Pool({
    host: process.env.DB_HOST || 'aws-1-ap-northeast-1.pooler.supabase.com',
    port: process.env.DB_PORT || 5432,
    database: process.env.DB_NAME || 'postgres',
    user: process.env.DB_USER || 'postgres.nzvkyxpgsegkpewhyqlc',
    pool_mode: 'session',
    password: process.env.DB_PASSWORD || 'PantangMenyerah123!',
});

async function checkSpecificOrder() {
    console.log('🔍 Checking Specific Order Issue');
    console.log('================================\n');

    const client = await pool.connect();
    try {
        // Check the specific order we created
        const orderToCheck = 'ORD-1769856608770-1LAHLVX52';

        console.log(`1. Checking order: ${orderToCheck}`);
        const orderResult = await client.query(
            `SELECT o.id, o.midtrans_order_id, o.total_amount, o.payment_status, 
                    s.user_id, s.store_name, o.created_at
             FROM orders o
             JOIN stores s ON o.store_id = s.id
             WHERE o.midtrans_order_id = $1`,
            [orderToCheck]
        );

        if (orderResult.rows.length === 0) {
            console.log('❌ Order not found!');
            return;
        }

        const order = orderResult.rows[0];
        console.log('✅ Order found:');
        console.log(`   Order ID: ${order.midtrans_order_id}`);
        console.log(`   Amount: Rp ${parseFloat(order.total_amount).toLocaleString('id-ID')}`);
        console.log(`   Status: ${order.payment_status}`);
        console.log(`   User ID: ${order.user_id}`);
        console.log(`   Store: ${order.store_name}`);

        // Check wallet for this user
        console.log(`\n2. Checking wallet for user ${order.user_id}...`);
        const walletResult = await client.query('SELECT balance FROM wallets WHERE user_id = $1', [order.user_id]);

        if (walletResult.rows.length === 0) {
            console.log('💰 No wallet found for this user');
        } else {
            const balance = parseFloat(walletResult.rows[0].balance);
            console.log(`💰 Current wallet balance: Rp ${balance.toLocaleString('id-ID')}`);
        }

        // Check if there are any financial records for this order
        console.log(`\n3. Checking financial records for this order...`);
        const financialResult = await client.query(
            `SELECT type, amount, description, created_at 
             FROM financial_records 
             WHERE user_id = $1 AND description LIKE $2
             ORDER BY created_at DESC`,
            [order.user_id, `%${orderToCheck}%`]
        );

        if (financialResult.rows.length === 0) {
            console.log('📊 No financial records found for this order');
        } else {
            console.log('📊 Financial records for this order:');
            financialResult.rows.forEach(record => {
                console.log(`   ${record.type}: Rp ${parseFloat(record.amount).toLocaleString('id-ID')} - ${record.description}`);
            });
        }

        // Check activity logs for this order
        console.log(`\n4. Checking activity logs for this order...`);
        const activityResult = await client.query(
            `SELECT activity_type, amount, description, created_at 
             FROM activity_logs 
             WHERE user_id = $1 AND description LIKE $2
             ORDER BY created_at DESC`,
            [order.user_id, `%${orderToCheck}%`]
        );

        if (activityResult.rows.length === 0) {
            console.log('📝 No activity logs found for this order');
            console.log('🔍 This suggests the payment callback did not process correctly');
        } else {
            console.log('📝 Activity logs for this order:');
            activityResult.rows.forEach(activity => {
                console.log(`   ${activity.activity_type}: Rp ${parseFloat(activity.amount).toLocaleString('id-ID')} - ${activity.description}`);
            });
        }

        // Now let's manually process this payment
        console.log(`\n5. Manually processing payment for order: ${orderToCheck}`);

        try {
            await client.query('BEGIN');

            // Check current wallet balance
            const currentWalletResult = await client.query('SELECT balance FROM wallets WHERE user_id = $1', [order.user_id]);
            let currentBalance = 0;
            if (currentWalletResult.rows.length > 0) {
                currentBalance = parseFloat(currentWalletResult.rows[0].balance);
            }
            console.log(`💰 Current balance before update: Rp ${currentBalance.toLocaleString('id-ID')}`);

            // Update wallet balance
            const walletUpdateResult = await client.query(
                `UPDATE wallets 
                 SET balance = balance + $1
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
                console.log(`💵 Amount added: Rp ${parseFloat(order.total_amount).toLocaleString('id-ID')}`);
            }

            // Record financial record
            await client.query(
                `INSERT INTO financial_records (user_id, type, amount, description, reference_id)
                 VALUES ($1, 'income', $2, $3, $4)`,
                [order.user_id, order.total_amount, `Payment received for order ${orderToCheck} from ${order.store_name}`, order.id]
            );
            console.log('✅ Financial record created');

            // Log activity
            await client.query(
                `INSERT INTO activity_logs (user_id, activity_type, amount, description)
                 VALUES ($1, $2, $3, $4)`,
                [order.user_id, 'payment', order.total_amount, `Payment received for order ${orderToCheck} - Added to wallet`]
            );
            console.log('✅ Activity logged');

            await client.query('COMMIT');
            console.log('✅ Manual payment processing completed successfully!');

        } catch (error) {
            await client.query('ROLLBACK');
            console.error('❌ Manual payment processing failed:', error.message);
        }

    } catch (error) {
        console.error('❌ Check failed:', error.message);
    } finally {
        client.release();
    }
}

// Run the check
if (require.main === module) {
    checkSpecificOrder().catch(console.error).finally(() => {
        pool.end();
    });
}

module.exports = { checkSpecificOrder };