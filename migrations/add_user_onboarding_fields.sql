-- Migration: Add User Onboarding Fields
-- Description: Adds onboarding_completed_at and membership fields to user table
-- Date: 2026-01-29

-- Add missing columns to user table
ALTER TABLE "user" ADD COLUMN onboarding_completed_at TIMESTAMP DEFAULT NULL;
ALTER TABLE "user" ADD COLUMN membership_status VARCHAR(50) DEFAULT 'free';
ALTER TABLE "user" ADD COLUMN membership_expires_at TIMESTAMP DEFAULT NULL;

-- Create index for membership status
CREATE INDEX IF NOT EXISTS idx_user_membership_status ON "user"(membership_status);
CREATE INDEX IF NOT EXISTS idx_user_onboarding_completed_at ON "user"(onboarding_completed_at);
