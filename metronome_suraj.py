import streamlit as st
import numpy as np
import time
import io
import random
from scipy.io import wavfile
import os

# ---------------- Settings ---------------- #
sample_rate = 44100
note_freq_base = {
    'S': 261.63, 'R': 293.66, 'G': 329.63, 'M': 349.23,
    'P': 392.00, 'D': 440.00, 'N': 493.88
}
octave_multipliers = {'low': 0.5, 'medium': 1.0, 'high': 2.0}
image_base_url = "https://raw.githubusercontent.com/surajdwivedi0307/surajmetronome/main/images/"

# ---------------- Streamlit State ---------------- #
if "is_playing" not in st.session_state:
    st.session_state.is_playing = False
if "sequence_to_play" not in st.session_state:
    st.session_state.sequence_to_play = []
if "bpm" not in st.session_state:
    st.session_state.bpm = 60
if "run_once" not in st.session_state:
    st.session_state.run_once = False

# ---------------- Functions ---------------- #
def generate_note_wave_flute_natural_vibrato(note, duration, octave='medium', fade_duration=0.01,
                                             vibrato_depth=0.001, vibrato_speed=2.5, add_swell=True):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    if note == '-' or note not in note_freq_base:
        tone = np.zeros_like(t)
    else:
        base_freq = note_freq_base[note] * octave_multipliers[octave]
        vibrato = vibrato_depth * np.sin(2 * np.pi * vibrato_speed * t)
        phase = 2 * np.pi * base_freq * t + vibrato
        fundamental = np.sin(phase)
        overtone1 = 0.2 * np.sin(2 * phase)
        overtone2 = 0.1 * np.sin(3 * phase)
        overtone3 = 0.05 * np.sin(4 * phase)
        noise = 0.003 * np.random.normal(0, 1, len(t))
        tone = fundamental + overtone1 + overtone2 + overtone3 + noise

    if add_swell and note != '-':
        swell = np.sin(np.pi * t / duration)
        tone *= swell

    n_samples = len(tone)
    n_fade = int(sample_rate * fade_duration)
    n_fade = min(n_fade, n_samples // 2)
    fade_in = np.linspace(0.0, 1.0, n_fade)
    fade_out = np.linspace(1.0, 0.0, n_fade)
    tone[:n_fade] *= fade_in
    tone[-n_fade:] *= fade_out

    tone *= 32767 / np.max(np.abs(tone) + 1e-5)
    return tone.astype(np.int16)

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

def play_notes_sequence(parsed_sequence, bpm=60):
    full_wave = np.array([], dtype=np.int16)
    for note_entry, multiplier, octave in parsed_sequence:
        duration = bpm_to_duration(bpm, multiplier)
        wave = generate_note_wave_flute_natural_vibrato(note_entry, duration, octave)
        full_wave = np.concatenate((full_wave, wave))
    return full_wave

def play_audio_in_streamlit(audio_data):
    buffer = io.BytesIO()
    wavfile.write(buffer, sample_rate, audio_data)
    st.audio(buffer.getvalue(), format='audio/wav')
    return buffer

def display_note_progress(parsed_sequence, bpm):
    note_display = st.empty()
    timer_display = st.empty()
    image_display = st.empty()

    total_duration = sum(bpm_to_duration(bpm, duration) for _, duration, _ in parsed_sequence)
    elapsed_time = 0.0

    for note_entry, multiplier, octave in parsed_sequence:
        duration = bpm_to_duration(bpm, multiplier)
        elapsed_time += duration

        note_name = f"{note_entry} ({octave})" if note_entry != '-' else "Rest"
        note_display.markdown(f"## 🎵 Playing: **{note_name}**")
        timer_display.markdown(f"### ⏱️ Duration: {elapsed_time:.2f}/{total_duration:.2f} seconds")

        if note_entry in note_freq_base:
            img_url = f"{image_base_url}bansuri_notes_{note_entry}.png"
            image_display.image(img_url, caption=f"{note_entry} fingering", use_container_width=True)
        else:
            image_display.empty()

        time.sleep(duration)

# ---------------- Streamlit UI ---------------- #
st.set_page_config(layout="wide")
st.title("🎶 Indian Flute Metronome + Melody Generator 🎶")
st.write("Generate and play melodies with flute note images and audio in sync.")

bpm_input = st.number_input("Enter BPM:", min_value=1, max_value=200, value=60)
note_input = st.text_input("Enter sequence (e.g., SGRG_RSN):", "DS>DP,GRSR,G-GR,GPD_")

col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("#### 🎵 Control Panel")
    if st.button("▶️ Play Input Sequence"):
        sequence = parse_notes_input(note_input)
        if not sequence:
            st.error("Invalid input sequence.")
        else:
            st.session_state.sequence_to_play = sequence
            st.session_state.bpm = bpm_input
            st.session_state.is_playing = True
            st.session_state.run_once = True

with col2:
    st.markdown("#### ℹ️ Instructions")
    st.markdown("- Use `>` for high octave, `<` for low octave.")
    st.markdown("- Use `_` to extend duration, and `,` for pauses.")
    st.markdown("- Example: `S>_R_G,,M--P`")

# ---------------- Playback Block ---------------- #
if st.session_state.run_once:
    display_note_progress(st.session_state.sequence_to_play, st.session_state.bpm)
    audio_data = play_notes_sequence(st.session_state.sequence_to_play, st.session_state.bpm)
    play_audio_in_streamlit(audio_data)
    st.session_state.run_once = False
