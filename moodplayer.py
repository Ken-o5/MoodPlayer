"""
==========================================================
                     MOODPLAYER
==========================================================

Project Type : Investigatory Project - Computer Science
Author       : Spidey
Purpose      : To create a Mood-Based Music Player that
               plays songs based on user mood with a
               graphical beat visualizer. Demonstrates
               database integration, GUI, and audio handling.

Description  :
MoodPlayer allows the user to enter their mood and then
plays songs from folders mapped to moods in a MySQL DB.
The GUI provides controls for playback, shuffle, volume
and displays a real-time visualizer that reacts to music.

Technologies :
- Python 3.x
- Tkinter (GUI)
- Pygame (audio playback)
- MySQL Connector
- OS Module (filesystem handling)
- Random module (for shuffle & visualizer)
- Threading (safe playback & GUI updates)

==========================================================
"""

# =============================
# IMPORTS
# =============================
import mysql.connector  # For database handling
import os              # For file/folder operations
import random          # Shuffle & visualizer randomness
import pygame          # Audio playback
import tkinter as tk   # GUI
from tkinter import ttk
import threading       # Thread-safe operations
import time            # Optional sleep for GUI tweaks

# =============================
# GLOBAL CONFIG
# =============================
# Theme colors
THEME = {
    "bg": "#121212",      # Background
    "button": "#ff0000",  # Buttons
    "button_fg": "#ffffff",
    "text": "#00aaff",    # Labels
    "select_bg": "#ff5555",
    "canvas_bar1": "#ff0000",
    "canvas_bar2": "#00aaff",
    "list_bg": "#1f1f1f",
    "list_fg": "#00aaff"
}

# Initialize Pygame Mixer
pygame.mixer.init()

# =============================
# DATABASE FUNCTIONS
# =============================
def connect_db():
    """
    Connects to MySQL database.
    Credentials are read from environment variables so that no password
    is stored in the source code (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME).
    Returns connection object or None if fails.
    """
    try:
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", ""),
            database=os.environ.get("DB_NAME", "musicplayerdb")
        )
        return conn
    except mysql.connector.Error as e:
        print("Database connection error:", e)
        return None

