from flask import redirect, url_for, request
from flask_login import current_user

from core.constants import PUBLIC_ENDPOINTS


def unified_access_guard():
    """
    Enforces:
    - Login protection
    - Coach onboarding completion
    - Employer onboarding completion
    """

    # Skip if not logged in
    if not current_user.is_authenticated:
        return

    # Allow static files
    if request.path.startswith("/static"):
        return

    endpoint = request.endpoint

    # Public routes always allowed
    if endpoint in PUBLIC_ENDPOINTS:
        return

    # -------------------------
    # Coach enforcement
    # -------------------------
    if current_user.role == "coach":
        if not current_user.onboarding_completed:
            return redirect(url_for("onboarding.onboarding_unified"))

    # -------------------------
    # Employer enforcement
    # -------------------------
    if current_user.role == "employer":
        if not current_user.employer_onboarding_completed:
            return redirect(url_for("onboarding.hirer_onboarding"))
from flask import abort
from flask_login import current_user


def require_role(*allowed_roles):
    """
    Enforce role-based access inside routes.
    Example:
        require_role("admin", "reviewer_l1")
    """
    if not current_user.is_authenticated:
        abort(401)

    if current_user.role not in allowed_roles:
        abort(403)
