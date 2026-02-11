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

## 4. Configuration (Security)
1.  **Create a `.env` file**:
    Copy the example file and rename it to `.env`:
    ```cmd
    copy .env.example .env
    ```
2.  **Add your API Key**:
    Open `.env` in a text editor and paste your Google Gemini API key:
    ```ini
    GOOGLE_API_KEY=your_actual_api_key_here
    ```

## 5. Usage
1.  **Run the Assistant**:
    ```bash
    python src/main.py
    ```
2.  **Interaction**:
    -   **Speak**: The system listens for your voice.
    -   **Pause**: Wait for **3 seconds** of silence.
    -   **Process**: It will capture audio + screen and analyze them.
    -   **Log**: Check `data/Research_Log.md` for the output.

## Troubleshooting
-   **Microphone Issue**: Run `python src/debug_audio.py` to test your mic.
-   **API Key Error**: Ensure your `.env` file has a valid `GOOGLE_API_KEY`.
-   **FFmpeg not found**: Ensure `ffmpeg` is in your PATH.
-   **PyAudio error**: If pip install fails, download the `.whl` from [lfd.uci.edu](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio).
-   **VAD Error**: Ensure your microphone supports 16kHz sample rate (the script attempts to configure this).

## Files

-   `ai_assistant.py`: Main application script.
-   `check_env.py`: Script to verify your environment setup.
-   `requirements.txt`: Python dependencies.
