"""
Language selection and management routes
Handles language preference setting and switching
"""

from flask import Blueprint, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from services.language_service import language_engine, set_language, get_user_language

language_bp = Blueprint('language', __name__, url_prefix='/language')


@language_bp.route('/set', methods=['POST'])
@login_required
def set_language_preference():
    """Set user's language preference via AJAX or form submission"""
    
    language = request.form.get('language') or request.json.get('language') if request.is_json else None
    
    if not language:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Language not specified'}), 400
        flash('Language not specified', 'error')
        return redirect(request.referrer or url_for('coach.dashboard'))
    
    # Validate language
    supported_languages = language_engine.get_supported_languages()
    if language not in supported_languages:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Unsupported language'}), 400
        flash('Unsupported language', 'error')
        return redirect(request.referrer or url_for('coach.dashboard'))
    
    # Set language preference
    success = set_language(current_user.id, language)
    
    if request.is_json:
        if success:
            return jsonify({
                'success': True, 
                'language': language,
                'language_info': supported_languages[language]
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to set language'}), 500
    
    # Form submission
    if success:
        flash(f'Language changed to {supported_languages[language]["name"]}', 'success')
    else:
        flash('Failed to change language', 'error')
    
    return redirect(request.referrer or url_for('coach.dashboard'))


@language_bp.route('/get', methods=['GET'])
@login_required
def get_language_preference():
    """Get user's current language preference"""
    
    language = get_user_language(current_user.id)
    supported_languages = language_engine.get_supported_languages()
    
    return jsonify({
        'current_language': language,
        'language_info': supported_languages.get(language, supported_languages['english']),
        'supported_languages': supported_languages
    })


@language_bp.route('/content/<content_key>')
@login_required
def get_localized_content(content_key):
    """Get localized content for a specific key"""
    
    language = get_user_language(current_user.id)
    
    # Get any format parameters from query string
    kwargs = request.args.to_dict()
    
    content = language_engine.get_localized_content(language, content_key, **kwargs)
    
    return jsonify({
        'content_key': content_key,
        'language': language,
        'content': content
    })


@language_bp.route('/stage/<int:stage>')
@login_required
def get_stage_content(stage):
    """Get all localized content for a specific onboarding stage"""
    
    language = get_user_language(current_user.id)
    stage_content = language_engine.get_stage_content(language, stage)
    
    return jsonify({
        'stage': stage,
        'language': language,
        'content': stage_content
    })


@language_bp.route('/audio/<int:stage>')
@login_required
def get_audio_instructions(stage):
    """Get audio instructions for a specific stage"""
    
    language = get_user_language(current_user.id)
    audio_text = language_engine.get_audio_instructions(language, stage)
    
    return jsonify({
        'stage': stage,
        'language': language,
        'audio_text': audio_text
    })