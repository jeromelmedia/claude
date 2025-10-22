#!/usr/bin/env python3
"""
AI Video Generation Macro - Browser Automation Version
Uses browser automation to interact with Claude.ai Project directly,
then uses GenAIPro API and FFmpeg for media generation.
"""

import os
import sys
import time
import json
import requests
import subprocess
import random
from pathlib import Path
from typing import Optional, List, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class VideoGenerationMacroBrowser:
    """Browser automation version - uses Claude.ai Project for content generation"""

    def __init__(self, config_path: str = "config.json"):
        self.config = self.load_config(config_path)
        self.project_id = self.config.get("claude_project_id")
        self.project_url = f"https://claude.ai/project/{self.project_id}"

        # Paths
        self.base_output_dir = Path("./output")
        self.base_output_dir.mkdir(exist_ok=True)
        self.working_dir = None  # Set after title generation

        # Character selection
        self.selected_character_folder = None
        self.selected_character_video = None

        # Browser
        self.driver = None

        print(f"Using Claude Project: {self.project_id}")
        print(f"Project URL: {self.project_url}")

    def load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file"""
        if not Path(config_path).exists():
            print(f"Error: {config_path} not found")
            print("Please copy config.example.json to config.json and fill in your details")
            sys.exit(1)

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def init_browser(self):
        """Initialize Chrome browser with persistent profile for automation"""
        print("\n🌐 Initializing browser...")

        chrome_options = Options()

        # Create a dedicated Chrome profile directory for this automation
        # This keeps you logged in between runs WITHOUT conflicting with your main Chrome
        automation_profile_dir = Path("./chrome_automation_profile").absolute()
        automation_profile_dir.mkdir(exist_ok=True)

        print(f"Using automation profile: {automation_profile_dir}")
        print("(This keeps you logged in between runs)")

        # Use the dedicated profile directory
        chrome_options.add_argument(f"user-data-dir={automation_profile_dir}")

        # Add compatibility options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✓ Browser initialized")
        except Exception as e:
            error_msg = str(e)

            if "user data directory is already in use" in error_msg.lower():
                print(f"\n✗ Chrome automation profile is already in use!")
                print("\n⚠️  SOLUTION: Close the automation browser window and try again.")
                print("\nLook for a Chrome window that was opened by this script and close it.")
                print("Then run the script again.")

                # Try to kill Chrome processes using this profile (Windows)
                if sys.platform == 'win32':
                    print("\nAttempting to close Chrome processes...")
                    try:
                        subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'],
                                     capture_output=True, timeout=5)
                        print("✓ Chrome processes closed. Please wait 5 seconds...")
                        time.sleep(5)

                        # Retry once
                        print("Retrying browser initialization...")
                        self.driver = webdriver.Chrome(options=chrome_options)
                        print("✓ Browser initialized successfully!")
                        return
                    except:
                        pass

                print("\nIf the problem persists, restart your computer.")
                raise
            else:
                print(f"\n✗ Failed to initialize Chrome: {e}")
                print("\nTroubleshooting:")
                print("1. Make sure Chrome is installed")
                print("2. Close ALL Chrome windows")
                print("3. Update Chrome to latest version")
                print("4. Try: pip install --upgrade selenium")
                raise

    def navigate_to_project(self):
        """Navigate to Claude.ai Project"""
        print(f"\n📂 Opening Claude Project...")
        self.driver.get(self.project_url)
        time.sleep(5)  # Wait for page load

        # Check if we're logged in
        try:
            # Look for chat input (indicates we're logged in and in project)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
            )
            print("✓ Successfully loaded project")
        except TimeoutException:
            print("\n⚠ Not logged in to Claude.ai")
            print("Please log in manually in the browser window...")
            print("Press Enter once you're logged in and see the chat interface")
            input()

    def send_prompt_and_wait(self, prompt: str, wait_time: int = 60) -> str:
        """Send a prompt to Claude and wait for response"""
        try:
            # Retry logic for DOM issues
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Find chat input
                    print(f"  Finding chat input (attempt {attempt + 1}/{max_retries})...")
                    chat_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
                    )
                    time.sleep(1)

                    # Click to focus
                    print(f"  Focusing input...")
                    chat_input.click()
                    time.sleep(0.5)

                    # Use JavaScript to set the text content directly (much more reliable than typing)
                    print(f"  Setting prompt text via JavaScript ({len(prompt)} chars)...")
                    # Escape single quotes in the prompt for JavaScript
                    escaped_prompt = prompt.replace("'", "\\'").replace("\n", "\\n").replace("\r", "")

                    # Set the text content using JavaScript
                    js_script = f"""
                    var element = arguments[0];
                    element.textContent = '{escaped_prompt}';

                    // Trigger input event to notify React/Vue that content changed
                    var event = new Event('input', {{ bubbles: true }});
                    element.dispatchEvent(event);
                    """

                    self.driver.execute_script(js_script, chat_input)
                    time.sleep(1)

                    # Now send the message - try both keyboard and button click
                    print(f"  Sending message...")

                    # Method 1: Try keyboard shortcut
                    try:
                        chat_input.click()
                        time.sleep(0.3)
                        chat_input.send_keys(Keys.CONTROL + Keys.RETURN)
                        print(f"  Sent via keyboard (Ctrl+Enter)")
                    except:
                        # Method 2: Find and click the send button
                        print(f"  Keyboard send failed, trying button click...")
                        try:
                            # Look for send button (various possible selectors)
                            send_button = None
                            button_selectors = [
                                "button[aria-label*='Send']",
                                "button[type='submit']",
                                "button:has(svg)",  # Send buttons often have SVG icons
                                "button[class*='send']"
                            ]

                            for selector in button_selectors:
                                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                if buttons:
                                    send_button = buttons[-1]  # Usually the last one
                                    break

                            if send_button:
                                send_button.click()
                                print(f"  Sent via button click")
                            else:
                                print(f"  ⚠ Could not find send button, message may not have been sent")
                        except Exception as e:
                            print(f"  ⚠ Button click also failed: {e}")

                    time.sleep(2)

                    # If we got here, we succeeded
                    print(f"  ✓ Message sent successfully")
                    break

                except Exception as e:
                    error_msg = str(e).lower()
                    if ("stale element" in error_msg or "no such element" in error_msg) and attempt < max_retries - 1:
                        print(f"  ⚠ Element issue, retrying... ({attempt + 1}/{max_retries})")
                        time.sleep(2)
                        continue
                    else:
                        raise  # Re-raise if not a retryable error or out of retries

            # Wait for response to start appearing
            print(f"  Waiting for Claude to start generating...")
            time.sleep(3)

            # Wait for "Stop generating" button to disappear (indicates completion)
            print(f"  Monitoring generation progress (max {wait_time}s)...")
            max_wait = wait_time
            start_time = time.time()
            generation_detected = False

            while time.time() - start_time < max_wait:
                try:
                    # Check if still generating
                    stop_button = self.driver.find_elements(By.XPATH, "//button[contains(., 'Stop')]")

                    if stop_button and not generation_detected:
                        print(f"  ⏳ Claude is generating...")
                        generation_detected = True

                    if not stop_button and generation_detected:
                        # Stop button disappeared - but wait to make sure it's REALLY done
                        print(f"  ✓ Stop button disappeared, waiting to ensure completion...")
                        break
                    elif not stop_button and not generation_detected:
                        # Check if response already appeared (fast response)
                        messages = self.driver.find_elements(By.CSS_SELECTOR, "div[data-test-render-count]")
                        if len(messages) > 0:
                            print(f"  ✓ Response detected!")
                            break
                except:
                    pass

                elapsed = int(time.time() - start_time)
                if elapsed % 10 == 0 and elapsed > 0:  # Progress update every 10 seconds
                    print(f"  ... still waiting ({elapsed}s elapsed)")

                time.sleep(2)

            # CRITICAL: Wait for response to fully stabilize
            # Claude may still be typing even after Stop button disappears
            print(f"  ⏱️  Waiting for response to stabilize (15 seconds)...")
            time.sleep(15)

            # Check if text is still changing (wait until stable)
            print(f"  🔍 Verifying response stability...")
            stable_count = 0
            last_text_length = 0

            for stability_check in range(5):  # Check 5 times
                try:
                    # Get current text length
                    current_js = "return document.body.innerText.length;"
                    current_length = self.driver.execute_script(current_js)

                    if current_length == last_text_length:
                        stable_count += 1
                        print(f"    Stable check {stable_count}/3 (length: {current_length})")
                        if stable_count >= 3:
                            print(f"  ✓ Response confirmed stable!")
                            break
                    else:
                        print(f"    Text still changing ({last_text_length} → {current_length})")
                        stable_count = 0

                    last_text_length = current_length
                    time.sleep(2)
                except:
                    time.sleep(2)

            # Final wait for DOM to settle
            print(f"  Extracting response text...")
            time.sleep(3)

            # Use JavaScript to extract response - MUCH more reliable!
            response_text = ""
            extraction_attempts = 5

            for extract_attempt in range(extraction_attempts):
                if extract_attempt > 0:
                    print(f"  Retry extraction attempt {extract_attempt + 1}/{extraction_attempts}...")
                    time.sleep(3)

                # JavaScript approach - scan the DOM and extract last message
                js_extract_script = """
                // Find all potential message containers
                var selectors = [
                    'div[data-test-render-count]',
                    'div[class*="Message"]',
                    'div[class*="message"]',
                    'div[role="article"]',
                    'div[class*="assistant"]',
                    'div[class*="response"]'
                ];

                var allMessages = [];

                for (var i = 0; i < selectors.length; i++) {
                    var elements = document.querySelectorAll(selectors[i]);
                    for (var j = 0; j < elements.length; j++) {
                        var text = elements[j].innerText || elements[j].textContent;
                        if (text && text.length > 20) {
                            allMessages.push({
                                text: text.trim(),
                                length: text.length,
                                selector: selectors[i],
                                index: j
                            });
                        }
                    }
                }

                // Return the last non-empty message
                if (allMessages.length > 0) {
                    // Sort by appearance order and get last
                    var lastMsg = allMessages[allMessages.length - 1];
                    return JSON.stringify({
                        success: true,
                        text: lastMsg.text,
                        method: lastMsg.selector,
                        count: allMessages.length
                    });
                }

                return JSON.stringify({success: false, text: '', count: 0});
                """

                try:
                    result_json = self.driver.execute_script(js_extract_script)
                    result = json.loads(result_json)

                    print(f"  [DEBUG] JavaScript extraction: found {result.get('count', 0)} messages")

                    if result.get('success') and result.get('text'):
                        response_text = result['text'].strip()
                        method = result.get('method', 'unknown')
                        print(f"  [DEBUG] Extracted via JS (selector: {method})")
                        print(f"  [DEBUG] Response preview: {response_text[:150]}...")
                        break

                except Exception as e:
                    print(f"  [DEBUG] JS extraction error: {e}")

                # Fallback: Try direct Selenium element finding
                if not response_text:
                    print(f"  [DEBUG] Trying Selenium fallback...")
                    all_divs = self.driver.find_elements(By.TAG_NAME, "div")
                    print(f"  [DEBUG] Found {len(all_divs)} total divs on page")

                    for div in reversed(all_divs):
                        try:
                            text = div.text.strip()
                            if text and len(text) > 20 and len(text) < 5000:
                                # Don't include if it contains the prompt
                                if prompt[:30] not in text:
                                    response_text = text
                                    print(f"  [DEBUG] Selenium fallback found text: {response_text[:100]}...")
                                    break
                        except:
                            continue

                if response_text:
                    break  # Got a response, stop retrying

            if response_text:
                print(f"  ✓ Response captured ({len(response_text)} characters)")
                return response_text
            else:
                print("\n" + "="*60)
                print("  ✗✗✗ EXTRACTION FAILED AFTER ALL RETRIES ✗✗✗")
                print("="*60)

                timestamp = int(time.time())

                # Save screenshot
                print("\n  📸 Saving screenshot for debugging...")
                try:
                    screenshot_path = f"debug_screenshot_{timestamp}.png"
                    self.driver.save_screenshot(screenshot_path)
                    print(f"  ✓ Screenshot saved: {screenshot_path}")
                except Exception as e:
                    print(f"  ✗ Screenshot failed: {e}")

                # Save page HTML
                print("\n  📄 Saving page HTML for debugging...")
                try:
                    html_path = f"debug_page_{timestamp}.html"
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    print(f"  ✓ HTML saved: {html_path}")
                except Exception as e:
                    print(f"  ✗ HTML save failed: {e}")

                # Get page text
                print("\n  📝 Extracting visible page text...")
                try:
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    page_text = body.text
                    print(f"  [DEBUG] Full page text length: {len(page_text)}")

                    # Save to file
                    text_path = f"debug_text_{timestamp}.txt"
                    with open(text_path, 'w', encoding='utf-8') as f:
                        f.write(page_text)
                    print(f"  ✓ Page text saved: {text_path}")

                    if len(page_text) > 500:
                        print(f"\n  Last 500 chars from page:\n  {page_text[-500:]}")
                    else:
                        print(f"\n  Full page text:\n  {page_text}")

                except Exception as e:
                    print(f"  ✗ Could not get page text: {e}")

                # Try one more time with a super aggressive JavaScript scan
                print("\n  🔍 Final attempt with aggressive JS scan...")
                try:
                    aggressive_js = """
                    // Get ALL text from the page
                    var allText = document.body.innerText || document.body.textContent;
                    return allText;
                    """
                    all_text = self.driver.execute_script(aggressive_js)
                    if all_text and len(all_text) > 50:
                        print(f"  [DEBUG] Aggressive JS got {len(all_text)} chars")
                        print(f"  [DEBUG] Text preview: {all_text[:300]}...")
                        # Use this as last resort
                        response_text = all_text.strip()
                        print(f"  ⚠ Using full page text as fallback response")
                        return response_text
                except Exception as e:
                    print(f"  ✗ Aggressive JS failed: {e}")

                print("\n" + "="*60)
                print("  Check the debug files above to see what's on the page!")
                print("="*60 + "\n")
                return ""

        except Exception as e:
            print(f"✗ Error sending prompt: {e}")
            import traceback
            traceback.print_exc()
            return ""

    def extract_generated_content(self, response: str) -> str:
        """
        Extract the actual generated content from Claude's response,
        filtering out thinking, searching, and explanatory text.
        """
        # Remove common Claude prefixes/explanations
        lines = response.split('\n')

        # Filter out lines that are clearly Claude's internal process
        skip_patterns = [
            'I need to',
            'I\'ll search',
            'Let me',
            'Searched project',
            'Searching for',
            'Based on',
            'Here\'s',
            'According to',
            'I can see',
            'Looking at',
            'relevant sections',
            'results'
        ]

        # Collect candidate lines (not process text)
        candidates = []
        for line in lines:
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                continue

            # Skip lines that match process patterns
            is_process = False
            for pattern in skip_patterns:
                if line_stripped.startswith(pattern):
                    is_process = True
                    break

            if not is_process and len(line_stripped) > 15:
                candidates.append(line_stripped)

        # The actual content is usually the LAST substantial line
        if candidates:
            # Return the last candidate line
            result = candidates[-1].strip('"\'')
            print(f"  [DEBUG] Extracted from {len(candidates)} candidate lines")
            return result

        # Fallback: Look for content after common intro phrases
        for intro in ['title:', 'here\'s an', 'here is', ':']:
            if intro in response.lower():
                parts = response.lower().split(intro)
                if len(parts) > 1:
                    # Get everything after the intro phrase
                    content = response[response.lower().index(intro) + len(intro):].strip()
                    # Get first line of that
                    first_line = content.split('\n')[0].strip().strip('"\'')
                    if first_line:
                        print(f"  [DEBUG] Extracted after intro phrase '{intro}'")
                        return first_line

        # Last resort: Return the whole response cleaned up
        print(f"  [DEBUG] Using full response as fallback")
        return response.strip().strip('"\'')

    def generate_title_browser(self) -> str:
        """Generate video title using Claude.ai Project with approval loop"""
        print("\n=== STEP 1: Generating Video Title (English) ===")

        while True:
            prompt = """Generate a YouTube video title in English.

