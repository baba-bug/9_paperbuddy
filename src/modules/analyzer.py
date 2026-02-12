import threading
import time
import os
import shutil
from .utils import ANALYSIS_INTERVAL
from .gemini_client import batch_analyze


class Analyzer:
    """Periodic batch analyzer: collects pending files, sends to Gemini, writes log."""

    def __init__(self, session):
        self.session = session
        self._running = False
        self._thread = None

    def start(self):
        """Start the analyzer as a background thread."""
        self._running = True
        self._thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self._thread.start()
        print(f"🧠 Analyzer running every {ANALYSIS_INTERVAL // 60} minutes")

    def stop(self):
        """Stop the analyzer."""
        self._running = False

    def run_now(self):
        """Trigger an immediate analysis (e.g. on shutdown)."""
        self._run_analysis()

    def _analysis_loop(self):
        """Main loop: sleep for ANALYSIS_INTERVAL, then run analysis."""
        while self._running:
            time.sleep(ANALYSIS_INTERVAL)
            if not self._running:
                break
            self._run_analysis()

    def _run_analysis(self):
        """Execute one round of batch analysis."""
        pending = self.session.pending_dir
        processing = self.session.processing_dir

        # ── Step 1: Lock — move pending → processing ──
        files = [f for f in os.listdir(pending) if os.path.isfile(os.path.join(pending, f))]
        if not files:
            print("🔍 [Analyzer] No pending files, skipping.")
            return

        print(f"\n{'='*50}")
        print(f"🧠 [Analyzer] Processing {len(files)} files...")

        # Move files atomically (only if they are not locked)
        moved_files = []
        for f in files:
            src = os.path.join(pending, f)
            dst = os.path.join(processing, f)
            try:
                # Try to rename - if locked (e.g. recording in progress), this will fail on Windows
                os.rename(src, dst)
                moved_files.append(dst)
            except OSError:
                # File is likely in use (recording), skip it for next batch
                print(f"  🔒 File locked (recording?), skipping: {f}")
            except Exception as e:
                print(f"  ⚠️ Could not move {f}: {e}")

        if not moved_files:
            print("  ❌ No files moved. Skipping analysis.")
            return

        # ── Step 2: Sort by timestamp (filename prefix) ──
        moved_files.sort(key=lambda x: os.path.basename(x))

        # ── Step 3: Send to Gemini ──
        success = batch_analyze(moved_files, self.session.log_file, self.session.archive_dir)

        # ── Step 4: Archive processed files ──
        if success:
            for f in moved_files:
                try:
                    shutil.move(f, os.path.join(self.session.archive_dir, os.path.basename(f)))
                except:
                    pass
            print(f"� [Analyzer] Archived {len(moved_files)} files → archive/")
        else:
            # On failure, move files back to pending for retry
            print("  ⚠️ Analysis failed. Moving files back to pending for retry.")
            for f in moved_files:
                try:
                    shutil.move(f, os.path.join(pending, os.path.basename(f)))
                except:
                    pass

        print(f"{'='*50}\n")
