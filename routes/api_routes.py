"""
API Routes for Real-time Data
Provides JSON endpoints for live statistics and updates
"""

from flask import Blueprint, jsonify, request
from services.stats_service import get_platform_stats, get_coach_stats, get_employer_stats, get_live_activity
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/stats/platform", methods=["GET"])
def platform_stats():
    """Get real-time platform statistics"""
    try:
        stats = get_platform_stats()
        return jsonify({
            "success": True,
            "data": stats,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching platform stats: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch platform statistics",
            "timestamp": datetime.utcnow().isoformat()
        }), 500


@api_bp.route("/stats/coach", methods=["GET"])
def coach_stats():
    """Get real-time coach statistics"""
    try:
        stats = get_coach_stats()
        return jsonify({
            "success": True,
            "data": stats,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching coach stats: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch coach statistics",
            "timestamp": datetime.utcnow().isoformat()
        }), 500


@api_bp.route("/stats/employer", methods=["GET"])
def employer_stats():
    """Get real-time employer statistics"""
    try:
        stats = get_employer_stats()
        return jsonify({
            "success": True,
            "data": stats,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching employer stats: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch employer statistics",
            "timestamp": datetime.utcnow().isoformat()
        }), 500


@api_bp.route("/stats/live-activity", methods=["GET"])
def live_activity():
    """Get recent live activity"""
    try:
        activity = get_live_activity()
        return jsonify({
            "success": True,
            "data": activity,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching live activity: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch live activity",
            "timestamp": datetime.utcnow().isoformat()
        }), 500


@api_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "KoachSmart API",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected"
    })


@api_bp.route("/stats/summary", methods=["GET"])
def stats_summary():
    """Get a summary of all statistics for dashboard"""
    try:
        platform = get_platform_stats()
        activity = get_live_activity()
        
        summary = {
            "overview": {
                "total_users": platform['total_coaches'] + platform['total_employers'],
                "total_coaches": platform['total_coaches'],
                "total_employers": platform['total_employers'],
                "verified_coaches": platform['verified_coaches']
            },
            "jobs": {
                "total_jobs": platform['total_jobs'],
                "active_jobs": platform['active_jobs'],
                "recent_jobs": platform['recent_jobs'],
                "weekly_jobs": platform.get('weekly_jobs', 0)
            },
            "applications": {
                "total_applications": platform['total_applications'],
                "recent_applications": platform['recent_applications'],
                "weekly_applications": platform.get('weekly_applications', 0),
                "hired_count": platform['hired_count']
            },
            "metrics": {
                "success_rate": platform['success_rate'],
                "avg_hire_time": platform['avg_hire_time'],
                "top_sports": platform['top_sports']
            },
            "activity": activity,
            "last_updated": platform['last_updated']
        }
        
        return jsonify({
            "success": True,
            "data": summary,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching stats summary: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch statistics summary",
            "timestamp": datetime.utcnow().isoformat()
        }), 500