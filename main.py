import tkinter as tk
from tkinter import scrolledtext, simpledialog
import threading
import speech_recognition as sr
import subprocess
import time
import ctypes
import pystray
from pystray import MenuItem, Icon
from PIL import Image
import pyttsx3
import os
import signal
import re

# Initialize TTS engine
def init_tts():
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)  # Change the index to your preferred voice
    engine.setProperty('rate', 200)
    engine.setProperty('volume', 1)  # Default TTS volume to on
    return engine

engine = init_tts()
muted = False

# Create global variables
is_recording = False
log_text = ""
tray_icon = None  # Global variable for the tray icon

def toggle_mute():
    global muted
    muted = not muted
    if muted:
        engine.setProperty('volume', 0)
        append_log("Text-to-Speech muted.")
    else:
        engine.setProperty('volume', 1)
        append_log("Text-to-Speech unmuted.")

def append_log(text):
    global log_text
    log_text += f"{text}\n"
    log_widget.configure(state=tk.NORMAL)
    log_widget.delete(1.0, tk.END)
    log_widget.insert(tk.END, log_text)
    log_widget.configure(state=tk.DISABLED)

def clear_log():
    global log_text
    log_text = ""  # Clear log text
    log_widget.configure(state=tk.NORMAL)
    log_widget.delete(1.0, tk.END)
    log_widget.configure(state=tk.DISABLED)
    append_log("Log cleared.")

def on_quit(icon, item):
    icon.stop()

def create_tray_icon():
    global tray_icon
    icon_image = Image.open("mic_icon.png")  # Load initial icon
    menu = (MenuItem('Open', show_window), MenuItem('Mute TTS', toggle_mute),
            MenuItem('Clear Log', clear_log), MenuItem('Quit', on_quit))
    tray_icon = Icon("VoiceRecorder", icon_image, "Voice Recorder", menu)
    tray_icon.run()

def show_window():
    root.deiconify()

def hide_window():
    root.withdraw()

def start_recording():
    global is_recording
    if is_recording:  # Prevent starting if already recording
        return
    stop_tts()  # Stop TTS before starting new recording
    reinitialize_tts()  # Reinitialize TTS engine
    is_recording = True
    append_log("Started recording...")
    update_icon("mic_work.png")  # Change icon when recording starts
    threading.Thread(target=record_audio).start()

def stop_recording():
    global is_recording
    is_recording = False
    append_log("Stopped recording.")
    update_icon("mic_icon.png")  # Change icon back when recording stops

def update_icon(icon_image):
    if tray_icon:  # Check if the tray icon exists
        tray_icon.icon = Image.open(icon_image)  # Update the tray icon image

def record_audio():
    global is_recording
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        while is_recording:
            audio = recognizer.listen(source, timeout=3)

            try:
                append_log("Transcribing...")
                text = recognizer.recognize_google(audio)
                append_log(f"Transcript: {text}")
                threading.Thread(target=send_to_terminal, args=(text,)).start()  # Process output in a thread
            except sr.UnknownValueError:
                append_log("Could not understand audio.")
            except sr.RequestError as e:
                append_log(f"Error with the request; {e}")

def send_to_terminal(text):
    global engine  # Use the global engine variable
    stop_tts()  # Ensure TTS is stopped before sending new text
    kill_tgpt_process()

    command = f'tgpt "{text}"'
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    
    output = result.stdout.strip()

    # List of unwanted messages to ignore for TTS
    ignore_messages_for_tts = [
        "â£¾  Loading", "â£½  Loading", "â£»  Loading", 
        "â¢¿  Loading", "â¡¿  Loading", "â£Ÿ  Loading", 
        "â£¯  Loading", "â£·  Loading"
    ]
    
    # Clean up any unwanted messages from output
    for unwanted_text in ignore_messages_for_tts:
        output = output.replace(unwanted_text, "")
    
    # Extract and save code if it matches the specified format
    extract_and_save_code(output)
    
    # Clean up any extra whitespace after filtering
    output = ' '.join(output.split()).strip()

    # Only log if there is valid output left after filtering
    if output:
        append_log(f"TGPT Output: {output}")
        if not muted and not any(msg in output for msg in ignore_messages_for_tts):
            engine.say(output)
            engine.runAndWait()  # Ensure the TTS speaks the output
    else:
        append_log("TGPT Output: No valid output after filtering.")

def extract_and_save_code(output):
    # Regex pattern to find text within triple backticks followed by 'python'
    pattern = r"```python(.*?)```"
    matches = re.findall(pattern, output, re.DOTALL)
    
    for match in matches:
        code_content = match.strip()  # Clean any extra spaces

        # Create a unique filename with a timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")  # Format: YYYYMMDD_HHMMSS
        filename = f"extracted_code_{timestamp}.py"  # Example: extracted_code_20231018_123456.py

        # Save the code to a file
        with open(filename, 'w') as f:
            f.write(code_content)
        append_log(f"Extracted code saved as: {filename}")

def stop_tts():
    engine.stop()  # Stop TTS if it's currently speaking

def reinitialize_tts():
    global engine
    engine = init_tts()  # Reinitialize TTS engine

def kill_tgpt_process():
    # Kill existing tgpt processes if running
    try:
        # Adjust the command below if tgpt is run using a different executable name
        for line in os.popen("tasklist"):
            if "tgpt.exe" in line:  # Change this to the name of your tgpt process
                pid = int(line.split()[1])
                os.kill(pid, signal.SIGTERM)
                append_log("Killed existing tgpt process.")
    except Exception as e:
        append_log(f"Error killing tgpt process: {e}")

def check_keypress():
    ctrl_pressed = False
    while True:
        # Check if Ctrl is pressed
        if ctypes.windll.user32.GetAsyncKeyState(0x11):  # 0x11 is the virtual key code for Ctrl
            ctrl_pressed = True
        else:
            ctrl_pressed = False

        # Wait for '.' key press while Ctrl is held down
        if ctrl_pressed and ctypes.windll.user32.GetAsyncKeyState(0xBE):  # 0xBE is the virtual key code for '.'
            toggle_recording()
            time.sleep(0.2)  # Delay of 200 milliseconds

        time.sleep(0.1)  # Short delay to reduce CPU usage

def toggle_recording():
    global is_recording
    if is_recording:
        stop_recording()
    else:
        start_recording()

def add_manual_text():
    text = simpledialog.askstring("Input", "Enter text manually:")
    if text:
        threading.Thread(target=send_to_terminal, args=(text,)).start()  # Process output in a thread

# GUI setup
root = tk.Tk()
root.title("Voice Recorder")
root.geometry("800x600")
root.configure(bg='black')

log_widget = scrolledtext.ScrolledText(root, state=tk.DISABLED, bg='black', fg='white', wrap=tk.WORD)
log_widget.pack(expand=True, fill=tk.BOTH)

# Add manual text button
manual_text_button = tk.Button(root, text="Add Manual Text", command=add_manual_text)
manual_text_button.pack(pady=10)

# Create tray icon in a separate thread
threading.Thread(target=create_tray_icon, daemon=True).start()

# Start the keypress thread
threading.Thread(target=check_keypress, daemon=True).start()

# Start the GUI loop
hide_window()
root.mainloop()
