import cv2
import numpy as np
import time
import sys
import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# Fügt das übergeordnete Verzeichnis zum Python-Pfad hinzu, um Modul-Importe zu ermöglichen
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.camera import CameraCapture
from modules.calibration import Calibration
from modules.interaction import InteractionTracking
from modules.midi_controller import MidiController

# --- Konfiguration ---
CAMERA_ID = 0
MARKER_COLOR_LOWER = np.array()
MARKER_COLOR_UPPER = np.array()
ROIS = {
    'play_button_1': (50, 100, 80, 80),
    'play_button_2': (670, 100, 80, 80),
    'crossfader': (250, 450, 300, 50),
    'volume_fader_1': (120, 200, 50, 200),
    'volume_fader_2': (630, 200, 50, 200),
}

class App:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        self.camera = CameraCapture(camera_id=CAMERA_ID)
        self.calibrator = Calibration(marker_color_lower=MARKER_COLOR_LOWER, marker_color_upper=MARKER_COLOR_UPPER)
        self.interaction_tracker = InteractionTracking(rois=ROIS)
        self.midi_controller = MidiController()

        self.is_calibrated = False

        width, height = self.camera.frame_size
        self.canvas = tk.Canvas(window, width=width, height=height)
        self.canvas.pack()

        self.btn_calibrate = tk.Button(window, text="Kalibrieren", width=50, command=self.calibrate)
        self.btn_calibrate.pack(anchor=tk.CENTER, expand=True)

        self.status_label = tk.Label(window, text="Status: Nicht kalibriert", fg="red")
        self.status_label.pack()

        if not self.camera.initialize():
            messagebox.showerror("Kamerafehler", "Kamera konnte nicht initialisiert werden.")
            self.window.destroy()
            return
        
        if not self.midi_controller.open_port():
            messagebox.showwarning("MIDI-Fehler", "Konnte virtuellen MIDI-Port nicht öffnen.")

        self.delay = 15
        self.update()

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()

    def calibrate(self):
        print("Starte Kalibrierung...")
        frame = self.camera.get_frame()
        if frame is not None:
            if self.calibrator.calculate_homography(frame):
                self.is_calibrated = True
                print("Kalibrierung erfolgreich!")
                self.status_label.config(text="Status: Kalibriert", fg="green")
                corrected_frame_for_ref = self.calibrator.apply_correction(frame)
                if corrected_frame_for_ref is not None:
                    self.interaction_tracker.update_reference_brightness(corrected_frame_for_ref)
            else:
                self.is_calibrated = False
                self.status_label.config(text="Status: Kalibrierung fehlgeschlagen", fg="red")
                messagebox.showwarning("Kalibrierung", "Kalibrierung fehlgeschlagen. Bitte sicherstellen, dass 4 Marker sichtbar sind.")

    def update(self):
        frame = self.camera.get_frame()
        if frame is not None:
            display_frame = frame
            if self.is_calibrated:
                corrected_frame = self.calibrator.apply_correction(frame)
                if corrected_frame is not None:
                    events = self.interaction_tracker.process_frame(corrected_frame)
                    for event in events:
                        self.midi_controller.process_event(event)
                    
                    for name, (x, y, w, h) in ROIS.items():
                        cv2.rectangle(corrected_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    display_frame = corrected_frame

            self.photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.window.after(self.delay, self.update)

    def on_closing(self):
        print("Anwendung wird beendet.")
        self.camera.release()
        self.midi_controller.close_port()
        self.window.destroy()

if __name__ == "__main__":
    App(tk.Tk(), "Paper-DJ Controller")