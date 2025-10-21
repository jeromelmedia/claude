# CapCut Action Recorder Instructions

## 🎯 Goal
Record your CapCut workflow once, then the macro will replay it automatically every time!

---

## 📦 Step 1: Install Dependencies

Open Command Prompt or PowerShell and run:

```bash
pip install pyautogui pynput
```

**Note:** If you get errors, try:
```bash
python -m pip install pyautogui pynput
```

---

## 🎬 Step 2: Record Your CapCut Workflow

### A. Launch the Recorder

In your project folder, run:

```bash
python PyAutoGuiRecorder.py
```

A GUI window will open that looks like this:

![PyAutoGUI Recorder GUI](images/PyAutoGUI-Recorder.png)

### B. Start Recording

1. **Click the RED "Record" button** in the GUI
2. **Perform your complete CapCut workflow:**
   - Launch CapCut
   - Click "Create Project"
   - Press `Ctrl+I` to import files
   - Type the path to your video file, press Enter
   - Click on the imported video in the media panel
   - Drag it to the timeline
   - Duplicate the video clip (Ctrl+D) multiple times for 90-second loop
   - Import images (Ctrl+I for each image)
   - Drag each image to timeline
   - Import voiceover (Ctrl+I)
   - Drag voiceover to audio track
   - Import subtitles (.srt file)
   - Press `Ctrl+E` to export
   - Type export path and settings
   - Click export button

3. **Click the STOP button** when done

### C. Review and Test

- The GUI shows all recorded actions (every click, keystroke, delay)
- **Click the PLAY button** to test your recording
- If it works correctly, proceed to save
- If not, click STOP, clear the list, and record again

### D. Save the Recording

1. **Click the DOWNLOAD button**
2. Save as: `capcut_automation.py`
3. The file contains pure Python code using PyAutoGUI!

---

## 🔧 Step 3: Integrate into Macro

You have **TWO OPTIONS**:

### **Option A: Use the Python File Directly (Easiest)**

Open `ai_video_generation_macro.py` and find the `edit_video_capcut()` method.

Replace the entire method with:

```python
def edit_video_capcut(self, voiceover_path: Optional[str], image_paths: List[str], subtitle_path: str) -> str:
    """Edit video using CapCut with recorded automation."""
    print("\n=== STEP 8: Editing Video in CapCut ===")
    print("Running recorded CapCut automation...")
    print("⚠ DO NOT TOUCH YOUR MOUSE OR KEYBOARD! ⚠")

    time.sleep(5)  # Give you time to prepare

    # Run your recorded automation
    import capcut_automation

    # Wait for export to complete
    export_path = self.working_dir / "final_video.mp4"
    max_wait = 600  # 10 minutes
    waited = 0

    print("\nWaiting for video export to complete...")
    while waited < max_wait:
        if export_path.exists() and export_path.stat().st_size > 1000:
            print(f"✓ Video exported successfully: {export_path}")
            return str(export_path)
        time.sleep(5)
        waited += 5
        if waited % 30 == 0:
            print(f"  Still waiting... ({waited}/{max_wait} seconds)")

    print("⚠ Export timeout - please check CapCut manually")
    return str(export_path)
```

### **Option B: Copy the Code Into the Method**

1. Open `capcut_automation.py` (the file you saved)
2. Copy ALL the code
3. Paste it into the `edit_video_capcut()` method in `ai_video_generation_macro.py`

---

## ⚠️ Important Tips

### **File Paths**
Your recording will have HARDCODED paths like:
```python
pyautogui.write('C:\\Users\\alexh\\..\\video.mp4')
```

You need to make these DYNAMIC. Replace hardcoded paths with:
- `self.selected_character_video` for the video file
- `voiceover_path` for the voiceover
- `subtitle_path` for the subtitles
- `image_paths[0]`, `image_paths[1]`, etc. for images

**Example transformation:**
```python
# BEFORE (hardcoded):
pyautogui.write('C:\\Users\\alexh\\Desktop\\video.mp4')

# AFTER (dynamic):
pyautogui.write(self.selected_character_video)
```

### **Timing Issues**
If CapCut is slow on your computer:
- Add extra `time.sleep()` calls after imports
- Increase delays before clicking buttons
- The recorder captures YOUR timing, but CapCut might be slower/faster later

### **Screen Resolution**
The recording uses ABSOLUTE coordinates (x=1234, y=567). This works if:
- ✅ You always use the same screen resolution
- ✅ CapCut window is in the same position
- ❌ Won't work if you change monitors or resolution

---

## 🐛 Troubleshooting

### "Module not found: pyautogui"
```bash
pip install pyautogui pynput
```

### "GUI doesn't open"
Make sure you're on Windows with a desktop environment (not WSL or SSH)

### "Playback doesn't work correctly"
- Record again, going slower
- Make sure CapCut is fully loaded before recording
- Add manual delays in the generated code

### "Clicks are in wrong position"
- Make sure CapCut window is maximized (same size as when you recorded)
- Or, record with CapCut in a specific window size

---

## 📝 Example Recorded Code

Your `capcut_automation.py` will look like:

```python
import pyautogui
import time

# Click at position
pyautogui.click(x=960, y=200)
time.sleep(2.5)

# Press Ctrl+I
pyautogui.keyDown('ctrl')
pyautogui.keyDown('i')
pyautogui.keyUp('i')
pyautogui.keyUp('ctrl')
time.sleep(1.0)

# Type file path
pyautogui.write('C:\\Users\\alexh\\video.mp4')
time.sleep(0.5)

# Press Enter
pyautogui.keyDown('enter')
pyautogui.keyUp('enter')
time.sleep(3.0)

# ... (continues for your entire workflow)
```

---

## ✅ Final Check

Before running your macro with recorded automation:

1. ✅ Recording plays back correctly in the recorder GUI
2. ✅ All file paths are made dynamic (not hardcoded)
3. ✅ Timing delays are appropriate for your system
4. ✅ CapCut window size/position is consistent
5. ✅ Export path points to correct location

---

## 🚀 Ready to Test!

Once you've:
1. Recorded your CapCut workflow
2. Saved it as `capcut_automation.py`
3. Integrated it into the macro
4. Made paths dynamic

Run your macro:
```bash
python ai_video_generation_macro.py
```

It will automatically replay your CapCut workflow when it reaches Step 8!
