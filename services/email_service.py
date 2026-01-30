from flask_mail import Message
from flask import current_app, render_template_string
from core.extensions import mail


def send_email(to, subject, body, html_body=None):
    """Send email with optional HTML body"""
    try:
        msg = Message(
            subject=subject,
            recipients=[to],
            body=body,
            html=html_body
        )
        mail.send(msg)
        current_app.logger.info(f"Email sent successfully to {to}")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {to}: {str(e)}")
        return False


def send_otp_email(email, otp):
    """Send OTP verification email with professional formatting"""
    subject = "KoachSmart - Email Verification Code"
    
    # Plain text body
    body = f"""
Hello,

Your KoachSmart email verification code is: {otp}

This code will expire in 5 minutes for security reasons.

If you didn't request this code, please ignore this email.

Best regards,
KoachSmart Team
    """.strip()
    
    # HTML body for better presentation
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Verification</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                background: #f9f9f9;
                padding: 30px;
                border-radius: 0 0 10px 10px;
                border: 1px solid #ddd;
            }}
            .otp-box {{
                background: #fff;
                border: 2px solid #667eea;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                margin: 20px 0;
            }}
            .otp-code {{
                font-size: 32px;
                font-weight: bold;
                color: #667eea;
                letter-spacing: 5px;
                margin: 10px 0;
            }}
            .footer {{
                text-align: center;
                margin-top: 20px;
                color: #666;
                font-size: 14px;
            }}
            .warning {{
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                color: #856404;
                padding: 15px;
                border-radius: 5px;
                margin: 15px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏆 KoachSmart</h1>
            <p>Email Verification Required</p>
        </div>
        
        <div class="content">
            <h2>Hello!</h2>
            <p>Thank you for joining KoachSmart! To complete your registration, please verify your email address using the code below:</p>
            
            <div class="otp-box">
                <p><strong>Your Verification Code:</strong></p>
                <div class="otp-code">{otp}</div>
                <p><small>Enter this code in the verification form</small></p>
            </div>
            
            <div class="warning">
                <strong>⏰ Important:</strong> This code will expire in <strong>5 minutes</strong> for security reasons.
            </div>
            
            <p>If you didn't request this verification code, please ignore this email. Your account remains secure.</p>
            
            <div class="footer">
                <p>Best regards,<br><strong>The KoachSmart Team</strong></p>
                <p><small>This is an automated email. Please do not reply to this message.</small></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(email, subject, body, html_body)


def send_welcome_email(email, name):
    """Send welcome email after successful onboarding"""
    subject = "Welcome to KoachSmart! 🎉"
    
    body = f"""
Hello {name},

Welcome to KoachSmart! 🎉

Your account has been successfully created and verified. You can now:

✅ Browse and apply for coaching jobs
✅ Build your professional profile
✅ Connect with sports academies and clubs
✅ Earn rewards and badges

Get started by completing your profile and exploring available opportunities.

Best regards,
KoachSmart Team
    """.strip()
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to KoachSmart</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                background: #f9f9f9;
                padding: 30px;
                border-radius: 0 0 10px 10px;
                border: 1px solid #ddd;
            }}
            .features {{
                background: #fff;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            }}
            .feature-item {{
                margin: 10px 0;
                padding: 10px;
                background: #f8f9fa;
                border-left: 4px solid #667eea;
            }}
            .cta-button {{
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏆 Welcome to KoachSmart!</h1>
            <p>Your coaching journey starts here</p>
        </div>
        
        <div class="content">
            <h2>Hello {name}! 👋</h2>
            <p>Congratulations! Your KoachSmart account has been successfully created and verified.</p>
            
            <div class="features">
                <h3>What you can do now:</h3>
                <div class="feature-item">✅ Browse and apply for coaching jobs</div>
                <div class="feature-item">✅ Build your professional profile</div>
                <div class="feature-item">✅ Connect with sports academies and clubs</div>
                <div class="feature-item">✅ Earn rewards and badges</div>
            </div>
            
            <p>Ready to get started? Complete your profile and start exploring opportunities!</p>
            
            <p>If you have any questions, our support team is here to help.</p>
            
            <div style="text-align: center;">
                <p>Best regards,<br><strong>The KoachSmart Team</strong></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(email, subject, body, html_body)


def send_password_reset_email(email, reset_token):
    """Send password reset email"""
    subject = "KoachSmart - Password Reset Request"
    
    # In a real app, you'd have a proper reset URL
    reset_url = f"https://koachsmart.com/reset-password?token={reset_token}"
    
    body = f"""
Hello,

You requested a password reset for your KoachSmart account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour for security reasons.

If you didn't request this reset, please ignore this email.

Best regards,
KoachSmart Team
    """.strip()
    
    return send_email(email, subject, body)
