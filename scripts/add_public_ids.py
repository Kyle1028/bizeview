"""
為 users、exhibitions 新增 public_id 欄位並回填既有資料
執行一次即可。新建立的 User/Exhibition 會由程式自動寫入 public_id。
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

if not os.environ.get("DATABASE_URL"):
    print("錯誤：缺少 DATABASE_URL 環境變數")
    sys.exit(1)

from app import app
from core.models import db, User, Exhibition, _public_id_user, _public_id_exhibition


def ensure_column(engine, table: str, column: str, spec: str):
    """若欄位不存在則 ALTER TABLE 新增。spec 例：VARCHAR(36) UNIQUE NULL"""
    from sqlalchemy import text, inspect
    insp = inspect(engine)
    cols = [c["name"] for c in insp.get_columns(table)]
    if column in cols:
        return
    with engine.begin() as c:
        c.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {spec}"))
    print(f"  已新增欄位 {table}.{column}")


def _is_new_format_user(pid):
    """是否已是 6+11+8 格式（20 字元且以 6 開頭）"""
    return pid and len(pid) == 20 and pid[0] == "6"


def _is_new_format_exhibition(pid):
    """是否已是 7+9+6 格式（16 字元且以 7 開頭）"""
    return pid and len(pid) == 16 and pid[0] == "7"


def backfill_public_ids(force=False):
    """
    force=True：全部改為新格式（含舊 UUID），適用於要把既有帳號/展覽的 public_id 換成 6+11+8、7+9+6。
    force=False：只補填 public_id 為 NULL 的筆數。
    """
    with app.app_context():
        engine = db.engine
        dialect = engine.dialect.name

        print("檢查並新增 public_id 欄位...")
        if dialect == "mysql":
            ensure_column(engine, "users", "public_id", "VARCHAR(36) NULL UNIQUE")
            ensure_column(engine, "exhibitions", "public_id", "VARCHAR(36) NULL UNIQUE")
        else:
            ensure_column(engine, "users", "public_id", "VARCHAR(36) UNIQUE")
            ensure_column(engine, "exhibitions", "public_id", "VARCHAR(36) UNIQUE")

        if force:
            print("強制以新格式覆寫 users.public_id（6+11位序號+8碼隨機）...")
            users = User.query.all()
        else:
            print("回填 users.public_id（6+11位序號+8碼隨機，僅補 NULL）...")
            users = [u for u in User.query.all() if u.public_id is None or not _is_new_format_user(u.public_id)]
        n_user = 0
        for u in users:
            u.public_id = _public_id_user(u.id)
            n_user += 1
        if n_user:
            db.session.commit()
        print(f"  已處理 {n_user} 筆 users")

        if force:
            print("強制以新格式覆寫 exhibitions.public_id（7+9位序號+6碼隨機）...")
            exhibitions = Exhibition.query.all()
        else:
            print("回填 exhibitions.public_id（7+9位序號+6碼隨機，僅補 NULL）...")
            exhibitions = [e for e in Exhibition.query.all() if e.public_id is None or not _is_new_format_exhibition(e.public_id)]
        n_ex = 0
        for e in exhibitions:
            e.public_id = _public_id_exhibition(e.id)
            n_ex += 1
        if n_ex:
            db.session.commit()
        print(f"  已處理 {n_ex} 筆 exhibitions")

        print("完成。")


if __name__ == "__main__":
    force = "--force" in sys.argv
    if force:
        print("使用 --force：將所有 users / exhibitions 的 public_id 改為新格式（覆寫舊 UUID）\n")
    backfill_public_ids(force=force)
