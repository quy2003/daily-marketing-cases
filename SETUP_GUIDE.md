# 🛠️ Hướng dẫn Thiết lập và Vận hành Hệ thống

Tài liệu này hướng dẫn anh từng bước cấu hình dự án trên GitHub để hệ thống tự động gửi bài phân tích & podcast về hòm thư Gmail vào lúc 12h00 trưa hàng ngày, cũng như đồng bộ lên giao diện Web App.

---

## Bước 1: Tạo Kho lưu trữ (GitHub Repository)
1. Truy cập [GitHub](https://github.com/) và tạo một repository mới (ví dụ đặt tên: `daily-marketing-cases`).
2. Chọn chế độ **Public** (Để sử dụng tính năng GitHub Pages miễn phí).
3. Đẩy toàn bộ mã nguồn này lên nhánh `main` của repository đó:
   - Các file: `index.html`, `requirements.txt`, `README.md`, `SETUP_GUIDE.md`, thư mục `src/`, thư mục `.github/`.

---

## Bước 2: Cấu hình GitHub Pages (Giao diện Web App)
1. Trên repository của anh trên GitHub, truy cập vào mục **Settings** (Cài đặt) ở thanh công cụ phía trên.
2. Chọn mục **Pages** ở danh mục bên trái.
3. Tại phần **Build and deployment**:
   - **Source:** Chọn `Deploy from a branch`.
   - **Branch:** Chọn `main` và thư mục `/ (root)`.
4. Nhấn **Save**. 
5. Chờ khoảng 1-2 phút, GitHub sẽ hiển thị đường link trang web của anh dạng: `https://<ten-user>.github.io/daily-marketing-cases/`.

---

## Bước 3: Lấy khóa Gemini API Key (Miễn phí)
1. Truy cập [Google AI Studio](https://aistudio.google.com/).
2. Đăng nhập bằng tài khoản Google của anh.
3. Nhấp vào nút **Get API key** ở góc trên bên trái.
4. Chọn **Create API key** và sao chép mã khóa (dạng `AIzaSy...`).

---

## Bước 4: Tạo Mật khẩu Ứng dụng (App Password) cho Gmail gửi đi
Để script Python tự động gửi email thông qua tài khoản Gmail của anh mà không bị Google chặn vì lý do bảo mật, anh cần tạo **Mật khẩu ứng dụng**:
1. Truy cập vào trang quản lý [Tài khoản Google của bạn](https://myaccount.google.com/).
2. Chọn mục **Bảo mật (Security)** ở danh mục bên trái.
3. Đảm bảo tài khoản của anh đã kích hoạt **Xác minh 2 bước (2-Step Verification)**.
4. Nhập vào ô tìm kiếm ở trên cùng từ khóa `"Mật khẩu ứng dụng"` hoặc `"App Passwords"`.
5. Tạo một mật khẩu ứng dụng mới:
   - Tên ứng dụng: Đặt tên gợi nhớ (ví dụ: `GitHub Actions Marketing`).
   - Nhấn **Tạo (Create)**.
6. Google sẽ hiển thị một cửa sổ có chứa **mã khóa 16 ký tự** (ví dụ: `abcd efgh ijkl mnop`). Hãy sao chép mã này (không cần sao chép dấu cách).

---

## Bước 5: Cấu hình GitHub Secrets (Bảo mật thông tin)
Để bảo mật API Key và Mật khẩu Gmail, anh cần khai báo chúng vào mục Secrets của Repository:
1. Trên repository GitHub, vào mục **Settings** -> **Secrets and variables** -> **Actions**.
2. Nhấn nút **New repository secret** ở góc phải.
3. Lần lượt tạo 4 Secret sau:
   - **`GEMINI_API_KEY`**: Dán mã API Key của Gemini lấy ở Bước 3.
   - **`SENDER_EMAIL`**: Địa chỉ Gmail của anh dùng để gửi email đi (ví dụ: `myemail@gmail.com`).
   - **`SENDER_PASSWORD`**: Dán mã mật khẩu ứng dụng 16 ký tự lấy ở Bước 4.
   - **`RECEIVER_EMAIL`**: Địa chỉ email nhận thông báo hàng ngày (có thể trùng với `SENDER_EMAIL` để anh tự gửi cho chính mình).

---

## Bước 6: Thay đổi Mật khẩu Vault cho Web App (Tùy chọn)
Mật khẩu truy cập mặc định trên Web App là **`cmo2026`**. Nếu anh muốn đổi sang mật khẩu của riêng mình:
1. Truy cập một trang web tạo mã Hash SHA-256 (ví dụ: [md5hashgenerator.com](https://www.md5hashgenerator.com/sha256-generator.html)).
2. Nhập mật khẩu mới của anh (ví dụ: `mysecretpass`) và nhấn tạo mã hash. Anh sẽ nhận được một chuỗi 64 ký tự dạng Hex (ví dụ: `d9...`).
3. Mở file [index.html](file:///d:/Tôi bị ngu CASE/index.html) trong dự án của anh.
4. Tìm đến dòng số `456`:
   ```javascript
   const VAULT_HASH = "b428d052d9a695b28d54d193d562211e406f5223363e157790b8fcf6144e5a95"; 
   ```
5. Thay thế chuỗi mã băm trong dấu ngoặc kép bằng chuỗi mã băm mật khẩu mới của anh.
6. Commit và Push thay đổi lên GitHub.

---

## Bước 7: Chạy kiểm thử thủ công ngay lập tức
Anh không cần chờ đến 12h trưa mai để biết hệ thống hoạt động ra sao. Anh có thể kích hoạt chạy thử thủ công:
1. Trên repository GitHub, truy cập vào mục **Actions** ở thanh công cụ phía trên.
2. Ở danh mục bên trái, chọn workflow **Daily Marketing Case Study Generator**.
3. Nhấp vào nút **Run workflow** -> Chọn Branch `main` -> Nhấp **Run workflow** (nút màu xanh).
4. Hệ thống sẽ bắt đầu chạy (mất khoảng 1-2 phút để Gemini sinh bài học và Edge TTS sinh file podcast giọng đọc). Sau khi chạy xong:
   - Anh mở hòm thư Email kiểm tra thư thông báo mới.
   - Nhấn nút trong email để mở Web App.
   - Đăng nhập bằng mật khẩu `cmo2026` và thưởng thức bài học đầu tiên!
