import tkinter as tk
from tkinter import *
from PIL import Image, ImageTk
import google.generativeai as genai
import pyttsx3
import speech_recognition as sr
import threading  # To handle speech recognition and TTS in the background

# Google API configuration
GOOGLE_API_KEY = "AIzaSyBW9CPIzjIsfdSMw9Era9pXQFZuQb6Pwek"
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


def speak(text):
    """Use TTS to speak text."""
    engine.say(text)
    engine.runAndWait()


def recognize_speech():
    """Capture and return user speech as text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            audio = recognizer.listen(source, timeout=5)
            return recognizer.recognize_google(audio)
        except (sr.UnknownValueError, sr.RequestError):
            return None


class Calc:
    def __init__(self, root):
        self.window = root
        self.window.geometry("1000x800")
        self.window.title("CALC")
        self.window.configure(bg="#808080")
        self.window.resizable(False, False)

        # Header Section
        self.canvas = tk.Canvas(self.window, bg="white")
        self.canvas.place(x=0, y=0, relwidth=1, relheight=0.1)
        self.header = tk.Label(self.window, text="CALC", font=("Arial", 31), bg="white")
        self.header.place(x=10, y=5)
        self.ver = tk.Label(self.window, text="Beta v1.0", font=("Arial", 10), bg="white")
        self.ver.place(x=130, y=25)

        # Chat Output
        self.output_box = tk.Text(self.window, width=70, height=10, bd=2, relief="flat", bg="#808080", fg="black", font=("Arial", 14), wrap="word")
        self.output_box.place(relheight=0.6, relwidth=0.8, relx=0.1, rely=0.12)
        self.output_box.configure(state="disabled", cursor="arrow")

        # Input Textbox
        self.textbox = tk.Text(self.window, font=("Arial", 12), height=1, width=50, bd=2, relief="flat")
        self.textbox.pack(side=tk.BOTTOM, pady=80, padx=10)

        # Image to represent the audio wave
        self.img = tk.PhotoImage(file="assets/audiowave.png")
        self.img_label = tk.Label(self.window, image=self.img, bg="#808080")
        self.img_label.place(relx=0.5, rely=0.41, anchor="center")

        # Welcome message displayed in the center
        self.greeting_text = tk.Label(self.window, text="Hi, my name is CALC. What can I do for you today?", font=("Arial", 18), bg="#808080", fg="black")
        self.greeting_text.place(relx=0.5, rely=0.5, anchor="center")

        # Voice Button
        self.voice_icon = tk.PhotoImage(file="assets/microphone.png")
        self.voice_button = tk.Button(
            self.window, image=self.voice_icon, bg="#808080", padx=10, pady=5, borderwidth=0, command=self.voice_interact
        )
        self.voice_button.place(relx=0.80, rely=0.88, anchor="center")

        # Send Button
        self.send_button = tk.Button(
            self.window, text="Send", font=("Arial", 12), command=self.handle_input, bg="#606060", fg="white"
        )
        self.send_button.place(relx=0.84, rely=0.88, anchor="center")

        # Stop Button (Interrupts current interaction)
        self.stop_button = tk.Button(
            self.window, text="Stop", font=("Arial", 12), command=self.stop_interaction, bg="#606060", fg="white"
        )
        self.stop_button.place(relx=0.76, rely=0.88, anchor="center")

        # Listening Message Label (Positioned above the Textbox)
        self.listening_label = tk.Label(self.window, text="I'm listening...", font=("Arial", 14), bg="#808080", fg="red")
        self.listening_label.place(relx=0.5, rely=0.88, )  # Adjusted to be above the textbox
        self.listening_label.place_forget()  # Hide by default

        # Tag configuration for user input color (blue)
        self.output_box.tag_configure("user_input", foreground="blue")

        self.processing = False  # Flag to track if the system is processing a response

    def append_to_output(self, text, sender="CALC"):
        """Add text to the output box with color for user input."""
        self.output_box.configure(state="normal")
        if sender == "You":
            self.output_box.insert(END, f"{sender}: ", "user_input")  # Apply the color tag for user input
            self.output_box.insert(END, f"{text}\n")  # Insert the user input text
        else:
            self.output_box.insert(END, f"{sender}: {text}\n")
        self.output_box.configure(state="disabled")
        self.output_box.see(END)

    def handle_input(self):
        """Handle user input from the textbox."""
        user_input = self.textbox.get("1.0", "end").strip()
        self.textbox.delete("1.0", END)
        if user_input and not self.processing:
            self.append_to_output(user_input, sender="You")
            self.generate_response(user_input)
        
        self.greeting_text.place_forget()
        self.img_label.place_forget()

    def generate_response(self, user_input):
        """Generate a response using Google Generative AI."""
        self.processing = True  # Set processing flag to True
        chat_session.send_message(user_input)
        response_text = chat_session.last.text
        self.append_to_output(response_text)
        self.speak_in_background(response_text)
        self.processing = False  # Reset processing flag

    def speak_in_background(self, response_text):
        """Run the speaking process in the background."""
        threading.Thread(target=self.speak, args=(response_text,)).start()

    def speak(self, text):
        """Speak the response using TTS."""
        speak(text)

    def voice_interact(self):
        """Handle voice input and output."""
        if not self.processing:  # Check if system is currently processing
            # Show Listening message
            self.listening_label.place(relx=0.5, rely=0.6, anchor="center")
            # Run voice recognition and TTS in a separate thread to avoid blocking the UI
            thread = threading.Thread(target=self.process_voice_input)
            thread.start()

    def process_voice_input(self):
        """Process the voice input in a separate thread."""
        user_input = recognize_speech()
        if user_input:
            self.append_to_output(user_input, sender="You")
            self.generate_response(user_input)
        else:
            self.append_to_output("Sorry, I couldn't understand that.", sender="CALC")
        
        # Hide the greeting message and the image once there's output
        self.greeting_text.place_forget()
        self.img_label.place_forget()
        # Hide Listening message
        self.listening_label.place_forget()

    def stop_interaction(self):
        """Stop the current response generation."""
        if self.processing:
            self.processing = False
            self.append_to_output("Interaction stopped. Please type a new command.", sender="CALC")
            speak("Interaction stopped. Please type a new command.")

        # Stop the speech if it's running but don't shut down the engine
        engine.endLoop()  # Stop the current speaking
        engine.runAndWait()  # Ensure the engine is reset and ready for the next input

    def on_exit(self):
        """Ensure cleanup when closing the application."""
        engine.stop()  # Ensure the TTS engine is stopped before the app closes
        self.window.quit()  # Properly exit the Tkinter window


def main():
    root = tk.Tk()
    calc = Calc(root)
    root.protocol("WM_DELETE_WINDOW", calc.on_exit)  # Ensures that the exit function is called when closing the app
    root.mainloop()


main()
