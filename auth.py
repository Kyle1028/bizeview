"""
使用者認證系統
處理註冊、登入、登出、個人資料管理等功能
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User
import re

# 建立認證，所有認證相關的路由都以 /auth 開頭
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# 建立登入管理器，用於管理使用者登入狀態
login_manager = LoginManager()


def init_auth(app):
    """
    初始化認證系統
    在 Flask 應用程式啟動時呼叫此函式
    """
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # 未登入時導向的頁面
    login_manager.login_message = "請先登入以訪問此頁面"  # 未登入時的提示訊息
    login_manager.login_message_category = "warning"  # 訊息類別（用於顯示樣式）
    
    # 註冊認證藍圖到應用程式
    app.register_blueprint(auth_bp)


@login_manager.user_loader
def load_user(user_id):
    """
    載入使用者
    Flask-Login 會自動呼叫此函式來取得目前登入的使用者資訊
    """
    return User.query.get(int(user_id))


def validate_email(email):
    """
    驗證電子郵件格式是否正確
    參數：email - 要驗證的電子郵件地址
    回傳：True（格式正確）或 False（格式錯誤）
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """
    驗證密碼強度
    規則：至少 8 個字元，必須包含英文字母和數字
    參數：password - 要驗證的密碼
    """
    if len(password) < 8:
        return False, "密碼長度至少需要 8 個字元"
    
    if not re.search(r'[A-Za-z]', password):
        return False, "密碼必須包含英文字母"
    
    if not re.search(r'\d', password):
        return False, "密碼必須包含數字"
    
    return True, "密碼符合要求"


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    註冊功能
    GET：顯示註冊頁面
    POST：處理註冊表單，建立新使用者
    """
    # 如果使用者已經登入，直接導向首頁
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    
    # 處理 POST 請求（使用者送出註冊表單）
    if request.method == "POST":
        # 取得表單資料並去除前後空白
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        password_confirm = request.form.get("password_confirm", "").strip()
        username = request.form.get("username", "").strip()
        
        # 步驟 1：驗證必填欄位是否都有填寫
        if not email or not password or not password_confirm:
            flash("請填寫所有必填欄位", "error")
            return render_template("register.html")
        
        # 步驟 2：驗證電子郵件格式
        if not validate_email(email):
            flash("電子郵件格式不正確", "error")
            return render_template("register.html")
        
        # 步驟 3：驗證密碼強度
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, "error")
            return render_template("register.html")
        
        # 步驟 4：確認兩次輸入的密碼一致
        if password != password_confirm:
            flash("兩次輸入的密碼不一致", "error")
            return render_template("register.html")
        
        # 步驟 5：檢查電子郵件是否已被註冊
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("此電子郵件已被註冊", "error")
            return render_template("register.html")
        
        # 步驟 6：建立新使用者並儲存到資料庫
        try:
            new_user = User(
                email=email,
                # 如果沒有填寫使用者名稱，就用電子郵件前半部
                username=username if username else email.split("@")[0]
            )
            new_user.set_password(password)  # 設定加密密碼
            
            db.session.add(new_user)  # 加入資料庫
            db.session.commit()  # 確認儲存
            
            flash("註冊成功！現在可以登入了", "success")
            return redirect(url_for("auth.login"))
            
        except Exception as e:
            # 如果發生錯誤，復原資料庫操作
            db.session.rollback()
            flash(f"註冊失敗：{str(e)}", "error")
            return render_template("register.html")
    
    # GET 請求：顯示註冊頁面
    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    登入功能
    GET：顯示登入頁面
    POST：處理登入表單，驗證帳號密碼
    """
    # 如果使用者已經登入，直接導向首頁
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    
    # 處理 POST 請求（使用者送出登入表單）
    if request.method == "POST":
        # 取得表單資料
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        remember = request.form.get("remember") == "on"  # 記住我（保持登入狀態）
        
        # 步驟 1：驗證必填欄位
        if not email or not password:
            flash("請輸入電子郵件和密碼", "error")
            return render_template("login.html")
        
        # 步驟 2：查詢使用者是否存在
        user = User.query.filter_by(email=email).first()
        
        # 步驟 3：驗證使用者和密碼
        if not user or not user.check_password(password):
            flash("電子郵件或密碼錯誤", "error")
            return render_template("login.html")
        
        # 步驟 4：檢查帳號是否被停用
        if not user.is_active:
            flash("您的帳號已被停用，請聯絡管理員", "error")
            return render_template("login.html")
        
        # 步驟 5：登入使用者
        login_user(user, remember=remember)
        
        # 步驟 6：更新最後登入時間
        user.last_login = datetime.now()
        db.session.commit()
        
        flash(f"歡迎回來，{user.username}！", "success")
        
        # 如果有指定要前往的頁面（例如被重導向到登入頁前的頁面），則導向該頁面
        next_page = request.args.get("next")
        if next_page:
            return redirect(next_page)
        return redirect(url_for("index"))
    
    # GET 請求：顯示登入頁面
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required  # 必須先登入才能登出
def logout():
    """
    登出功能
    清除使用者的登入狀態
    """
    logout_user()
    flash("您已成功登出", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile")
@login_required  # 必須登入才能查看個人資料
def profile():
    """
    個人資料頁面
    顯示目前登入使用者的資料
    """
    return render_template("profile.html", user=current_user)


@auth_bp.route("/update_username", methods=["POST"])
@login_required  # 必須登入才能更新
def update_username():
    """
    更新使用者名稱
    允許使用者修改顯示名稱
    """
    new_username = request.form.get("new_username", "").strip()
    
    # 驗證使用者名稱不能為空
    if not new_username:
        flash("使用者名稱不能為空", "error")
        return redirect(url_for("auth.profile"))
    
    # 驗證長度限制
    if len(new_username) > 80:
        flash("使用者名稱不能超過 80 個字元", "error")
        return redirect(url_for("auth.profile"))
    
    # 更新到資料庫
    try:
        current_user.username = new_username
        db.session.commit()
        flash("使用者名稱已更新！", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"更新失敗：{str(e)}", "error")
    
    return redirect(url_for("auth.profile"))


@auth_bp.route("/update_email", methods=["POST"])
@login_required  # 必須登入才能更新
def update_email():
    """
    更新電子郵件
    為了安全，需要驗證密碼才能修改
    """
    new_email = request.form.get("new_email", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()
    
    # 步驟 1：驗證必填欄位
    if not new_email or not confirm_password:
        flash("請填寫所有欄位", "error")
        return redirect(url_for("auth.profile"))
    
    # 步驟 2：驗證密碼（安全考量）
    if not current_user.check_password(confirm_password):
        flash("密碼驗證失敗", "error")
        return redirect(url_for("auth.profile"))
    
    # 步驟 3：驗證電子郵件格式
    if not validate_email(new_email):
        flash("電子郵件格式不正確", "error")
        return redirect(url_for("auth.profile"))
    
    # 步驟 4：檢查電子郵件是否已被其他使用者使用
    existing_user = User.query.filter_by(email=new_email).first()
    if existing_user and existing_user.id != current_user.id:
        flash("此電子郵件已被其他帳號使用", "error")
        return redirect(url_for("auth.profile"))
    
    # 步驟 5：更新到資料庫
    try:
        current_user.email = new_email
        db.session.commit()
        flash("電子郵件已更新！", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"更新失敗：{str(e)}", "error")
    
    return redirect(url_for("auth.profile"))


@auth_bp.route("/change_password", methods=["POST"])
@login_required  # 必須登入才能更新
def change_password():
    """
    變更密碼
    需要驗證目前密碼，確認後會自動登出要求重新登入
    """
    current_password = request.form.get("current_password", "").strip()
    new_password = request.form.get("new_password", "").strip()
    new_password_confirm = request.form.get("new_password_confirm", "").strip()
    
    # 步驟 1：驗證必填欄位
    if not current_password or not new_password or not new_password_confirm:
        flash("請填寫所有欄位", "error")
        return redirect(url_for("auth.profile"))
    
    # 步驟 2：驗證目前密碼是否正確
    if not current_user.check_password(current_password):
        flash("目前密碼錯誤", "error")
        return redirect(url_for("auth.profile"))
    
    # 步驟 3：驗證新密碼強度
    is_valid, message = validate_password(new_password)
    if not is_valid:
        flash(message, "error")
        return redirect(url_for("auth.profile"))
    
    # 步驟 4：確認兩次輸入的新密碼一致
    if new_password != new_password_confirm:
        flash("兩次輸入的新密碼不一致", "error")
        return redirect(url_for("auth.profile"))
    
    # 步驟 5：檢查新密碼是否與舊密碼相同
    if current_password == new_password:
        flash("新密碼不能與目前密碼相同", "error")
        return redirect(url_for("auth.profile"))
    
    # 步驟 6：更新密碼並登出
    try:
        current_user.set_password(new_password)
        db.session.commit()
        flash("密碼已更新！請使用新密碼登入", "success")
        # 變更密碼後強制登出，確保安全性
        logout_user()
        return redirect(url_for("auth.login"))
    except Exception as e:
        db.session.rollback()
        flash(f"更新失敗：{str(e)}", "error")
        return redirect(url_for("auth.profile"))