Use the "korean video titles.txt" file in this project as reference for:
- Topics to cover (health, finance, lifestyle for seniors 60+)
- Title structure and format
- Tone and urgency level
- Use of numbers and specific details

Create ONE title in English following that style.

JUST OUTPUT THE TITLE. No explanations."""

            response = self.send_prompt_and_wait(prompt, wait_time=60)

            print(f"  [DEBUG] Raw response received ({len(response)} chars)")
            print(f"  [DEBUG] First 300 chars: '{response[:300]}...'")
            print(f"  [DEBUG] Last 300 chars: '...{response[-300:]}'")

            # Parse the response to extract JUST the title (not Claude's thinking/searching)
            title = self.extract_generated_content(response)

            print(f"\n📋 Generated Title:\n{title}\n")
            print(f"  [DEBUG] Final title after processing: '{title}'")

            # Get user approval
            choice = input("Options: [a]pprove, [d]eny (regenerate), [m]odify: ").lower().strip()

            if choice == 'a':
                print(f"✓ Title approved: {title}")
                return title
            elif choice == 'd':
                print("\n🔄 Regenerating title...")
                continue
            elif choice == 'm':
                modification = input("\nWhat would you like to change? ")
                print(f"\n✏️ Modifying title...")

                modify_prompt = f"""Current title: "{title}"

