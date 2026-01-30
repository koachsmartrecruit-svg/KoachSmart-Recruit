"""
Membership Routes
Handles membership plans, subscriptions, and billing
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from models.user import User
from models.membership import MembershipPlan, UserSubscription, SubscriptionHistory
from core.membership_guard import get_user_membership_info, check_membership_access
from core.extensions import db
from datetime import datetime, date, timedelta
import json

membership_bp = Blueprint('membership', __name__, url_prefix='/membership')


@membership_bp.route('/plans')
def plans():
    """Display membership plans"""
    try:
        # Get user info if logged in
        user = None
        current_membership = None
        
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user:
                current_membership = get_user_membership_info(user)
        
        # Get all active plans
        coach_plans = MembershipPlan.query.filter_by(
            user_type='coach',
            is_active=True
        ).order_by(MembershipPlan.display_order).all()
        
        employer_plans = MembershipPlan.query.filter_by(
            user_type='employer',
            is_active=True
        ).order_by(MembershipPlan.display_order).all()
        
        # If no plans exist, create default ones
        if not coach_plans or not employer_plans:
            create_default_plans()
            coach_plans = MembershipPlan.query.filter_by(
                user_type='coach',
                is_active=True
            ).order_by(MembershipPlan.display_order).all()
            
            employer_plans = MembershipPlan.query.filter_by(
                user_type='employer',
                is_active=True
            ).order_by(MembershipPlan.display_order).all()
        
        return render_template('membership_plans.html',
                             coach_plans=coach_plans,
                             employer_plans=employer_plans,
                             current_membership=current_membership,
                             user=user)
        
    except Exception as e:
        current_app.logger.error(f"Error displaying membership plans: {str(e)}")
        flash('Error loading membership plans. Please try again.', 'error')
        return redirect(url_for('main.home'))


@membership_bp.route('/subscribe/<int:plan_id>')
def subscribe(plan_id):
    """Subscribe to a membership plan"""
    if 'user_id' not in session:
        flash('Please log in to subscribe to a membership plan.', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        user = User.query.get(session['user_id'])
        plan = MembershipPlan.query.get_or_404(plan_id)
        
        # Check if plan matches user type
        if plan.user_type != user.role:
            flash('This plan is not available for your account type.', 'error')
            return redirect(url_for('membership.plans'))
        
        # Check if user already has this plan
        existing_subscription = UserSubscription.query.filter_by(user_id=user.id).first()
        if existing_subscription and existing_subscription.plan_id == plan_id and existing_subscription.is_active():
            flash('You already have this membership plan.', 'info')
            return redirect(url_for('membership.dashboard'))
        
        # For free plans, create subscription immediately
        if plan.price == 0:
            success = create_subscription(user.id, plan_id, 'free')
            if success:
                flash(f'Successfully subscribed to {plan.name} plan!', 'success')
                return redirect(url_for('membership.dashboard'))
            else:
                flash('Error creating subscription. Please try again.', 'error')
                return redirect(url_for('membership.plans'))
        
        # For paid plans, redirect to payment
        return redirect(url_for('membership.payment', plan_id=plan_id))
        
    except Exception as e:
        current_app.logger.error(f"Error subscribing to plan: {str(e)}")
        flash('Error processing subscription. Please try again.', 'error')
        return redirect(url_for('membership.plans'))


@membership_bp.route('/payment/<int:plan_id>')
def payment(plan_id):
    """Payment page for membership subscription"""
    if 'user_id' not in session:
        flash('Please log in to continue.', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        user = User.query.get(session['user_id'])
        plan = MembershipPlan.query.get_or_404(plan_id)
        
        # Check if plan matches user type
        if plan.user_type != user.role:
            flash('This plan is not available for your account type.', 'error')
            return redirect(url_for('membership.plans'))
        
        # Calculate total amount (including taxes if applicable)
        base_amount = float(plan.price)
        tax_amount = base_amount * 0.18  # 18% GST
        total_amount = base_amount + tax_amount
        
        return render_template('membership_payment.html',
                             plan=plan,
                             user=user,
                             base_amount=base_amount,
                             tax_amount=tax_amount,
                             total_amount=total_amount)
        
    except Exception as e:
        current_app.logger.error(f"Error loading payment page: {str(e)}")
        flash('Error loading payment page. Please try again.', 'error')
        return redirect(url_for('membership.plans'))


@membership_bp.route('/process-payment', methods=['POST'])
def process_payment():
    """Process membership payment"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in to continue.'})
    
    try:
        data = request.get_json()
        user = User.query.get(session['user_id'])
        plan = MembershipPlan.query.get(data.get('plan_id'))
        
        if not plan:
            return jsonify({'success': False, 'message': 'Invalid plan selected.'})
        
        # Simulate payment processing (replace with actual payment gateway)
        payment_method = data.get('payment_method', 'card')
        payment_id = f"pay_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{user.id}"
        
        # Create subscription history record
        history = SubscriptionHistory(
            user_id=user.id,
            plan_id=plan.id,
            action='purchase',
            amount=plan.price,
            status='completed',
            transaction_id=payment_id,
            payment_method=payment_method
        )
        db.session.add(history)
        
        # Create or update subscription
        success = create_subscription(user.id, plan.id, payment_method, payment_id)
        
        if success:
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'Successfully subscribed to {plan.name} plan!',
                'redirect_url': url_for('membership.dashboard')
            })
        else:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Error creating subscription.'})
        
    except Exception as e:
        current_app.logger.error(f"Error processing payment: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Payment processing failed.'})


@membership_bp.route('/dashboard')
def dashboard():
    """Membership dashboard"""
    if 'user_id' not in session:
        flash('Please log in to view your membership dashboard.', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        user = User.query.get(session['user_id'])
        membership_info = get_user_membership_info(user)
        
        # Get subscription history
        history = SubscriptionHistory.query.filter_by(
            user_id=user.id
        ).order_by(SubscriptionHistory.created_at.desc()).limit(10).all()
        
        # Get usage statistics
        usage_stats = get_usage_statistics(user)
        
        return render_template('membership_dashboard.html',
                             user=user,
                             membership=membership_info,
                             history=history,
                             usage_stats=usage_stats)
        
    except Exception as e:
        current_app.logger.error(f"Error loading membership dashboard: {str(e)}")
        flash('Error loading dashboard. Please try again.', 'error')
        return redirect(url_for('main.home'))


@membership_bp.route('/cancel')
def cancel_subscription():
    """Cancel current subscription"""
    if 'user_id' not in session:
        flash('Please log in to continue.', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        user = User.query.get(session['user_id'])
        subscription = UserSubscription.query.filter_by(user_id=user.id).first()
        
        if not subscription or not subscription.is_active():
            flash('No active subscription found to cancel.', 'info')
            return redirect(url_for('membership.dashboard'))
        
        # Cancel subscription
        subscription.cancel()
        
        # Create history record
        history = SubscriptionHistory(
            user_id=user.id,
            plan_id=subscription.plan_id,
            action='cancel',
            amount=0,
            status='completed'
        )
        db.session.add(history)
        db.session.commit()
        
        flash('Your subscription has been cancelled successfully.', 'success')
        return redirect(url_for('membership.dashboard'))
        
    except Exception as e:
        current_app.logger.error(f"Error cancelling subscription: {str(e)}")
        flash('Error cancelling subscription. Please try again.', 'error')
        return redirect(url_for('membership.dashboard'))


@membership_bp.route('/upgrade/<int:plan_id>')
def upgrade(plan_id):
    """Upgrade to a higher plan"""
    if 'user_id' not in session:
        flash('Please log in to continue.', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        user = User.query.get(session['user_id'])
        new_plan = MembershipPlan.query.get_or_404(plan_id)
        current_subscription = UserSubscription.query.filter_by(user_id=user.id).first()
        
        # Check if upgrade is valid
        if not current_subscription:
            flash('No current subscription found.', 'error')
            return redirect(url_for('membership.plans'))
        
        if new_plan.price <= current_subscription.plan.price:
            flash('You can only upgrade to a higher plan.', 'error')
            return redirect(url_for('membership.plans'))
        
        # Calculate prorated amount
        days_remaining = current_subscription.days_remaining()
        daily_rate_old = float(current_subscription.plan.price) / current_subscription.plan.duration_days
        daily_rate_new = float(new_plan.price) / new_plan.duration_days
        
        credit_amount = days_remaining * daily_rate_old
        upgrade_amount = float(new_plan.price) - credit_amount
        
        return render_template('membership_upgrade.html',
                             current_plan=current_subscription.plan,
                             new_plan=new_plan,
                             days_remaining=days_remaining,
                             credit_amount=credit_amount,
                             upgrade_amount=max(0, upgrade_amount))
        
    except Exception as e:
        current_app.logger.error(f"Error processing upgrade: {str(e)}")
        flash('Error processing upgrade. Please try again.', 'error')
        return redirect(url_for('membership.plans'))


def create_subscription(user_id, plan_id, payment_method, payment_id=None):
    """
    Create or update user subscription
    
    Args:
        user_id: User ID
        plan_id: Plan ID
        payment_method: Payment method used
        payment_id: Payment transaction ID
    
    Returns:
        bool: Success status
    """
    try:
        plan = MembershipPlan.query.get(plan_id)
        if not plan:
            return False
        
        # Check for existing subscription
        existing_subscription = UserSubscription.query.filter_by(user_id=user_id).first()
        
        if existing_subscription:
            # Update existing subscription
            existing_subscription.plan_id = plan_id
            existing_subscription.status = 'active'
            existing_subscription.start_date = date.today()
            existing_subscription.end_date = date.today() + timedelta(days=plan.duration_days)
            existing_subscription.payment_method = payment_method
            existing_subscription.payment_id = payment_id
            existing_subscription.auto_renew = True
        else:
            # Create new subscription
            subscription = UserSubscription(
                user_id=user_id,
                plan_id=plan_id,
                status='active',
                start_date=date.today(),
                end_date=date.today() + timedelta(days=plan.duration_days),
                payment_method=payment_method,
                payment_id=payment_id,
                auto_renew=True
            )
            db.session.add(subscription)
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error creating subscription: {str(e)}")
        return False


def create_default_plans():
    """Create default membership plans if they don't exist"""
    try:
        default_plans = MembershipPlan.get_default_plans()
        
        for user_type, plans in default_plans.items():
            for plan_key, plan_data in plans.items():
                # Check if plan already exists
                existing_plan = MembershipPlan.query.filter_by(
                    name=plan_data['name'],
                    user_type=user_type
                ).first()
                
                if not existing_plan:
                    plan = MembershipPlan(
                        name=plan_data['name'],
                        user_type=user_type,
                        price=plan_data['price'],
                        duration_days=plan_data['duration_days'],
                        features=plan_data['features'],
                        monthly_applications=plan_data.get('monthly_applications'),
                        monthly_job_posts=plan_data.get('monthly_job_posts'),
                        is_active=True,
                        display_order=list(plans.keys()).index(plan_key)
                    )
                    db.session.add(plan)
        
        db.session.commit()
        current_app.logger.info("Default membership plans created successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error creating default plans: {str(e)}")
        db.session.rollback()


def get_usage_statistics(user):
    """
    Get usage statistics for a user
    
    Args:
        user: User object
    
    Returns:
        dict: Usage statistics
    """
    try:
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        stats = {
            'monthly_applications': 0,
            'monthly_job_posts': 0,
            'total_applications': 0,
            'total_job_posts': 0
        }
        
        if user.role == 'coach':
            # Count applications
            from models.application import Application
            stats['monthly_applications'] = Application.query.filter(
                Application.user_id == user.id,
                Application.created_at >= current_month
            ).count()
            
            stats['total_applications'] = Application.query.filter_by(user_id=user.id).count()
        
        elif user.role == 'employer':
            # Count job posts
            from models.job import Job
            stats['monthly_job_posts'] = Job.query.filter(
                Job.hirer_id == user.id,
                Job.created_at >= current_month
            ).count()
            
            stats['total_job_posts'] = Job.query.filter_by(hirer_id=user.id).count()
        
        return stats
        
    except Exception as e:
        current_app.logger.error(f"Error getting usage statistics: {str(e)}")
        return {
            'monthly_applications': 0,
            'monthly_job_posts': 0,
            'total_applications': 0,
            'total_job_posts': 0
        }