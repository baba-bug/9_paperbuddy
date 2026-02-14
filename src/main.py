import os
import sys
import argparse

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import keyboard
from modules.utils import check_ffmpeg, create_session, list_sessions, ANALYSIS_INTERVAL
from modules.logger import Logger
from modules.analyzer import Analyzer


def main():
    parser = argparse.ArgumentParser(description="AI 论文伴侣 v2 — Logger + Analyzer")
    parser.add_argument("--resume", type=str, default=None,
                        help="Resume a previous session by name (e.g. session_20260211_223000)")
    parser.add_argument("--list", action="store_true",
                        help="List all available sessions")
    args = parser.parse_args()

    print("🚀 AI 论文伴侣 v2 已启动")
    print("   架构: Logger (采集) + Analyzer (分析)")

    if args.list:
        list_sessions()
        return

    if not check_ffmpeg():
        return

    # Create or resume session
    session = create_session(resume_name=args.resume)
    if not session:
        return

    print(f"📝 日志: {session.log_file}")
    print(f"📂 待处理: {session.pending_dir}")
    print(f"🧠 分析间隔: {ANALYSIS_INTERVAL // 60} 分钟")
    print("-" * 50)

    # Start Analyzer (background thread)
    analyzer = Analyzer(session)
    analyzer.start()

    # Start Logger (blocking on main thread)
    logger = Logger(session)
    
    # Register global hotkey for pause/resume
    hotkey = "ctrl+alt+shift+capslock+p"
    keyboard.add_hotkey(hotkey, logger.toggle_pause)
    print(f"🎙️  开始监听... 按 Ctrl+C 退出")
    print(f"⏯️  快捷键暂停/恢复: {hotkey}")

    try:
        logger.start()
    except KeyboardInterrupt:
        pass
    finally:
        print("\n🛑 正在关闭...")
        logger.stop()
        analyzer.stop()

        # Run final analysis on remaining pending files
        print("🧠 正在处理剩余文件...")
        analyzer.run_now()

        print(f"📁 Session saved: {session.name}")
        print(f"📝 Log: {session.log_file}")


if __name__ == "__main__":
    main()