User wants this change: {modification}

Generate the modified title. JUST OUTPUT THE NEW TITLE."""

                response = self.send_prompt_and_wait(modify_prompt, wait_time=60)
                title = self.extract_generated_content(response)
                print(f"\n📋 Modified Title:\n{title}\n")

                # Ask for approval again
                if input("Approve this version? [y/n]: ").lower() == 'y':
                    print(f"✓ Title approved: {title}")
                    return title
                else:
                    print("\n🔄 Starting over...")
                    continue
            else:
                print("Invalid choice. Please enter 'a', 'd', or 'm'")
                continue

    def generate_description_browser(self, title: str) -> str:
        """Generate video description using Claude.ai Project with approval loop"""
        print("\n=== STEP 2: Generating Video Description (English) ===")
        print(f"  [DEBUG] Title parameter received: '{title}'")
        print(f"  [DEBUG] Title length: {len(title)} characters")

        while True:
            prompt = f"""Generate a video description for this title: "{title}"

Use the "korean video descriptions.txt" file in this project as reference for:
- Description format and structure
- Tone and urgency
- How to create curiosity
- Call to action style

Write 2-4 sentences in English following that style.

JUST OUTPUT THE DESCRIPTION."""

            response = self.send_prompt_and_wait(prompt, wait_time=60)
            description = self.extract_generated_content(response)

            print(f"\n📋 Generated Description:\n{description}\n")

            choice = input("Options: [a]pprove, [d]eny (regenerate), [m]odify: ").lower().strip()

            if choice == 'a':
                print(f"✓ Description approved")
                return description
            elif choice == 'd':
                print("\n🔄 Regenerating description...")
                continue
            elif choice == 'm':
                modification = input("\nWhat would you like to change? ")
                modify_prompt = f"""Current description: "{description}"

