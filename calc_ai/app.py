import tkinter as tk
from tkinter import END
from PIL import Image, ImageTk
import google.generativeai as genai
import pyttsx3
import speech_recognition as sr
import threading  # To handle speech recognition and TTS in the background

# Constants for GUI configuration
BG_COLOR = "#808080"
TEXT_COLOR = "black"
HEADER_BG = "white"
BTN_BG = "#606060"
FONT_HEADER = ("Arial", 31)
FONT_SUBHEADER = ("Arial", 10)
FONT_TEXT = ("Arial", 14)
FONT_INPUT = ("Arial", 12)

# Google API configuration
GOOGLE_API_KEY = "AIzaSyBW9CPIzjIsfdSMw9Era9pXQFZuQb6Pwek"  # Replace with your API key
genai.configure(api_key=GOOGLE_API_KEY)

generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction=(
        "You are an expert teacher teaching high-school level mathematics specifically algebra. "
        "Your name is CALC and it stands for Computational Assistance and Learning Companion. Introduce yourself as a teacher. "
        "You should strictly only answer questions related to algebra."
        "Your job is to provide students an easy and effective learning experience so that they "
        "can internalize the topics presented to them. Make it as interactive and enjoyable as possible."
    ),
)

chat_session = model.start_chat()

# Text-to-speech engine
engine = pyttsx3.init()
engine.setProperty("rate", 150)
engine.setProperty("volume", 1.0)


