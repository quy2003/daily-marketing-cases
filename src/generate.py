import os
import json
import asyncio
import random
import re
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import google.generativeai as genai
import edge_tts
import typing_extensions as typing
from pydantic import BaseModel, Field

class GlossaryItem(BaseModel):
    term: str = Field(description="Tên thuật ngữ marketing")
    definition: str = Field(description="Định nghĩa thuật ngữ")
    example: str = Field(description="Ví dụ minh họa thuật ngữ")

class CaseBrief(BaseModel):
    client_profile: str = Field(description="Thông tin/Bối cảnh của doanh nghiệp")
    market_context: str = Field(description="Bối cảnh thị trường và đối thủ")
    target_insight: str = Field(description="Sự thật ngầm hiểu về khách hàng")
    problem_statement: str = Field(description="Bài toán chiến lược cần giải")

class ChampionProposal(BaseModel):
    positioning: str = Field(description="Định hướng định vị thương hiệu")
    big_idea: str = Field(description="Ý tưởng lớn/Slogan chiến dịch")
    imc_plan: str = Field(description="Kế hoạch truyền thông tích hợp")
    kpi_budget: str = Field(description="KPIs đo lường và phân bổ ngân sách")

class MarketingCase(BaseModel):
    brand: str = Field(description="Tên thương hiệu")
    title: str = Field(description="Tiêu đề bài phân tích")
    theme: str = Field(description="Chủ đề cốt lõi của case")
    one_minute_takeaway: str = Field(description="Tóm tắt nhanh trong 1 phút")
    case_brief: CaseBrief = Field(description="Nội dung Case Brief")
    champion_proposal: ChampionProposal = Field(description="Nội dung giải pháp đạt giải")
    historical_reflection: str = Field(description="Đối chiếu thực tế lịch sử hoặc bình luận chiến lược")
    glossary: typing.List[GlossaryItem] = Field(description="Từ điển thuật ngữ marketing thực chiến")
    action_checklist: typing.List[str] = Field(description="Danh sách hành động thực tế ngày mai (3 hành động)")
    reflection_questions: typing.List[str] = Field(description="Góc nghiền ngẫm với 3 câu hỏi gợi mở")
    podcast_script: str = Field(description="Kịch bản Podcast tiếng Việt thời lượng dài tự nhiên")

# Cấu hình đường dẫn
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES_MD_DIR = os.path.join(BASE_DIR, "cases", "markdown")
CASES_AUDIO_DIR = os.path.join(BASE_DIR, "cases", "audio")
DATA_FILE = os.path.join(BASE_DIR, "data.json")
README_FILE = os.path.join(BASE_DIR, "README.md")

# Tạo các thư mục nếu chưa tồn tại
os.makedirs(CASES_MD_DIR, exist_ok=True)
os.makedirs(CASES_AUDIO_DIR, exist_ok=True)

def load_env():
    """Tự động tải các biến môi trường từ file .env nếu có (không cần cài thêm python-dotenv)."""
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        print("Loading environment variables from local .env file...")
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip().strip('"').strip("'")

# Tải cấu hình từ .env nếu chạy ở máy cục bộ
load_env()

# Lấy các biến môi trường
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")
# Fallback local URL or custom URL for GitHub Pages
GITHUB_PAGES_URL = os.environ.get("GITHUB_PAGES_URL", "https://your-github-username.github.io/daily-marketing-cases")

# Khởi tạo Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not found in environment. Local test may fail.")

def get_existing_cases():
    """Đọc dữ liệu data.json hiện tại."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading data.json: {e}")
            return []
    return []

def save_cases_data(data):
    """Lưu dữ liệu vào data.json."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_skills_xp(case_type):
    """Sinh điểm XP ngẫu nhiên nhưng hợp lý cho các nhóm kỹ năng."""
    skills = ["Branding", "Growth Hacking", "Crisis Management", "Product Fit"]
    xp_distribution = {}
    
    # Phân bổ XP ngẫu nhiên tổng cộng khoảng 25-40 XP mỗi case
    total_xp = random.randint(25, 40)
    
    # Chọn 1 kỹ năng chủ đạo nhận nhiều XP nhất
    primary_skill = random.choice(skills)
    xp_distribution[primary_skill] = random.randint(15, 25)
    
    remaining_xp = total_xp - xp_distribution[primary_skill]
    secondary_skill = random.choice([s for s in skills if s != primary_skill])
    xp_distribution[secondary_skill] = remaining_xp
    
    # Điền 0 XP cho các kỹ năng còn lại
    for s in skills:
        if s not in xp_distribution:
            xp_distribution[s] = 0
            
    return xp_distribution