def get_folder_by_mood(mood):
    """
    Fetches folder path from mood_folders table for a given mood.
    Returns folder path string or None.
    """
    try:
        conn = connect_db()
        if not conn:
            return None
        cursor = conn.cursor()
        cursor.execute("SELECT folder_path FROM mood_folders WHERE mood=%s", (mood,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except mysql.connector.Error as e:
        print("Database error:", e)
        return None

def get_mp3_files(folder):
    """
    Retrieves all .mp3 files from a given folder.
    Returns list of full paths.
    """
    if folder and os.path.exists(folder):
        return [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".mp3")]
    return []

# =============================
# MUSIC PLAYER CLASS
# =============================
class MusicPlayer:
    """
    Handles music playback: play, pause, stop, next, shuffle, volume.
    Thread-safe operations to avoid GUI freezing.
    """
    def __init__(self):
        self.songs = []          # List of song file paths
        self.index = 0           # Current song index
        self.playing = False
        self.paused = False
        self.shuffle = False
        self.volume = 0.7        # Default volume (0.0 - 1.0)
        pygame.mixer.music.set_volume(self.volume)
        self.lock = threading.Lock()  # Thread lock

    def load_songs(self, songs):
        """
        Loads a list of songs.
        """
        with self.lock:
            self.songs = songs
            self.index = 0

    def play(self, index=None):
        """
        Plays a song by index. If none, uses current index.
        """
        with self.lock:
            if not self.songs:
                return
            if index is not None:
                self.index = index
            pygame.mixer.music.stop()  # Stop previous
            pygame.mixer.music.load(self.songs[self.index])
            pygame.mixer.music.play()
            self.playing = True
            self.paused = False
            pygame.mixer.music.set_volume(self.volume)

    def pause(self):
        """
        Toggles pause/resume.
        """
        with self.lock:
            if self.playing:
                if not self.paused:
                    pygame.mixer.music.pause()
                    self.paused = True
                else:
                    pygame.mixer.music.unpause()
                    self.paused = False

    def stop(self):
        """
        Stops music playback.
        """
        with self.lock:
            pygame.mixer.music.stop()
            self.playing = False
            self.paused = False

    def next_song(self):
        """
        Plays next song. Shuffle mode if enabled.
        """
        with self.lock:
            if not self.songs:
                return
            if self.shuffle:
                self.index = random.randint(0, len(self.songs) - 1)
            else:
                self.index = (self.index + 1) % len(self.songs)
            self.play(self.index)

    def toggle_shuffle(self):
        """
        Enables/disables shuffle mode.
        """
        with self.lock:
            self.shuffle = not self.shuffle

    def set_volume(self, vol):
        """
        Sets volume (0.0 - 1.0)
        """
        with self.lock:
            self.volume = max(0.0, min(1.0, vol))
            pygame.mixer.music.set_volume(self.volume)

# =============================
# GUI CLASS
# =============================
class MoodPlayerGUI:
    """
    Tkinter GUI for MoodPlayer with visualizer.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("MoodPlayer")
        self.root.geometry("650x550")
        self.root.configure(bg=THEME["bg"])
        self.player = MusicPlayer()

        # --- Title ---
        tk.Label(root, text="MoodPlayer 🎵", fg=THEME["button"], bg=THEME["bg"],
                 font=("Helvetica", 24, "bold")).pack(pady=10)

        # --- Mood input ---
        tk.Label(root, text="Enter your mood:", fg=THEME["text"], bg=THEME["bg"],
                 font=("Helvetica", 12, "bold")).pack()
        self.mood_entry = tk.Entry(root, font=("Helvetica", 12),
                                   bg=THEME["list_bg"], fg=THEME["list_fg"],
                                   insertbackground='white')
        self.mood_entry.pack(pady=5)
        tk.Button(root, text="Load Songs", command=self.load_songs,
                  bg=THEME["button"], fg=THEME["button_fg"]).pack(pady=5)

        # --- Song list ---
        self.song_listbox = tk.Listbox(root, bg=THEME["list_bg"], fg=THEME["list_fg"],
                                       selectbackground=THEME["select_bg"], height=6)
        self.song_listbox.pack(fill=tk.X, padx=20, pady=5)

        # --- Controls ---
        controls = tk.Frame(root, bg=THEME["bg"])
        controls.pack(pady=5)
        tk.Button(controls, text="▶️ Play/Pause", command=self.play_pause,
                  bg=THEME["button"], fg=THEME["button_fg"], width=12).grid(row=0, column=0, padx=5)
        tk.Button(controls, text="⏭️ Next", command=self.next_song,
                  bg=THEME["button"], fg=THEME["button_fg"], width=12).grid(row=0, column=1, padx=5)
        tk.Button(controls, text="⏹️ Stop", command=self.stop_music,
                  bg=THEME["button"], fg=THEME["button_fg"], width=12).grid(row=0, column=2, padx=5)
        tk.Button(controls, text="🔀 Shuffle", command=self.toggle_shuffle,
                  bg=THEME["button"], fg=THEME["button_fg"], width=12).grid(row=1, column=0, columnspan=3, pady=5)
        tk.Button(controls, text="❌ Exit", command=self.exit_player,
                  bg=THEME["button"], fg=THEME["button_fg"], width=12).grid(row=1, column=2, columnspan=3, padx=5)


        # --- Volume Slider ---
        tk.Label(root, text="Volume:", fg=THEME["text"], bg=THEME["bg"]).pack()
        self.volume_slider = tk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL,
                                      command=self.set_volume, bg=THEME["bg"], fg=THEME["text"],
                                      highlightthickness=0, troughcolor="#333333")
        self.volume_slider.set(70)
        self.volume_slider.pack(pady=5, fill=tk.X, padx=50)

        # --- Current Song Label ---
        self.current_song_label = tk.Label(root, text="No song playing",
                                           fg=THEME["text"], bg=THEME["bg"], font=("Helvetica", 12))
        self.current_song_label.pack(pady=5)

        # --- Visualizer Canvas ---
        self.canvas = tk.Canvas(root, width=600, height=120, bg=THEME["bg"], highlightthickness=0)
        self.canvas.pack(pady=10)
        self.bar_count = 25
        self.bars = [self.canvas.create_rectangle(i*24+2, 120, i*24+20, 120,
                                                  fill=THEME["canvas_bar1"]) for i in range(self.bar_count)]

        # --- Periodic updates ---
        self.update_visualizer()
        self.check_song_end()

    # ----------------- GUI METHODS -----------------
    def load_songs(self):
        mood = self.mood_entry.get().strip().lower()
        folder = get_folder_by_mood(mood)
        if not folder:
            self.song_listbox.delete(0, tk.END)
            self.current_song_label.config(text=f"No folder found for '{mood}'")
            return
        songs = get_mp3_files(folder)
        if not songs:
            self.song_listbox.delete(0, tk.END)
            self.current_song_label.config(text="No .mp3 files found in folder")
            return
        self.player.load_songs(songs)
        self.song_listbox.delete(0, tk.END)
        for s in songs:
            self.song_listbox.insert(tk.END, os.path.basename(s))
        self.current_song_label.config(text=f"Loaded {len(songs)} songs for '{mood}'")

    def play_pause(self):
        if not self.player.playing:
            selected = self.song_listbox.curselection()
            index = selected[0] if selected else 0
            self.player.play(index)
        else:
            self.player.pause()
        self.update_current_song_label()

    def next_song(self):
        """
        Plays next song safely in a separate thread to prevent GUI freezing.
        """
        if not self.player.songs:
            return

        def play_next():
            # Stop current song
            self.player.stop()
            
            # Choose next song
            if self.player.shuffle:
                self.player.index = random.randint(0, len(self.player.songs) - 1)
            else:
                self.player.index = (self.player.index + 1) % len(self.player.songs)

            try:
                # Load and play next
                pygame.mixer.music.load(self.player.songs[self.player.index])
                pygame.mixer.music.play()
                self.player.playing = True
                self.player.paused = False
            except Exception as e:
                print("Error playing next song:", e)
                return

            # Update GUI safely from main thread
            self.root.after(0, self.update_current_song_label)
            self.root.after(0, lambda: self.song_listbox.select_clear(0, tk.END))
            self.root.after(0, lambda: self.song_listbox.select_set(self.player.index))

        threading.Thread(target=play_next, daemon=True).start()


    def stop_music(self):
        self.player.stop()
        self.update_current_song_label()

    def toggle_shuffle(self):
        self.player.toggle_shuffle()
        state = "ON" if self.player.shuffle else "OFF"
        self.current_song_label.config(text=f"Shuffle {state}")

    def set_volume(self, val):
        vol = int(val)/100
        self.player.set_volume(vol)

    def update_current_song_label(self):
        if self.player.playing:
            song_name = os.path.basename(self.player.songs[self.player.index])
            self.current_song_label.config(text=f"🎵 Now Playing: {song_name}")
        else:
            self.current_song_label.config(text="No song playing")

    def check_song_end(self):
        if self.player.playing and not pygame.mixer.music.get_busy() and not self.player.paused:
            self.next_song()
        self.root.after(500, self.check_song_end)

    def update_visualizer(self):
        """
        Bars pulse according to the current audio volume.
        """
        if self.player.playing and not self.player.paused:
            # Get pseudo-volume using built-in volume (simplistic)
            volume = self.player.volume  # 0.0 to 1.0
            for i, bar in enumerate(self.bars):
                # Height reacts to volume with small randomness
                height = int(volume*100) + random.randint(5, 40)
                color = THEME["canvas_bar1"] if i % 2 == 0 else THEME["canvas_bar2"]
                self.canvas.coords(bar, i*24+2, 120-height, i*24+20, 120)
                self.canvas.itemconfig(bar, fill=color)
        else:
            for bar in self.bars:
                self.canvas.coords(bar, self.canvas.coords(bar)[0], 120, self.canvas.coords(bar)[2], 120)
        self.root.after(100, self.update_visualizer)
    def exit_player(self):
        """
        Stops music and exits the application safely.
        """
        try:
            self.player.stop()  # stop current music
        except:
            pass
        self.root.destroy()  # close Tkinter window


# =============================
# MAIN
# =============================
if __name__ == "__main__":
    root = tk.Tk()
    gui = MoodPlayerGUI(root)
    root.mainloop()
