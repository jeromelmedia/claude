# Quick Start Guide

## Super Simple Setup (Recommended)

### 1. Configure API Keys (First Time Only)

Copy `config.example.json` to `config.json` and edit it:
```json
{
  "anthropic_api_key": "sk-ant-xxxxx",
  "claude_project_id": "your-project-id",
  "voice_id": "your-voice-id",
  "video_clip_path": "./talking_person.mp4"
}
```

**Where to get these:**

- **Anthropic API Key**: https://console.anthropic.com/settings/keys
- **Claude Project ID**: https://console.anthropic.com/projects
  - Create a new project
  - Train it with sample scripts in your desired writing style
  - Copy the project ID
- **Voice ID**: https://genaipro.vn
  - Sign up and browse available voices
  - Copy the voice ID you want to use
- **Video Clip**: Record or download a video of someone talking (MP4 format)

### 2. Install Additional Software

- **CapCut**: https://www.capcut.com/
- **FFmpeg**:
  - macOS: `brew install ffmpeg`
  - Ubuntu: `sudo apt-get install ffmpeg`
  - Windows: https://ffmpeg.org/download.html

### 3. Add Your Talking Person Video

Place your pre-recorded talking person video as `talking_person.mp4` in the same folder.

## Running the Macro

**NO VIRTUAL ENVIRONMENT NEEDED! Just run:**

**Windows:**
- Double-click `RUN_ME.bat`

**OR from command line:**
```bash
python run_video_macro.py
```

**Linux/macOS:**
```bash
./run_me.sh
```

**OR:**
```bash
python3 run_video_macro.py
```

The launcher will **automatically**:
- Check for required packages
- Install missing packages
- Run the video generation macro

**That's it!** No pip install, no venv activate, nothing.

## Workflow Steps

The macro will guide you through 8 steps:

1. **Title Generation** - Approve, tweak, or regenerate (a/t/d)
2. **Premise Generation** - Automatic
3. **Script Writing** - 6000-7000 words, generated in segments
4. **Korean Translation** - Automatic
5. **Voiceover** - Browser automation (some manual steps)
6. **Image Generation** - Automatic (3-5 images)
7. **Video Editing** - Manual steps in CapCut
8. **Thumbnail** - Manual steps in Canva

## Expected Time

- **Automated steps**: ~15-20 minutes
- **Manual steps** (CapCut + Canva): ~15-20 minutes
- **Total**: ~30-40 minutes per video

## Output Location

All files are saved to `output/`:
- `video_script.txt` - Original script
- `video_script_korean.txt` - Korean translation
- `voiceover.mp3` - Generated voice
- `person_image_*.jpg` - Generated images
- `final_video.mp4` - Finished video
- `thumbnail.png` - Video thumbnail

## Troubleshooting

### "No config.json found"
Run `setup.sh` or copy `config.example.json` to `config.json`

### "ChromeDriver error"
Install or update ChromeDriver:
```bash
pip install webdriver-manager
```

### "FFmpeg not found"
Install FFmpeg (see setup instructions above)

### "Cannot find voiceover file"
Check your Downloads folder and manually move it to `output/voiceover.mp3`

## Tips

- **Train your Claude project well** - Add sample scripts to get better results
- **Test voice ID first** - Try genaipro.vn manually before running the macro
- **Prepare video clip** - Have a high-quality talking person clip ready
- **Clear browser cache** - If automation fails, clear Chrome cache and try again

## Cost per Video

- Anthropic API: ~$0.50-$2.00
- genaipro.vn: Varies by plan
- pollinations.ai: Free
- Total: ~$1-5 per video

## Support

For detailed documentation, see `README.md`

For issues, check:
1. All API keys are correct in `config.json`
2. All dependencies are installed
3. File paths are correct
4. Services (genaipro.vn, Canva) are accessible
