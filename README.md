  
# Paper-DJ Controller  

## Beschreibung  
Die **Paper-DJ Controller**-Anwendung ist eineOpen-Source-Software, die gedruckte DJ-Steuerungen (Mixer, Plattenspieler, MIDI-Controller) über eine Webcam erkennt und in MIDI-Befehle für Mixxx Übersetzung umwandelt.  

## Installation  
1. **Abhängigkeiten installieren**:  
   ```bash  
   pip install -r requirements.txt  
   ```  
2. **Projektstruktur**:  
   - Das Projekt ist modular aufgebaut mit den Hauptmodulen: `camera.py`, `calibration.py`, `interaction.py`, `midi_controller.py`.  

## Ausführung  
1. **Starten der Anwendung**:  
   ```bash  
   myenv/bin/python app/main.py  
   ```  
2. **Kalibrierung**:  
   - Drucken Sie Markierungen auf dieDJ-Steuerungen (z.B. 4 Ecken und Mittelpunkt von Tasten/Fadern).  
   - Follow die Anweisungen in der Benutzeroberfläche für die Homographie-Korrektur.  

## MIDI-Integration  
- Stellen Sie sicher, dass Ihre MIDI-Eingabegeräte (z.B. Mixxx) erkannt werden.  
- Teste die MIDI-Ausgabe manuell in der App oder direkt in Mixxx.  

## Fehlerbehebung  
- **Syntaxfehler in `calibration.py`**:  
  - Linie 2 muss eine Funktion mit Doppelpunkt beenden (`def ...():`).  