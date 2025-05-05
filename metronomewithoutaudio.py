import streamlit as st
import numpy as np
import random
import time
from PIL import Image
import threading

# Settings
saved_melodies = []
stop_flag = threading.Event()

note_freq_base = {
    'S': 261.63, 'R': 293.66, 'G': 329.63, 'M': 349.23,
    'P': 392.00, 'D': 440.00, 'N': 493.88
}
octave_multipliers = {'low': 0.5, 'medium': 1.0, 'high': 2.0}

# GitHub-hosted images
image_base_url = "https://raw.githubusercontent.com/surajdwivedi0307/surajmetronome/main/images/"

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

def display_note_progress(parsed_sequence, bpm):
    note_display = st.empty()
    timer_display = st.empty()
    image_display = st.empty()

    total_duration = sum(bpm_to_duration(bpm, duration) for _, duration, _ in parsed_sequence)
    elapsed_time = 0.0

    for note_entry, multiplier, octave in parsed_sequence:
        if stop_flag.is_set():
            break

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
st.write("Generate and visualize melodies or input your own sequence!")

bpm_input_user = st.number_input("Enter BPM:", min_value=1, max_value=200, value=60, help="Beats per minute for melody speed.")
user_input = st.text_input("Enter sequence (e.g., SGRG_RSN):", "DS>DP,GRSR,G-GR,GPD_")

col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("#### 🎵 Control Panel")
    if st.button("▶️ Play Notes"):
        stop_flag.clear()
        parsed_user = parse_notes_input(user_input)
        if not parsed_user:
            st.error("Invalid input sequence. Please check your notes.")
        else:
            display_note_progress(parsed_user, bpm_input_user)  # ⬅️ Audio removed, only display

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
        display_note_progress(parsed_random, bpm_input_user)  # ⬅️ Only visual, no audio

    if st.button("💾 Save All Generated Melodies"):
        if saved_melodies:
            save_melodies_to_file(saved_melodies)
            st.success("All melodies saved to 'saved_melodies.txt'.")
        else:
            st.warning("No melodies to save yet.")
