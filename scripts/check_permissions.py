"""
權限系統驗證腳本
檢查權限系統是否正確設置
"""

import os
import sys
from pathlib import Path

# 添加專案根目錄到路徑
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# 設定 UTF-8 輸出
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 檢查環境變數
if not os.environ.get("DATABASE_URL"):
    print("錯誤：缺少 DATABASE_URL 環境變數")
    print("請先設置環境變數，例如：")
    print("  set DATABASE_URL=mysql+pymysql://root:password@localhost:3306/photobluuring")
    sys.exit(1)

# 初始化 Flask 應用
from app import app
from core.models import db, User, Exhibition

def check_permissions_system():
    """檢查權限系統設置"""
    print("=" * 60)
    print("權限系統驗證")
    print("=" * 60)
    
    with app.app_context():
        # 1. 檢查資料庫欄位
        print("\n[1] 檢查資料庫欄位...")
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            has_role = 'role' in columns
            has_is_super_admin = 'is_super_admin' in columns
            
            if has_role and has_is_super_admin:
                print("  ✓ role 欄位存在")
                print("  ✓ is_super_admin 欄位存在")
            else:
                print("  ✗ 缺少必要欄位！")
                if not has_role:
                    print("    - 缺少 role 欄位")
                if not has_is_super_admin:
                    print("    - 缺少 is_super_admin 欄位")
                return False
        except Exception as e:
            print(f"  ✗ 檢查資料庫欄位失敗：{str(e)}")
            return False
        
        # 2. 檢查用戶角色
        print("\n[2] 檢查用戶角色...")
        try:
            users = User.query.all()
            if not users:
                print("  ⚠ 資料庫中沒有用戶")
                return False
            
            print(f"  找到 {len(users)} 個用戶：")
            super_admin_count = 0
            admin_count = 0
            user_count = 0
            
            for user in users:
                role_display = user.role if hasattr(user, 'role') else '未知'
                is_super = user.is_super_admin if hasattr(user, 'is_super_admin') else False
                
                if is_super or role_display == User.ROLE_SUPER_ADMIN:
                    super_admin_count += 1
                    print(f"    - {user.email} (ID: {user.id}) - {role_display} [超級管理員]")
                elif role_display == User.ROLE_ADMIN:
                    admin_count += 1
                    print(f"    - {user.email} (ID: {user.id}) - {role_display} [管理員]")
                else:
                    user_count += 1
                    print(f"    - {user.email} (ID: {user.id}) - {role_display} [一般使用者]")
            
            if super_admin_count == 0:
                print("\n  ⚠ 警告：沒有超級管理員！")
                print("  請執行以下 SQL 設置第一個用戶為超級管理員：")
                print("  UPDATE users SET role = 'SUPER_ADMIN', is_super_admin = TRUE WHERE id = 1 LIMIT 1;")
            else:
                print(f"\n  ✓ 找到 {super_admin_count} 個超級管理員")
            
        except Exception as e:
            print(f"  ✗ 檢查用戶角色失敗：{str(e)}")
            return False
        
        # 3. 檢查 User 模型方法
        print("\n[3] 檢查 User 模型方法...")
        try:
            test_user = User.query.first()
            if not test_user:
                print("  ⚠ 沒有用戶可以測試")
            else:
                methods = [
                    'is_super_admin_role',
                    'is_admin_role',
                    'can_manage_exhibition',
                    'can_set_user_role'
                ]
                all_exist = True
                for method_name in methods:
                    if hasattr(test_user, method_name):
                        print(f"  ✓ {method_name}() 方法存在")
                    else:
                        print(f"  ✗ {method_name}() 方法不存在")
                        all_exist = False
                
                if all_exist:
                    # 測試方法是否正常工作
                    try:
                        is_super = test_user.is_super_admin_role()
                        is_admin = test_user.is_admin_role()
                        print(f"  ✓ 方法測試通過（is_super_admin_role: {is_super}, is_admin_role: {is_admin}）")
                    except Exception as e:
                        print(f"  ✗ 方法執行錯誤：{str(e)}")
                        return False
        except Exception as e:
            print(f"  ✗ 檢查 User 模型方法失敗：{str(e)}")
            return False
        
        # 4. 檢查展覽權限
        print("\n[4] 檢查展覽權限...")
        try:
            exhibitions = Exhibition.query.all()
            print(f"  找到 {len(exhibitions)} 個展覽")
            
            if exhibitions and test_user:
                exhibition = exhibitions[0]
                can_manage = test_user.can_manage_exhibition(exhibition)
                print(f"  測試用戶 {test_user.email} 對展覽 '{exhibition.title}' 的管理權限：{can_manage}")
        except Exception as e:
            print(f"  ✗ 檢查展覽權限失敗：{str(e)}")
        
        # 5. 檢查路由模組
        print("\n[5] 檢查路由模組...")
        try:
            from core import decorators
            from core import admin
            
            # 檢查裝飾器
            decorators_list = ['super_admin_required', 'admin_required', 'can_manage_exhibition']
            for dec_name in decorators_list:
                if hasattr(decorators, dec_name):
                    print(f"  ✓ {dec_name} 裝飾器存在")
                else:
                    print(f"  ✗ {dec_name} 裝飾器不存在")
            
            # 檢查 admin 藍圖
            if hasattr(admin, 'admin_bp'):
                print(f"  ✓ admin 藍圖存在")
                print(f"    路由前綴：{admin.admin_bp.url_prefix}")
            else:
                print(f"  ✗ admin 藍圖不存在")
                return False
                
        except Exception as e:
            print(f"  ✗ 檢查路由模組失敗：{str(e)}")
            return False
        
        # 總結
        print("\n" + "=" * 60)
        print("驗證完成！")
        print("=" * 60)
        print("\n下一步：")
        print("1. 啟動應用程式：python app.py")
        print("2. 使用超級管理員帳號登入")
        print("3. 訪問管理員頁面：")
        print("   - http://localhost:5000/admin/users (用戶管理)")
        print("   - http://localhost:5000/admin/exhibitions (展覽管理)")
        print("\n如果看到 403 錯誤，請確認：")
        print("- 已登入")
        print("- 當前用戶是超級管理員或管理員")
        print("- 資料庫中的 role 和 is_super_admin 欄位已正確設置")
        
        return True


if __name__ == "__main__":
    success = check_permissions_system()
    sys.exit(0 if success else 1)
