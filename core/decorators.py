"""
權限檢查裝飾器模組
提供統一的權限檢查機制，確保所有需要權限的路由都在後端進行檢查
"""

from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user


def super_admin_required(f):
    """
    裝飾器：需要超級管理員權限
    
    使用方式：
    @app.route("/admin/users")
    @super_admin_required
    def manage_users():
        ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("請先登入以訪問此頁面", "warning")
            return redirect(url_for("auth.login"))
        
        if not current_user.is_super_admin_role():
            abort(403, "此功能需要超級管理員權限")
        
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    裝飾器：需要管理員權限（包含超級管理員）
    
    使用方式：
    @app.route("/admin/exhibitions")
    @admin_required
    def manage_exhibitions():
        ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("請先登入以訪問此頁面", "warning")
            return redirect(url_for("auth.login"))
        
        if not current_user.is_admin_role():
            abort(403, "此功能需要管理員權限")
        
        return f(*args, **kwargs)
    return decorated_function


def can_manage_exhibition(exhibition_id_param='exhibition_id'):
    """
    裝飾器工廠：檢查是否可以管理指定的展覽
    
    參數：
        exhibition_id_param: URL 參數或函數參數名稱，用於取得展覽 ID
    
    使用方式：
    @app.route("/exhibition/<int:exhibition_id>/edit")
    @can_manage_exhibition('exhibition_id')
    def edit_exhibition(exhibition_id):
        ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("請先登入以訪問此頁面", "warning")
                return redirect(url_for("auth.login"))
            
            # 從 kwargs 取得展覽 public_id（對外不可猜）
            from core.models import Exhibition
            
            exhibition_public_id = kwargs.get(exhibition_id_param)
            if not exhibition_public_id:
                abort(400, "缺少展覽識別")
            
            exhibition = Exhibition.query.filter_by(public_id=exhibition_public_id).first_or_404()
            
            # 檢查權限
            if not current_user.can_manage_exhibition(exhibition):
                abort(403, "您沒有權限管理此展覽")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