class Calc:
    def __init__(self, root):
        self.window = root
        self.window.geometry("800x600")
        self.window.title("CALC")
        self.window.configure(bg=BG_COLOR)
        self.window.resizable(False, False)
        
        icon = Image.open("assets/icon.png")
        icon = icon.resize((42, 42))
        self.window.iconphoto(True, ImageTk.PhotoImage(icon))

        self.tts_enabled = True  # Initialize TTS as enabled
        self.processing = False  # Flag to track if the system is processing a response

        self.setup_header()
        self.setup_output()
        self.setup_input()
        self.setup_buttons()
        self.show_welcome_message()

    def setup_header(self):
        """Setup header section."""
        self.canvas = tk.Canvas(self.window, bg=HEADER_BG)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=0.1)
        self.header = tk.Label(self.window, text="CALC", font=FONT_HEADER, bg=HEADER_BG)
        self.header.place(x=10, y=5)
        self.ver = tk.Label(self.window, text="Beta v1.0", font=FONT_SUBHEADER, bg=HEADER_BG)
        self.ver.place(x=130, y=25)

    def setup_output(self):
        """Setup output box."""
        self.output_box = tk.Text(
            self.window, width=70, height=10, bd=2, relief="flat", bg=BG_COLOR, fg=TEXT_COLOR, font=FONT_TEXT, wrap="word"
        )
        self.output_box.place(relheight=0.6, relwidth=0.8, relx=0.1, rely=0.12)
        self.output_box.configure(state="disabled", cursor="arrow")
        self.output_box.tag_configure("user_input", foreground="blue")

    def setup_input(self):
        """Setup input box."""
        self.textbox = tk.Text(self.window, font=FONT_INPUT, height=1, width=50, bd=2, relief="flat")
        self.textbox.pack(side=tk.BOTTOM, pady=80, padx=10)

    def setup_buttons(self):
        """Setup interaction buttons."""
        self.voice_icon = tk.PhotoImage(file="assets/microphone.png")
        self.voice_button = tk.Button(
            self.window, image=self.voice_icon, bg=BG_COLOR, padx=10, pady=5, borderwidth=0, command=self.voice_interact
        )
        self.voice_button.place(relx=0.801, rely=0.842, anchor="center")

        self.send_button = tk.Button(
            self.window, text="Send", font=FONT_INPUT, command=self.handle_input, bg=BTN_BG, fg="white"
        )
        self.send_button.place(relx=0.85, rely=0.842, anchor="center")


        self.tts_toggle_button = tk.Button(
            self.window, text="Speak: On", font=FONT_INPUT, command=self.toggle_tts, bg=BTN_BG, fg="white"
        )
        self.tts_toggle_button.place(relx=0.15, rely=0.842, anchor="center")

        self.listening_label = tk.Label(self.window, text="I'm listening...", font=("Arial", 14), bg=BG_COLOR, fg="red")
        self.listening_label.place(relx=0.5, rely=0.88)
        self.listening_label.place_forget()  # Hidden by default

    def toggle_tts(self):
        """Toggle text-to-speech functionality."""
        self.tts_enabled = not self.tts_enabled
        status = "On" if self.tts_enabled else "Off"
        self.tts_toggle_button.config(text=f"TTS: {status}")
        self.append_to_output(f"Text-to-speech is now {status}.", sender="CALC")

    def show_welcome_message(self):
        """Display welcome message."""
        self.audio_wave = tk.PhotoImage(file="assets/audiowave.png")
        self.audio_wave_label = tk.Label(self.window, image=self.audio_wave, bg=BG_COLOR)
        self.audio_wave_label.place(relx=0.5, rely=0.4, anchor="center")
        self.greeting_text = tk.Label(
            self.window, text="Hi, my name is CALC. What can I do for you today?", font=("Arial", 18), bg=BG_COLOR, fg=TEXT_COLOR
        )
        self.greeting_text.place(relx=0.5, rely=0.5, anchor="center")

    def append_to_output(self, text, sender="CALC"):
        """Add text to the output box."""
        self.output_box.configure(state="normal")
        if sender == "You":
            self.output_box.insert(END, f"{sender}: ", "user_input")
            self.output_box.insert(END, f"{text}\n")
        else:
            self.output_box.insert(END, f"{sender}: {text}\n")
        self.output_box.configure(state="disabled")
        self.output_box.see(END)

    def handle_input(self):
        """Handle user input."""
        user_input = self.textbox.get("1.0", "end").strip()
        self.textbox.delete("1.0", END)
        if user_input and not self.processing:
            self.append_to_output(user_input, sender="You")
            self.generate_response(user_input)
            
        self.greeting_text.place_forget()
        self.audio_wave_label.place_forget()

    def generate_response(self, user_input):
        """Generate a response using Google Generative AI."""
        self.processing = True
        try:
            response = chat_session.send_message(user_input)
            response_text = response.text
            self.append_to_output(response_text)
            self.speak(response_text)  # TTS based on toggle status
        except AttributeError:
            self.append_to_output("An error occurred while generating the response.", sender="CALC")
        self.processing = False

    def speak(self, text):
        """Speak the response only if TTS is enabled."""
        if self.tts_enabled:
            threading.Thread(target=self._speak_in_background, args=(text,), daemon=True).start()
    def _speak_in_background(self, text):
        """Perform TTS in a separate thread to avoid blocking the GUI."""
        tts_engine = pyttsx3.init()
        tts_engine.setProperty("rate", 150)
        tts_engine.setProperty("volume", 1.0)
        tts_engine.say(text)
        tts_engine.runAndWait()
        
    def voice_interact(self):
        """Handle voice input."""
        if not self.processing:
            self.listening_label.place(relx=0.5, rely=0.6, anchor="center")
            threading.Thread(target=self.process_voice_input).start()

    def process_voice_input(self):
        """Process voice input."""
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                audio = recognizer.listen(source, timeout=5)
                user_input = recognizer.recognize_google(audio)
                self.append_to_output(user_input, sender="You")
                self.generate_response(user_input)
            except sr.UnknownValueError:
                self.append_to_output("Sorry, I couldn't understand that.", sender="CALC")
            except sr.RequestError:
                self.append_to_output("Speech recognition service is unavailable.", sender="CALC")
        self.listening_label.place_forget()
        
        self.greeting_text.place_forget()
        self.audio_wave_label.place_forget()

    def on_exit(self):
        """Ensure cleanup on exit."""
        engine.stop()
        self.window.quit()


def main():
    root = tk.Tk()
    calc = Calc(root)
    root.protocol("WM_DELETE_WINDOW", calc.on_exit)
    root.mainloop()


main()
