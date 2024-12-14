# Voice-to-Text AI Assistant

This project is a Python-based application that allows users to register voice inputs, transcribe them into text, and send the transcriptions to an AI for processing using `tgpt`. Users can interact with the AI either through voice or manual text input. Additionally, there are options to mute the text-to-speech (TTS) output and adjust various settings.

## Features
- **Voice Registration**: Capture voice input using `speech_recognition` and send it to an AI for processing.
- **Text or Voice Prompts**: Allows users to choose whether to interact with the AI using text or voice.
- **Mute TTS**: Option to mute/unmute the text-to-speech functionality.
- **Log**: A log of activities is displayed within the app.
- **Tray Icon**: The app runs in the system tray, with options to mute TTS, clear the log, or quit the application.
- **Manual Text Input**: Users can manually input text to interact with the AI.
- **Process and Save Code**: The AI's response may include code snippets which are saved as `.py` files.

## Requirements
- Python 3.x
- `tkinter` for GUI
- `pyttsx3` for Text-to-Speech
- `pystray` for system tray icon
- `speech_recognition` for voice input
- `subprocess` for running external commands (e.g., `tgpt`)
- `ctypes` for keypress detection

You can install the required libraries with the following:
```bash
pip install tkinter pyttsx3 pystray speech_recognition
