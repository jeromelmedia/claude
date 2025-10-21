#!/usr/bin/env python3
"""
AI Video Generation Macro
A comprehensive automation script for generating videos with AI-generated content,
voiceovers, and thumbnails.
"""

import os
import sys
import time
import json
import requests
import subprocess
from pathlib import Path
from typing import Optional, List, Dict
import anthropic
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import pyautogui

# Optional imports for audio handling
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("Note: pydub not available, will use ffprobe for audio duration")


class VideoGenerationMacro:
    """Main class for orchestrating the AI video generation pipeline."""

    def __init__(self, config_path: str = "config.json"):
        """Initialize the macro with configuration."""
        self.config = self.load_config(config_path)
        self.claude_client = anthropic.Anthropic(api_key=self.config['anthropic_api_key'])
        self.project_id = self.config['claude_project_id']
        self.voice_id = self.config['voice_id']
        self.working_dir = Path("./output")
        self.working_dir.mkdir(exist_ok=True)

    def load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Create default config template
            default_config = {
                "anthropic_api_key": "your-api-key-here",
                "claude_project_id": "your-project-id-here",
                "voice_id": "your-voice-id-here",
                "genaipro_api_key": "",
                "video_clip_path": "./talking_person.mp4",
                "chrome_profile_path": ""
            }
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"Created default config at {config_path}. Please fill in your details.")
            sys.exit(1)

    def generate_title(self) -> str:
        """Generate a video title using Claude with approval loop."""
        print("\n=== STEP 1: Generating Video Title ===")

        while True:
            print("\nGenerating title...")

            message = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": "Generate a compelling video title based on your training. Just provide the title, nothing else."
                }],
                metadata={"user_id": self.project_id}
            )

            title = message.content[0].text.strip()
            print(f"\nGenerated Title: {title}")

            response = input("\nOptions: [a]pprove, [t]weak, [d]eny (regenerate): ").lower()

            if response == 'a':
                print(f"✓ Title approved: {title}")
                return title
            elif response == 't':
                tweak = input("Enter your tweaked version: ")
                print(f"✓ Using tweaked title: {tweak}")
                return tweak
            elif response == 'd':
                print("Regenerating title...")
                continue
            else:
                print("Invalid input. Please try again.")

    def generate_premise(self, title: str) -> str:
        """Generate a 2-3 sentence premise for the video."""
        print("\n=== STEP 2: Generating Video Premise ===")

        message = self.claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"Write a 2-3 sentence premise/description for a video titled '{title}'. This should explain what the video is about."
            }],
            metadata={"user_id": self.project_id}
        )

        premise = message.content[0].text.strip()
        print(f"\nPremise: {premise}")
        return premise

    def count_words(self, text: str) -> int:
        """Count words in text."""
        return len(text.split())

    def generate_script_segment(self, title: str, premise: str, segment_num: int,
                                 total_segments: int, previous_content: str = "") -> str:
        """Generate a segment of the video script."""
        target_words_per_segment = 7000 // total_segments + 200  # Buffer

        prompt = f"""You are writing segment {segment_num} of {total_segments} for a video script.

Title: {title}
Premise: {premise}

Target words for this segment: approximately {target_words_per_segment} words.

"""
        if previous_content:
            prompt += f"Previous content summary: {previous_content[:500]}...\n\n"

        if segment_num == 1:
            prompt += "Write the opening segment of the script. Start with a hook and introduction."
        elif segment_num == total_segments:
            prompt += "Write the final segment of the script. Include conclusion and call-to-action."
        else:
            prompt += f"Write segment {segment_num}, continuing the narrative naturally."

        prompt += f"\n\nWrite approximately {target_words_per_segment} words in your trained writing style."

        message = self.claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            metadata={"user_id": self.project_id}
        )

        return message.content[0].text.strip()

    def generate_full_script(self, title: str, premise: str) -> str:
        """Generate full video script in segments, ensuring 6000-7000 words."""
        print("\n=== STEP 3: Generating Full Video Script ===")
        print("Target: 6000-7000 words")

        segments = []
        total_segments = 4  # Generate in 4 segments

        for i in range(1, total_segments + 1):
            print(f"\nGenerating segment {i}/{total_segments}...")

            previous = segments[-1] if segments else ""
            segment = self.generate_script_segment(title, premise, i, total_segments, previous)
            segments.append(segment)

            word_count = self.count_words(segment)
            print(f"Segment {i} word count: {word_count}")

        # Combine all segments
        full_script = "\n\n".join(segments)
        total_words = self.count_words(full_script)
        print(f"\nInitial total word count: {total_words}")

        # If under 6000 words, generate additional content
        while total_words < 6000:
            print(f"\nWord count ({total_words}) is below target. Generating additional content...")

            additional_prompt = f"""The current script has {total_words} words but needs to be 6000-7000 words.

Title: {title}
Premise: {premise}

Add more content to expand on the topic. Write approximately {6000 - total_words} more words to reach the target."""

            message = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[{"role": "user", "content": additional_prompt}],
                metadata={"user_id": self.project_id}
            )

            additional_content = message.content[0].text.strip()
            full_script += "\n\n" + additional_content
            total_words = self.count_words(full_script)
            print(f"Updated word count: {total_words}")

        # If over 7000 words, trim
        if total_words > 7000:
            print(f"\nWord count ({total_words}) exceeds target. Trimming to ~7000 words...")
            words = full_script.split()
            full_script = " ".join(words[:7000])
            total_words = 7000

        print(f"\n✓ Final script word count: {total_words} words")

        # Save script
        script_path = self.working_dir / "video_script.txt"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(f"TITLE: {title}\n\n")
            f.write(f"PREMISE: {premise}\n\n")
            f.write(f"WORD COUNT: {total_words}\n\n")
            f.write("=" * 50 + "\n\n")
            f.write(full_script)

        print(f"✓ Script saved to: {script_path}")
        return full_script

    def translate_to_korean(self, script: str) -> str:
        """Translate the script to Korean."""
        print("\n=== STEP 4: Translating Script to Korean ===")

        # Split script into chunks for translation (API token limits)
        chunks = []
        words = script.split()
        chunk_size = 2000

        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)

        translated_chunks = []

        for i, chunk in enumerate(chunks, 1):
            print(f"Translating chunk {i}/{len(chunks)}...")

            message = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": f"Translate the following text to Korean. Maintain the tone and style:\n\n{chunk}"
                }]
            )

            translated = message.content[0].text.strip()
            translated_chunks.append(translated)
            time.sleep(1)  # Rate limiting

        korean_script = "\n\n".join(translated_chunks)

        # Save Korean script
        korean_path = self.working_dir / "video_script_korean.txt"
        with open(korean_path, 'w', encoding='utf-8') as f:
            f.write(korean_script)

        print(f"✓ Korean script saved to: {korean_path}")
        return korean_script

    def generate_voiceover(self, korean_script: str) -> str:
        """Generate voiceover using genaipro.vn."""
        print("\n=== STEP 5: Generating Voiceover ===")

        # Setup Chrome driver
        chrome_options = Options()
        if self.config.get('chrome_profile_path'):
            chrome_options.add_argument(f"user-data-dir={self.config['chrome_profile_path']}")

        driver = webdriver.Chrome(options=chrome_options)

        try:
            # Navigate to genaipro.vn
            driver.get("https://genaipro.vn")
            time.sleep(3)

            # Find text input and paste script
            print("Entering script into voiceover generator...")
            text_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea, [contenteditable='true']"))
            )
            text_input.clear()
            text_input.send_keys(korean_script)

            # Select voice
            print(f"Selecting voice ID: {self.voice_id}")
            # This will need to be customized based on the actual website structure
            voice_selector = driver.find_element(By.ID, "voice-selector")  # Adjust selector
            voice_selector.click()
            time.sleep(1)

            voice_option = driver.find_element(By.XPATH, f"//option[@value='{self.voice_id}']")
            voice_option.click()

            # Generate voiceover
            print("Generating voiceover...")
            generate_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Generate') or contains(text(), 'Tạo')]")
            generate_button.click()

            # Wait for generation to complete
            print("Waiting for voiceover generation to complete...")
            time.sleep(30)  # Adjust based on typical generation time

            # Download voiceover
            print("Downloading voiceover...")
            download_button = WebDriverWait(driver, 120).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Download') or contains(text(), 'Tải')]"))
            )
            download_button.click()

            time.sleep(10)  # Wait for download

            # Find the downloaded file (assumes it goes to default downloads folder)
            downloads_path = Path.home() / "Downloads"
            voiceover_files = sorted(downloads_path.glob("*.mp3"), key=lambda x: x.stat().st_mtime, reverse=True)

            if voiceover_files:
                latest_voiceover = voiceover_files[0]
                voiceover_path = self.working_dir / "voiceover.mp3"
                latest_voiceover.rename(voiceover_path)
                print(f"✓ Voiceover saved to: {voiceover_path}")
                return str(voiceover_path)
            else:
                raise Exception("Could not find downloaded voiceover file")

        finally:
            driver.quit()

    def get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds."""
        # Try using pydub first (if available and working)
        if PYDUB_AVAILABLE:
            try:
                audio = AudioSegment.from_mp3(audio_path)
                return len(audio) / 1000.0  # Convert milliseconds to seconds
            except Exception as e:
                print(f"pydub failed: {e}, trying ffprobe...")

        # Fall back to ffprobe
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(audio_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
            return duration
        except subprocess.CalledProcessError:
            print("Warning: Could not get audio duration. Using default 300 seconds (5 minutes)")
            return 300.0  # Default fallback
        except FileNotFoundError:
            print("Warning: ffprobe not found. Please install FFmpeg.")
            print("Using default duration of 300 seconds (5 minutes)")
            return 300.0

    def generate_images(self, title: str, premise: str, num_images: int = 4) -> List[str]:
        """Generate images using pollinations.ai."""
        print(f"\n=== STEP 6: Generating {num_images} Images ===")

        # Generate prompt for the person in the images
        message = self.claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": f"Based on this video title '{title}' and premise '{premise}', describe the person who is presenting this video in 1-2 sentences. Focus on their appearance and setting."
            }]
        )

        person_description = message.content[0].text.strip()
        print(f"Person description: {person_description}")

        image_paths = []

        for i in range(num_images):
            print(f"\nGenerating image {i+1}/{num_images}...")

            # Create varied prompts for each image
            prompt = f"{person_description}, professional portrait, high quality, variation {i+1}"

            # Use pollinations.ai API
            image_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"

            print(f"Downloading image from: {image_url}")
            response = requests.get(image_url, timeout=60)

            if response.status_code == 200:
                image_path = self.working_dir / f"person_image_{i+1}.jpg"
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                image_paths.append(str(image_path))
                print(f"✓ Image {i+1} saved to: {image_path}")
            else:
                print(f"✗ Failed to download image {i+1}")

            time.sleep(2)  # Rate limiting

        return image_paths

    def edit_video_capcut(self, voiceover_path: str, image_paths: List[str]) -> str:
        """Edit video using CapCut (automation via PyAutoGUI)."""
        print("\n=== STEP 7: Editing Video in CapCut ===")
        print("Note: This requires CapCut to be installed and this will automate the GUI.")
        print("Please ensure CapCut is closed before continuing.")
        input("Press Enter when ready to start CapCut automation...")

        # Get audio duration
        audio_duration = self.get_audio_duration(voiceover_path)
        print(f"Voiceover duration: {audio_duration:.2f} seconds")

        # Launch CapCut
        print("Launching CapCut...")
        if sys.platform == "darwin":  # macOS
            os.system("open -a CapCut")
        elif sys.platform == "win32":  # Windows
            os.system("start CapCut")
        else:  # Linux
            print("Please launch CapCut manually and press Enter when ready...")
            input()

        time.sleep(5)

        # Click "New Project"
        print("Creating new project...")
        # These coordinates will need to be adjusted based on screen resolution
        # This is a template - user will need to adjust
        pyautogui.click(960, 540)  # Center of screen - adjust as needed
        time.sleep(2)

        # Import talking person video clip
        video_clip_path = self.config['video_clip_path']
        print(f"Importing video clip: {video_clip_path}")
        # Drag and drop or use import button
        # This needs to be customized based on CapCut's interface

        print("\n⚠ CAPCUT AUTOMATION LIMITATION ⚠")
        print("Automated GUI control for CapCut is complex and screen-resolution dependent.")
        print("Please complete the following steps manually in CapCut:")
        print(f"\n1. Import the talking person video: {video_clip_path}")
        print("2. Drag it to the timeline")
        print("3. Loop it for 1.5 minutes (90 seconds)")
        print(f"4. At 1.5 min mark, add images from: {self.working_dir}")
        print(f"5. Display each image for {(audio_duration - 90) / len(image_paths):.1f} seconds")
        print(f"6. Import voiceover: {voiceover_path}")
        print("7. Add voiceover to audio track")
        print("8. Export as MP4")

        export_path = self.working_dir / "final_video.mp4"
        print(f"\n9. Save exported video to: {export_path}")

        input("\nPress Enter when you've completed the video editing and export...")

        if not export_path.exists():
            manual_path = input(f"Could not find {export_path}. Enter the full path to your exported video: ")
            export_path = Path(manual_path)

        print(f"✓ Video exported to: {export_path}")
        return str(export_path)

    def create_thumbnail_canva(self, title: str) -> str:
        """Create thumbnail using Canva."""
        print("\n=== STEP 8: Creating Thumbnail in Canva ===")

        # Setup Chrome driver
        chrome_options = Options()
        if self.config.get('chrome_profile_path'):
            chrome_options.add_argument(f"user-data-dir={self.config['chrome_profile_path']}")

        driver = webdriver.Chrome(options=chrome_options)

        try:
            # Navigate to Canva
            driver.get("https://www.canva.com")
            time.sleep(3)

            # Search for YouTube thumbnail template
            print("Searching for YouTube thumbnail template...")
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Search']"))
            )
            search_box.send_keys("YouTube thumbnail")
            search_box.send_keys(Keys.RETURN)
            time.sleep(3)

            # Select first template
            print("Selecting thumbnail template...")
            first_template = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-test='template-card']"))
            )
            first_template.click()
            time.sleep(5)

            print("\n⚠ CANVA AUTOMATION LIMITATION ⚠")
            print("Automated thumbnail creation in Canva requires manual steps.")
            print(f"\nPlease customize the thumbnail with the title: {title}")
            print("Then download it.")

            thumbnail_path = self.working_dir / "thumbnail.png"
            print(f"\nSave the thumbnail to: {thumbnail_path}")

            input("\nPress Enter when you've downloaded the thumbnail...")

            if not thumbnail_path.exists():
                manual_path = input(f"Could not find {thumbnail_path}. Enter the full path to your thumbnail: ")
                thumbnail_path = Path(manual_path)

            print(f"✓ Thumbnail saved to: {thumbnail_path}")
            return str(thumbnail_path)

        finally:
            driver.quit()

    def run(self):
        """Run the complete video generation pipeline."""
        print("=" * 60)
        print("AI VIDEO GENERATION MACRO")
        print("=" * 60)

        try:
            # Step 1: Generate and approve title
            title = self.generate_title()

            # Step 2: Generate premise
            premise = self.generate_premise(title)

            # Step 3: Generate full script
            script = self.generate_full_script(title, premise)

            # Step 4: Translate to Korean
            korean_script = self.translate_to_korean(script)

            # Step 5: Generate voiceover
            voiceover_path = self.generate_voiceover(korean_script)

            # Step 6: Generate images
            image_paths = self.generate_images(title, premise)

            # Step 7: Edit video in CapCut
            video_path = self.edit_video_capcut(voiceover_path, image_paths)

            # Step 8: Create thumbnail in Canva
            thumbnail_path = self.create_thumbnail_canva(title)

            print("\n" + "=" * 60)
            print("✓ VIDEO GENERATION COMPLETE!")
            print("=" * 60)
            print(f"\nTitle: {title}")
            print(f"Video: {video_path}")
            print(f"Thumbnail: {thumbnail_path}")
            print(f"All files are in: {self.working_dir}")

        except Exception as e:
            print(f"\n✗ Error occurred: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Main entry point."""
    macro = VideoGenerationMacro()
    macro.run()


if __name__ == "__main__":
    main()
