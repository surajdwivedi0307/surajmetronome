import streamlit as st
import numpy as np
import random
import time
import io
from PIL import Image
import soundfile as sf

# Settings
sample_rate = 44100
note_freq_base = {
    'S': 261.63, 'R': 293.66, 'G': 329.63, 'M': 349.23,
    'P': 392.00, 'D': 440.00, 'N': 493.88
}
octave_multipliers = {'low': 0.5, 'medium': 1.0, 'high': 2.0}
image_base_url = "https://raw.githubusercontent.com/surajdwivedi0307/surajmetronome/main/images/"

# Streamlit UI setup
st.set_page_config(layout="wide", page_title="Flute Metronome", page_icon="🎶")
st.markdown("""
    <style>
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
        }
    </style>
""", unsafe_allow_html=True)
st.title("🎶 Indian Flute Visual Metronome + Melody Generator")

# --- Session State ---
for key, default in {
    "audio_ready": False,
    "play_requested": False,
    "audio_file": None,
    "sequence": [],
    "bpm": 60
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- Utility Functions ---
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

def generate_audio(note, octave, duration):
    if note == '-':
        return np.zeros(int(sample_rate * duration))
    frequency = note_freq_base[note] * octave_multipliers[octave]
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return np.sin(2 * np.pi * frequency * t)

def generate_audio_and_prepare_playback(parsed_sequence, bpm):
    st.session_state.bpm = bpm
    st.session_state.sequence = parsed_sequence

    full_audio_data = np.concatenate([
        generate_audio(note, octave, bpm_to_duration(bpm, mult))
        for note, mult, octave in parsed_sequence
    ])
    audio_file = io.BytesIO()
    sf.write(audio_file, full_audio_data, sample_rate, format="WAV")
    audio_file.seek(0)

    st.session_state.audio_file = audio_file
    st.session_state.audio_ready = True
    st.session_state.play_requested = False
    st.success("✅ Audio is ready. Click the '🎶 Ready to Play' button below.")

def playback_and_animation():
    sequence = st.session_state.sequence
    bpm = st.session_state.bpm
    total_duration = sum(bpm_to_duration(bpm, d) for _, d, _ in sequence)

    container_note = st.empty()
    container_image = st.empty()
    container_progress = st.empty()

    elapsed = 0.0
    for idx, (note, mult, octave) in enumerate(sequence):
        duration = bpm_to_duration(bpm, mult)
        note_name = f"{note} ({octave})" if note != '-' else "Rest"
        container_note.markdown(f"<div class='note-box'>🎵 {note_name}</div>", unsafe_allow_html=True)

        if note in note_freq_base:
            image_url = f"{image_base_url}bansuri_notes_{note}.png"
            container_image.image(image_url, width=300)
        else:
            container_image.empty()

        container_progress.progress(min(elapsed / total_duration, 1.0))
        time.sleep(duration)
        elapsed += duration

    container_progress.progress(1.0)
    st.audio(st.session_state.audio_file, format='audio/wav')

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

# --- UI Layout ---
bpm = st.slider("🎚️ Set BPM (Speed)", min_value=40, max_value=180, value=st.session_state.bpm)
note_input = st.text_input("✍️ Enter melody sequence (e.g., SGRG_RSN):", "DS>DP,GRSR,G-GR,GPD_")

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("▶️ Play Input Sequence"):
        sequence = parse_notes_input(note_input)
        if not sequence:
            st.error("❌ Invalid note sequence.")
        else:
            st.info("⏳ Please wait... processing audio.")
            generate_audio_and_prepare_playback(sequence, bpm)

with col2:
    if st.button("🎲 Generate & Play Random Melody"):
        melody = generate_random_melody()
        st.success(f"Random Melody: `{melody}`")
        sequence = parse_notes_input(melody)
        generate_audio_and_prepare_playback(sequence, bpm)

if st.button("⏹️ Stop Playback"):
    st.session_state.audio_ready = False
    st.session_state.play_requested = False

# Phase 2: User clicks ready to play
if st.session_state.audio_ready and not st.session_state.play_requested:
    if st.button("🎶 Ready to Play"):
        st.session_state.play_requested = True

if st.session_state.play_requested:
    playback_and_animation()