User wants this change: {modification}

Generate the modified description. JUST OUTPUT THE NEW DESCRIPTION."""

                response = self.send_prompt_and_wait(modify_prompt, wait_time=60)
                description = self.extract_generated_content(response)
                print(f"\n📋 Modified Description:\n{description}\n")

                if input("Approve this version? [y/n]: ").lower() == 'y':
                    print(f"✓ Description approved")
                    return description
                else:
                    print("\n🔄 Starting over...")
                    continue
            else:
                print("Invalid choice. Please enter 'a', 'd', or 'm'")
                continue

    def generate_premise_browser(self, title: str) -> str:
        """Generate video premise using Claude.ai Project with approval loop"""
        print("\n=== STEP 3: Generating Video Premise (English) ===")

        while True:
            prompt = f"""Generate a video premise based on this title: "{title}"

Write 2-3 sentences in English that:
- Introduce the expert/authority with years of experience
- State the main discovery/solution with specific details
- Preview the key benefits viewers will learn

JUST OUTPUT THE PREMISE."""

            response = self.send_prompt_and_wait(prompt, wait_time=60)
            premise = self.extract_generated_content(response)

            print(f"\n📋 Generated Premise:\n{premise}\n")

            choice = input("Options: [a]pprove, [d]eny (regenerate), [m]odify: ").lower().strip()

            if choice == 'a':
                print(f"✓ Premise approved")
                return premise
            elif choice == 'd':
                print("\n🔄 Regenerating premise...")
                continue
            elif choice == 'm':
                modification = input("\nWhat would you like to change? ")
                modify_prompt = f"""Current premise: "{premise}"

User wants this change: {modification}

Generate the modified premise. JUST OUTPUT THE NEW PREMISE."""

                response = self.send_prompt_and_wait(modify_prompt, wait_time=60)
                premise = self.extract_generated_content(response)
                print(f"\n📋 Modified Premise:\n{premise}\n")

                if input("Approve this version? [y/n]: ").lower() == 'y':
                    print(f"✓ Premise approved")
                    return premise
                else:
                    print("\n🔄 Starting over...")
                    continue
            else:
                print("Invalid choice. Please enter 'a', 'd', or 'm'")
                continue

    def generate_script_segment_browser(self, title: str, premise: str, segment_num: int, total_segments: int) -> str:
        """Generate one segment of the script using Claude.ai Project"""

        prompt = f"""Write script segment {segment_num} of {total_segments} for this video.

Title: "{title}"
Premise: {premise}

