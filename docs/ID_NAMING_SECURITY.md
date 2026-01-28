# ID / 命名規則與防爬、防猜解建議

## 一、目前系統的弱點（容易被爬蟲／破解的原因）

| 項目 | 現況 | 風險 |
|------|------|------|
| **展覽 URL** | `/exhibition/1`, `/exhibition/2`… 連續整數 | 腳本可輕鬆跑 `/exhibition/1`～`/exhibition/9999` 把全部展覽撈完 |
| **媒體管理 URL** | `/media/exhibition/3`、`/media/abc123/download` | 展覽 id 可列舉；media_id 若含規律也較好猜 |
| **media_id 內容** | `20260127_143052_U1_E3_video_demo_f2c1` | 內含日期時間、使用者 id(U1)、展覽 id(E3)，可推測規律、用量、結構 |
| **photo_id** | 整數 1, 2, 3… | 同一展覽下可被列舉，猜出所有照片 |

只要「編號可預測、可列舉」，就會：
- 被爬蟲依序請求，大量抓取
- 被攻擊者用腳本猜出有效 id，取得不該看到的資源

---

## 二、建議的命名／ID 規則（不易被爬、不易被破解）

### 1. 對外識別碼不要用「連續整數」

- **不要**：`/exhibition/3`、`/user/5`、`/photo/12`
- **要**：用「不可預測、不可列舉」的識別碼，例如：
  - **UUID v4**：`a1b2c3d4-e5f6-4789-abcd-ef0123456789`（或去掉 `-` 的 32 字元）
  - **隨機 token**：至少 16～24 字元，來自 `secrets.token_urlsafe(24)` 或 `uuid.uuid4().hex`
- 資料庫內部仍可保留 `id` 整數做主鍵，對外則用 `public_id` / `token` 查詢。

### 2. 檔案／媒體 ID 不要暴露「誰、什麼展覽、何時」

- **不要**：`20260127_143052_U1_E3_demo_f2c1`（時間 + 使用者 + 展覽 + 短隨機）
- **要**：純隨機字串，例如：
  - `a3f8c2e91b4d5f6a7e8c9d0b1a2f3e4`（uuid4.hex）
  - 或 `kR2vN8pQ_xYz4wL9mT3sB6h`（token_urlsafe）
- 使用者、展覽、時間等只存在資料庫欄位，不對外出現在檔名或 URL。

### 3. 長度與字元集

- **長度**：至少 16 字元，建議 24～32 字元，讓暴力猜測成本極高。
- **字元集**：`0-9a-f`（hex）或 `0-9a-zA-Z_-`（urlsafe），避免有語意的前綴（如 U、E、日期）。

### 4. 統一回應，避免「列舉差異」

- 無效 id 或無權限時，**不要**用不同訊息暗示「此 id 存在但你不該看」。
- 建議：無效 id 與無權限都回 **404** 或統一的錯誤頁，減少「試出有效 id」的資訊。

### 5. 搭配其他防護（不是命名，但要一起做）

- **登入與權限**：需登入的資料一律檢查 `current_user` 與資源所屬。
- **Rate limit**：同一 IP／同一帳號的請求頻率限制，降低爬蟲與暴力猜 id 的效果。
- **CAPTCHA / 機器人偵測**：在敏感操作（下載、大量查詢）可考慮加上。

---

## 三、規則簡表（方便對照）

| 原則 | 實作方式 |
|------|----------|
| 對外 ID 不連續、不可列舉 | 展覽／使用者／照片的「公開連結」改用 UUID 或 long random token |
| 媒體 ID 不帶語意 | 僅用 `uuid4().hex` 或 `secrets.token_urlsafe(24)`，不包含 U/E/時間 |
| 長度足夠 | 至少 16 字元，建議 24～32 |
| 無洩漏的錯誤差異 | 無效／無權限都回 404 或同一錯誤，不透露「id 是否存在」 |

---

## 四、媒體 ID（media_id）已採用格式

已實作為「8 + 15 位數字序號 + 4 碼隨機數字」（共 20 字元），例：`8000000000000001XXXX`。

- **序號**：依 `media.id` 產生，寫入 DB 後才可知序號，故上傳流程為「暫用 temp_id 存檔 → 建立 Media 並 commit → 以 `media.id` 算出正式 media_id → rename 相關檔案並更新 DB」。
- **編修**：若上傳時未做隱私處理、之後才在媒體管理按「處理」並送出選項，則**只重算最後 4 碼隨機數字**，前 16 字元不變；同時 rename 所有以該 media_id 命名的檔案（upload、output、preview、faces.json、face crops、overlay），並更新 `Media` 與 `ExhibitionPhoto` 的路徑。

`Media.media_id` 欄位為 `String(50)`，20 字元已足夠。

---

## 五、已實作：User / Exhibition / Media 對外 ID 格式（確定版）

本專案已採用以下格式，之後依此為準、不再變更：

### 1. User public_id

- **格式**：`600000000001XXXXXXXX`（共 20 字元）
- **規則**：**6** + **11 位數字序號**（依 `users.id`）+ **8 碼隨機數字**（0–9）
- 後台網址：`/admin/users/<user_public_id>/set_role`、`/toggle_active`。

### 2. Exhibition public_id

- **格式**：`700000000001XXXXXXXX`（共 16 字元）
- **規則**：**7** + **9 位數字序號**（依 `exhibitions.id`）+ **6 碼隨機數字**（0–9）
- 網址：`/exhibition/<exhibition_public_id>`、`/exhibition/<exhibition_public_id>/cover`、`/exhibition/<exhibition_public_id>/photo/<photo_id>` 等；媒體管理為 `/media/exhibition/<exhibition_public_id>`。

### 3. Media media_id（影像檔）

- **格式**：`8000000000000001XXXX`（共 20 字元）
- **規則**：**8** + **15 位數字序號**（依 `media.id`）+ **4 碼隨機數字**（0–9）
- **編修**：若上傳時未做隱私處理、之後才在「媒體管理」按「處理」並送出隱私選項，系統會**只重算 media_id 最後 4 碼隨機數字**，其餘不變；同時會將對應的檔名、路徑（upload、output、preview、faces.json、face crops 等）一併 rename 並更新 DB。

### 4. 既有資料與內部 id

- 請執行一次：`py scripts/add_public_ids.py`（需先設定 `DATABASE_URL`），會回填 `users.public_id`、`exhibitions.public_id`。Media 新上傳一律使用上述 8+15+4 格式。
- 程式內部、DB 關聯、權限檢查仍用整數 `id`；對外連結與重新導向使用各表之對外 ID。
