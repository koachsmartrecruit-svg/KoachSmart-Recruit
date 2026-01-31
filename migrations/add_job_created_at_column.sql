-- Migration: Add created_at column to job table
-- Date: 2026-01-31
-- Description: Add missing created_at column to job table to fix SQLAlchemy model mismatch

-- Check if job table exists, if not create it
CREATE TABLE IF NOT EXISTS job (
    id SERIAL PRIMARY KEY,
    employer_id INTEGER NOT NULL REFERENCES "user"(id),
    title VARCHAR(150) NOT NULL,
    sport VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    location VARCHAR(150) NOT NULL,
    venue VARCHAR(150),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    lat FLOAT,
    lng FLOAT,
    requirements TEXT,
    screening_questions TEXT,
    required_skills VARCHAR(300),
    salary_range VARCHAR(100),
    job_type VARCHAR(50) DEFAULT 'Full Time',
    working_hours VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    posted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add created_at column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'job' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE job ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        
        -- Update existing records to have created_at same as posted_date
        UPDATE job SET created_at = posted_date WHERE created_at IS NULL;
    END IF;
END $$;