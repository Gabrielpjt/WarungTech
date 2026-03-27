// Database setup script
require('dotenv').config();
const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');

const pool = new Pool({
    host: process.env.DB_HOST || 'aws-1-ap-northeast-1.pooler.supabase.com',
    port: process.env.DB_PORT || 5432,
    database: process.env.DB_NAME || 'postgres',
    user: process.env.DB_USER || 'postgres.nzvkyxpgsegkpewhyqlc',
    password: process.env.DB_PASSWORD || 'PantangMenyerah123!',
});

async function setupDatabase() {
    try {
        console.log('🔄 Connecting to database...');

        // Read the SQL file
        const sqlFile = path.join(__dirname, 'database_setup.sql');
        const sql = fs.readFileSync(sqlFile, 'utf8');

        console.log('📄 Executing database setup script...');

        // Execute the SQL
        await pool.query(sql);

        console.log('✅ Database setup completed successfully!');
        console.log('📊 All tables and indexes have been created.');

    } catch (error) {
        console.error('❌ Database setup failed:', error.message);
        console.error('Full error:', error);
    } finally {
        await pool.end();
        console.log('🔌 Database connection closed.');
    }
}

// Run the setup
setupDatabase();