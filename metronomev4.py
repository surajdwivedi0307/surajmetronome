import streamlit as st
import numpy as np
from scipy.io import wavfile
import io
from PIL import Image
import os
import time

# Constants
NOTE_FREQUENCIES = {
    "S": 261.63, "R": 293.66, "G": 329.63, "M": 349.23,
    "P": 392.00, "D": 440.00, "N": 493.88, "S'": 523.25,
}
SAMPLE_RATE = 44100
IMAGE_FOLDER = "images"

# Functions
def generate_note(freq, duration=0.5):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    waveform = 0.5 * np.sin(2 * np.pi * freq * t)
    return waveform.astype(np.float32)

def create_melody(note_sequence, bpm=60):
    beat_duration = 60 / bpm
    melody = np.concatenate([
        generate_note(NOTE_FREQUENCIES[n], beat_duration)
        for n in note_sequence if n in NOTE_FREQUENCIES
    ])
    buf = io.BytesIO()
    wavfile.write(buf, SAMPLE_RATE, melody)
    buf.seek(0)
    return buf

def get_image(note):
    path = os.path.join(IMAGE_FOLDER, f"{note}.png")
    return Image.open(path) if os.path.exists(path) else None

# UI
st.title("🎼 Indian Flute Melody Player (One Note at a Time)")
note_input = st.text_input("🎵 Enter note sequence (space-separated):", "S R G M P D N S'")
bpm = st.slider("🕒 BPM (beats per minute):", 40, 180, 60)
play = st.button("▶️ Play Melody")

if play:
    notes = note_input.strip().split()
    audio_data = create_melody(notes, bpm)
    st.audio(audio_data, format="audio/wav")

    st.write("🖼️ Playing notes with images:")
    placeholder = st.empty()
    delay = 60 / bpm

    for note in notes:
        img = get_image(note)
        if img:
            placeholder.image(img, caption=f"Note: {note}", width=200)
        else:
            placeholder.warning(f"No image for: {note}")
        time.sleep(delay)
