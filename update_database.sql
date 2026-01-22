-- 更新 media 資料表，新增 user_id 欄位
-- 如果您的資料庫中已經有重要資料，請使用這個 SQL 腳本

USE photobluuring;

-- 新增 user_id 欄位到 media 資料表
ALTER TABLE media 
ADD COLUMN user_id INT NULL AFTER processed_at,
ADD FOREIGN KEY (user_id) REFERENCES users(id);

-- 查看更新後的資料表結構
DESCRIBE media;

SELECT 'Database updated successfully!' AS status;
