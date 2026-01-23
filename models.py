"""
資料庫模型定義檔案
定義了使用者(User)和媒體檔案(Media)兩個資料表
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# 建立資料庫物件，用於操作資料庫
db = SQLAlchemy()


class User(UserMixin, db.Model):
    """
    使用者資料表
    儲存註冊使用者的帳號資訊
    """
    __tablename__ = "users"  # 資料表名稱
    
    # 欄位定義
    id = db.Column(db.Integer, primary_key=True)  # 使用者 ID（主鍵，自動遞增）
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)  # 電子郵件（唯一，不可為空）
    password_hash = db.Column(db.String(255), nullable=False)  # 加密後的密碼
    username = db.Column(db.String(80), nullable=True)  # 使用者名稱（可選）
    created_at = db.Column(db.DateTime, default=datetime.now)  # 註冊時間
    last_login = db.Column(db.DateTime)  # 最後登入時間
    is_active = db.Column(db.Boolean, default=True)  # 帳號是否啟用（預設：啟用）
    verified_at = db.Column(db.DateTime, default=datetime.now)  # 帳號驗證時間
    
    def set_password(self, password):
        """
        設定密碼（會自動加密）
        參數：password - 使用者輸入的明文密碼
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        驗證密碼是否正確
        參數：password - 使用者輸入的明文密碼
        回傳：True（正確）或 False（錯誤）
        """
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        """物件的字串表示（用於除錯）"""
        return f"<User {self.email}>"


class Media(db.Model):
    """
    媒體檔案資料表
    儲存使用者上傳的照片/影片資訊
    """
    __tablename__ = "media"  # 資料表名稱
    
    # 欄位定義
    id = db.Column(db.Integer, primary_key=True)  # 媒體檔案 ID（主鍵，自動遞增）
    media_id = db.Column(db.String(50), unique=True, nullable=False, index=True)  # 媒體檔案的唯一識別碼
    original_filename = db.Column(db.String(255))  # 原始檔案名稱
    file_type = db.Column(db.String(10), nullable=False)  # 檔案類型（image 或 video）
    upload_path = db.Column(db.String(500))  # 上傳檔案的儲存路徑
    output_path = db.Column(db.String(500))  # 處理後檔案的儲存路徑
    process_mode = db.Column(db.String(20))  # 處理模式（mosaic：馬賽克 / eyes：遮眼 / replace：替換）
    face_count = db.Column(db.Integer, default=0)  # 偵測到的人臉數量
    status = db.Column(db.String(20), default="uploaded")  # 檔案狀態（uploaded：已上傳 / processed：已處理）
    created_at = db.Column(db.DateTime, default=datetime.now)  # 上傳時間
    processed_at = db.Column(db.DateTime)  # 處理完成時間
    
    # 關聯欄位：這個媒體檔案屬於哪個使用者
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    
    def __repr__(self):
        """物件的字串表示（用於除錯）"""
        return f"<Media {self.media_id}>"
