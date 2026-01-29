from enum import Enum

# -----------------------------
# Review Status Enum
# -----------------------------
class ReviewStatus(str, Enum):
    pending = "Pending"
    approved = "Approved"
    rejected = "Rejected"
    not_required = "Not Required"


# -----------------------------
# Hiring Mode Enum
# -----------------------------
class HiringMode(str, Enum):
    single = "Single"
    multiple = "Multiple"


# -----------------------------
# Public Endpoints (Access Guard)
# -----------------------------
PUBLIC_ENDPOINTS = {
    # Auth
    "auth.login", "auth.register", "auth.logout",
    "auth.login_google", "auth.authorize_google", "auth.select_role",
    "auth.forgot_password", "auth.reset_password_mock",
    "employer.register", "employer.login",

    # Public pages
    "public.home", "public.about", "public.careers", "public.success_stories", "public.pricing",
    "public.coach_guide", "public.academy_guide", "public.safety", "public.help_center",
    "public.about_page", "public.error_demo",

    # Payments
    "payment.payment_pending", "payment.stripe_webhook", "payment.create_checkout_session",

    # Onboarding
    "onboarding.onboarding_unified", "onboarding.hirer_onboarding",

    # Admin routes (allow admin access)
    "admin.super_admin", "admin.admin_users", "admin.admin_jobs", "admin.admin_hirers",
    "admin.admin_coach_verification", "admin.admin_coach_verification_detail",
    "admin.verify_coach", "admin.reject_coach", "admin.verify_document",
    "admin.update_hirer_review", "admin.admin_change_role",

    # Verification routes (allow access)
    "verification.verification_dashboard", "verification.stage1", "verification.stage2",
    "verification.stage3", "verification.stage4", "verification.verify_phone",
    "verification.confirm_phone", "verification.verify_email", "verification.confirm_email",
    "verification.verify_aadhar", "verification.create_username", "verification.set_location",
    "verification.add_education", "verification.add_experience", "verification.add_certifications",
    "verification.upload_document", "verification.public_coach_profile",
    "verification.api_verification_progress", "verification.api_verification_documents",

    # Flask safety
    None
}
