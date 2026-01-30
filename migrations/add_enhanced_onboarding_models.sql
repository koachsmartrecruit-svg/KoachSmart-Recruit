-- Enhanced Multi-Language Onboarding System Database Migration
-- This migration adds language preferences, enhanced referral system, and verification tracking

-- Add new fields to existing user table (using quotes for reserved keyword)
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(50) DEFAULT 'english';
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS digital_id VARCHAR(100);
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS referred_by_code VARCHAR(20);
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS premium_subscription BOOLEAN DEFAULT FALSE;
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS premium_expires_at TIMESTAMP;
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS cv_builder_access BOOLEAN DEFAULT FALSE;

-- Add unique constraint for digital_id if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'user_digital_id_key'
    ) THEN
        ALTER TABLE "user" ADD CONSTRAINT user_digital_id_key UNIQUE (digital_id);
    END IF;
END $$;

-- Create language_preference table
CREATE TABLE IF NOT EXISTS language_preference (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    primary_language VARCHAR(50) DEFAULT 'english',
    secondary_language VARCHAR(50),
    audio_instructions BOOLEAN DEFAULT TRUE,
    form_language VARCHAR(50),
    notification_language VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES "user" (id) ON DELETE CASCADE
);

-- Create referral_system table
CREATE TABLE IF NOT EXISTS referral_system (
    id SERIAL PRIMARY KEY,
    referrer_id INTEGER NOT NULL,
    referred_id INTEGER NOT NULL,
    referral_code VARCHAR(20) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    coins_awarded INTEGER DEFAULT 0,
    milestone_reached VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (referrer_id) REFERENCES "user" (id) ON DELETE CASCADE,
    FOREIGN KEY (referred_id) REFERENCES "user" (id) ON DELETE CASCADE
);

-- Create enhanced_verification_stage table
CREATE TABLE IF NOT EXISTS enhanced_verification_stage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    stage_number INTEGER NOT NULL,
    stage_name VARCHAR(100),
    stage_start_time TIMESTAMP,
    stage_completion_time TIMESTAMP,
    time_spent_minutes INTEGER DEFAULT 0,
    completion_percentage REAL DEFAULT 0.0,
    requirements_met JSONB, -- JSON data
    documents_uploaded JSONB, -- JSON data
    verification_status VARCHAR(50) DEFAULT 'pending',
    coins_earned INTEGER DEFAULT 0,
    badge_awarded VARCHAR(50),
    referral_code_generated BOOLEAN DEFAULT FALSE,
    referrals_count INTEGER DEFAULT 0,
    referral_coins_earned INTEGER DEFAULT 0,
    premium_features_unlocked BOOLEAN DEFAULT FALSE,
    cv_builder_completed BOOLEAN DEFAULT FALSE,
    social_media_integration BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES "user" (id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_language_preference_user_id ON language_preference(user_id);
CREATE INDEX IF NOT EXISTS idx_referral_system_referrer_id ON referral_system(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referral_system_referred_id ON referral_system(referred_id);
CREATE INDEX IF NOT EXISTS idx_referral_system_code ON referral_system(referral_code);
CREATE INDEX IF NOT EXISTS idx_enhanced_verification_user_id ON enhanced_verification_stage(user_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_verification_stage ON enhanced_verification_stage(stage_number);
CREATE INDEX IF NOT EXISTS idx_user_digital_id ON "user"(digital_id);
CREATE INDEX IF NOT EXISTS idx_user_preferred_language ON "user"(preferred_language);

-- Insert default language preferences for existing users
INSERT INTO language_preference (user_id, primary_language, audio_instructions)
SELECT id, 'english', TRUE 
FROM "user" 
WHERE id NOT IN (SELECT user_id FROM language_preference WHERE user_id IS NOT NULL);

-- Update existing users with default referral codes if they don't have one
UPDATE "user" 
SET referral_code = UPPER(SUBSTR(username, 1, 3) || SUBSTR(CAST(ABS(RANDOM()) AS TEXT), 1, 5))
WHERE referral_code IS NULL OR referral_code = '';

COMMIT;