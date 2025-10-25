import rtmidi
import time
from typing import Optional, Dict, Any

class MidiController:
    """
    MIDI-Steuerungsmodul.
    Verwaltet die Erstellung eines virtuellen MIDI-Ports und sendet MIDI-Nachrichten.
    """

    def __init__(self, port_name: str = "PaperDJ-Controller"):
        """
        Initialisiert den MIDI-Controller.

        Args:
            port_name: Der Name des zu erstellenden virtuellen MIDI-Ports.
        """
        self.port_name = port_name
        self.midi_out = rtmidi.MidiOut()
        self.port_open = False
        self.control_mapping = self._get_default_mapping()

    def _get_default_mapping(self) -> Dict[str, Dict[str, int]]:
        """
        Definiert ein Standard-Mapping von Steuerelement-Namen zu MIDI-Nachrichten.
        Dies sollte in einer Konfigurationsdatei ausgelagert werden.
        """
        return {
            # Buttons / Pads -> Note On/Off
            'play_button_1': {'type': 'note', 'channel': 1, 'note': 60}, # C4
            'play_button_2': {'type': 'note', 'channel': 2, 'note': 60}, # C4

            # Faders / Knobs -> Control Change (CC)
            'crossfader':    {'type': 'cc', 'channel': 1, 'control': 10},
            'volume_fader_1':{'type': 'cc', 'channel': 1, 'control': 11},
            'volume_fader_2':{'type': 'cc', 'channel': 2, 'control': 11},
            'eq_high_knob_1':{'type': 'cc', 'channel': 1, 'control': 20},
            'eq_mid_knob_1': {'type': 'cc', 'channel': 1, 'control': 21},
            'eq_low_knob_1': {'type': 'cc', 'channel': 1, 'control': 22},
        }

    def open_port(self) -> bool:
        """
        Öffnet den virtuellen MIDI-Ausgangsport.

        Returns:
            bool: True, wenn der Port erfolgreich geöffnet wurde, sonst False.
        """
        try:
            self.midi_out.open_virtual_port(self.port_name)
            self.port_open = True
            print(f"Virtueller MIDI-Port '{self.port_name}' erfolgreich geöffnet.")
            return True
        except Exception as e:
            print(f"Fehler beim Öffnen des virtuellen MIDI-Ports: {e}")
            self.port_open = False
            return False

    def close_port(self):
        """Schließt den MIDI-Port und gibt die Ressourcen frei."""
        if self.port_open:
            self.midi_out.close_port()
            self.port_open = False
            print(f"MIDI-Port '{self.port_name}' geschlossen.")
    
    def __del__(self):
        """Destruktor, um sicherzustellen, dass der Port geschlossen wird."""
        self.close_port()

    def process_event(self, event: Dict[str, Any]):
        """
        Verarbeitet ein einzelnes Event vom InteractionTracking-Modul und sendet eine MIDI-Nachricht.

        Args:
            event: Das Event-Dictionary (z.B. {'type': 'button', 'name': 'play_button_1', 'state': 'pressed'}).
        """
        if not self.port_open:
            print("MIDI-Port ist nicht geöffnet. Senden nicht möglich.")
            return

        control_name = event.get('name')
        if control_name not in self.control_mapping:
            # print(f"Warnung: Kein MIDI-Mapping für '{control_name}' gefunden.")
            return

        mapping = self.control_mapping[control_name]
        event_type = event.get('type')

        message = None
        if event_type == 'button' and mapping['type'] == 'note':
            note = mapping['note']
            channel = mapping['channel'] - 1 # rtmidi ist 0-basiert
            state = event.get('state')
            velocity = 127 if state == 'pressed' else 0
            # Note On: 0x90, Note Off: 0x80. rtmidi behandelt velocity=0 als Note Off.
            message = [(0x90 + channel), note, velocity]

        elif event_type == 'fader' and mapping['type'] == 'cc':
            control = mapping['control']
            channel = mapping['channel'] - 1
            value = event.get('value', 0)
            # Control Change: 0xB0
            message = [(0xB0 + channel), control, value]

        if message:
            self.midi_out.send_message(message)
            # print(f"MIDI gesendet: {message} für Event: {event}")


# Beispiel für die Verwendung
if __name__ == '__main__':
    midi_controller = MidiController()
    
    if midi_controller.open_port():
        print("Sende Test-MIDI-Nachrichten...")

        # Test 1: Simuliere einen Tastendruck für 'play_button_1'
        print("\n-- Test Button --")
        play_event_press = {'type': 'button', 'name': 'play_button_1', 'state': 'pressed'}
        midi_controller.process_event(play_event_press)
        time.sleep(0.5)
        play_event_release = {'type': 'button', 'name': 'play_button_1', 'state': 'released'}
        midi_controller.process_event(play_event_release)
        print("Button-Test abgeschlossen.")

        # Test 2: Simuliere eine Fader-Bewegung für 'crossfader'
        print("\n-- Test Fader --")
        for val in range(0, 128, 16):
            fader_event = {'type': 'fader', 'name': 'crossfader', 'value': val}
            midi_controller.process_event(fader_event)
            time.sleep(0.1)
        # Zurück zur Mitte
        fader_event = {'type': 'fader', 'name': 'crossfader', 'value': 64}
        midi_controller.process_event(fader_event)
        print("Fader-Test abgeschlossen.")

        # Test 3: Unbekanntes Event
        print("\n-- Test unbekanntes Event --")
        unknown_event = {'type': 'button', 'name': 'unknown_control', 'state': 'pressed'}
        midi_controller.process_event(unknown_event)
        print("Test für unbekanntes Event abgeschlossen.")

        midi_controller.close_port()
    else:
        print("Konnte den MIDI-Port nicht öffnen. Tests werden übersprungen.")