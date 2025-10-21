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
import random
import glob
from pathlib import Path
from typing import Optional, List, Dict, Tuple
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

    def generate_title(self) -> str:
        """Generate a video title in English and get approval. Returns english_title."""
        print("\n=== STEP 1: Generating Video Title (English) ===")

        english_title = None
        while True:
            print("\nGenerating English title...")

            max_retries = 3
            for attempt in range(max_retries):
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
                    break  # Success, exit retry loop
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
                except Exception as e:
                    if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                        delay = 10 * (2 ** attempt)  # 10s, 20s, 40s
                        print(f"⚠ Rate limit hit. Waiting {delay} seconds before retry {attempt + 1}/{max_retries}...")
                        time.sleep(delay)
                    else:
                        raise

            english_title = message.content[0].text.strip()
            print(f"\nGenerated English Title: {english_title}")
            print(f"✓ Auto-approved (running in full automation mode)")
            break

        # Delay after heavy API call to avoid rate limiting
        # With 50K tokens/min limit and ~20K per call, we need 60+ seconds between calls
        print("⏱ Waiting 65 seconds to avoid rate limit (this is necessary with your API limits)...")
        time.sleep(65)

        return english_title

    def generate_description(self, english_title: str) -> str:
        """Generate video description based on description files. Returns english_description."""
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
                    delay = 10 * (2 ** attempt)  # 10s, 20s, 40s
                    print(f"⚠ Rate limit hit. Waiting {delay} seconds before retry...")
                    time.sleep(delay)
                else:
                    raise

        english_description = message.content[0].text.strip()
        print(f"\nGenerated English Description:\n{english_description}")
        print(f"✓ Auto-approved (running in full automation mode)")

        # Delay after heavy API call to avoid rate limiting
        # With 50K tokens/min limit and ~20K per call, we need 60+ seconds between calls
        print("⏱ Waiting 65 seconds to avoid rate limit (this is necessary with your API limits)...")
        time.sleep(65)

        return english_description

    def generate_premise(self, english_title: str) -> str:
        """Generate a 2-3 sentence premise for the video. Returns english_premise."""
        print("\n=== STEP 3: Generating Video Premise (English) ===")

        max_retries = 3
        for attempt in range(max_retries):
            try:
                message = self.claude_client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    system=self.custom_instructions,
                    messages=[{
                        "role": "user",
                        "content": f"Write a 2-3 sentence premise for a video titled '{english_title}'. This explains what the video will cover and serves as a guide for the full script. Be specific about the key points that will be discussed."
                    }]
                )
                break  # Success, exit retry loop
            except Exception as e:
                if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                    delay = 10 * (2 ** attempt)  # 10s, 20s, 40s
                    print(f"⚠ Rate limit hit. Waiting {delay} seconds before retry {attempt + 1}/{max_retries}...")
                    time.sleep(delay)
                else:
                    raise

        english_premise = message.content[0].text.strip()
        print(f"\nGenerated English Premise:\n{english_premise}")
        print(f"✓ Auto-approved (running in full automation mode)")

        # Delay after heavy API call to avoid rate limiting
        # With 50K tokens/min limit and ~20K per call, we need 60+ seconds between calls
        print("⏱ Waiting 65 seconds to avoid rate limit (this is necessary with your API limits)...")
        time.sleep(65)

        return english_premise

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

        max_retries = 3
        for attempt in range(max_retries):
            try:
                message = self.claude_client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=self.custom_instructions,
                    messages=[{"role": "user", "content": prompt}]
                )
                break  # Success, exit retry loop
            except Exception as e:
                if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                    delay = 10 * (2 ** attempt)  # 10s, 20s, 40s
                    print(f"  ⚠ Rate limit hit. Waiting {delay} seconds before retry...")
                    time.sleep(delay)
                else:
                    raise

        # Delay after heavy API call (script segments use project files)
        # With 50K tokens/min limit and ~20K per call, we need 60+ seconds between calls
        print(f"  ⏱ Waiting 65 seconds to avoid rate limit (this is necessary with your API limits)...")
        time.sleep(65)

        return message.content[0].text.strip()

    def generate_full_script(self, english_title: str, english_premise: str) -> str:
        """Generate full video script in English and get approval. Returns english_script."""
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
            print("⏱ Waiting 65 seconds before generating more content...")
            time.sleep(65)

            additional_prompt = f"""The current script has {total_words} words but needs to be 6000-7000 words.

Title: {english_title}
Premise: {english_premise}

Add more content to expand on the topic. Write approximately {6000 - total_words} more words to reach the target."""

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    message = self.claude_client.messages.create(
                        model=self.model,
                        max_tokens=4096,
                        system=self.custom_instructions,
                        messages=[{"role": "user", "content": additional_prompt}]
                    )
                    break  # Success, exit retry loop
                except Exception as e:
                    if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                        delay = 10 * (2 ** attempt)  # 10s, 20s, 40s
                        print(f"  ⚠ Rate limit hit. Waiting {delay} seconds before retry...")
                        time.sleep(delay)
                    else:
                        raise

            additional_content = message.content[0].text.strip()
            full_script += "\n\n" + additional_content
            total_words = self.count_words(full_script)
            print(f"Updated word count: {total_words}")

            # Delay after heavy API call
            print("  ⏱ Waiting 65 seconds to avoid rate limit...")
            time.sleep(65)

        # If over 7000 words, trim
        if total_words > 7000:
            print(f"\nWord count ({total_words}) exceeds target. Trimming to ~7000 words...")
            words = full_script.split()
            full_script = " ".join(words[:7000])
            total_words = 7000

        print(f"\n✓ Final English script word count: {total_words} words")

        # Show preview
        print("\n" + "=" * 60)
        print("SCRIPT PREVIEW (first 500 characters):")
        print("=" * 60)
        print(full_script[:500] + "...")
        print("=" * 60)
        print(f"\n✓ Auto-approved (running in full automation mode)")

        # Save English script
        english_script_path = self.working_dir / "video_script_english.txt"
        with open(english_script_path, 'w', encoding='utf-8') as f:
            f.write(f"TITLE: {english_title}\n\n")
            f.write(f"PREMISE: {english_premise}\n\n")
            f.write(f"WORD COUNT: {total_words}\n\n")
            f.write("=" * 50 + "\n\n")
            f.write(full_script)

        print(f"✓ English script saved to: {english_script_path}")

        return full_script

    def translate_all_content(self, english_title: str, english_description: str,
                              english_premise: str, english_script: str) -> dict:
        """Translate all English content to Korean in one batch operation.

        Returns dict with keys: korean_title, korean_description, korean_premise, korean_script
        """
        print("\n" + "=" * 60)
        print("=== TRANSLATING ALL CONTENT TO KOREAN ===")
        print("=" * 60)
        print("\nNow that all English content is approved, translating everything to Korean...")
        print("This will take a few minutes.\n")

        # Step 1: Translate short content (title + description + premise) in one call for consistency
        print("Step 1/2: Translating title, description, and premise...")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                message = self.claude_client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    messages=[{
                        "role": "user",
                        "content": f"""Translate the following to Korean, maintaining consistent terminology across all three:

TITLE:
{english_title}

DESCRIPTION:
{english_description}

PREMISE:
{english_premise}

Format your response exactly as:
TITLE: [Korean translation]
DESCRIPTION: [Korean translation]
PREMISE: [Korean translation]"""
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

        # Parse the response
        response_text = message.content[0].text.strip()
        lines = response_text.split('\n')

        korean_title = ""
        korean_description = ""
        korean_premise = ""

        current_section = None
        for line in lines:
            if line.startswith("TITLE:"):
                korean_title = line.replace("TITLE:", "").strip()
                current_section = "title"
            elif line.startswith("DESCRIPTION:"):
                korean_description = line.replace("DESCRIPTION:", "").strip()
                current_section = "description"
            elif line.startswith("PREMISE:"):
                korean_premise = line.replace("PREMISE:", "").strip()
                current_section = "premise"
            elif line.strip() and current_section:
                # Multi-line content
                if current_section == "title":
                    korean_title += " " + line.strip()
                elif current_section == "description":
                    korean_description += " " + line.strip()
                elif current_section == "premise":
                    korean_premise += " " + line.strip()

        print(f"✓ Korean title: {korean_title}")
        print(f"✓ Korean description: {korean_description[:100]}...")
        print(f"✓ Korean premise: {korean_premise[:100]}...")

        time.sleep(2)  # Small delay

        # Step 2: Translate full script in chunks
        print("\nStep 2/2: Translating full script...")
        korean_script = self.translate_to_korean(english_script)

        print("\n✓ All content translated to Korean!")

        return {
            "korean_title": korean_title,
            "korean_description": korean_description,
            "korean_premise": korean_premise,
            "korean_script": korean_script
        }

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

    def generate_voiceover(self, korean_script: str) -> str:
        """Generate voiceover using GenAIPro Max API."""
        print("\n=== STEP 5: Generating Voiceover ===")

        # Always generate fresh voiceover (full automation mode)
        voiceover_path = self.working_dir / "voiceover.mp3"
        if voiceover_path.exists():
            print(f"✓ Found existing voiceover, will overwrite with new generation (full automation mode)")

        # Get GenAIPro API credentials from config
        genaipro_api_key = self.config.get('genaipro_api_key')
        if not genaipro_api_key:
            print("\n✗ GenAIPro API key not found in config.json!")
            print("Please add your API key:")
            print('  "genaipro_api_key": "your-api-key-here"')
            sys.exit(1)

        # Get voice ID from config, or use default Korean voice
        voice_id = self.config.get('genaipro_voice_id', '226893671006272')  # Default Korean voice

        print(f"\nGenerating voiceover with GenAIPro Max API...")
        print(f"Voice ID: {voice_id}")
        print(f"Script length: {len(korean_script)} characters")
        print("\nThis may take a few minutes depending on script length...")

        try:
            # Step 1: Create TTS task
            headers = {
                "Authorization": f"Bearer {genaipro_api_key}",
                "Content-Type": "application/json"
            }

            create_task_data = {
                "text": korean_script,
                "title": "Video Voiceover",
                "voice_id": voice_id,
                "model_id": "speech-2.5-hd-preview",
                "language": "Korean",
                "speed": self.config.get('tts_speed', 1.0),
                "pitch": self.config.get('tts_pitch', 0),
                "volume": self.config.get('tts_volume', 1.0),
                "is_clone": False
            }

            print("Creating TTS task...")
            response = requests.post(
                "https://genaipro.vn/api/v1/max/tasks",
                headers=headers,
                json=create_task_data,
                timeout=30
            )

            if response.status_code != 200:
                raise Exception(f"API error: {response.status_code} - {response.text}")

            task_data = response.json()
            task_id = task_data['id']
            print(f"✓ Task created: {task_id}")

            # Step 2: Poll for completion
            print("Waiting for voiceover generation...")
            max_attempts = 180  # 15 minutes max (180 × 5 seconds) - long scripts need more time
            attempt = 0

            while attempt < max_attempts:
                time.sleep(5)  # Wait 5 seconds between checks

                response = requests.get(
                    f"https://genaipro.vn/api/v1/max/tasks/{task_id}",
                    headers=headers,
                    timeout=30
                )

                if response.status_code != 200:
                    raise Exception(f"API error: {response.status_code} - {response.text}")

                task_status = response.json()
                status = task_status.get('status')
                progress = task_status.get('process_percentage', 0)

                print(f"  Progress: {progress}% - Status: {status}")

                if status == 'completed':
                    result_url = task_status.get('result')
                    if not result_url:
                        raise Exception("No result URL in completed task")

                    # Fix relative URL paths from API
                    if not result_url.startswith('http'):
                        result_url = f"https://genaipro.vn{result_url}"

                    # Step 3: Download the MP3 file
                    print(f"\n✓ Voiceover generated! Downloading...")
                    print(f"  URL: {result_url}")
                    mp3_response = requests.get(result_url, timeout=60)

                    if mp3_response.status_code == 200:
                        with open(voiceover_path, 'wb') as f:
                            f.write(mp3_response.content)

                        file_size = voiceover_path.stat().st_size / (1024 * 1024)  # MB
                        print(f"✓ Voiceover downloaded successfully!")
                        print(f"  File: {voiceover_path}")
                        print(f"  Size: {file_size:.2f} MB")
                        return str(voiceover_path)
                    else:
                        raise Exception(f"Failed to download MP3: {mp3_response.status_code}")

                elif status == 'failed':
                    error_msg = task_status.get('error', 'Unknown error')
                    raise Exception(f"Task failed: {error_msg}")

                attempt += 1

            raise Exception("Task timed out after 15 minutes")

        except Exception as e:
            print(f"\n✗ Voiceover generation failed: {e}")
            print("\nTroubleshooting:")
            print("1. Check your GenAIPro API key in config.json")
            print("2. Check your balance at https://genaipro.vn")
            print("3. Verify the voice_id is correct")
            print("4. Check your internet connection")
            print("\n✗ Exiting due to error (full automation mode - no retries)")
            sys.exit(1)

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

    def select_character(self) -> Tuple[str, Path]:
        """Prompt user to select a character folder.

        Returns:
            Tuple of (character_name, character_folder_path)
        """
        print("\n" + "=" * 60)
        print("=== CHARACTER SELECTION ===")
        print("=" * 60)

        # Get base characters path from config
        characters_base_path = self.config.get('characters_base_path', './characters')
        base_path = Path(characters_base_path)

        if not base_path.exists():
            print(f"\n✗ Characters folder not found: {base_path}")
            print("\nPlease create character folders with this structure:")
            print("  characters/")
            print("    talking_person1/")
            print("      talking_person1.mp4")
            print("      image1.jpg")
            print("      image2.png")
            print("      ...")
            print("    talking_person2/")
            print("      talking_person2.mp4")
            print("      ...")
            sys.exit(1)

        # Find all character folders
        character_folders = [d for d in base_path.iterdir() if d.is_dir()]

        if not character_folders:
            print(f"\n✗ No character folders found in: {base_path}")
            print("\nPlease create at least one character folder.")
            sys.exit(1)

        # Display available characters
        print(f"\nFound {len(character_folders)} character(s):\n")
        for i, folder in enumerate(character_folders, 1):
            # Count images in folder
            image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp']
            image_count = sum(len(list(folder.glob(ext))) for ext in image_extensions)

            # Check for MP4 file
            mp4_files = list(folder.glob('*.mp4'))
            has_video = "✓" if mp4_files else "✗"

            print(f"  {i}. {folder.name}")
            print(f"     Video: {has_video} | Images: {image_count}")

        # Get user choice
        while True:
            try:
                choice = input(f"\nSelect character (1-{len(character_folders)}): ").strip()
                choice_idx = int(choice) - 1

                if 0 <= choice_idx < len(character_folders):
                    selected_folder = character_folders[choice_idx]
                    print(f"\n✓ Selected: {selected_folder.name}")
                    return selected_folder.name, selected_folder
                else:
                    print(f"Please enter a number between 1 and {len(character_folders)}")
            except (ValueError, KeyboardInterrupt):
                print("\n✗ Cancelled by user")
                sys.exit(0)

    def get_character_images(self, character_folder: Path, num_images: int = 4) -> List[str]:
        """Load pre-generated images from character folder.

        Args:
            character_folder: Path to character folder containing images
            num_images: Number of images to randomly select

        Returns:
            List of image file paths
        """
        print(f"\n=== STEP 6: Loading Images from Character Folder ===")

        # Find all images in the folder
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.JPG', '*.JPEG', '*.PNG', '*.WEBP']
        all_images = []

        for ext in image_extensions:
            all_images.extend(character_folder.glob(ext))

        if not all_images:
            print(f"\n✗ No images found in: {character_folder}")
            print("\nPlease add images to this character folder.")
            sys.exit(1)

        print(f"✓ Found {len(all_images)} image(s) in character folder")

        # Randomly select N images
        if len(all_images) <= num_images:
            selected_images = all_images
            print(f"✓ Using all {len(selected_images)} images")
        else:
            selected_images = random.sample(all_images, num_images)
            print(f"✓ Randomly selected {num_images} images from {len(all_images)} available")

        # Convert to strings and print
        image_paths = [str(img) for img in selected_images]
        for i, img_path in enumerate(image_paths, 1):
            print(f"  {i}. {Path(img_path).name}")

        return image_paths

    def replay_capcut_actions(self, actions_path: Path) -> None:
        """Replay recorded CapCut actions from JSON file."""
        print("\n🎬 Replaying recorded CapCut actions...")

        with open(actions_path, 'r') as f:
            recording_data = json.load(f)

        actions = recording_data.get('actions', [])
        total_actions = len(actions)

        print(f"✓ Loaded {total_actions} recorded actions")
        print(f"Recording date: {recording_data.get('recorded_at', 'unknown')}")
        print("\n⚠ DO NOT TOUCH YOUR MOUSE OR KEYBOARD! ⚠")
        print("Starting playback in 5 seconds...\n")
        time.sleep(5)

        for i, action in enumerate(actions, 1):
            # Wait for the recorded delay before this action
            delay = action.get('delay_before', 0)
            if delay > 0:
                time.sleep(delay)

            action_type = action.get('type')

            if action_type == 'click':
                x = action.get('x')
                y = action.get('y')
                print(f"[{i}/{total_actions}] Click at ({x}, {y})")
                pyautogui.click(x, y)

            elif action_type == 'key':
                key = action.get('key')
                print(f"[{i}/{total_actions}] Press key: {key}")
                pyautogui.press(key)

            elif action_type == 'special_key':
                key = action.get('key')
                print(f"[{i}/{total_actions}] Press special key: {key}")
                pyautogui.press(key)

        print("\n✓ Finished replaying all actions!")

    def edit_video_ffmpeg(self, voiceover_path: Optional[str], image_paths: List[str], subtitle_path: str) -> str:
        """Edit video using FFmpeg - reliable command-line video editing.

        Steps:
        1. Loop the talking person video to match voiceover duration
        2. Overlay images at different timestamps
        3. Replace audio with voiceover
        4. Burn in subtitles from SRT file
        5. Export as final_video.mp4
        """
        print("\n=== STEP 8: Editing Video with FFmpeg ===")

        # Get paths
        video_path = self.selected_character_video
        output_path = self.working_dir / "final_video.mp4"

        # Get voiceover duration to know how long the final video should be
        if voiceover_path:
            audio_duration = self.get_audio_duration(voiceover_path)
            print(f"✓ Voiceover duration: {audio_duration:.2f} seconds")
        else:
            audio_duration = 90  # Default 90 seconds
            print("✓ No voiceover - using 90 second default")

        print(f"✓ Input video: {Path(video_path).name}")
        print(f"✓ Images to overlay: {len(image_paths)}")
        print(f"✓ Subtitles: {Path(subtitle_path).name}")
        print(f"✓ Output: {output_path}")

        # Build FFmpeg command
        print("\n🎬 Building video with FFmpeg...")

        # Step 1: Create base video (loop talking person to match audio duration)
        temp_looped = self.working_dir / "temp_looped.mp4"
        print("  [1/4] Looping base video to match audio duration...")

        loop_cmd = [
            'ffmpeg', '-y',
            '-stream_loop', '-1',  # Loop indefinitely
            '-i', str(video_path),
            '-t', str(audio_duration),  # Cut to exact duration
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-an',  # No audio yet
            str(temp_looped)
        ]

        result = subprocess.run(loop_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"✗ Error looping video: {result.stderr}")
            sys.exit(1)
        print("    ✓ Base video looped")

        # Step 2: Overlay images at different timestamps
        temp_with_images = self.working_dir / "temp_with_images.mp4"
        print(f"  [2/4] Overlaying {len(image_paths)} images...")

        if image_paths:
            # Build filter_complex for image overlays
            # Images will appear at evenly spaced intervals throughout the video
            interval = audio_duration / (len(image_paths) + 1)

            # Build inputs: -i base_video -i img1 -i img2 ...
            overlay_inputs = ['-i', str(temp_looped)]
            for img_path in image_paths:
                overlay_inputs.extend(['-i', str(img_path)])

            # Build filter chain for overlays
            # Each image scales to fit screen, fades in/out, appears at specific time
            filters = []
            current_input = '0:v'

            for i, img_path in enumerate(image_paths):
                img_num = i + 1
                start_time = interval * (i + 1)
                duration = 3.0  # Each image shows for 3 seconds

                # Scale image to fit 1/4 of screen (bottom-right corner)
                scale_filter = f"[{img_num}:v]scale=480:270[img{i}]"
                filters.append(scale_filter)

                # Overlay with fade in/out
                overlay_filter = f"[{current_input}][img{i}]overlay=W-w-20:H-h-20:enable='between(t,{start_time},{start_time+duration})'[v{i}]"
                filters.append(overlay_filter)
                current_input = f"v{i}"

            filter_complex = ';'.join(filters)

            overlay_cmd = [
                'ffmpeg', '-y'
            ] + overlay_inputs + [
                '-filter_complex', filter_complex,
                '-map', f'[{current_input}]',
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                str(temp_with_images)
            ]

            result = subprocess.run(overlay_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"✗ Error overlaying images: {result.stderr}")
                # Continue without images
                temp_with_images = temp_looped
                print("    ⚠ Continuing without image overlays")
            else:
                print(f"    ✓ {len(image_paths)} images overlaid")
        else:
            # No images, just copy the looped video
            temp_with_images = temp_looped
            print("    ⚠ No images to overlay")

        # Step 3: Add subtitles
        temp_with_subs = self.working_dir / "temp_with_subs.mp4"
        print("  [3/4] Burning in subtitles...")

        # Escape subtitle path for FFmpeg filter
        subtitle_path_escaped = str(subtitle_path).replace('\\', '/').replace(':', '\\:')

        subs_cmd = [
            'ffmpeg', '-y',
            '-i', str(temp_with_images),
            '-vf', f"subtitles='{subtitle_path_escaped}'",
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            str(temp_with_subs)
        ]

        result = subprocess.run(subs_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"✗ Error adding subtitles: {result.stderr}")
            # Continue without subtitles
            temp_with_subs = temp_with_images
            print("    ⚠ Continuing without subtitles")
        else:
            print("    ✓ Subtitles burned in")

        # Step 4: Add voiceover audio and export final video
        print("  [4/4] Adding voiceover and exporting final video...")

        if voiceover_path:
            final_cmd = [
                'ffmpeg', '-y',
                '-i', str(temp_with_subs),
                '-i', str(voiceover_path),
                '-c:v', 'copy',  # Don't re-encode video
                '-c:a', 'aac',
                '-b:a', '192k',
                '-map', '0:v:0',  # Video from first input
                '-map', '1:a:0',  # Audio from second input
                '-shortest',  # Cut to shortest stream
                str(output_path)
            ]
        else:
            # No voiceover, just copy the video with subtitles
            final_cmd = [
                'ffmpeg', '-y',
                '-i', str(temp_with_subs),
                '-c', 'copy',
                str(output_path)
            ]

        result = subprocess.run(final_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"✗ Error creating final video: {result.stderr}")
            sys.exit(1)

        print("    ✓ Final video exported")

        # Clean up temp files
        print("\n🧹 Cleaning up temporary files...")
        for temp_file in [temp_looped, temp_with_images, temp_with_subs]:
            if temp_file.exists() and temp_file != output_path:
                temp_file.unlink()
                print(f"    ✓ Removed {temp_file.name}")

        print(f"\n✅ Video editing complete: {output_path}")
        print(f"   Duration: {audio_duration:.2f} seconds")
        print(f"   Size: {output_path.stat().st_size / (1024*1024):.2f} MB")

        return str(output_path)

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
            # STEP 0: Select character to use for this video
            character_name, character_folder = self.select_character()

            # Find the character's MP4 file
            mp4_files = list(character_folder.glob('*.mp4'))
            if not mp4_files:
                print(f"\n✗ No MP4 file found in {character_folder}")
                print("Please add a video file to this character folder.")
                sys.exit(1)

            character_video_path = str(mp4_files[0])
            print(f"✓ Using video: {Path(character_video_path).name}")

            # Store character info for later use
            self.selected_character_folder = character_folder
            self.selected_character_video = character_video_path

            # PHASE 1: Generate all English content
            print("\n📝 PHASE 1: GENERATE ALL ENGLISH CONTENT")
            print("=" * 60)

            # Step 1: Generate and approve title (English only)
            english_title = self.generate_title()

            # Step 2: Generate and approve description (English only)
            english_description = self.generate_description(english_title)

            # Step 3: Generate and approve premise (English only)
            english_premise = self.generate_premise(english_title)

            # Step 4: Generate and approve full script (English only)
            english_script = self.generate_full_script(english_title, english_premise)

            # PHASE 2: Translate everything to Korean
            print("\n🌐 PHASE 2: TRANSLATE ALL CONTENT TO KOREAN")
            print("=" * 60)

            translations = self.translate_all_content(
                english_title,
                english_description,
                english_premise,
                english_script
            )

            korean_title = translations["korean_title"]
            korean_description = translations["korean_description"]
            korean_premise = translations["korean_premise"]
            korean_script = translations["korean_script"]

            # PHASE 3: Generate media assets
            print("\n🎬 PHASE 3: GENERATE MEDIA ASSETS")
            print("=" * 60)

            # Step 5: Generate voiceover from Korean script
            voiceover_path = self.generate_voiceover(korean_script)

            # Step 6: Generate subtitles from Korean script
            subtitle_path = self.generate_subtitles(korean_script)

            # Step 7: Load images from character folder
            num_images = self.config.get('num_images', 4)
            image_paths = self.get_character_images(self.selected_character_folder, num_images)

            # Step 8: Edit video with FFmpeg
            video_path = self.edit_video_ffmpeg(voiceover_path, image_paths, subtitle_path)

            # Step 9: Create thumbnail in Canva
            thumbnail_path = self.create_thumbnail_canva(english_title)

            print("\n" + "=" * 60)
            print("✓ VIDEO GENERATION COMPLETE!")
            print("=" * 60)
            print(f"\nEnglish Title: {english_title}")
            print(f"Korean Title: {korean_title}")
            print(f"English Description: {english_description}")
            print(f"Korean Description: {korean_description}")
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
