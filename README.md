# AI Video Generation Macro

A comprehensive Python automation script for generating educational/informational videos with AI-generated content, Korean voiceovers, and thumbnails.

## Features

- **AI-Powered Content Generation**: Uses Claude AI to generate video titles, premises, and full scripts (6000-7000 words)
- **Interactive Approval Loop**: Review and approve/tweak/regenerate titles before proceeding
- **Segmented Script Generation**: Ensures accurate word count targets by generating scripts in segments
- **Korean Translation**: Automatically translates scripts to Korean
- **Voiceover Generation**: Integrates with genaipro.vn for AI voice generation
- **Image Generation**: Creates presenter images using pollinations.ai
- **Video Editing**: Automates video assembly in CapCut
- **Thumbnail Creation**: Generates YouTube thumbnails in Canva

## Prerequisites

### Software Requirements

1. **Python 3.8+**
2. **Google Chrome** (for web automation)
3. **ChromeDriver** (compatible with your Chrome version)
4. **CapCut** (desktop application)
5. **FFmpeg** (for audio processing)

### API Keys & Accounts

- **Anthropic API Key**: Get from https://console.anthropic.com/
- **Claude Project ID**: Create and train a Claude project with your desired writing style
- **genaipro.vn Account**: Sign up at https://genaipro.vn and get voice ID
- **Canva Account**: Sign up at https://canva.com

## Installation

### 1. Clone or Download

```bash
cd /path/to/your/workspace
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install System Dependencies

#### macOS
```bash
brew install ffmpeg
brew install chromedriver
```

#### Ubuntu/Linux
```bash
sudo apt-get update
sudo apt-get install ffmpeg
sudo apt-get install chromium-chromedriver
```

#### Windows
- Download FFmpeg from https://ffmpeg.org/download.html
- Download ChromeDriver from https://chromedriver.chromium.org/
- Add both to your system PATH

### 4. Configure the Script

Run the script once to generate the configuration template:

```bash
python ai_video_generation_macro.py
```

This will create `config.json`. Edit it with your details:

```json
{
  "anthropic_api_key": "sk-ant-xxxxx",
  "claude_project_id": "your-project-id",
  "voice_id": "your-genaipro-voice-id",
  "genaipro_api_key": "",
  "video_clip_path": "./talking_person.mp4",
  "chrome_profile_path": ""
}
```

#### Configuration Fields:

- **anthropic_api_key**: Your Anthropic API key
- **claude_project_id**: Your trained Claude project ID
- **voice_id**: The voice ID from genaipro.vn you want to use
- **video_clip_path**: Path to your pre-recorded talking person video clip
- **chrome_profile_path**: (Optional) Chrome profile path to maintain login sessions

### 5. Prepare Your Talking Person Video

Create or obtain a video clip of a person talking on screen. Save it as `talking_person.mp4` in the same directory as the script, or update the path in `config.json`.

## Usage

### Basic Usage

Run the macro:

```bash
python ai_video_generation_macro.py
```

### Workflow

The script will guide you through each step:

1. **Title Generation**
   - Claude generates a video title
   - You can approve, tweak, or regenerate
   - Options: `a` (approve), `t` (tweak), `d` (deny/regenerate)

2. **Premise Generation**
   - Automatically generates 2-3 sentence video description

3. **Script Generation**
   - Generates script in segments
   - Automatically ensures 6000-7000 word count
   - Saves to `output/video_script.txt`

4. **Korean Translation**
   - Translates entire script to Korean
   - Saves to `output/video_script_korean.txt`

5. **Voiceover Generation**
   - Opens genaipro.vn in browser
   - Automates voiceover generation with your chosen voice
   - Downloads as `output/voiceover.mp3`

6. **Image Generation**
   - Generates 3-5 images using pollinations.ai
   - Saves to `output/person_image_1.jpg`, etc.

7. **Video Editing (CapCut)**
   - Provides manual instructions for CapCut editing
   - You'll need to complete some steps manually:
     - Loop talking video for 1.5 minutes
     - Add images for remaining duration
     - Add voiceover track
     - Export as MP4

8. **Thumbnail Creation (Canva)**
   - Opens Canva in browser
   - Guides you to create thumbnail
   - Save as `output/thumbnail.png`

### Output Files

All generated files are saved to the `output/` directory:

```
output/
├── video_script.txt          # Original English script
├── video_script_korean.txt   # Korean translation
├── voiceover.mp3             # Generated voiceover
├── person_image_1.jpg        # Generated images
├── person_image_2.jpg
├── person_image_3.jpg
├── person_image_4.jpg
├── final_video.mp4           # Exported video
└── thumbnail.png             # Video thumbnail
```

## Customization

### Adjusting Word Count

Edit the `generate_full_script()` method to change target word count:

```python
# In ai_video_generation_macro.py, line ~143
while total_words < 6000:  # Change minimum
    ...

if total_words > 7000:  # Change maximum
    ...
```

### Changing Number of Images

Modify the `generate_images()` call in `run()`:

```python
# Default is 4 images
image_paths = self.generate_images(title, premise, num_images=5)  # Change to 5
```

### Custom Chrome Profile

To maintain login sessions for genaipro.vn and Canva, set your Chrome profile path:

```json
{
  "chrome_profile_path": "/Users/yourname/Library/Application Support/Google/Chrome/Default"
}
```

## Troubleshooting

### ChromeDriver Issues

If you get ChromeDriver errors:

```bash
# Install webdriver-manager
pip install webdriver-manager

# Update the script to use it
from webdriver_manager.chrome import ChromeDriverManager
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
```

### Audio File Issues

If voiceover download fails:
- Check your Downloads folder manually
- Move the file to `output/voiceover.mp3`
- The script will continue

### CapCut Automation Limitations

CapCut automation is limited due to its GUI-based nature. The script provides detailed manual instructions. For full automation, consider:
- Using a video editing API/library like MoviePy
- Creating custom automation with computer vision

### Rate Limiting

If you encounter API rate limits:
- Add delays between API calls
- Consider using Claude's batch API for script generation
- Check your API usage quotas

## Advanced Configuration

### Using Claude Projects

To get the best results, train a Claude project with:
1. Sample video scripts in your desired style
2. Examples of your preferred tone and structure
3. Any domain-specific knowledge

Then use that project ID in `config.json`.

### Batch Processing

To generate multiple videos, create a wrapper script:

```python
titles = ["Title 1", "Title 2", "Title 3"]

for title in titles:
    macro = VideoGenerationMacro()
    # Override title generation
    # ... run pipeline
```

## Cost Estimates

Approximate costs per video:

- **Anthropic API**: $0.50 - $2.00 (depending on usage)
- **genaipro.vn**: Varies by plan
- **pollinations.ai**: Free
- **Total**: ~$1-5 per video

## License

This script is provided as-is for educational and personal use.

## Support

For issues:
1. Check the troubleshooting section
2. Verify all API keys and accounts are configured
3. Ensure all dependencies are installed
4. Check that file paths are correct

## Disclaimer

This automation script interacts with third-party services. Always review and comply with the terms of service for:
- Anthropic
- genaipro.vn
- pollinations.ai
- Canva
- CapCut

Automated usage may be subject to rate limits or restrictions.
