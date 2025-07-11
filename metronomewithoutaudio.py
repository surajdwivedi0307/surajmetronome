import streamlit as st
import numpy as np
import random
import time
import threading

# Constants
sample_rate = 44100
note_freq_base = {
    'S': 261.63, 'R': 293.66, 'G': 329.63, 'M': 349.23,
    'P': 392.00, 'D': 440.00, 'N': 493.88
}
octave_multipliers = {'low': 0.5, 'medium': 1.0, 'high': 2.0}
image_base_url = "https://raw.githubusercontent.com/surajdwivedi0307/surajmetronome/main/images/"
stop_flag = threading.Event()

# Session State
if "countdown_started" not in st.session_state:
    st.session_state.countdown_started = False
if "sequence_to_play" not in st.session_state:
    st.session_state.sequence_to_play = []
if "bpm" not in st.session_state:
    st.session_state.bpm = 60

# Styling
st.set_page_config(layout="wide", page_title="Flute Metronome", page_icon="🎶")
st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
        }
        h1, h3 {
            color: #2c3e50;
        }
        .note-box {
            padding: 1.2rem;
            margin-bottom: 1rem;
            background: #eef6f8;
            border-radius: 12px;
            border-left: 6px solid #3498db;
            font-size: 20px;
            font-weight: bold;
            color: #34495e;
        }
        .stProgress > div > div > div > div {
            background-color: #3498db;
            transition: width 0.2s ease-in-out;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🎶 Indian Flute Visual Metronome + Melody Generator")

# Utility Functions
def parse_notes_input(note_string):
    parsed_sequence = []
    entry = note_string.strip()
    i = 0
    while i < len(entry):
        if entry[i] in [',', '-']:
            parsed_sequence.append(('-', 1, 'medium'))
            i += 1
        else:
            note = entry[i]
            i += 1
            if note not in note_freq_base:
                continue
            octave = 'medium'
            if i < len(entry) and entry[i] == '>':
                octave = 'high'
                i += 1
            elif i < len(entry) and entry[i] == '<':
                octave = 'low'
                i += 1
            count = 0
            while i < len(entry) and entry[i] == '_':
                count += 1
                i += 1
            duration = 1 + count
            parsed_sequence.append((note, duration, octave))
    return parsed_sequence

def bpm_to_duration(bpm, note_length=1):
    return (60.0 / bpm) * note_length

def show_countdown():
    countdown_placeholder = st.empty()
    for i in range(3, 0, -1):
        countdown_placeholder.markdown(
            f"<h1 style='text-align:center; color:#e74c3c; font-size:72px;'>⏳ {i}</h1>",
            unsafe_allow_html=True
        )
        time.sleep(1)
    countdown_placeholder.markdown(
        f"<h1 style='text-align:center; color:#2ecc71; font-size:64px;'>🎼 Start!</h1>",
        unsafe_allow_html=True
    )
    time.sleep(1)
    countdown_placeholder.empty()

def display_note_animation(parsed_sequence, bpm):
    container_note = st.empty()
    container_next = st.empty()
    container_image = st.empty()
    container_progress = st.empty()

    total_notes = len(parsed_sequence)
    total_duration = sum(bpm_to_duration(bpm, d) for _, d, _ in parsed_sequence)
    elapsed = 0.0

    for idx, (note, multiplier, octave) in enumerate(parsed_sequence):
        if stop_flag.is_set():
            break

        duration = bpm_to_duration(bpm, multiplier)
        note_name = f"{note} ({octave})" if note != '-' else "Rest"
        next_note_name = ""
        if idx + 1 < total_notes:
            next_n, _, next_octave = parsed_sequence[idx + 1]
            next_note_name = f"{next_n} ({next_octave})" if next_n != '-' else "Rest"

        remaining_time = duration
        start_time = time.time()
        while time.time() - start_time < duration:
            elapsed_time = time.time() - start_time
            remaining_time = duration - elapsed_time
            container_note.markdown(
                f"<div class='note-box'>🎵 Now Playing: {note_name} &nbsp;&nbsp; ⏱️ {elapsed_time:.2f}s / {duration:.2f}s left</div>", 
                unsafe_allow_html=True)
            container_next.markdown(f"##### 🔜 Next: `{next_note_name}`" if next_note_name else "", unsafe_allow_html=True)

            if note in note_freq_base:
                image_url = f"{image_base_url}bansuri_notes_{note}.png"
                container_image.image(image_url, caption=f"{note} fingering", use_container_width=True)
            else:
                container_image.empty()

            progress = (elapsed + elapsed_time) / total_duration
            container_progress.progress(min(progress, 1.0))

            time.sleep(0.05)

        elapsed += duration

# Melody Generator
def generate_random_melody(length=12):
    notes = ['S', 'R', 'G', 'M', 'P', 'D', 'N', '-']
    octaves = ['', '>', '<']
    melody = ''
    for _ in range(length):
        note = random.choice(notes)
        octave = random.choice(octaves) if note != '-' else ''
        underscore = '_' * random.randint(0, 2)
        separator = ',' if random.random() < 0.15 else ''
        melody += f"{note}{octave}{underscore}{separator}"
    return melody

# --- Streamlit UI Layout ---
st.session_state.bpm = st.slider("🎚️ Set BPM (Speed)", min_value=40, max_value=180, value=60)
note_input = st.text_input("✍️ Enter melody sequence (e.g., SGRG_RSN):", "DS>DP,GRSR,G-GR,GPD_")

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("▶️ Play Input Sequence"):
        stop_flag.clear()
        sequence = parse_notes_input(note_input)
        if not sequence:
            st.error("Invalid note sequence.")
        else:
            st.session_state.sequence_to_play = sequence
            st.session_state.countdown_started = True

with col2:
    if st.button("🎲 Generate & Play Random Melody"):
        stop_flag.clear()
        melody = generate_random_melody()
        st.success(f"Random Melody: `{melody}`")
        sequence = parse_notes_input(melody)
        st.session_state.sequence_to_play = sequence
        st.session_state.countdown_started = True

if st.button("⏹️ Stop Playback"):
    stop_flag.set()

# Run Countdown and Playback
if st.session_state.countdown_started and not stop_flag.is_set():
    show_countdown()
    display_note_animation(st.session_state.sequence_to_play, st.session_state.bpm)
    st.session_state.countdown_started = False
