import streamlit as st
import time
import random
import threading

# --- Setup ---
stop_flag = threading.Event()
saved_melodies = []

note_freq_base = {
    'S': 261.63, 'R': 293.66, 'G': 329.63, 'M': 349.23,
    'P': 392.00, 'D': 440.00, 'N': 493.88
}
octave_multipliers = {'low': 0.5, 'medium': 1.0, 'high': 2.0}
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

def display_note_progress_bar(parsed_sequence, bpm):
    note_text = st.empty()
    next_note_text = st.empty()
    progress_bar = st.progress(0)
    image_display = st.empty()

    total_duration = sum(bpm_to_duration(bpm, duration) for _, duration, _ in parsed_sequence)
    elapsed = 0

    for i, (note, duration_mult, octave) in enumerate(parsed_sequence):
        if stop_flag.is_set():
            break

        duration = bpm_to_duration(bpm, duration_mult)
        next_note = parsed_sequence[i + 1][0] if i + 1 < len(parsed_sequence) else '—'
        current_note_label = f"{note} ({octave})" if note != '-' else "Rest"
        next_note_label = f"Next: {next_note}" if next_note != '-' else "Next: Rest"

        note_text.markdown(f"### 🎵 Playing: **{current_note_label}**")
        next_note_text.markdown(f"##### ⏭️ {next_note_label}")

        # Show note image
        if note in note_freq_base:
            img_url = f"{image_base_url}bansuri_notes_{note}.png"
            image_display.image(img_url, caption=f"{note} fingering", use_container_width=True)
        else:
            image_display.empty()

        # Animate total progress bar
        steps = 25
        for step in range(steps):
            if stop_flag.is_set():
                break
            time.sleep(duration / steps)
            elapsed += duration / steps
            overall_progress = min(int((elapsed / total_duration) * 100), 100)
            progress_bar.progress(overall_progress)

    note_text.markdown("### ✅ Done!")
    next_note_text.empty()
    image_display.empty()
    progress_bar.progress(100)

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

# --- Streamlit UI ---
st.set_page_config(layout="centered")
st.title("🎶 Smooth Flute Metronome")
st.caption("One animated progress bar with live notes and images")

bpm_input_user = st.slider("🎚️ BPM", min_value=30, max_value=200, value=60)
user_input = st.text_input("✍️ Enter note sequence", "SG>R_,GGM,DP-")

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### ▶️ Playback")
    if st.button("Play Sequence"):
        stop_flag.clear()
        parsed_user = parse_notes_input(user_input)
        if parsed_user:
            display_note_progress_bar(parsed_user, bpm_input_user)
        else:
            st.error("Invalid input.")

    if st.button("⏹️ Stop"):
        stop_flag.set()

with col2:
    st.markdown("#### 🎲 Random Melody")
    if st.button("Generate Random"):
        stop_flag.clear()
        rand_melody = generate_random_melody()
        saved_melodies.append(rand_melody)
        st.write(f"`{rand_melody}`")
        parsed = parse_notes_input(rand_melody)
        display_note_progress_bar(parsed, bpm_input_user)

    if st.button("💾 Save All"):
        if saved_melodies:
            save_melodies_to_file(saved_melodies)
            st.success("Saved to saved_melodies.txt")
        else:
            st.warning("No melodies to save.")
