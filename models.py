from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """使用者資料表"""
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    verified_at = db.Column(db.DateTime, default=datetime.now)  # 註冊時間
    
    def set_password(self, password):
        """設定加密密碼"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """驗證密碼"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User {self.email}>"


class Media(db.Model):

    __tablename__ = "media"
    
    id = db.Column(db.Integer, primary_key=True)
    media_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    original_filename = db.Column(db.String(255))
    file_type = db.Column(db.String(10), nullable=False)  # image / video
    upload_path = db.Column(db.String(500))
    output_path = db.Column(db.String(500))
    process_mode = db.Column(db.String(20))  # mosaic / eyes / replace
    face_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="uploaded")  # uploaded / processed
    created_at = db.Column(db.DateTime, default=datetime.now)
    processed_at = db.Column(db.DateTime)
    
    # 關聯使用者（可選，未來功能）
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    
    def __repr__(self):
        return f"<Media {self.media_id}>"
