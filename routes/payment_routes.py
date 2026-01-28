import stripe

from flask import (
    Blueprint, request, redirect,
    url_for, render_template, current_app
)
from flask_login import login_required, current_user

from core.extensions import db
from models.user import User

# ---------------------------
# Blueprint
# ---------------------------
payment_bp = Blueprint("payment", __name__)

@payment_bp.route("/plans")
def show_plans():
    return render_template("plans.html")


# ---------------------------
# Create Checkout Session
# ---------------------------
@payment_bp.route("/create-checkout-session/<plan>", methods=["POST"])
@login_required
def create_checkout_session(plan):
    try:
        price_id = None

        if plan == "basic":
            price_id = current_app.config["STRIPE_PRICE_BASIC"]
        elif plan == "pro":
            price_id = current_app.config["STRIPE_PRICE_PRO"]
        else:
            return "Invalid plan", 400

        stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]

        session_stripe = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer_email=current_user.email,
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=url_for("coach.dashboard", _external=True),
            cancel_url=url_for("payment.show_plans", _external=True),
        )

        return redirect(session_stripe.url, code=303)

    except Exception as e:
        return str(e), 400


# ---------------------------
# Stripe Webhook
# ---------------------------
@payment_bp.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = current_app.config["STRIPE_WEBHOOK_SECRET"]

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except Exception:
        return "Invalid signature", 400

    # Subscription activated
    if event["type"] == "checkout.session.completed":
        data = event["data"]["object"]
        user = User.query.filter_by(
            email=data.get("customer_email")
        ).first()

        if user:
            user.subscription_status = "active"
            user.stripe_customer_id = data.get("customer")
            db.session.commit()

    # Subscription cancelled / failed
    if event["type"] in [
        "customer.subscription.deleted",
        "invoice.payment_failed"
    ]:
        sub = event["data"]["object"]
        user = User.query.filter_by(
            stripe_customer_id=sub.get("customer")
        ).first()

        if user:
            user.subscription_status = "free"
            db.session.commit()

    return "OK", 200


# ---------------------------
# Payment Pending Page
# ---------------------------
@payment_bp.route("/payment/pending")
@login_required
def payment_pending():
    return render_template("payment_pending.html")