async def generate_podcast_audio(script_text, output_path):
    """Sử dụng Edge-TTS để tạo file âm thanh tiếng Việt chất lượng cao."""
    # vi-VN-HoaiMyNeural là giọng nữ miền Nam rất tự nhiên
    # vi-VN-NamMinhNeural là giọng nam miền Nam rất tự nhiên
    voice = "vi-VN-HoaiMyNeural" 
    
    # Làm sạch kịch bản (loại bỏ các thẻ như [MC1], [MC2], hay các ghi chú trong ngoặc vuông)
    clean_text = re.sub(r'\[.*?\]', '', script_text)
    clean_text = re.sub(r'\(.*?\)', '', clean_text)
    
    communicate = edge_tts.Communicate(clean_text, voice)
    await communicate.save(output_path)
    print(f"Saved Podcast audio: {os.path.basename(output_path)}")

def build_prompt(case_number, is_present, covered_brands):
    """Tạo Prompt chất lượng cao gửi cho Gemini API."""
    brands_str = ", ".join(covered_brands) if covered_brands else "chưa có"
    
    if is_present:
        type_desc = "HIỆN TẠI (Năm 2025/2026)"
        scenario_guideline = (
            "Hãy chọn một bài toán Marketing/Kinh doanh THỰC TẾ và NÓNG HỔI mà một tập đoàn lớn trên thế giới hoặc ở Việt Nam "
            "(như VinFast, Shopee, OpenAI, Netflix, Tesla, TikTok, Coca-Cola, Apple...) ĐANG ĐỐI MẶT ở thời điểm hiện tại. "
            "Phân tích sâu sắc các xu hướng mới nhất như AI Marketing, bảo mật dữ liệu, sự dịch chuyển hành vi của Gen Z/Gen Alpha, "
            "sự bùng nổ của video ngắn, thương mại điện tử thế hệ mới..."
        )
    else:
        type_desc = "QUÁ KHỨ (Lịch sử)"
        scenario_guideline = (
            "Hãy chọn một Case Study Marketing KINH ĐIỂN và THÀNH CÔNG trong lịch sử (như Nike 1988, Airbnb 2009, Spotify 2011, "
            "Pepsi, Starbucks, Pepsi Challenge, Apple 1997 'Think Different'...). Tập trung sâu vào bối cảnh văn hóa - xã hội thời kỳ đó, "
            "lịch sử thương hiệu và phân tích nguyên nhân gốc rễ (Root Cause) vì sao họ đưa ra các quyết định sinh tử đó."
        )

    prompt = f"""
Bạn là một Giám đốc Marketing (CMO) kỳ cựu và là chuyên gia biên soạn đề thi Giải Case Study Marketing.
Nhiệm vụ của bạn là tạo ra Case Study thứ #{case_number} thuộc thể loại {type_desc}.

CÁC THƯƠNG HIỆU ĐÃ ĐƯỢC HỌC (KHÔNG ĐƯỢC CHỌN LẠI): {brands_str}. Hãy chọn một thương hiệu nổi tiếng khác ngoài danh sách này.

HƯỚNG DẪN NỘI DUNG:
{scenario_guideline}

Hãy thiết kế nội dung bài phân tích này theo cấu trúc chuẩn của một Cuộc thi Giải Case Marketing danh giá và trả về kết quả dưới dạng cấu trúc JSON chính xác như định nghĩa bên dưới.

LƯU Ý QUAN TRỌNG VỀ ĐỘ DÀI: Để đảm bảo phản hồi không bị quá tải giới hạn token của hệ thống, hãy viết cực kỳ ngắn gọn, súc tích và cô đọng. Tránh viết quá dài dòng ở các mục.

YÊU CẦU CẤU TRÚC JSON PHẢN HỒI:
Trả về duy nhất một đối tượng JSON (không chứa ký tự thừa bên ngoài, đặt trong block ```json ... ```) có các trường sau:

1. "brand": Tên thương hiệu (ví dụ: "Nike")
2. "title": Tiêu đề Case Study ngắn gọn (ví dụ: "Nike 1988: Vực dậy bằng 'Just Do It'")
3. "theme": Chủ đề cốt lõi (ví dụ: "Emotional Branding")
4. "one_minute_takeaway": Tóm tắt nhanh trong 2-3 câu ngắn gọn chứa giá trị cốt lõi.
5. "case_brief" (chứa các chuỗi Markdown ngắn gọn):
   - "client_profile": Giới thiệu doanh nghiệp và tình thế (tối đa 3 câu).
   - "market_context": Bối cảnh thị trường, đối thủ cạnh tranh (tối đa 3 câu).
   - "target_insight": Thấu hiểu khách hàng / sự thật ngầm hiểu (tối đa 2 câu).
   - "problem_statement": Câu hỏi chiến lược / Bài toán cốt lõi cần giải quyết (1 câu).
6. "champion_proposal" (chứa các chuỗi Markdown ngắn gọn):
   - "positioning": Định hướng định vị thương hiệu ngắn gọn (tối đa 2 câu).
   - "big_idea": Ý tưởng lớn đột phá / Slogan chiến dịch.
   - "imc_plan": Kế hoạch truyền thông 3 giai đoạn (Trigger - Engage - Amplify) viết ngắn gọn dưới dạng gạch đầu dòng.
   - "kpi_budget": KPIs hiệu quả và phân bổ ngân sách tóm tắt ngắn.
7. "historical_reflection": Bình luận & Đối chiếu thực tế lịch sử hoặc xu hướng tương lai ngắn gọn trong 1 đoạn văn (tối đa 4-5 câu).
8. "glossary": Danh sách 2 thuật ngữ marketing cốt lõi sử dụng trong bài:
   - Một mảng gồm các đối tượng: {{"term": "Tên thuật ngữ", "definition": "Định nghĩa bình dân ngắn gọn", "example": "Ví dụ cụ thể rất ngắn"}}
9. "action_checklist": Mảng gồm 3 hành động cụ thể áp dụng được ngay vào ngày mai (Checklist hành động ngắn).
10. "reflection_questions": Mảng gồm 3 câu hỏi gợi mở để người học tự suy ngẫm.
11. "podcast_script": Kịch bản Podcast Tiếng Việt thời lượng ngắn gọn, súc tích (khoảng 300 - 450 từ).
    - Viết dưới dạng kịch bản nói cuốn hút, tự nhiên, đi thẳng vào các ý chính (bối cảnh, giải pháp, bài học cốt lõi).
    - Không viết dài dòng lê thê để tránh bị cắt cụt. Kịch bản viết bằng tiếng Việt trôi chảy, không chứa các ký tự hướng dẫn giọng đọc trong ngoặc.

Chú ý: Hãy đảm bảo văn phong chuyên nghiệp, cô đọng, sâu sắc.
"""
    return prompt

