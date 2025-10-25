import cv2
import numpy as np
from typing import Dict, Any, Optional, Tuple

class InteractionTracking:
    """
    Interaktions-Tracking-Modul.
    Verarbeitet den korrigierten Frame und erkennt Benutzeraktionen.
    """

    def __init__(self, rois: Dict[str, Tuple[int, int, int, int]]):
        """
        Initialisiert das Tracking-Modul.

        Args:
            rois: Ein Dictionary mit den Regions of Interest (ROI) für jedes Steuerelement.
                  Format: {'control_name': (x, y, w, h)}
        """
        self.rois = rois
        self.control_states: Dict[str, Any] = {name: {} for name in rois}
        self._initialize_control_states()

    def _initialize_control_states(self):
        """Initialisiert die Referenzzustände für die Steuerelemente."""
        # Hier würden normalerweise die Referenzwerte (z.B. Helligkeit) für jedes ROI
        # aus einem "sauberen" Frame (ohne Interaktion) extrahiert.
        # Für dieses Beispiel verwenden wir statische Annahmen.
        for name, roi in self.rois.items():
            if 'button' in name:
                self.control_states[name] = {'pressed': False, 'ref_brightness': 128} # Annahme
            elif 'fader' in name:
                self.control_states[name] = {'value': 0, 'marker_color_lower': np.array(), 'marker_color_upper': np.array()} # Annahme für roten Marker
            elif 'knob' in name:
                 self.control_states[name] = {'angle': 0, 'prev_angle': 0}

    def update_reference_brightness(self, corrected_frame: np.ndarray):
        """
        Aktualisiert die Referenzhelligkeit für alle Tasten-ROIs.
        Sollte auf einem Frame ohne Fingerinteraktion aufgerufen werden.
        """
        gray_frame = cv2.cvtColor(corrected_frame, cv2.COLOR_BGR2GRAY)
        for name, roi in self.rois.items():
            if 'button' in name:
                x, y, w, h = roi
                roi_gray = gray_frame[y:y+h, x:x+w]
                self.control_states[name]['ref_brightness'] = np.mean(roi_gray)
                print(f"Referenzhelligkeit für {name} gesetzt auf: {self.control_states[name]['ref_brightness']:.2f}")


    def track_button(self, name: str, roi_gray: np.ndarray, threshold_factor: float = 0.7) -> Optional[Dict[str, Any]]:
        """
        Überwacht eine Taste auf einen Tastendruck.

        Args:
            name: Der Name der Taste.
            roi_gray: Der Graustufen-ROI der Taste.
            threshold_factor: Faktor, um den die Helligkeit sinken muss, um einen Druck zu erkennen.

        Returns:
            Ein Event-Dictionary {'type': 'button', 'name': name, 'state': 'pressed'/'released'} oder None.
        """
        current_brightness = np.mean(roi_gray)
        ref_brightness = self.control_states[name]['ref_brightness']
        is_pressed = self.control_states[name]['pressed']
        
        event = None
        if current_brightness < ref_brightness * threshold_factor and not is_pressed:
            self.control_states[name]['pressed'] = True
            event = {'type': 'button', 'name': name, 'state': 'pressed'}
        elif current_brightness >= ref_brightness * threshold_factor and is_pressed:
            self.control_states[name]['pressed'] = False
            event = {'type': 'button', 'name': name, 'state': 'released'}
            
        return event

    def track_fader(self, name: str, roi_bgr: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Verfolgt die Position eines Schiebereglers.

        Args:
            name: Der Name des Faders.
            roi_bgr: Der BGR-ROI des Faders.

        Returns:
            Ein Event-Dictionary {'type': 'fader', 'name': name, 'value': 0-127} oder None.
        """
        hsv_roi = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)
        lower = self.control_states[name]['marker_color_lower']
        upper = self.control_states[name]['marker_color_upper']
        
        mask = cv2.inRange(hsv_roi, lower, upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        # Finde die größte Kontur
        c = max(contours, key=cv2.contourArea)
        M = cv2.moments(c)
        if M["m00"] == 0:
            return None
            
        # Schwerpunkt des Markers
        cY = int(M["m01"] / M["m00"])
        
        # Normalisiere die Y-Position auf einen Wert von 0-127
        fader_height = roi_bgr.shape
        value = int(np.interp(cY, [0, fader_height],))
        
        # Sende nur, wenn sich der Wert ändert
        if value != self.control_states[name]['value']:
            self.control_states[name]['value'] = value
            return {'type': 'fader', 'name': name, 'value': value}
        
        return None


    def process_frame(self, corrected_frame: np.ndarray) -> list:
        """
        Verarbeitet einen einzelnen korrigierten Frame und erkennt alle Interaktionen.

        Args:
            corrected_frame: Der perspektivisch korrigierte Frame.

        Returns:
            Eine Liste von erkannten Events.
        """
        events = []
        gray_frame = cv2.cvtColor(corrected_frame, cv2.COLOR_BGR2GRAY)

        for name, (x, y, w, h) in self.rois.items():
            roi_gray = gray_frame[y:y+h, x:x+w]
            roi_bgr = corrected_frame[y:y+h, x:x+w]

            event = None
            if 'button' in name:
                event = self.track_button(name, roi_gray)
            elif 'fader' in name:
                event = self.track_fader(name, roi_bgr)
            # Hier könnten weitere Tracker für Knobs, Turntables etc. aufgerufen werden

            if event:
                events.append(event)
        
        return events

# Beispiel für die Verwendung
if __name__ == '__main__':
    # Dummy Frame und ROIs für den Test
    test_frame = np.full((600, 800, 3), 200, dtype=np.uint8)
    
    rois = {
        'play_button_1': (50, 100, 80, 80),
        'crossfader': (200, 400, 300, 50)
    }
    
    tracker = InteractionTracking(rois)
    tracker.update_reference_brightness(test_frame)

    # 1. Simuliere einen Tastendruck (Finger als dunkler Fleck)
    cv2.circle(test_frame, (90, 140), 30, (50, 50, 50), -1)
    
    # 2. Simuliere einen Fader-Marker
    cv2.rectangle(test_frame, (300, 405, 20, 40), (0, 0, 255), -1) # Roter Marker

    detected_events = tracker.process_frame(test_frame)
    print("Erkannte Events:", detected_events)

    cv2.imshow("Test Frame", test_frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()