Target: {6500 // total_segments} words for this segment

SEGMENT FOCUS:
{self._get_segment_focus(segment_num, total_segments)}

WRITING STYLE - Match the Korean .txt script files in this project:
- Use their dramatic storytelling style
- Copy their structure (opening hooks, patient stories, expert credibility, solutions, timelines)
- Match their tone for seniors (60+)
- Include specific numbers, ages, measurements like they do
- Use "you" language and conversational style
- Scientific explanations in simple terms

JUST WRITE THE SCRIPT SEGMENT IN ENGLISH."""

        response = self.send_prompt_and_wait(prompt, wait_time=120)
        return response.strip()

    def _get_segment_focus(self, segment_num: int, total_segments: int) -> str:
        """Get focus instructions for each segment"""
        if segment_num == 1:
            return "Opening hook, introduction, credibility building, preview of main points"
        elif segment_num == total_segments:
            return "Final main points, practical application steps, call to action, conclusion"
        else:
            return f"Main content point {segment_num-1}, detailed explanations, examples, transitions"

    def generate_full_script_browser(self, title: str, premise: str) -> str:
        """Generate full script using Claude.ai Project in segments"""
        print("\n=== STEP 4: Generating Full Video Script (English) ===")
        print("Target: 6000-7000 words")

        num_segments = 4
        segments = []

        for i in range(1, num_segments + 1):
            print(f"\nGenerating segment {i}/{num_segments}...")
            segment = self.generate_script_segment_browser(title, premise, i, num_segments)
            segments.append(segment)

            word_count = len(segment.split())
            print(f"Segment {i} word count: {word_count}")

            # Wait between segments to avoid rate limits
            if i < num_segments:
                print("⏱ Waiting 10 seconds before next segment...")
                time.sleep(10)

        # Combine segments
        full_script = "\n\n".join(segments)
        total_words = len(full_script.split())

        print(f"\nInitial total word count: {total_words}")

        # Adjust if needed
        if total_words < 6000:
            print(f"\nWord count ({total_words}) is below target. Generating additional content...")
            additional_prompt = f"""The current script is {total_words} words. We need to reach 6000-7000 words.

Add more detailed content to this script:
- More examples and stories
- More specific tips and actionable steps
- More scientific explanations
- More call-back references to earlier points

Add approximately {6500 - total_words} words of additional content that flows naturally with the existing script.

Current script:
{full_script[:1000]}... [script continues]

Generate the ADDITIONAL content only:"""

            additional = self.send_prompt_and_wait(additional_prompt, wait_time=120)
            full_script += "\n\n" + additional
            total_words = len(full_script.split())
            print(f"Updated word count: {total_words}")

        if total_words > 7000:
            print(f"\nWord count ({total_words}) exceeds target. Trimming to ~7000 words...")
            words = full_script.split()
            full_script = " ".join(words[:7000])
            total_words = 7000

        print(f"\n✓ Final English script word count: {total_words} words")

        # Show preview and get approval
        while True:
            print("\n" + "="*60)
            print("SCRIPT PREVIEW (first 500 characters):")
            print(full_script[:500] + "...")
            print("="*60)

            choice = input("\nOptions: [a]pprove, [d]eny (regenerate all), [m]odify: ").lower().strip()

            if choice == 'a':
                print(f"✓ Script approved")
                return full_script
            elif choice == 'd':
                print("\n🔄 Regenerating entire script from scratch...")
                # Recursive call to regenerate
                return self.generate_full_script_browser(title, premise)
            elif choice == 'm':
                modification = input("\nWhat would you like to change in the script? ")
                print(f"\n✏️ Modifying script...")

                modify_prompt = f"""Current script ({total_words} words):

{full_script[:2000]}... [script continues]

User wants this change: {modification}

Generate the modified FULL script incorporating this change. Keep it 6000-7000 words.

JUST OUTPUT THE COMPLETE MODIFIED SCRIPT."""

                response = self.send_prompt_and_wait(modify_prompt, wait_time=180)
                full_script = response.strip()
                total_words = len(full_script.split())

                print(f"\n✓ Modified script word count: {total_words} words")
                print("\n" + "="*60)
                print("MODIFIED SCRIPT PREVIEW:")
                print(full_script[:500] + "...")
                print("="*60)

                if input("\nApprove this version? [y/n]: ").lower() == 'y':
                    print(f"✓ Script approved")
                    return full_script
                else:
                    print("\n🔄 Continuing with modifications...")
                    continue
            else:
                print("Invalid choice. Please enter 'a', 'd', or 'm'")
                continue

    def translate_to_korean_browser(self, text: str, content_type: str = "text") -> str:
        """Translate text to Korean using Claude.ai Project"""
        print(f"\nTranslating {content_type} to Korean...")

        prompt = f"""DO NOT explain. Translate NOW.

Translate to natural Korean for seniors (60+):

{text}

JUST OUTPUT THE KOREAN TEXT. No English, no explanations."""

        response = self.send_prompt_and_wait(prompt, wait_time=90)
        return response.strip()

    def translate_script_to_korean_browser(self, english_script: str) -> str:
        """Translate full script to Korean in chunks"""
        print("\n=== Translating Full Script to Korean ===")
        print("This may take a few minutes...")

        # Split into chunks of ~1500 words
        words = english_script.split()
        chunk_size = 1500
        chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

        korean_chunks = []

        for i, chunk in enumerate(chunks, 1):
            print(f"Translating chunk {i}/{len(chunks)}...")
            korean_chunk = self.translate_to_korean_browser(chunk, f"chunk {i}")
            korean_chunks.append(korean_chunk)

            if i < len(chunks):
                print("⏱ Waiting 10 seconds...")
                time.sleep(10)

        korean_script = "\n\n".join(korean_chunks)
        print("✓ Script translated to Korean")

        return korean_script

    # === CHARACTER SELECTION ===

    def select_character(self) -> Tuple[str, str]:
        """Let user select which character to use"""
        characters_base = Path(self.config.get("characters_base_path", "./characters"))

        if not characters_base.exists():
            print(f"Error: Characters folder not found: {characters_base}")
            sys.exit(1)

        # Find all character folders
        character_folders = [f for f in characters_base.iterdir() if f.is_dir()]

        if not character_folders:
            print(f"Error: No character folders found in {characters_base}")
            sys.exit(1)

        print("\n" + "="*60)
        print("=== CHARACTER SELECTION ===")
        print(f"\nFound {len(character_folders)} character(s):\n")

        for i, folder in enumerate(character_folders, 1):
            # Check for video file
            video_files = list(folder.glob("*.mp4"))
            has_video = "✓" if video_files else "✗"

            # Count images
            image_files = list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg")) + \
                         list(folder.glob("*.png")) + list(folder.glob("*.webp"))
            num_images = len(image_files)

            print(f"  {i}. {folder.name}")
            print(f"     Video: {has_video} | Images: {num_images}")

        # Get selection
        while True:
            try:
                choice = int(input(f"\nSelect character (1-{len(character_folders)}): "))
                if 1 <= choice <= len(character_folders):
                    break
                print(f"Please enter a number between 1 and {len(character_folders)}")
            except ValueError:
                print("Please enter a valid number")

        selected_folder = character_folders[choice - 1]

        # Get video file
        video_files = list(selected_folder.glob("*.mp4"))
        if not video_files:
            print(f"Error: No .mp4 file found in {selected_folder}")
            sys.exit(1)

        video_file = video_files[0]

        print(f"\n✓ Selected: {selected_folder.name}")
        print(f"✓ Using video: {video_file.name}")

        return str(selected_folder), str(video_file)

    def get_character_images(self, num_images: int = 4) -> List[str]:
        """Get random images from selected character folder"""
        folder = Path(self.selected_character_folder)

        # Get all image files
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
            image_files.extend(folder.glob(ext))

        if not image_files:
            print(f"Warning: No images found in {folder}")
            return []

        # Randomly select
        num_to_select = min(num_images, len(image_files))
        selected = random.sample(image_files, num_to_select)

        print(f"\n✓ Found {len(image_files)} image(s) in character folder")
        print(f"✓ Randomly selected {num_to_select} images from {len(image_files)} available\n")

        for img in selected:
            print(f"  - {img.name}")

        return [str(img) for img in selected]

    # === REST OF THE PIPELINE (GenAIPro + FFmpeg) - Keep from original macro ===

    def generate_voiceover_genaipro(self, korean_script: str, output_path: str) -> Optional[str]:
        """Generate voiceover using GenAIPro Max API"""
        print("\n=== STEP 5: Generating Voiceover ===")

        api_key = self.config.get("genaipro_api_key")
        if not api_key:
            print("Error: genaipro_api_key not found in config.json")
            return None

        voice_id = self.config.get("genaipro_voice_id", "226893671006272")

        print(f"\nGenerating voiceover with GenAIPro Max API...")
        print(f"Voice ID: {voice_id}")
        print(f"Script length: {len(korean_script)} characters")
        print(f"\nThis may take a few minutes depending on script length...")

        # Create TTS task
        url = "https://genaipro.vn/api/v1/max/tasks"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "text": korean_script,
            "voice_id": voice_id,
            "model_id": self.config.get("tts_model", "speech-2.5-hd-preview"),
            "language": "Korean",
            "speed": self.config.get("tts_speed", 1.0),
            "pitch": self.config.get("tts_pitch", 0),
            "volume": self.config.get("tts_volume", 1.0),
            "is_clone": False
        }

        try:
            print("Creating TTS task...")
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            task_data = response.json()
            task_id = task_data.get("id")

            print(f"✓ Task created: {task_id}")
            print("Waiting for voiceover generation...")

            # Poll for completion
            task_url = f"https://genaipro.vn/api/v1/max/tasks/{task_id}"
            max_attempts = 180  # 15 minutes
            attempt = 0

            while attempt < max_attempts:
                time.sleep(5)
                attempt += 1

                task_response = requests.get(task_url, headers=headers)
                task_response.raise_for_status()
                task_info = task_response.json()

                status = task_info.get("status")
                progress = task_info.get("process_percentage", 0)

                print(f"Progress: {progress}% - Status: {status}")

                if status == "completed":
                    result_url = task_info.get("result")

                    if not result_url:
                        print("✗ No result URL in response")
                        return None

                    # Fix relative URL if needed
                    if not result_url.startswith('http'):
                        result_url = f"https://genaipro.vn{result_url}"

                    print(f"\n✓ Voiceover generated! Downloading...")
                    print(f"  URL: {result_url}")

                    # Download
                    audio_response = requests.get(result_url)
                    audio_response.raise_for_status()

                    with open(output_path, 'wb') as f:
                        f.write(audio_response.content)

                    file_size = Path(output_path).stat().st_size / (1024 * 1024)
                    print(f"✓ Voiceover downloaded successfully!")
                    print(f"  File: {output_path}")
                    print(f"  Size: {file_size:.2f} MB")

                    return output_path

                elif status == "failed":
                    error = task_info.get("error", "Unknown error")
                    print(f"✗ Task failed: {error}")
                    return None

            print("✗ Task timed out after 15 minutes")
            return None

        except Exception as e:
            print(f"✗ Error generating voiceover: {e}")
            return None

    def generate_subtitles(self, korean_script: str, output_path: str, duration: float = 300.0) -> str:
        """Generate SRT subtitle file from Korean script"""
        print("\n=== Generating Subtitles (SRT format) ===")

        # Split script into sentences
        sentences = korean_script.replace('\n\n', '. ').replace('\n', ' ').split('. ')
        sentences = [s.strip() for s in sentences if s.strip()]

        # Calculate timing
        time_per_subtitle = duration / len(sentences)

        # Generate SRT content
        srt_content = []
        for i, sentence in enumerate(sentences, 1):
            start_time = (i - 1) * time_per_subtitle
            end_time = i * time_per_subtitle

            start_srt = self._seconds_to_srt_time(start_time)
            end_srt = self._seconds_to_srt_time(end_time)

            srt_content.append(f"{i}")
            srt_content.append(f"{start_srt} --> {end_srt}")
            srt_content.append(sentence)
            srt_content.append("")

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(srt_content))

        print(f"✓ Subtitles saved to: {output_path}")
        print(f"Total subtitle entries: {len(sentences)}")
        print(f"Estimated duration: {duration:.1f} seconds")

        return output_path

    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT timestamp format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file using ffprobe"""
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', audio_path],
                capture_output=True,
                text=True,
                check=True
            )
            return float(result.stdout.strip())
        except:
            print("Warning: ffprobe not found. Please install FFmpeg.")
            print("Using default duration of 300 seconds (5 minutes)")
            return 300.0

    def edit_video_ffmpeg(self, voiceover_path: str, image_paths: List[str], subtitle_path: str, output_path: str) -> Optional[str]:
        """Edit video using FFmpeg - 90s looped video + images for remainder"""
        print("\n=== STEP 8: Editing Video with FFmpeg ===")

        # Get voiceover duration
        voiceover_duration = self.get_audio_duration(voiceover_path)
        print(f"✓ Voiceover duration: {voiceover_duration:.2f} seconds")

        video_path = self.selected_character_video
        print(f"✓ Input video: {Path(video_path).name}")
        print(f"✓ Images to overlay: {len(image_paths)}")
        print(f"✓ Subtitles: {Path(subtitle_path).name}")
        print(f"✓ Output: {Path(output_path).name}")

        print(f"\n🎬 Building video with FFmpeg...")

        working_dir = Path(output_path).parent
        temp_looped = working_dir / "temp_looped.mp4"
        temp_concat_list = working_dir / "concat_list.txt"
        temp_concatenated = working_dir / "temp_concatenated.mp4"
        temp_with_subs = working_dir / "temp_with_subs.mp4"

        try:
            # Step 1: Create 90-second looped video
            print("  [1/6] Creating 90-second looped video...")
            loop_cmd = [
                'ffmpeg', '-y',
                '-stream_loop', '-1',  # Loop indefinitely
                '-i', video_path,
                '-t', '90',  # 90 seconds
                '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
                '-an',  # No audio
                str(temp_looped)
            ]
            subprocess.run(loop_cmd, capture_output=True, check=True)
            print("    ✓ 90-second video created")

            # Step 2: Create video segments from images
            print(f"  [2/6] Creating video segments from {len(image_paths)} images...")

            remaining_duration = voiceover_duration - 90
            if remaining_duration <= 0:
                print("    ⚠ Voiceover is 90 seconds or less, skipping images")
                image_segments = []
            else:
                duration_per_image = remaining_duration / len(image_paths)
                print(f"    Each image will display for {duration_per_image:.1f} seconds")

                image_segments = []
                for i, img_path in enumerate(image_paths, 1):
                    temp_img_video = working_dir / f"temp_image_{i}.mp4"

                    img_cmd = [
                        'ffmpeg', '-y',
                        '-loop', '1',
                        '-i', img_path,
                        '-t', str(duration_per_image),
                        '-vf', f'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black',
                        '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
                        '-pix_fmt', 'yuv420p',
                        '-an',
                        str(temp_img_video)
                    ]
                    subprocess.run(img_cmd, capture_output=True, check=True)
                    image_segments.append(temp_img_video)

                print(f"    ✓ {len(image_segments)} image segments created")

            # Step 3: Concatenate all segments
            print("  [3/6] Concatenating video segments...")

            # Create concat list
            with open(temp_concat_list, 'w', encoding='utf-8') as f:
                f.write(f"file '{temp_looped.absolute()}'\n")
                for seg in image_segments:
                    f.write(f"file '{seg.absolute()}'\n")

            concat_cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(temp_concat_list),
                '-c', 'copy',
                str(temp_concatenated)
            ]
            subprocess.run(concat_cmd, capture_output=True, check=True)
            print("    ✓ Segments concatenated")

            # Step 4: Add subtitles
            print("  [4/6] Burning in subtitles...")

            # Windows path fix for subtitles
            subtitle_path_fixed = str(Path(subtitle_path).absolute()).replace('\\', '/')
            subtitle_path_fixed = subtitle_path_fixed.replace(':', '\\\\:')

            subtitle_cmd = [
                'ffmpeg', '-y',
                '-i', str(temp_concatenated),
                '-vf', f"subtitles='{subtitle_path_fixed}':force_style='FontName=Arial,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,Outline=2,Shadow=1,MarginV=40'",
                '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
                '-c:a', 'copy',
                str(temp_with_subs)
            ]
            subprocess.run(subtitle_cmd, capture_output=True, check=True)
            print("    ✓ Subtitles burned in")

            # Step 5: Add voiceover
            print("  [5/6] Adding voiceover and exporting final video...")

            final_cmd = [
                'ffmpeg', '-y',
                '-i', str(temp_with_subs),
                '-i', voiceover_path,
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-shortest',
                str(output_path)
            ]
            subprocess.run(final_cmd, capture_output=True, check=True)
            print("    ✓ Final video exported")

            # Step 6: Cleanup
            print("  [6/6] Cleaning up temporary files...")
            temp_looped.unlink(missing_ok=True)
            temp_concat_list.unlink(missing_ok=True)
            temp_concatenated.unlink(missing_ok=True)
            temp_with_subs.unlink(missing_ok=True)
            for seg in image_segments:
                seg.unlink(missing_ok=True)
            print("    ✓ Cleanup complete")

            # Show result
            file_size = Path(output_path).stat().st_size / (1024 * 1024)
            print(f"\n✅ Video editing complete: {output_path}")
            print(f"   Duration: {voiceover_duration:.2f} seconds")
            print(f"   Size: {file_size:.2f} MB")

            return output_path

        except subprocess.CalledProcessError as e:
            print(f"✗ FFmpeg error: {e}")
            if e.stderr:
                print(f"Error details: {e.stderr.decode()}")
            return None
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    def play_video(self, video_path: str):
        """Automatically open the video in default player"""
        print(f"\n🎬 Opening video automatically...")
        try:
            if sys.platform == 'win32':
                os.startfile(video_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', video_path])
            else:  # Linux
                subprocess.run(['xdg-open', video_path])
            print("✓ Video opened in default player")
        except Exception as e:
            print(f"⚠ Could not auto-open video: {e}")
            print(f"Please open manually: {video_path}")

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by removing invalid characters"""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')

        # Replace multiple spaces with single space
        filename = ' '.join(filename.split())

        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')

        # Truncate to reasonable length
        max_length = 100
        if len(filename) > max_length:
            filename = filename[:max_length].strip()

        # Default if empty
        if not filename:
            filename = "untitled_video"

        return filename

    def run(self):
        """Main execution flow - browser automation for content, API for media"""
        try:
            print("\n" + "="*60)
            print("AI VIDEO GENERATION MACRO - BROWSER VERSION")
            print("="*60)

            # === CHARACTER SELECTION ===
            self.selected_character_folder, self.selected_character_video = self.select_character()

            # === INITIALIZE BROWSER ===
            self.init_browser()
            self.navigate_to_project()

            # === PHASE 1: GENERATE ENGLISH CONTENT (Browser) ===
            print("\n" + "="*60)
            print("📝 PHASE 1: GENERATE ALL ENGLISH CONTENT (Browser)")
            print("="*60)

            english_title = self.generate_title_browser()
            print(f"\n  [DEBUG MAIN] Returned title: '{english_title}'")
            print(f"  [DEBUG MAIN] Title type: {type(english_title)}, length: {len(english_title)}")
            time.sleep(5)

            english_description = self.generate_description_browser(english_title)
            print(f"\n  [DEBUG MAIN] Returned description: '{english_description[:100]}...'")
            time.sleep(5)

            english_premise = self.generate_premise_browser(english_title)
            time.sleep(5)

            english_script = self.generate_full_script_browser(english_title, english_premise)

            # === CREATE OUTPUT FOLDER ===
            folder_name = self.sanitize_filename(english_title)
            self.working_dir = self.base_output_dir / folder_name
            self.working_dir.mkdir(exist_ok=True)

            print(f"\n✓ Created output folder: {self.working_dir}")
            print("   All files for this video will be saved here.")

            # Save English content
            script_path = self.working_dir / "video_script_english.txt"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(f"Title: {english_title}\n\n")
                f.write(f"Description: {english_description}\n\n")
                f.write(f"Premise: {english_premise}\n\n")
                f.write(f"Script:\n{english_script}")
            print(f"✓ English script saved to: {script_path}")

            # === PHASE 2: TRANSLATE TO KOREAN (Browser) ===
            print("\n" + "="*60)
            print("🌐 PHASE 2: TRANSLATE ALL CONTENT TO KOREAN (Browser)")
            print("="*60)

            korean_title = self.translate_to_korean_browser(english_title, "title")
            time.sleep(5)

            korean_description = self.translate_to_korean_browser(english_description, "description")
            time.sleep(5)

            korean_premise = self.translate_to_korean_browser(english_premise, "premise")
            time.sleep(5)

            korean_script = self.translate_script_to_korean_browser(english_script)

            # Save Korean content
            korean_script_path = self.working_dir / "video_script_korean.txt"
            with open(korean_script_path, 'w', encoding='utf-8') as f:
                f.write(f"Title: {korean_title}\n\n")
                f.write(f"Description: {korean_description}\n\n")
                f.write(f"Premise: {korean_premise}\n\n")
                f.write(f"Script:\n{korean_script}")
            print(f"✓ Korean script saved to: {korean_script_path}")

            # === CLOSE BROWSER ===
            print("\n🌐 Closing browser...")
            self.driver.quit()
            print("✓ Browser closed")

            # === PHASE 3: GENERATE MEDIA (API + FFmpeg) ===
            print("\n" + "="*60)
            print("🎬 PHASE 3: GENERATE MEDIA ASSETS (API + FFmpeg)")
            print("="*60)

            # Generate voiceover
            voiceover_path = self.working_dir / "voiceover.mp3"
            voiceover_result = self.generate_voiceover_genaipro(korean_script, str(voiceover_path))

            if not voiceover_result:
                print("✗ Voiceover generation failed. Exiting.")
                return

            # Get voiceover duration for subtitles
            duration = self.get_audio_duration(str(voiceover_path))

            # Generate subtitles
            subtitle_path = self.working_dir / "subtitles.srt"
            self.generate_subtitles(korean_script, str(subtitle_path), duration)

            # Load images
            print("\n=== STEP 6: Loading Images from Character Folder ===")
            num_images = self.config.get("num_images", 4)
            image_paths = self.get_character_images(num_images)

            # Generate video
            final_video_path = self.working_dir / "final_video.mp4"
            video_result = self.edit_video_ffmpeg(
                str(voiceover_path),
                image_paths,
                str(subtitle_path),
                str(final_video_path)
            )

            if not video_result:
                print("✗ Video editing failed. Exiting.")
                return

            # === COMPLETION ===
            print("\n" + "="*60)
            print("✅ VIDEO GENERATION COMPLETE!")
            print("="*60)
            print(f"English Title: {english_title}")
            print(f"Korean Title: {korean_title}")
            print(f"Video: {final_video_path}")
            print(f"\nAll files are in: {self.working_dir}")

            # Auto-play video
            self.play_video(str(final_video_path))

        except KeyboardInterrupt:
            print("\n\n⚠ Process interrupted by user")
            if self.driver:
                self.driver.quit()
        except Exception as e:
            print(f"\n✗ Error occurred: {e}")
            import traceback
            traceback.print_exc()
            if self.driver:
                self.driver.quit()

def main():
    """Main entry point"""
    macro = VideoGenerationMacroBrowser()
    macro.run()

if __name__ == "__main__":
    main()
