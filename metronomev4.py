import streamlit as st
import numpy as np
import random
import time
import io
import os
from scipy.io import wavfile
from PIL import Image
import threading

# Settings
sample_rate = 44100
saved_melodies = []
stop_flag = threading.Event()

note_freq_base = {
    'S': 261.63, 'R': 293.66, 'G': 329.63, 'M': 349.23,
    'P': 392.00, 'D': 440.00, 'N': 493.88
}
octave_multipliers = {'low': 0.5, 'medium': 1.0, 'high': 2.0}
image_folder = "/Users/surajdwivedi/Downloads/surajmetronome"  # Adjust for your folder location

def generate_note_wave_flute_natural_vibrato(note, duration, octave='medium', fade_duration=0.01,
                                             vibrato_depth=0.001, vibrato_speed=2.5, add_swell=True):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    if note == '-':
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

    tone *= 32767 / np.max(np.abs(tone))
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

def play_audio_in_streamlit(audio_data):
    buffer = io.BytesIO()
    wavfile.write(buffer, sample_rate, audio_data)
    st.audio(buffer.getvalue(), format='audio/wav')
    return buffer

# Update the image folder to GitHub raw URLs
image_base_url = "https://raw.githubusercontent.com/surajdwivedi0307/surajmetronome/main/images/"

def display_note_progress(parsed_sequence, bpm):
    note_display = st.empty()
    timer_display = st.empty()
    image_display = st.empty()
    total_notes = len(parsed_sequence)

    for idx, (note_entry, multiplier, octave) in enumerate(parsed_sequence):
        if stop_flag.is_set():
            break

        duration = bpm_to_duration(bpm, multiplier)
        note_name = f"{note_entry} ({octave})" if note_entry != '-' else "Rest"

        timer_display.markdown(f"### ⏱️ Duration: {duration:.2f} seconds")
        note_display.markdown(f"## 🎵 Playing: **{note_name}**")

        # Display image for current note
        if note_entry != '-':
            img_url = f"{image_base_url}bansuri_notes_{note_entry}.png"
            image_display.image(img_url, caption=f"{note_entry} fingering", use_container_width=True)
        else:
            image_display.empty()

        # Split sleep into small steps to allow stop
        step = 0.1  # seconds
        elapsed = 0.0
        while elapsed < duration:
            if stop_flag.is_set():
                return
            time.sleep(min(step, duration - elapsed))
            elapsed += step


def play_notes_sequence(parsed_sequence, bpm=60):
    full_wave = np.array([], dtype=np.int16)
    for note_entry, multiplier, octave in parsed_sequence:
        duration = bpm_to_duration(bpm, multiplier)
        if note_entry not in note_freq_base and note_entry != '-':
            continue
        wave = generate_note_wave_flute_natural_vibrato(note_entry, duration, octave)
        full_wave = np.concatenate((full_wave, wave))
        if note_entry == '-':
            gap_wave = np.zeros(int(sample_rate * 0.1), dtype=np.int16)
            full_wave = np.concatenate((full_wave, gap_wave))
    return full_wave

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

def save_melodies_to_file(melodies, filename='saved_melodies.txt'):
    with open(filename, 'w') as f:
        for melody in melodies:
            f.write(melody + '\n')

# ---- Streamlit UI ----
st.set_page_config(layout="wide")
st.title("🎶 Indian Flute Metronome + Melody Generator 🎶")
st.write("Generate and play random melodies or input your own sequence!")

# Layout and Inputs
bpm_input_user = st.number_input("Enter BPM:", min_value=1, max_value=200, value=60, help="Beats per minute for melody speed.")
user_input = st.text_input("Enter sequence (e.g., SGRG_RSN):", "DS>DP,GRSR,G-GR,GPD_")

col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("#### 🎵 Control Panel")
    if st.button("▶️ Play Notes"):
        stop_flag.clear()
        parsed_user = parse_notes_input(user_input)
        audio_data = play_notes_sequence(parsed_user, bpm_input_user)
        play_audio_in_streamlit(audio_data)
        display_note_progress(parsed_user, bpm_input_user)

        buffer = io.BytesIO()
        wavfile.write(buffer, sample_rate, audio_data)
        st.download_button("💽 Download WAV", data=buffer.getvalue(),
                           file_name="flute_sequence.wav", mime="audio/wav")

with col2:
    st.markdown("#### 🎶 Melody Generator")
    if st.button("⏹️ Stop"):
        stop_flag.set()

    if st.button("🎲 Generate Random Melody"):
        stop_flag.clear()
        random_melody = generate_random_melody()
        saved_melodies.append(random_melody)
        st.write(f"**Random Melody:** `{random_melody}`")
        parsed_random = parse_notes_input(random_melody)
        audio_data = play_notes_sequence(parsed_random, bpm_input_user)
        play_audio_in_streamlit(audio_data)
        display_note_progress(parsed_random, bpm_input_user)

        buffer = io.BytesIO()
        wavfile.write(buffer, sample_rate, audio_data)
        st.download_button("💽 Download Random Melody", data=buffer.getvalue(),
                           file_name="random_melody.wav", mime="audio/wav")

    if st.button("💾 Save All Generated Melodies"):
        if saved_melodies:
            save_melodies_to_file(saved_melodies)
            st.success("All melodies saved to 'saved_melodies.txt'.")
        else:
            st.warning("No melodies to save yet.")
