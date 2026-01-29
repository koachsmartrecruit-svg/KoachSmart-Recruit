-- Migration: Add Admin Models
-- Description: Creates tables for admin role hierarchy and activity tracking
-- Date: 2026-01-29

-- Create admin table
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    role VARCHAR(50) NOT NULL DEFAULT 'regional_admin',
    assigned_cities JSON DEFAULT '[]',
    permissions JSON DEFAULT '{"verify_coaches": true, "approve_documents": true, "manage_admins": false, "view_analytics": true, "handle_appeals": true, "send_notifications": true, "export_reports": true}',
    api_key VARCHAR(255) UNIQUE,
    api_secret VARCHAR(255),
    last_login DATETIME,
    login_count INTEGER DEFAULT 0,
    total_verifications INTEGER DEFAULT 0,
    total_approvals INTEGER DEFAULT 0,
    total_rejections INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- Create admin_activity_log table
CREATE TABLE IF NOT EXISTS admin_activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    old_value JSON,
    new_value JSON,
    ip_address VARCHAR(50),
    user_agent VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES admin(id) ON DELETE CASCADE
);

-- Create admin_permission table
CREATE TABLE IF NOT EXISTS admin_permission (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    description VARCHAR(255),
    category VARCHAR(50)
);

-- Create admin_role table
CREATE TABLE IF NOT EXISTS admin_role (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    permissions JSON
);

-- Insert predefined permissions
INSERT OR IGNORE INTO admin_permission (name, description, category) VALUES
('verify_coaches', 'Verify coach documents and profiles', 'verification'),
('approve_documents', 'Approve or reject coach documents', 'verification'),
('manage_admins', 'Create and manage other admins', 'management'),
('view_analytics', 'View platform analytics and reports', 'reporting'),
('handle_appeals', 'Handle coach appeals and disputes', 'management'),
('send_notifications', 'Send notifications to coaches', 'communication'),
('export_reports', 'Export verification reports', 'reporting'),
('manage_subscriptions', 'Manage user subscriptions', 'management'),
('view_payments', 'View payment information', 'reporting'),
('manage_plans', 'Manage membership plans', 'management');

-- Insert predefined roles
INSERT OR IGNORE INTO admin_role (name, description, permissions) VALUES
('super_admin', 'Platform owner with full access', '{"verify_coaches": true, "approve_documents": true, "manage_admins": true, "view_analytics": true, "handle_appeals": true, "send_notifications": true, "export_reports": true, "manage_subscriptions": true, "view_payments": true, "manage_plans": true}'),
('regional_admin', 'City-level admin for verification', '{"verify_coaches": true, "approve_documents": true, "manage_admins": false, "view_analytics": true, "handle_appeals": true, "send_notifications": true, "export_reports": true, "manage_subscriptions": false, "view_payments": false, "manage_plans": false}'),
('verification_officer', 'Document verification only', '{"verify_coaches": true, "approve_documents": true, "manage_admins": false, "view_analytics": false, "handle_appeals": false, "send_notifications": false, "export_reports": false, "manage_subscriptions": false, "view_payments": false, "manage_plans": false}');

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_admin_user_id ON admin(user_id);
CREATE INDEX IF NOT EXISTS idx_admin_role ON admin(role);
CREATE INDEX IF NOT EXISTS idx_admin_is_active ON admin(is_active);
CREATE INDEX IF NOT EXISTS idx_admin_activity_log_admin_id ON admin_activity_log(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_activity_log_created_at ON admin_activity_log(created_at);
CREATE INDEX IF NOT EXISTS idx_admin_activity_log_action ON admin_activity_log(action);
