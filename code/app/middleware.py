from flask import make_response, request

def no_cache_middleware(app):
    """Disables caching for all responses."""
    @app.after_request
    def add_no_cache_headers(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return app


from flask import redirect, url_for
from flask_login import LoginManager, current_user
from functools import wraps

def redirect_if_logged_in(view_function):
    @wraps(view_function)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated:  # Check if the user is logged in
            user_role = getattr(current_user, 'role', None)  # Get the role from current_user
            if user_role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user_role == 'teacher':
                return redirect(url_for('teacher.dashboard'))
            elif user_role == 'student':
                return redirect(url_for('student.dashboard'))
        return view_function(*args, **kwargs)
    return wrapper

def student_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            # Not logged in: go to student login page with next param
            return redirect(url_for('student.login', next=request.path))
        
        if current_user.role != 'student':
            # Logged in but not a student: redirect to home or dashboard
            return redirect(url_for('home_bp.home'))  # adjust blueprint.route_name as needed
        
        # Logged in and is a student: proceed
        return f(*args, **kwargs)
    return decorated_function



class CustomLoginManager(LoginManager):
    def unauthorized(self):
        path = request.path.lower()

        if path.startswith('/student'):
            return redirect(url_for('student.login'))
        elif path.startswith('/teacher'):
            return redirect(url_for('teacher.login'))
        elif path.startswith('/admin'):
            return redirect(url_for('admin.login'))
        else:
            # Default fallback
            return redirect(url_for('home_bp.login'))
