-- Day 5 Migration: Ensure search_sessions has all needed columns
-- Run this on your Managed PostgreSQL:
-- psql $DATABASE_URL -f /opt/eduscout/data/migration_day5.sql

-- Add columns if they don't exist (safe to run multiple times)

DO $$
BEGIN
    -- preferred_neighborhood
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
        WHERE table_name='search_sessions' AND column_name='preferred_neighborhood') THEN
        ALTER TABLE search_sessions ADD COLUMN preferred_neighborhood VARCHAR(100);
    END IF;

    -- needs_wheelchair_access
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
        WHERE table_name='search_sessions' AND column_name='needs_wheelchair_access') THEN
        ALTER TABLE search_sessions ADD COLUMN needs_wheelchair_access BOOLEAN DEFAULT FALSE;
    END IF;

    -- interests (text field, comma-separated)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
        WHERE table_name='search_sessions' AND column_name='interests') THEN
        ALTER TABLE search_sessions ADD COLUMN interests TEXT;
    END IF;

    -- intake_complete flag
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
        WHERE table_name='search_sessions' AND column_name='intake_complete') THEN
        ALTER TABLE search_sessions ADD COLUMN intake_complete BOOLEAN DEFAULT FALSE;
    END IF;

    -- special_needs as TEXT (if it was TEXT[] array, we need to handle differently)
    -- Check if it's already text type
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
        WHERE table_name='search_sessions' AND column_name='special_needs') THEN
        ALTER TABLE search_sessions ADD COLUMN special_needs TEXT;
    END IF;

END
$$;

-- Verify
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'search_sessions'
ORDER BY ordinal_position;
