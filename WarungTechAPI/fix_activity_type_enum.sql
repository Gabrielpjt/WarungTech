-- Fix activity_type enum constraint
-- This script will update the database to allow all activity types used in the code

-- First, check if the enum exists and what values it has
-- If you're using an enum, you need to add the missing values

-- Option 1: If using enum, add missing values
-- ALTER TYPE activity_type_enum ADD VALUE IF NOT EXISTS 'payment';
-- ALTER TYPE activity_type_enum ADD VALUE IF NOT EXISTS 'topup';
-- ALTER TYPE activity_type_enum ADD VALUE IF NOT EXISTS 'withdraw';
-- ALTER TYPE activity_type_enum ADD VALUE IF NOT EXISTS 'invest_buy';
-- ALTER TYPE activity_type_enum ADD VALUE IF NOT EXISTS 'invest_sell';
-- ALTER TYPE activity_type_enum ADD VALUE IF NOT EXISTS 'transaction';

-- Option 2: Convert enum to VARCHAR (recommended for flexibility)
-- This is safer and allows for future activity types without schema changes

-- Step 1: Add a temporary column
ALTER TABLE activity_logs ADD COLUMN activity_type_temp VARCHAR(100);

-- Step 2: Copy data from enum to varchar
UPDATE activity_logs SET activity_type_temp = activity_type::text;

-- Step 3: Drop the old column
ALTER TABLE activity_logs DROP COLUMN activity_type;

-- Step 4: Rename the temp column
ALTER TABLE activity_logs RENAME COLUMN activity_type_temp TO activity_type;

-- Step 5: Add NOT NULL constraint
ALTER TABLE activity_logs ALTER COLUMN activity_type SET NOT NULL;

-- Step 6: Add index for performance
CREATE INDEX IF NOT EXISTS idx_activity_logs_activity_type ON activity_logs(activity_type);

-- Verify the change
-- SELECT DISTINCT activity_type FROM activity_logs;