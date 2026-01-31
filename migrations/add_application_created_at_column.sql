-- Migration: Add created_at column to application table
-- Date: 2026-01-31
-- Description: Add missing created_at column to application table to fix SQLAlchemy model mismatch

-- Check if application table exists, if not create it
CREATE TABLE IF NOT EXISTS application (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES job(id),
    user_id INTEGER NOT NULL REFERENCES "user"(id),
    status VARCHAR(50) DEFAULT 'Applied',
    match_score INTEGER,
    match_reasons TEXT,
    applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    custom_resume_path VARCHAR(300),
    screening_answers TEXT
);

-- Add created_at column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'application' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE application ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        
        -- Update existing records to have created_at same as applied_date
        UPDATE application SET created_at = applied_date WHERE created_at IS NULL;
    END IF;
END $$;