def generate_case_study(case_number, is_present, covered_brands):
    """Gọi Gemini API để tạo nội dung Case Study."""
    prompt = build_prompt(case_number, is_present, covered_brands)
    
    # Cấu hình model
    # gemini-2.5-flash là model nhanh và có hỗ trợ JSON output định cấu trúc tốt
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    print(f"Calling Gemini API to generate Case Study #{case_number} ({'Present' if is_present else 'Past'})...")
    response = model.generate_content(
        prompt,
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": MarketingCase,
            "max_output_tokens": 8192
        },
        request_options={"timeout": 180}
    )
    
    # Parse JSON
    try:
        content_text = response.text.strip()
        try:
            with open("debug_response.txt", "w", encoding="utf-8") as f:
                f.write(content_text)
        except Exception as write_err:
            print(f"Could not save debug response: {write_err}")

        if content_text.startswith("```json"):
            content_text = content_text[7:]
        if content_text.endswith("```"):
            content_text = content_text[:-3]
        content_text = content_text.strip()
        
        case_data = json.loads(content_text)
        return case_data
    except Exception as e:
        print(f"Error parsing JSON from Gemini: {e}")
        try:
            with open("debug_response.txt", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("Received invalid response. Raw text saved to debug_response.txt for inspection.")
        except Exception as write_err:
            print(f"Could not save debug response: {write_err}")
        raise e

def save_to_markdown(case, case_number, date_str):
    """Chuyển đổi dữ liệu JSON thành file Markdown đẹp mắt để lưu trữ trên GitHub."""
    brand = case.get("brand", "Unknown")
    filename = f"{date_str}-{brand.lower().replace(' ', '-')}.md"
    filepath = os.path.join(CASES_MD_DIR, filename)
    
    # Định dạng mảng thành Markdown
    glossary_md = ""
    for item in case.get("glossary", []):
        glossary_md += f"**{item.get('term', '')}**: {item.get('definition', '')}\n* *Ví dụ:* {item.get('example', '')}\n\n"
        
    checklist_md = ""
    for item in case.get("action_checklist", []):
        checklist_md += f"- [ ] {item}\n"
        
    questions_md = ""
    for i, item in enumerate(case.get("reflection_questions", [])):
        questions_md += f"{i+1}. {item}\n"

    case_brief = case.get("case_brief", {})
    champion_proposal = case.get("champion_proposal", {})

    # Tạo nội dung Markdown
    md_content = f"""# [CASE #{case_number}] {case.get('title', 'Untitled')}

- **Thương hiệu:** {brand}
- **Chủ đề cốt lõi:** `{case.get('theme', 'General')}`
- **Phân loại:** `{'Hiện tại (2025/2026)' if case.get('type') == 'Present' or case_number % 3 == 0 else 'Quá khứ (Lịch sử)'}`
- **Ngày phát hành:** {date_str}

---

## ⚡ TÓM TẮT 1 PHÚT (The 1-Minute Takeaway)
{case.get('one_minute_takeaway', '')}

---

## 🏆 ĐỀ BÀI CHI TIẾT (Case Brief)

### 🏢 Bối cảnh Doanh nghiệp (Client Profile)
{case_brief.get('client_profile', '')}

### 📊 Bối cảnh Thị trường & Đối thủ (Market Context)
{case_brief.get('market_context', '')}

### 🧠 Thấu hiểu khách hàng (Consumer Insights)
{case_brief.get('target_insight', '')}

### 🎯 Bài toán Chiến lược cần giải quyết (Problem Statement)
> **{case_brief.get('problem_statement', '')}**

---

## 💡 ĐỀ XUẤT ĐẠT GIẢI QUÁN QUÂN (Champion Proposal)

### 🚀 Định vị & Mục tiêu (Positioning)
{champion_proposal.get('positioning', '')}

### 🔮 Ý tưởng lớn (The Big Idea)
> ### **"{champion_proposal.get('big_idea', '')}"**

### 📅 Kế hoạch truyền thông tích hợp (IMC Plan)
{champion_proposal.get('imc_plan', '')}

### 📊 Đo lường & Ngân sách (KPIs & Budget)
{champion_proposal.get('kpi_budget', '')}

---

## 🏛️ ĐỐI CHIẾU THỰC TẾ & BÌNH LUẬN CHIẾN LƯỢC
{case.get('historical_reflection', '')}

---

## 📚 TỪ ĐIỂN THUẬT NGỮ THỰC CHIẾN
{glossary_md}

---

## ✅ HÀNH ĐỘNG THỰC TẾ NGÀY MAI (Actionable Checklist)
{checklist_md}

---

## 🔮 GÓC NGHIỀN NGẪM (Reflection Questions)
{questions_md}
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    print(f"Saved Markdown file: {filename}")
    return filepath, filename

def update_readme(cases_list):
    """Cập nhật README.md với danh sách Case Study và Sơ đồ tư duy liên kết (Mermaid)."""
    # 1. Tạo sơ đồ Mermaid kết nối kiến thức
    # Lấy tối đa 10 case gần nhất để vẽ tránh quá tải biểu đồ
    recent_cases = cases_list[-10:]
    mermaid_lines = []
    mermaid_lines.append("graph TD")
    mermaid_lines.append("    Start[Bắt đầu hành trình học tập] --> DailyCases[Danh sách Case Study]")
    
    unique_themes = set()
    for case in recent_cases:
        brand = case["brand"]
        theme = case["theme"].split("&")[0].strip() # Lấy chủ đề đầu tiên cho ngắn gọn
        unique_themes.add(theme)
        
        # Format ID an toàn cho Mermaid
        brand_id = re.sub(r'[^a-zA-Z0-9]', '', brand)
        theme_id = re.sub(r'[^a-zA-Z0-9]', '', theme)
        
        mermaid_lines.append(f"    DailyCases --> {brand_id}[\"{brand}\"]")
        mermaid_lines.append(f"    {brand_id} --> {theme_id}[\"{theme}\"]")
        
    mermaid_str = "\n".join(mermaid_lines)
    
    # 2. Tạo bảng nhật ký học tập
    table_rows = []
    for case in reversed(cases_list):
        c_type = "🔴 Hiện tại" if case["type"] == "Present" else "🔵 Quá khứ"
        relative_md_path = f"cases/markdown/{case['date']}-{case['brand'].lower().replace(' ', '-')}.md"
        table_rows.append(
            f"| #{case['case_number']} | {case['date']} | **{case['brand']}** | {c_type} | `{case['theme']}` | [Xem chi tiết]({relative_md_path}) |"
        )
    table_str = "\n".join(table_rows)
    
    # 3. Đọc README hiện tại và thay thế nội dung bằng regex hoặc viết lại hoàn toàn
    readme_template = f"""# 🎙️ Daily Marketing Cases & Podcast (WOW Edition)

Hệ thống tự động nghiên cứu, phân tích chuyên sâu các Case Study Marketing kinh điển và hiện đại dưới dạng **Podcast Tiếng Việt** và **Bài viết chuẩn Cuộc thi Giải Case**. Hệ thống tự động gửi thông báo qua Email vào lúc 12h00 trưa hàng ngày và đồng bộ lên giao diện Web App Premium trên GitHub Pages.

---

## 🌀 Các Tính năng Đặc biệt

1. **🔄 Tỷ lệ Học tập 2:1 (Quá khứ & Hiện tại):**
   - 2 Case Quá khứ: Đọc và học các nguyên lý marketing cốt lõi từ các thương hiệu lớn trong lịch sử.
   - 1 Case Hiện tại: Phân tích các thách thức marketing thời sự nóng hổi của các doanh nghiệp lớn ở thời điểm hiện tại (2025/2026).
2. **🏆 Bài giải Chuẩn Cuộc thi (Case Competition Style):**
   - Phân tích chi tiết Thấu hiểu khách hàng (Target Insight), Ý tưởng lớn (Big Idea) và Kế hoạch truyền thông tích hợp (IMC Plan) 3 giai đoạn.
3. **🎙️ Podcast Tiếng Việt Chuyên sâu (7-15 phút):**
   - Bản tin âm thanh phân tích sinh động bằng giọng đọc AI tự nhiên, giúp anh "nghe và thấm" mọi lúc mọi nơi.
4. **🔒 Web App Premium bảo mật (GitHub Pages):**
   - Giao diện Dark Mode, tích hợp trình phát Audio và bộ lọc thông minh, bảo mật bằng mật khẩu cá nhân.

---

## 🕸️ Bản đồ Liên kết Kiến thức (Knowledge Graph)

Dưới đây là sơ đồ liên kết các case study đã học (tự động cập nhật):

```mermaid
{mermaid_str}
```

---

## 📈 Nhật ký Học tập (Study Log)

| Số | Ngày học | Thương hiệu | Phân loại | Chủ đề cốt lõi | Chi tiết |
| :--- | :--- | :--- | :--- | :--- | :--- |
{table_str}

---

## 🛠️ Hướng dẫn cài đặt và thiết lập dự án

*Mở file hướng dẫn thiết lập của dự án để cấu hình GitHub Secrets.*
"""
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(readme_template)
    print("Updated README.md file.")

def send_notification_email(case, case_number, date_str, audio_filename, web_url):
    """Gửi email HTML thông báo (Daily Trigger Email) cho người dùng."""
    if not SENDER_EMAIL or not SENDER_PASSWORD or not RECEIVER_EMAIL:
        print("WARNING: Missing email configuration (SENDER_EMAIL / SENDER_PASSWORD / RECEIVER_EMAIL). Skipping email.")
        return False
        
    c_type = "Hiện tại (2025/2026)" if case.get("type") == "Present" else "Quá khứ (Lịch sử)"
    brand_name = case.get("brand", "Unknown").upper()
    title_name = case.get("title", "Untitled")
    subject = f"[Daily Marketing Case] #{case_number}: {brand_name} - {title_name}"
    
    # Tạo HTML Template sang trọng
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #0d0e12;
                color: #e2e8f0;
                margin: 0;
                padding: 40px 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: rgba(26, 27, 38, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            }}
            .header {{
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
                padding-bottom: 20px;
                margin-bottom: 25px;
            }}
            .badge {{
                display: inline-block;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                border-radius: 20px;
                letter-spacing: 0.5px;
                margin-right: 8px;
            }}
            .badge-past {{
                background-color: rgba(59, 130, 246, 0.15);
                color: #60a5fa;
                border: 1px solid rgba(59, 130, 246, 0.3);
            }}
            .badge-present {{
                background-color: rgba(239, 68, 68, 0.15);
                color: #f87171;
                border: 1px solid rgba(239, 68, 68, 0.3);
            }}
            .title {{
                font-size: 20px;
                font-weight: bold;
                color: #ffffff;
                margin-top: 15px;
                margin-bottom: 5px;
            }}
            .subtitle {{
                font-size: 14px;
                color: #94a3b8;
                margin-bottom: 20px;
            }}
            .takeaway-box {{
                background: rgba(255, 255, 255, 0.03);
                border-left: 4px solid #8b5cf6;
                padding: 15px;
                border-radius: 0 12px 12px 0;
                margin-bottom: 30px;
                line-height: 1.6;
            }}
            .takeaway-title {{
                font-weight: 600;
                color: #c084fc;
                margin-bottom: 8px;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .btn-container {{
                text-align: center;
                margin: 35px 0;
            }}
            .btn {{
                background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
                color: #ffffff !important;
                text-decoration: none;
                padding: 14px 30px;
                font-size: 14px;
                font-weight: 600;
                border-radius: 30px;
                box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
                display: inline-block;
                transition: transform 0.2s;
            }}
            .footer {{
                text-align: center;
                font-size: 12px;
                color: #64748b;
                border-top: 1px solid rgba(255, 255, 255, 0.08);
                padding-top: 20px;
                margin-top: 30px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <span class="badge {'badge-present' if case.get('type') == 'Present' else 'badge-past'}">{c_type}</span>
                <span class="badge" style="background-color: rgba(139, 92, 246, 0.15); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.3);">{case.get('theme', 'General')}</span>
                <div class="title">CASE #{case_number}: {case.get('brand', 'Unknown').upper()}</div>
                <div class="subtitle">{case.get('title', 'Untitled')}</div>
            </div>
            
            <div class="takeaway-box">
                <div class="takeaway-title">⚡ TÓM TẮT NHANH 1 PHÚT</div>
                <div>{case.get('one_minute_takeaway', '')}</div>
            </div>
            
            <div class="btn-container">
                <a href="{web_url}?case={case_number}" class="btn">🎧 BẤM ĐỂ HỌC VÀ NGHE PODCAST TRÊN WEB APP</a>
            </div>
            
            <div style="font-size: 13px; color: #94a3b8; line-height: 1.6;">
                Bấm vào nút trên để mở Web App học tập của bạn. Tại đó bạn có thể:<br>
                - 🎙️ Nghe Podcast phân tích tiếng Việt thời lượng dài.<br>
                - 🏆 Xem bài giải mẫu Quán quân cuộc thi với cấu trúc chi tiết.<br>
                - 📚 Học từ điển thuật ngữ thực chiến và checklist hành động ngày mai.<br>
                - 🔑 Bảo mật truy cập bằng mật khẩu riêng của bạn.
            </div>
            
            <div class="footer">
                Chúc anh một buổi trưa học tập đầy cảm hứng!<br>
                Dự án tự học Marketing | Vận hành bởi GitHub Actions & Gemini AI
            </div>
        </div>
    </body>
    </html>
    """
    
    # Gửi email qua SMTP
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        
        part = MIMEText(html_content, 'html')
        msg.attach(part)
        
        # Kết nối tới Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        
        print("Notification email sent successfully!")
        return True
    except Exception as e:
        print(f"Error sending email via SMTP: {e}")
        return False

async def main():
    print("=== STARTING DAILY MARKETING CASE STUDY GENERATION ===")
    
    # 1. Lấy dữ liệu cũ để đếm số thứ tự case và lấy danh sách brand đã học
    existing_cases = get_existing_cases()
    case_number = len(existing_cases) + 1
    
    # Xác định loại case theo quy luật xoay tua 2:1 (Quá khứ - Quá khứ - Hiện tại)
    # Case #1 (Quá khứ), Case #2 (Quá khứ), Case #3 (Hiện tại)
    # Tức là nếu case_number chia hết cho 3 thì là Hiện tại (Present), ngược lại là Quá khứ (Past)
    is_present = (case_number % 3 == 0)
    
    covered_brands = [c["brand"] for c in existing_cases]
    
    # 2. Gọi Gemini sinh nội dung
    try:
        case_data = generate_case_study(case_number, is_present, covered_brands)
    except Exception as e:
        print(f"Could not generate case study from Gemini: {e}")
        return
        
    date_str = datetime.now().strftime("%Y-%m-%d")
    brand = case_data.get("brand", "Unknown")
    
    # 3. Tạo file âm thanh podcast từ kịch bản của Gemini
    audio_filename = f"{date_str}-{brand.lower().replace(' ', '-')}.mp3"
    audio_path = os.path.join(CASES_AUDIO_DIR, audio_filename)
    
    podcast_script = case_data.get("podcast_script", "Xin chào anh, hôm nay chúng ta sẽ cùng học một case marketing rất hay...")
    try:
        await generate_podcast_audio(podcast_script, audio_path)
    except Exception as e:
        print(f"Error generating Audio file: {e}")
        # Vẫn tiếp tục chạy để không bị gián đoạn sinh text
        audio_filename = ""
        
    # 4. Lưu file Markdown
    md_filepath, md_filename = save_to_markdown(case_data, case_number, date_str)
    
    # 5. Sinh điểm XP ngẫu nhiên
    skills_xp = generate_skills_xp(case_data.get("type", "Present" if is_present else "Past"))
    
    # 6. Cập nhật dữ liệu vào data.json
    new_case_summary = {
        "case_number": case_number,
        "brand": case_data.get("brand", "Unknown"),
        "title": case_data.get("title", "Untitled"),
        "theme": case_data.get("theme", "General"),
        "type": "Present" if is_present else "Past",
        "date": date_str,
        "one_minute_takeaway": case_data.get("one_minute_takeaway", ""),
        "markdown_filename": md_filename,
        "audio_filename": audio_filename if audio_filename else "",
        "skills_xp": skills_xp
    }
    
    existing_cases.append(new_case_summary)
    save_cases_data(existing_cases)
    print("Updated data.json with new case.")
    
    # 7. Cập nhật README.md
    update_readme(existing_cases)
    
    # 8. Gửi Email thông báo kích hoạt học tập
    send_notification_email(
        case_data, 
        case_number, 
        date_str, 
        audio_filename, 
        GITHUB_PAGES_URL
    )
    
    print("=== COMPLETED GENERATION SUCCESSFULLY ===")

if __name__ == "__main__":
    asyncio.run(main())
