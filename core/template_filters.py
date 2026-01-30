"""
Template filters for enhanced onboarding system
Provides localization and other utility filters for Jinja2 templates
"""

from flask import current_app
from flask_login import current_user
from services.language_service import language_engine, get_user_language


def register_template_filters(app):
    """Register custom template filters with Flask app"""
    
    @app.template_filter('localize')
    def localize_filter(content_key, **kwargs):
        """
        Template filter for localizing content
        Usage: {{ 'stage_1_title'|localize }}
        Usage with params: {{ 'coins_earned'|localize(coins=200, badge='Orange Badge') }}
        """
        if current_user.is_authenticated:
            language = get_user_language(current_user.id)
        else:
            language = 'english'
        
        return language_engine.get_localized_content(language, content_key, **kwargs)
    
    @app.template_filter('get_stage_content')
    def get_stage_content_filter(stage_number):
        """
        Template filter for getting stage content
        Usage: {{ 1|get_stage_content }}
        """
        if current_user.is_authenticated:
            language = get_user_language(current_user.id)
        else:
            language = 'english'
        
        return language_engine.get_stage_content(language, stage_number)
    
    @app.template_filter('get_supported_languages')
    def get_supported_languages_filter():
        """
        Template filter for getting supported languages
        Usage: {{ ''|get_supported_languages }}
        """
        return language_engine.get_supported_languages()
    
    @app.template_filter('get_user_language')
    def get_user_language_filter():
        """
        Template filter for getting current user's language
        Usage: {{ ''|get_user_language }}
        """
        if current_user.is_authenticated:
            return get_user_language(current_user.id)
        return 'english'
    
    @app.template_global()
    def localize_global(content_key, **kwargs):
        """
        Global template function for localization
        Usage: {{ localize('stage_1_title') }}
        Usage with params: {{ localize('coins_earned', coins=200, badge='Orange Badge') }}
        """
        if current_user.is_authenticated:
            language = get_user_language(current_user.id)
        else:
            language = 'english'
        
        return language_engine.get_localized_content(language, content_key, **kwargs)
    
    @app.template_global()
    def get_language_info():
        """
        Global template function for getting current language info
        Usage: {{ get_language_info() }}
        """
        if current_user.is_authenticated:
            language_code = get_user_language(current_user.id)
        else:
            language_code = 'english'
        
        languages = language_engine.get_supported_languages()
        return languages.get(language_code, languages['english'])
    
    return app