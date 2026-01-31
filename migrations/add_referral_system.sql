-- Add referral system table
CREATE TABLE IF NOT EXISTS referral_system (
    id SERIAL PRIMARY KEY,
    referrer_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    referred_user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    referral_code VARCHAR(20) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    milestone_reached VARCHAR(50),
    reward_awarded BOOLEAN DEFAULT FALSE,
    reward_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(referrer_id, referred_user_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_referral_system_referrer ON referral_system(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referral_system_referred ON referral_system(referred_user_id);
CREATE INDEX IF NOT EXISTS idx_referral_system_code ON referral_system(referral_code);

-- Add referral_code column to user table if it doesn't exist
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS referral_code VARCHAR(20) UNIQUE;

-- Create index for referral codes
CREATE INDEX IF NOT EXISTS idx_user_referral_code ON "user"(referral_code);