from flask_mail import Message
from core.extensions import mail


def send_email(to, subject, body):
    msg = Message(
        subject=subject,
        recipients=[to],
        body=body
    )
    mail.send(msg)


def send_otp_email(email, otp):
    subject = "Your Verification OTP"
    body = f"Your OTP is {otp}. It expires in 5 minutes."
    send_email(email, subject, body)
