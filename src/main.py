import os
import sys
import argparse

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.utils import check_ffmpeg, create_session, list_sessions
from modules.audio_recorder import AudioRecorder
from modules.speech_processor import SpeechProcessor


def main():
    parser = argparse.ArgumentParser(description="AI 论文伴侣")
    parser.add_argument("--resume", type=str, default=None,
                        help="Resume a previous session by name (e.g. session_20260211_223000)")
    parser.add_argument("--list", action="store_true",
                        help="List all available sessions")
    args = parser.parse_args()

    print("🚀 AI 论文伴侣 已启动")

    if args.list:
        list_sessions()
        return

    if not check_ffmpeg():
        return

    # Create or resume session
    session = create_session(resume_name=args.resume)
    if not session:
        return

    print(f"📝 笔记: {session.log_file}")
    print(f"📂 录音: {session.recordings_dir}")
    print("-" * 50)
    print("🎙️  请开始看论文并说话 (等待3秒静音提交)... 按 Ctrl+C 退出")

    recorder = AudioRecorder()
    if not recorder.start_stream():
        return

    processor = SpeechProcessor(recorder, session)

    try:
        processor.process_loop()
    except KeyboardInterrupt:
        pass
    finally:
        recorder.close()
        print(f"\n📁 Session saved: {session.name}")


if __name__ == "__main__":
    main()
