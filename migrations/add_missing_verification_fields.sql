-- Add missing verification fields to user table
-- These fields are referenced in the coach profile but don't exist in the database

-- Add email_verified column
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;

-- Add aadhar_verified column  
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS aadhar_verified BOOLEAN DEFAULT FALSE;

-- Update existing users to have email verified if they have an email
UPDATE "user" SET email_verified = TRUE WHERE email IS NOT NULL AND email != '';

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_email_verified ON "user"(email_verified);
CREATE INDEX IF NOT EXISTS idx_user_aadhar_verified ON "user"(aadhar_verified);

-- Add comment for documentation
COMMENT ON COLUMN "user".email_verified IS 'Whether the user has verified their email address';
COMMENT ON COLUMN "user".aadhar_verified IS 'Whether the user has verified their Aadhar document';