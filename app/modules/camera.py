import cv2
import numpy as np
from typing import Optional, Tuple


class CameraCapture:
    """
    Kameramodul für die kontinuierliche Bildaufnahme.
    Verantwortlich für die Initialisierung der Webcam und das Einlesen von Frames.
    """
    
    def __init__(self, camera_id: int = 0):
        """
        Initialisiert die Kamera.
        
        Args:
            camera_id: Kamera-ID (Standard: 0 für die Standard-Webcam)
        """
        self.camera_id = camera_id
        self.cap = None
        self.is_initialized = False
        self.frame_size = (640, 480)  # Standardauflösung
        
    def initialize(self) -> bool:
        """
        Initialisiert die Kameraverbindung.
        
        Returns:
            bool: True bei erfolgreicher Initialisierung, False bei Fehler
        """
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                print(f"Fehler: Konnte Kamera mit ID {self.camera_id} nicht öffnen")
                return False
            
            # Setze Auflösung
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_size[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_size[1])
            
            # Überprüfe, ob die Auflösung gesetzt wurde
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            self.frame_size = (actual_width, actual_height)
            print(f"Kamera initialisiert: {self.frame_size[0]}x{self.frame_size[1]}")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"Fehler bei der Kamerainitialisierung: {e}")
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Liest einen Frame von der Kamera.
        
        Returns:
            Optional[np.ndarray]: Frame als NumPy-Array oder None bei Fehler
        """
        if not self.is_initialized or self.cap is None:
            print("Kamera nicht initialisiert")
            return None
        
        try:
            ret, frame = self.cap.read()
            if not ret:
                print("Fehler: Konnte Frame nicht lesen")
                return None
            
            return frame
            
        except Exception as e:
            print(f"Fehler beim Lesen des Frames: {e}")
            return None
    
    def get_frame_rgb(self) -> Optional[np.ndarray]:
        """
        Liest einen Frame von der Kamera und konvertiert ihn zu RGB.
        
        Returns:
            Optional[np.ndarray]: Frame als RGB-NumPy-Array oder None bei Fehler
        """
        frame = self.get_frame()
        if frame is not None:
            # Konvertiere BGR zu RGB
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return None
    
    def release(self):
        """Gibt die Kameraressourcen frei."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            self.is_initialized = False
            print("Kamera freigegeben")
    
    def is_running(self) -> bool:
        """Prüft, ob die Kamera läuft."""
        return self.is_initialized and self.cap is not None and self.cap.isOpened()
    
    def get_camera_info(self) -> dict:
        """Gibt Informationen über die Kamera zurück."""
        if not self.is_initialized:
            return {"status": "not_initialized"}
        
        return {
            "status": "initialized",
            "camera_id": self.camera_id,
            "frame_size": self.frame_size,
            "fps": self.cap.get(cv2.CAP_PROP_FPS) if self.cap else 0,
            "fourcc": self.cap.get(cv2.CAP_PROP_FOURCC) if self.cap else 0
        }
    
    def __del__(self):
        """Destruktor zur Sicherstellung der Ressourcenfreigabe."""
        self.release()


# Beispiel für die Verwendung
if __name__ == "__main__":
    camera = CameraCapture()
    
    if camera.initialize():
        print("Kamera erfolgreich initialisiert")
        
        # Test: Einige Frames anzeigen
        for i in range(10):
            frame = camera.get_frame()
            if frame is not None:
                print(f"Frame {i+1} erhalten: {frame.shape}")
                
                # Zeige Frame an (optional)
                cv2.imshow('Camera Test', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        camera.release()
        cv2.destroyAllWindows()
    else:
        print("Kamerainitialisierung fehlgeschlagen")