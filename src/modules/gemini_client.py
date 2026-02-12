import google.generativeai as genai
from PIL import Image
import os
import time
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def batch_analyze(file_list, output_file, archive_dir=None):
    """
    Upload a batch of files (images, audio, video) to Gemini and get a summary.
    
    Args:
        file_list: List of absolute file paths, sorted by timestamp.
        output_file: Path to Research_Log.md to append results.
        archive_dir: Path to archive directory (for embedding file links in log).
    """
    if not model:
        print("❌ Model not configured. Check your .env file.")
        return False

    if not file_list:
        print("  (no files to analyze)")
        return True

    print(f"  📤 Uploading {len(file_list)} files to Gemini (parallel)...")
    uploaded_files = []
    content_parts = []

    try:
        # Upload all files in parallel
        def _upload_one(fpath):
            uploaded = genai.upload_file(path=fpath)
            print(f"    ✅ {os.path.basename(fpath)}")
            return uploaded

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(_upload_one, fp): fp for fp in file_list}
            for future in as_completed(futures):
                fpath = futures[future]
                try:
                    uploaded_files.append(future.result())
                except Exception as e:
                    print(f"    ❌ Failed to upload {os.path.basename(fpath)}: {e}")

        if not uploaded_files:
            print("  ❌ No files were uploaded successfully.")
            return False

        # Wait for files to become ACTIVE
        print("  ⏳ Waiting for files to be processed...")
        for uf in uploaded_files:
            _wait_for_active(uf)

        # Build file inventory with explicit timestamps
        inventory_lines = []
        for fpath in file_list:
            fname = os.path.basename(fpath)
            # Parse timestamp from filename "HHMMSS_..."
            try:
                ts_str = fname.split("_")[0]
                if len(ts_str) == 6 and ts_str.isdigit():
                    t_obj = datetime.datetime.strptime(ts_str, "%H%M%S")
                    time_fmt = t_obj.strftime("%H:%M:%S")
                else:
                    time_fmt = "UNKNOWN"
            except:
                time_fmt = "UNKNOWN"
            
            ftype = "未知"
            if fname.endswith(".jpg"): ftype = "截图"
            elif fname.endswith(".wav"): ftype = "语音"
            elif fname.endswith(".mp4"): ftype = "录屏"
            
            inventory_lines.append(f"- [{time_fmt}] {ftype}: {fname}")
        
        inventory_str = "\n".join(inventory_lines)

        # Build prompt
        prompt = f"""
你是一个AI研究助手。以下是用户过去一段时间的工作流记录。

**这是本次分析的文件列表及其对应的绝对时间（已解析）：**
{inventory_str}

**请严格基于上述时间点（[HH:MM:SS]）生成时间轴。**

数据包含：
- **语音片段** (.wav)：用户在看论文/写代码时说的话
- **屏幕录像** (.mp4)：与语音同步的屏幕录制
- **定时截图** (.jpg)：每10秒自动截取的屏幕画面

请按照时间顺序，完成以下任务：
1. **逐字转录**：将每段语音转录为文字。**自动过滤掉无意义的语气词（如“嗯”、“啊”、“那个”、“就是”等），只保留有意义的内容。**
2. **结构化总结**：生成Markdown格式的总结。

输出格式：
## 📋 时间段总结 [HH:MM:SS - HH:MM:SS]

### 🗣️ 语音转录（根据语音片段，如果没有.wav文件则为空）
- **[HH:MM:SS]** (转录内容...)
或者
- (无语音片段)


### 📝 关键事件，忽略不变化的事件
- **[HH:MM:SS]** (事件描述...)

"""
        content_parts.append(prompt)
        content_parts.extend(uploaded_files)

        print("  🧠 Analyzing with Gemini...")
        response = model.generate_content(content_parts)

        # Build file reference section
        file_refs = _build_file_references(file_list, output_file, archive_dir)

        # Write to log
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        note_content = f"\n---\n\n> **[Batch Analysis: {timestamp}]**\n\n{response.text}\n\n{file_refs}\n\n---\n"

        with open(output_file, "a", encoding="utf-8") as f:
            f.write(note_content)

        print(f"  ✅ 分析完成, 写入: {os.path.basename(output_file)}")

        # Cleanup cloud uploads
        for uf in uploaded_files:
            try:
                uf.delete()
            except:
                pass

        return True

    except Exception as e:
        print(f"  ❌ Batch analysis error: {e}")
        return False


def _build_file_references(file_list, output_file, archive_dir):
    """Build markdown section with links to archived media files."""
    if not archive_dir:
        return ""

    # Calculate relative path from Research_Log.md to archive/
    log_dir = os.path.dirname(output_file)
    rel_archive = os.path.relpath(archive_dir, log_dir)

    screenshots = []
    audio_clips = []
    video_clips = []

    for fpath in file_list:
        fname = os.path.basename(fpath)
        rel_path = f"{rel_archive}/{fname}"
        if fname.endswith(".jpg"):
            screenshots.append(f"![{fname}]({rel_path})")
        elif fname.endswith(".wav"):
            audio_clips.append(f"- 🎙️ [{fname}]({rel_path})")
        elif fname.endswith(".mp4"):
            video_clips.append(f"- 🎬 [{fname}]({rel_path})")

    parts = ["<details>\n<summary>📎 本次分析的原始素材</summary>\n"]

    if screenshots:
        parts.append("**截图:**")
        for s in screenshots:
            parts.append(s)
        parts.append("")

    if audio_clips:
        parts.append("**语音:**")
        parts.extend(audio_clips)
        parts.append("")

    if video_clips:
        parts.append("**录屏:**")
        parts.extend(video_clips)
        parts.append("")

    parts.append("</details>")
    return "\n".join(parts)


def _wait_for_active(uploaded_file, timeout=120):
    """Wait for an uploaded file to become ACTIVE (ready for use)."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            f = genai.get_file(uploaded_file.name)
            if f.state.name == "ACTIVE":
                return True
        except:
            pass
        time.sleep(2)
    print(f"  ⚠️ File {uploaded_file.name} did not become ACTIVE in time.")
    return False
