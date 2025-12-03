"""
Authentication middleware for Django Bluetooth Presence Detection backend.
"""

import jwt
import logging
from django.conf import settings
from django.http import JsonResponse
from functools import wraps

logger = logging.getLogger(__name__)


def jwt_required(view_func):
    """
    Decorator to validate Supabase JWT tokens and attach user_id to request.
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        # Get Authorization header
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            logger.warning("Missing or invalid Authorization header")
            return JsonResponse({
                'success': False,
                'error': 'Authentication required',
                'message': 'Please provide a valid Bearer token'
            }, status=401)

        # Extract token
        token = auth_header.replace('Bearer ', '')

        try:
            # Verify JWT using Supabase JWT secret
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=['HS256'],
                audience='authenticated'
            )

            # Attach user_id to request
            request.user_id = payload.get('sub')  # Supabase user ID
            request.user_email = payload.get('email')

            logger.debug(f"Authenticated user: {request.user_id}")

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return JsonResponse({
                'success': False,
                'error': 'Token expired',
                'message': 'Your session has expired. Please login again.'
            }, status=401)

        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Invalid token',
                'message': 'Authentication failed. Please login again.'
            }, status=401)

        except Exception as e:
            logger.error(f"JWT validation error: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Authentication error',
                'message': 'An error occurred during authentication'
            }, status=500)

        return view_func(request, *args, **kwargs)

    return wrapped_view


def scanner_api_key_required(view_func):
    """
    Decorator to validate scanner API key for Raspberry Pi scanner requests.
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        # Get X-Scanner-API-Key header
        api_key = request.headers.get('X-Scanner-API-Key', '')

        if not api_key:
            logger.warning("Missing X-Scanner-API-Key header")
            return JsonResponse({
                'success': False,
                'error': 'API key required',
                'message': 'Scanner API key is missing'
            }, status=401)

        # Validate API key
        if api_key != settings.SCANNER_API_KEY:
            logger.warning(f"Invalid scanner API key attempt")
            return JsonResponse({
                'success': False,
                'error': 'Invalid API key',
                'message': 'Scanner API key is invalid'
            }, status=401)

        logger.debug("Scanner API key validated")
        return view_func(request, *args, **kwargs)

    return wrapped_view
