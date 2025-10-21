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
import asyncio
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

# Import project knowledge loader
try:
    from project_loader import ProjectKnowledgeLoader
    PROJECT_LOADER_AVAILABLE = True
except ImportError:
    PROJECT_LOADER_AVAILABLE = False

# Optional imports for audio handling
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("Note: pydub not available, will use ffprobe for audio duration")

# Import edge-tts for voiceover generation
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("Note: edge-tts not available, will try browser automation")


class VideoGenerationMacro:
    """Main class for orchestrating the AI video generation pipeline."""

    def __init__(self, config_path: str = "config.json"):
        """Initialize the macro with configuration."""
        self.config = self.load_config(config_path)
        self.claude_client = anthropic.Anthropic(api_key=self.config['anthropic_api_key'])
        self.project_id = self.config['claude_project_id']
        self.voice_id = self.config.get('voice_id', '')
        # Use configured model or default to claude-3-sonnet-20240229 (most widely available)
        self.model = self.config.get('claude_model', 'claude-3-sonnet-20240229')

        # Load custom instructions from project (if provided)
        base_instructions = self.config.get('custom_instructions',
            "You are a video script writer. Follow your training and the writing style you've been taught in this project.")

        # Load project knowledge base from files
        project_files_dir = self.config.get('project_files_dir', './project_files')
        if PROJECT_LOADER_AVAILABLE:
            loader = ProjectKnowledgeLoader(project_files_dir)
            project_files = loader.get_file_list()

            if project_files:
                print(f"\n✓ Loading {len(project_files)} project file(s) from: {project_files_dir}")
                for f in project_files:
                    print(f"  - {f}")
                self.custom_instructions = loader.create_system_prompt(base_instructions)
                print(f"✓ Project knowledge loaded ({len(self.custom_instructions)} chars)")
            else:
                print(f"\n⚠ No project files found in: {project_files_dir}")
                print("  To use project files: create 'project_files' folder and add your reference files")
                self.custom_instructions = base_instructions
        else:
            self.custom_instructions = base_instructions

        print(f"\nUsing Claude model: {self.model}")
        print(f"Project ID: {self.project_id}")

        self.working_dir = Path("./output")
        self.working_dir.mkdir(exist_ok=True)

    def load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                print(f"\n✗ ERROR: Invalid JSON in {config_path}")
                print(f"   {e}")
                print("\nCommon issues:")
                print("1. Windows paths need FORWARD slashes or DOUBLE backslashes:")
                print("   ✓ Good: \"C:/Users/Name/path\"")
                print("   ✓ Good: \"C:\\\\Users\\\\Name\\\\path\"")
                print("   ✗ Bad:  \"C:\\Users\\Name\\path\"")
                print("\n2. Make sure all strings are in quotes")
                print("3. No trailing commas after last item")
                print(f"\nPlease fix {config_path} and try again.")
                sys.exit(1)
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

    def translate_to_korean_simple(self, text: str, label: str = "text") -> str:
        """Translate a short text to Korean with rate limit retry.

        NOTE: This method does NOT use project files to save tokens.
        Translation doesn't need the 83K+ chars of context.
        """
        print(f"\nTranslating {label} to Korean...")
        print("  (Using lightweight API call without project files)")

        max_retries = 5
        base_delay = 2

        for attempt in range(max_retries):
            try:
                message = self.claude_client.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    # NOTE: No system= parameter here = no project files sent
                    # This saves ~20,000 tokens per translation!
                    messages=[{
                        "role": "user",
                        "content": f"Translate the following {label} to Korean. Maintain the tone and style:\n\n{text}"
                    }]
                )

                translation = message.content[0].text.strip()
                print(f"Korean {label}: {translation}")
                return translation

            except Exception as e:
                if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    print(f"⚠ Rate limit hit. Waiting {delay} seconds before retry {attempt + 1}/{max_retries}...")
                    time.sleep(delay)
                else:
                    raise  # Re-raise if not a rate limit error or max retries exceeded

    def generate_title(self) -> tuple:
        """Generate a video title in English, get approval, then translate to Korean. Returns (english_title, korean_title)."""
        print("\n=== STEP 1: Generating Video Title (English) ===")

        english_title = None
        while True:
            print("\nGenerating English title...")

            try:
                message = self.claude_client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    system=self.custom_instructions,
                    messages=[{
                        "role": "user",
                        "content": "Generate a compelling video title in English in the style and topic you've been trained on in this project. Just provide the title, nothing else."
                    }]
                )
            except anthropic.NotFoundError as e:
                print(f"\n✗ ERROR: Model '{self.model}' not found or not accessible")
                print("\nYour API key doesn't have access to this model.")
                print("\nAvailable models you can try (add 'claude_model' to config.json):")
                print("  - claude-3-sonnet-20240229 (recommended)")
                print("  - claude-3-haiku-20240307 (fastest)")
                print("  - claude-3-opus-20240229 (most capable)")
                print("  - claude-3-5-sonnet-20241022 (latest)")
                print("\nTo check your API access, visit:")
                print("  https://console.anthropic.com/settings/keys")
                raise

            english_title = message.content[0].text.strip()
            print(f"\nGenerated English Title: {english_title}")

            response = input("\nOptions: [a]pprove, [t]weak, [d]eny (regenerate): ").lower()

            if response == 'a':
                print(f"✓ English title approved: {english_title}")
                break
            elif response == 't':
                tweak = input("Enter your tweaked English title: ")
                english_title = tweak
                print(f"✓ Using tweaked title: {english_title}")
                break
            elif response == 'd':
                print("Regenerating title...")
                continue
            else:
                print("Invalid input. Please try again.")

        # Translate to Korean
        korean_title = self.translate_to_korean_simple(english_title, "title")

        # Small delay to avoid rate limiting
        time.sleep(2)

        return english_title, korean_title

    def generate_description(self, english_title: str) -> tuple:
        """Generate video description based on description files. Returns (english_description, korean_description)."""
        print("\n=== STEP 2: Generating Video Description (English) ===")

        max_retries = 3
        for attempt in range(max_retries):
            try:
                message = self.claude_client.messages.create(
                    model=self.model,
                    max_tokens=800,
                    system=self.custom_instructions,
                    messages=[{
                        "role": "user",
                        "content": f"Based on the video title '{english_title}' and using the description format/style from the project files, write a compelling video description. This should be 2-4 sentences that will appear in the video description box on YouTube. Make it engaging and include a call-to-action if appropriate."
                    }]
                )
                break
            except Exception as e:
                if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                    delay = 5 * (2 ** attempt)
                    print(f"⚠ Rate limit hit. Waiting {delay} seconds before retry...")
                    time.sleep(delay)
                else:
                    raise

        english_description = message.content[0].text.strip()
        print(f"\nGenerated English Description:\n{english_description}")

        response = input("\nApprove this description? [y/n]: ").lower()

        if response != 'y':
            tweak = input("Enter your version (or press Enter to regenerate): ")
            if tweak:
                english_description = tweak
                print(f"✓ Using your description")
            else:
                return self.generate_description(english_title)  # Regenerate

        print(f"✓ Description approved")

        # Translate to Korean
        korean_description = self.translate_to_korean_simple(english_description, "description")

        # Small delay to avoid rate limiting
        time.sleep(2)

        return english_description, korean_description

    def generate_premise(self, english_title: str) -> tuple:
        """Generate a 2-3 sentence premise for the video. Returns (english_premise, korean_premise)."""
        print("\n=== STEP 3: Generating Video Premise (English) ===")

        message = self.claude_client.messages.create(
            model=self.model,
            max_tokens=500,
            system=self.custom_instructions,
            messages=[{
                "role": "user",
                "content": f"Write a 2-3 sentence premise for a video titled '{english_title}'. This explains what the video will cover and serves as a guide for the full script. Be specific about the key points that will be discussed."
            }]
        )

        english_premise = message.content[0].text.strip()
        print(f"\nGenerated English Premise:\n{english_premise}")

        response = input("\nApprove this premise? [y/n]: ").lower()

        if response != 'y':
            tweak = input("Enter your version (or press Enter to regenerate): ")
            if tweak:
                english_premise = tweak
                print(f"✓ Using your premise")
            else:
                return self.generate_premise(english_title)  # Regenerate

        print(f"✓ Premise approved")

        # Translate to Korean
        korean_premise = self.translate_to_korean_simple(english_premise, "premise")

        return english_premise, korean_premise

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
            model=self.model,
            max_tokens=4096,
            system=self.custom_instructions,
            messages=[{"role": "user", "content": prompt}]
        )

        return message.content[0].text.strip()

    def generate_full_script(self, english_title: str, english_premise: str) -> tuple:
        """Generate full video script in English, get approval, then translate to Korean. Returns (english_script, korean_script)."""
        print("\n=== STEP 4: Generating Full Video Script (English) ===")
        print("Target: 6000-7000 words")

        segments = []
        total_segments = 4  # Generate in 4 segments

        for i in range(1, total_segments + 1):
            print(f"\nGenerating segment {i}/{total_segments}...")

            previous = segments[-1] if segments else ""
            segment = self.generate_script_segment(english_title, english_premise, i, total_segments, previous)
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

