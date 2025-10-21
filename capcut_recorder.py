"""
CapCut Action Recorder - Train the macro by performing the CapCut workflow once

This script records all your mouse clicks, keyboard inputs, and delays between actions.
The recorded actions are saved to capcut_actions.json for the macro to replay.

Instructions:
1. Run this script: python capcut_recorder.py
2. Press 's' to START recording
3. Perform your CapCut workflow (open app, import files, edit, export)
4. Press 'q' to STOP recording and save
5. The macro will automatically use capcut_actions.json if it exists

Controls:
- Press 's' to start recording
- Press 'q' to quit and save
- All mouse clicks and keyboard inputs between start/stop will be recorded
"""

import json
import time
from pathlib import Path
from pynput import mouse, keyboard
from datetime import datetime

class CapCutRecorder:
    def __init__(self):
        self.actions = []
        self.recording = False
        self.start_time = None
        self.last_action_time = None

    def on_click(self, x, y, button, pressed):
        """Record mouse clicks"""
        if not self.recording:
            return

        if pressed:  # Only record on button press, not release
            current_time = time.time()
            delay = 0
            if self.last_action_time:
                delay = current_time - self.last_action_time

            action = {
                "type": "click",
                "x": x,
                "y": y,
                "button": str(button),
                "delay_before": round(delay, 2)
            }
            self.actions.append(action)
            self.last_action_time = current_time
            print(f"✓ Recorded click at ({x}, {y}) - {len(self.actions)} actions")

    def on_key_press(self, key):
        """Record keyboard inputs"""
        if not self.recording:
            # Check for start/stop commands
            try:
                if hasattr(key, 'char') and key.char == 's':
                    self.start_recording()
                elif hasattr(key, 'char') and key.char == 'q':
                    self.stop_recording()
            except AttributeError:
                pass
            return

        current_time = time.time()
        delay = 0
        if self.last_action_time:
            delay = current_time - self.last_action_time

        # Handle special keys
        if hasattr(key, 'char'):
            action = {
                "type": "key",
                "key": key.char,
                "delay_before": round(delay, 2)
            }
        else:
            # Special keys (ctrl, enter, etc.)
            key_name = str(key).replace('Key.', '')
            action = {
                "type": "special_key",
                "key": key_name,
                "delay_before": round(delay, 2)
            }

        self.actions.append(action)
        self.last_action_time = current_time
        print(f"✓ Recorded key: {action['key']} - {len(self.actions)} actions")

    def start_recording(self):
        """Start recording actions"""
        if self.recording:
            print("⚠ Already recording!")
            return

        self.recording = True
        self.start_time = time.time()
        self.last_action_time = time.time()
        self.actions = []
        print("\n" + "="*60)
        print("🔴 RECORDING STARTED")
        print("="*60)
        print("Perform your CapCut workflow now...")
        print("Press 'q' when done to save and quit\n")

    def stop_recording(self):
        """Stop recording and save to file"""
        if not self.recording:
            print("⚠ Not recording!")
            return

        self.recording = False

        # Save to JSON file
        output_path = Path(__file__).parent / "capcut_actions.json"

        recording_data = {
            "recorded_at": datetime.now().isoformat(),
            "total_actions": len(self.actions),
            "actions": self.actions
        }

        with open(output_path, 'w') as f:
            json.dump(recording_data, f, indent=2)

        print("\n" + "="*60)
        print("✅ RECORDING STOPPED AND SAVED")
        print("="*60)
        print(f"Total actions recorded: {len(self.actions)}")
        print(f"Saved to: {output_path}")
        print("\nThe macro will now use these recorded actions for CapCut automation!")

        # Exit the program
        return False  # This will stop the listener

    def run(self):
        """Run the recorder"""
        print("\n" + "="*60)
        print("CapCut Action Recorder")
        print("="*60)
        print("\nInstructions:")
        print("1. Press 's' to START recording")
        print("2. Perform your complete CapCut workflow:")
        print("   - Launch CapCut (or switch to it if already open)")
        print("   - Click 'Create Project'")
        print("   - Import video clip (Ctrl+I or click import button)")
        print("   - Drag video to timeline")
        print("   - Duplicate video clips (Ctrl+D or right-click duplicate)")
        print("   - Import and add images to timeline")
        print("   - Import and add voiceover to audio track")
        print("   - Import and add subtitles")
        print("   - Export video (Ctrl+E or click export)")
        print("   - Choose export location and settings")
        print("3. Press 'q' to STOP recording and save")
        print("\n⚠ Make sure to perform the COMPLETE workflow from start to finish!")
        print("\nReady? Press 's' to start recording...\n")

        # Start listeners
        mouse_listener = mouse.Listener(on_click=self.on_click)
        keyboard_listener = keyboard.Listener(on_press=self.on_key_press)

        mouse_listener.start()
        keyboard_listener.start()

        # Keep running until user quits
        keyboard_listener.join()

if __name__ == "__main__":
    recorder = CapCutRecorder()
    recorder.run()
