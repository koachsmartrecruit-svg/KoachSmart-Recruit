from flask import Blueprint, render_template

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    return render_template("home.html")


@public_bp.route("/about")
def about():
    return render_template("pages/about.html")


@public_bp.route("/careers")
def careers():
    return render_template("pages/careers.html")


@public_bp.route("/success-stories")
def success_stories():
    return render_template("pages/success_stories.html")


@public_bp.route("/pricing")
def pricing():
    return render_template("pages/pricing.html")


@public_bp.route("/coach-guide")
def coach_guide():
    return render_template("pages/coach_guide.html")


@public_bp.route("/academy-guide")
def academy_guide():
    return render_template("pages/academy_guide.html")


@public_bp.route("/safety")
def safety():
    return render_template("pages/safety.html")


@public_bp.route("/help")
def help_center():
    return render_template("pages/help.html")
