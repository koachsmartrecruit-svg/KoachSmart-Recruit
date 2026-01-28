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

    # Flask safety
    None
}
