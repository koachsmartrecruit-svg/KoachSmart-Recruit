-- Add comprehensive onboarding fields to User table
ALTER TABLE user ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE user ADD COLUMN aadhar_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE user ADD COLUMN badges TEXT DEFAULT '';

-- Add comprehensive onboarding fields to Profile table
ALTER TABLE profile ADD COLUMN aadhar_number VARCHAR(20);
ALTER TABLE profile ADD COLUMN sport2 VARCHAR(100);
ALTER TABLE profile ADD COLUMN location VARCHAR(200);
ALTER TABLE profile ADD COLUMN serviceable_area VARCHAR(50);
ALTER TABLE profile ADD COLUMN range_km INTEGER DEFAULT 5;
ALTER TABLE profile ADD COLUMN specific_locations TEXT;
ALTER TABLE profile ADD COLUMN job_types TEXT;
ALTER TABLE profile ADD COLUMN education VARCHAR(100);
ALTER TABLE profile ADD COLUMN specialization VARCHAR(200);
ALTER TABLE profile ADD COLUMN has_professional_cert BOOLEAN DEFAULT FALSE;
ALTER TABLE profile ADD COLUMN cert_name VARCHAR(200);
ALTER TABLE profile ADD COLUMN playing_level VARCHAR(100);
ALTER TABLE profile ADD COLUMN education_doc_path VARCHAR(300);
ALTER TABLE profile ADD COLUMN cert_doc_path VARCHAR(300);
ALTER TABLE profile ADD COLUMN playing_doc_path VARCHAR(300);
ALTER TABLE profile ADD COLUMN public_slug VARCHAR(200) UNIQUE;

-- Update experience_years to be string instead of integer
ALTER TABLE profile ALTER COLUMN experience_years TYPE VARCHAR(50);

-- Create index for public_slug for faster lookups
CREATE INDEX idx_profile_public_slug ON profile(public_slug);