Title: {english_title}
Premise: {english_premise}

Add more content to expand on the topic. Write approximately {6000 - total_words} more words to reach the target."""

            message = self.claude_client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.custom_instructions,
                messages=[{"role": "user", "content": additional_prompt}]
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

        print(f"\n✓ Final English script word count: {total_words} words")

        # Show preview and get approval
        print("\n" + "=" * 60)
        print("SCRIPT PREVIEW (first 500 characters):")
        print("=" * 60)
        print(full_script[:500] + "...")
        print("=" * 60)

        response = input("\nApprove this script? [y/n]: ").lower()

        if response != 'y':
            print("\n✗ Script not approved. Regenerating...")
            return self.generate_full_script(english_title, english_premise)

        print(f"✓ English script approved")

        # Save English script
        english_script_path = self.working_dir / "video_script_english.txt"
        with open(english_script_path, 'w', encoding='utf-8') as f:
            f.write(f"TITLE: {english_title}\n\n")
            f.write(f"PREMISE: {english_premise}\n\n")
            f.write(f"WORD COUNT: {total_words}\n\n")
            f.write("=" * 50 + "\n\n")
            f.write(full_script)

        print(f"✓ English script saved to: {english_script_path}")

        # Translate to Korean
        korean_script = self.translate_to_korean(full_script)

        return full_script, korean_script

    def translate_to_korean(self, script: str) -> str:
        """Translate the full English script to Korean.

        NOTE: This method does NOT use project files to save tokens.
        Each chunk translation is lightweight (~2000 words + small prompt).
        """
        print("\n=== Translating Full Script to Korean ===")
        print("This may take a few minutes...")
        print("  (Using lightweight API calls without project files)")

        # Split script into chunks for translation (API token limits)
        chunks = []
        words = script.split()
        chunk_size = 2000

        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)

        translated_chunks = []
        max_retries = 3

        for i, chunk in enumerate(chunks, 1):
            print(f"Translating chunk {i}/{len(chunks)}...")

            # Retry logic for each chunk
            for attempt in range(max_retries):
                try:
                    message = self.claude_client.messages.create(
                        model=self.model,
                        max_tokens=4096,
                        # NOTE: No system= parameter = no project files sent!
                        messages=[{
                            "role": "user",
                            "content": f"Translate the following text to Korean. Maintain the tone and style:\n\n{chunk}"
                        }]
                    )

                    translated = message.content[0].text.strip()
                    translated_chunks.append(translated)
                    break  # Success, exit retry loop

                except Exception as e:
                    if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                        delay = 5 * (2 ** attempt)
                        print(f"  ⚠ Rate limit hit. Waiting {delay} seconds before retry...")
                        time.sleep(delay)
                    else:
                        raise

            # Small delay between chunks to avoid rate limiting
            time.sleep(2)

        korean_script = "\n\n".join(translated_chunks)

        # Save Korean script
        korean_path = self.working_dir / "video_script_korean.txt"
        with open(korean_path, 'w', encoding='utf-8') as f:
            f.write(korean_script)

        print(f"✓ Korean script saved to: {korean_path}")
        return korean_script

    async def _generate_voiceover_edge_tts(self, korean_script: str, output_path: str, voice: str = "ko-KR-SunHiNeural"):
        """Internal async function to generate voiceover using edge-tts."""
        communicate = edge_tts.Communicate(korean_script, voice)
        await communicate.save(output_path)

    def generate_voiceover(self, korean_script: str) -> str:
        """Generate voiceover using Microsoft Edge TTS (FREE, no API key needed)."""
        print("\n=== STEP 5: Generating Voiceover ===")

        # Check if manual voiceover already exists
        voiceover_path = self.working_dir / "voiceover.mp3"
        if voiceover_path.exists():
            print(f"✓ Found existing voiceover at: {voiceover_path}")
            use_existing = input("Use this existing voiceover? [y/n]: ").lower()
            if use_existing == 'y':
                return str(voiceover_path)

        if not EDGE_TTS_AVAILABLE:
            print("\n✗ edge-tts not installed!")
            print("Installing edge-tts...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "edge-tts", "--user"])
                print("✓ edge-tts installed! Please run the script again.")
                sys.exit(0)
            except:
                print("✗ Failed to install edge-tts")
                print("\nPlease install manually:")
                print("  pip install edge-tts")
                sys.exit(1)

        # Get voice from config, or use default Korean voice
        voice_name = self.config.get('tts_voice', 'ko-KR-SunHiNeural')

        print(f"\nGenerating voiceover with Microsoft Edge TTS...")
        print(f"Voice: {voice_name}")
        print(f"Script length: {len(korean_script)} characters")
        print("\nThis may take a few minutes depending on script length...")

        try:
            # Run async function
            asyncio.run(self._generate_voiceover_edge_tts(
                korean_script,
                str(voiceover_path),
                voice_name
            ))

            if voiceover_path.exists():
                file_size = voiceover_path.stat().st_size / (1024 * 1024)  # MB
                print(f"\n✓ Voiceover generated successfully!")
                print(f"  File: {voiceover_path}")
                print(f"  Size: {file_size:.2f} MB")
                return str(voiceover_path)
            else:
                raise Exception("Voiceover file was not created")

        except Exception as e:
            print(f"\n✗ Voiceover generation failed: {e}")
            print("\nTroubleshooting:")
            print("1. Check your internet connection (edge-tts needs to connect to Microsoft servers)")
            print("2. Try a different voice in config.json:")
            print("   'tts_voice': 'ko-KR-InJoonNeural' (Male)")
            print("   'tts_voice': 'ko-KR-SunHiNeural' (Female, default)")
            print("\n3. To see all available voices, run:")
            print("   edge-tts --list-voices | grep ko-KR")

            choice = input("\nOptions:\n  [r] Retry\n  [s] Skip voiceover\n  [q] Quit\nChoice: ").lower()

            if choice == 'r':
                return self.generate_voiceover(korean_script)  # Retry
            elif choice == 's':
                print("Skipping voiceover...")
                return None
            else:
                print("Exiting...")
                sys.exit(0)

    def generate_subtitles(self, korean_script: str) -> str:
        """Generate SRT subtitles from Korean script."""
        print("\n=== Generating Subtitles (SRT format) ===")

        subtitle_path = self.working_dir / "subtitles.srt"

        print("Creating subtitle file with timed segments...")

        # Split script into sentences
        sentences = korean_script.replace('! ', '!\n').replace('? ', '?\n').replace('. ', '.\n').split('\n')
        sentences = [s.strip() for s in sentences if s.strip()]

        # Estimate timing (average speaking rate: ~2.5 seconds per sentence)
        srt_content = ""
        current_time = 0.0
        duration_per_sentence = 2.5

        for i, sentence in enumerate(sentences, 1):
            start_time = current_time
            end_time = current_time + duration_per_sentence

            # Format timestamps
            start_ts = self._format_srt_timestamp(start_time)
            end_ts = self._format_srt_timestamp(end_time)

            # Add subtitle entry
            srt_content += f"{i}\n"
            srt_content += f"{start_ts} --> {end_ts}\n"
            srt_content += f"{sentence}\n\n"

            current_time = end_time

        # Save SRT file
        with open(subtitle_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)

        print(f"✓ Subtitles saved to: {subtitle_path}")
        print(f"  Total subtitle entries: {len(sentences)}")
        print(f"  Estimated duration: {current_time:.1f} seconds")

        return str(subtitle_path)

    def _format_srt_timestamp(self, seconds: float) -> str:
        """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

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
            model=self.model,
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

    def edit_video_capcut(self, voiceover_path: Optional[str], image_paths: List[str], subtitle_path: str) -> str:
        """Edit video using CapCut (automation via PyAutoGUI)."""
        print("\n=== STEP 8: Editing Video in CapCut ===")
        print("Note: This requires CapCut to be installed and this will automate the GUI.")
        print("Please ensure CapCut is closed before continuing.")
        input("Press Enter when ready to start CapCut automation...")

        # Get audio duration
        if voiceover_path:
            audio_duration = self.get_audio_duration(voiceover_path)
            print(f"Voiceover duration: {audio_duration:.2f} seconds")
        else:
            audio_duration = 300  # Default 5 minutes if no voiceover
            print("No voiceover - using default 5 minute duration")

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

        if voiceover_path:
            print(f"6. Import voiceover: {voiceover_path}")
            print("7. Add voiceover to audio track")
            print(f"8. Import subtitles: {subtitle_path}")
            print("9. Add subtitles to the video (CapCut: Text -> Auto Captions or manually import SRT)")
            print("10. Export as MP4")
        else:
            print("6. (No voiceover - skip audio track)")
            print(f"7. Import subtitles: {subtitle_path}")
            print("8. Add subtitles to the video")
            print("9. Export as MP4")

        export_path = self.working_dir / "final_video.mp4"
        print(f"\n{'10' if voiceover_path else '9'}. Save exported video to: {export_path}")

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
            # Step 1: Generate and approve title (English → Korean)
            english_title, korean_title = self.generate_title()

            # Step 2: Generate and approve description (English → Korean)
            english_description, korean_description = self.generate_description(english_title)

            # Step 3: Generate and approve premise (English → Korean)
            english_premise, korean_premise = self.generate_premise(english_title)

            # Step 4: Generate and approve full script (English → Korean)
            english_script, korean_script = self.generate_full_script(english_title, english_premise)

            # Step 5: Generate voiceover from Korean script
            voiceover_path = self.generate_voiceover(korean_script)

            # Step 6: Generate subtitles from Korean script
            subtitle_path = self.generate_subtitles(korean_script)

            # Step 7: Generate images
            image_paths = self.generate_images(english_title, english_premise)

            # Step 8: Edit video in CapCut
            video_path = self.edit_video_capcut(voiceover_path, image_paths, subtitle_path)

            # Step 9: Create thumbnail in Canva
            thumbnail_path = self.create_thumbnail_canva(english_title)

            print("\n" + "=" * 60)
            print("✓ VIDEO GENERATION COMPLETE!")
            print("=" * 60)
            print(f"\nEnglish Title: {english_title}")
            print(f"Korean Title: {korean_title}")
            print(f"Description: {english_description}")
            print(f"Video: {video_path}")
            print(f"Thumbnail: {thumbnail_path}")
            print(f"Subtitles: {subtitle_path}")
            print(f"\nAll files are in: {self.working_dir}")

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
