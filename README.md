# AI Research Paper Companion (Windows / RTX 4060)

A voice-activated AI assistant that captures your speech and screen to generate structured research notes using Google Gemini 1.5 Flash.

## Prerequisites

1.  **Python 3.8+**
2.  **FFmpeg**: 
    - Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (release-essentials.zip).
    - Extract and add the `bin` folder to your System PATH.
    - Verify with `ffmpeg -version` in CMD.
3.  **Google Gemini API Key**: Get one from [Google AI Studio](https://aistudio.google.com/).

## Installation

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Configuration**:
    - Open `ai_assistant.py` and set your `API_KEY` (or set it as an environment variable `GOOGLE_API_KEY`).
    - Adjust `OUTPUT_FILE` if needed.

2.  **Run the Assistant**:
    ```bash
    python ai_assistant.py
    ```

3.  **How to use**:
    - Open your research paper (PDF, web page, etc.).
    - **Speak** your thoughts/questions.
    - **Pause** for ~1.5 seconds.
    - The assistant will capture the audio and screen, analyze it with Gemini, and append the notes to `Research_Log.md`.

## Troubleshooting

-   **FFmpeg not found**: Ensure `ffmpeg` is in your PATH.
-   **PyAudio error**: If pip install fails, download the `.whl` from [lfd.uci.edu](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio).
-   **VAD Error**: Ensure your microphone supports 16kHz sample rate (the script attempts to configure this).

## Files

-   `ai_assistant.py`: Main application script.
-   `check_env.py`: Script to verify your environment setup.
-   `requirements.txt`: Python dependencies.
