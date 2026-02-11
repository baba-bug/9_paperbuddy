import google.generativeai as genai
from PIL import Image
import os
import datetime
from .utils import API_KEY, MODEL_NAME


def configure_genai():
    if not API_KEY:
        print("⚠️  WARNING: API Key not set. Please create a .env file.")
        return None
    try:
        genai.configure(api_key=API_KEY)
        return genai.GenerativeModel(MODEL_NAME)
    except Exception as e:
        print(f"❌ Failed to configure Gemini API: {e}")
        return None


# Global model instance
model = configure_genai()


def analyze_content(audio_path, screenshot_path, output_file):
    """Send to Gemini for multimodal analysis."""
    print(" -> 正在上传并分析...")
    if not model:
        print("❌ Model not configured. Check your .env file.")
        return

    try:
        if not os.path.exists(audio_path):
            print(f"❌ Audio file not found: {audio_path}")
            return
        if not os.path.exists(screenshot_path):
            print(f"❌ Screenshot file not found: {screenshot_path}")
            return

        # Upload audio
        audio_file = genai.upload_file(path=audio_path)

        # Open image
        img = Image.open(screenshot_path)

        prompt = """
        场景：我正在电脑上看论文/写代码，这是我的屏幕截图，附件是我刚才说的话。
        任务：请结合屏幕内容，把我的口语（可能包含吐槽、疑问、思路）转化为这篇论文的结构化笔记。
        要求：
        1. **逐字稿**：首先你需要尽可能准确地转录我说的话（Verbatim Transcript）。
        2. **分析**：如果我在读特定段落，请结合截图指出我关注的内容。
        3. 用中文回答，格式简洁，使用Markdown结构。
        
        输出格式如下：
        ## 🗣️ 口语逐字稿
        (你的转录内容)
        
        ## 📝 结构化笔记
        (你的分析内容)
        """

        response = model.generate_content([prompt, img, audio_file])

        # Write to file
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        filename = os.path.basename(screenshot_path)
        relative_img_path = f"screenshots/{filename}"

        note_content = f"""
> **[{timestamp}]**
{response.text}

<details>
<summary>📸 点击查看屏幕截图</summary>
<img src="{relative_img_path}" width="800" />
</details>

---
"""

        with open(output_file, "a", encoding="utf-8") as f:
            f.write(note_content)

        print(f"✅ 笔记已更新: {os.path.basename(output_file)}")

        # Cleanup cloud upload
        try:
            audio_file.delete()
        except:
            pass

    except Exception as e:
        print(f"❌ 分析出错: {e}")
