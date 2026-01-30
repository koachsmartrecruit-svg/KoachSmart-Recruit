-- Add Membership Tables Migration
-- Creates membership_plan, user_subscription, subscription_history, and onboarding_progress tables

-- Create membership_plan table
CREATE TABLE IF NOT EXISTS membership_plan (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    user_type VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'INR',
    duration_days INTEGER DEFAULT 30,
    features JSON DEFAULT '{}',
    monthly_applications INTEGER,
    monthly_job_posts INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user_subscription table
CREATE TABLE IF NOT EXISTS user_subscription (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    plan_id INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    start_date DATE DEFAULT CURRENT_DATE,
    end_date DATE NOT NULL,
    auto_renew BOOLEAN DEFAULT TRUE,
    payment_method VARCHAR(50),
    payment_id VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES membership_plan(id) ON DELETE CASCADE
);

-- Create subscription_history table
CREATE TABLE IF NOT EXISTS subscription_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    plan_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'INR',
    status VARCHAR(50) DEFAULT 'pending',
    transaction_id VARCHAR(100) UNIQUE,
    payment_method VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES membership_plan(id) ON DELETE CASCADE
);

-- Create onboarding_progress table
CREATE TABLE IF NOT EXISTS onboarding_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    current_step INTEGER DEFAULT 1,
    completed_steps JSON DEFAULT '[]',
    coins_earned INTEGER DEFAULT 0,
    badges_earned JSON DEFAULT '[]',
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_membership_plan_user_type ON membership_plan(user_type);
CREATE INDEX IF NOT EXISTS idx_membership_plan_active ON membership_plan(is_active);
CREATE INDEX IF NOT EXISTS idx_user_subscription_user_id ON user_subscription(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscription_status ON user_subscription(status);
CREATE INDEX IF NOT EXISTS idx_subscription_history_user_id ON subscription_history(user_id);
CREATE INDEX IF NOT EXISTS idx_subscription_history_created_at ON subscription_history(created_at);
CREATE INDEX IF NOT EXISTS idx_onboarding_progress_user_id ON onboarding_progress(user_id);

-- Add unique constraints (only if they don't exist)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'unique_plan_per_type' 
        AND table_name = 'membership_plan'
    ) THEN
        ALTER TABLE membership_plan ADD CONSTRAINT unique_plan_per_type UNIQUE (name, user_type);
    END IF;
END $$;

COMMIT;