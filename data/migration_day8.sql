-- Day 8 Migration: Add preferred_methodology column
-- Run: psql $DATABASE_URL -f /opt/eduscout/data/migration_day8.sql

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
        WHERE table_name='search_sessions' AND column_name='preferred_methodology') THEN
        ALTER TABLE search_sessions ADD COLUMN preferred_methodology VARCHAR(50);
        RAISE NOTICE 'Added preferred_methodology column';
    ELSE
        RAISE NOTICE 'preferred_methodology column already exists';
    END IF;
END
$$;

-- Verify all session columns
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'search_sessions'
ORDER BY ordinal_position;
