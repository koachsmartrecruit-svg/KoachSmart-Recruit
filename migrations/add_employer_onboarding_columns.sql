-- Migration: Add employer onboarding columns to user table
-- Date: 2026-01-26
-- Description: Adds employer_onboarding_step and employer_onboarding_completed columns

-- Add employer_onboarding_step column (default: 1)
ALTER TABLE "user" 
ADD COLUMN IF NOT EXISTS employer_onboarding_step INTEGER DEFAULT 1;

-- Add employer_onboarding_completed column (default: false)
ALTER TABLE "user" 
ADD COLUMN IF NOT EXISTS employer_onboarding_completed BOOLEAN DEFAULT FALSE;

-- Update existing employer users to have default values
UPDATE "user" 
SET employer_onboarding_step = 1, employer_onboarding_completed = FALSE 
WHERE employer_onboarding_step IS NULL OR employer_onboarding_completed IS NULL;

-- Verify the columns were added
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'user' 
AND column_name IN ('employer_onboarding_step', 'employer_onboarding_completed');

