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

# Import local translator for offline translation
try:
    from local_translator import LocalTranslator
    LOCAL_TRANSLATOR_AVAILABLE = True
except ImportError:
    LOCAL_TRANSLATOR_AVAILABLE = False
    print("Note: local_translator not available, will use Claude API")

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
        self.character_name = None

        # Browser
        self.driver = None

        # Initialize local translator (loads once, reused for all translations)
        if LOCAL_TRANSLATOR_AVAILABLE:
            print("\nInitializing local translator...")
            self.local_translator = LocalTranslator()
            print("✓ Local translator ready (will use offline translation)")
        else:
            self.local_translator = None
            print("\n⚠ Local translator not available - will use Claude API (uses tokens)")

        print(f"\nUsing Claude Project: {self.project_id}")
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
        print("\nInitializing browser...")

        chrome_options = Options()

        # Create a dedicated Chrome profile directory for this automation
        # This keeps you logged in between runs WITHOUT conflicting with your main Chrome
        automation_profile_dir = Path("./chrome_automation_profile").absolute()
        automation_profile_dir.mkdir(exist_ok=True)

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
            print("Browser ready")
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
        print("\nOpening Claude Project...")
        self.driver.get(self.project_url)
        time.sleep(5)  # Wait for page load

        # Check if we're logged in
        try:
            # Look for chat input (indicates we're logged in and in project)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
            )
            print("Project loaded\n")
        except TimeoutException:
            print("\nNot logged in - please log in manually in the browser window")
            print("Press Enter once you see the chat interface")
            input()

    def send_prompt_and_wait(self, prompt: str, wait_time: int = 60,
                             stabilization_wait: int = 20, max_stability_checks: int = 15,
                             stability_threshold: int = 5, stability_check_interval: int = 5,
                             previous_content_to_filter: str = "") -> str:
        """
        Send a prompt to Claude and wait for response

        Args:
            prompt: The prompt to send
            wait_time: Max time to wait for generation to complete
            stabilization_wait: Seconds to wait after Stop button disappears (default 20)
            max_stability_checks: Max number of stability checks (default 15)
            stability_threshold: Number of consecutive stable checks required (default 5)
            stability_check_interval: Seconds to wait between stability checks (default 5)
            previous_content_to_filter: Previous content to filter out from extraction (e.g., description text)
        """
        try:
            # Retry logic for DOM issues
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Find chat input
                    chat_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
                    )
                    time.sleep(1)

                    # Click to focus - try JavaScript if regular click is intercepted
                    try:
                        chat_input.click()
                    except Exception as click_error:
                        # Click intercepted - try to close any overlays by pressing Escape
                        if "intercepted" in str(click_error).lower():
                            try:
                                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                                time.sleep(0.5)
                            except:
                                pass
                            # Use JavaScript to click instead
                            self.driver.execute_script("arguments[0].focus(); arguments[0].click();", chat_input)
                        else:
                            raise
                    time.sleep(0.5)

                    # Use JavaScript to set the text content directly (much more reliable than typing)
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
                    # Method 1: Try keyboard shortcut
                    try:
                        chat_input.click()
                        time.sleep(0.3)
                        chat_input.send_keys(Keys.CONTROL + Keys.RETURN)
                    except:
                        # Method 2: Find and click the send button
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
                        except:
                            pass

                    time.sleep(2)
                    break

                except Exception as e:
                    error_msg = str(e).lower()
                    if ("stale element" in error_msg or "no such element" in error_msg) and attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    else:
                        raise  # Re-raise if not a retryable error or out of retries

            # Wait for response to start appearing
            print("  Waiting for response...")
            time.sleep(3)

            # Wait for "Stop generating" button to disappear (indicates completion)
            max_wait = wait_time
            start_time = time.time()
            generation_detected = False

            while time.time() - start_time < max_wait:
                try:
                    # Check if still generating
                    stop_button = self.driver.find_elements(By.XPATH, "//button[contains(., 'Stop')]")

                    if stop_button and not generation_detected:
                        generation_detected = True

                    if not stop_button and generation_detected:
                        break
                    elif not stop_button and not generation_detected:
                        # Check if response already appeared (fast response)
                        messages = self.driver.find_elements(By.CSS_SELECTOR, "div[data-test-render-count]")
                        if len(messages) > 0:
                            break
                except:
                    pass

                time.sleep(2)

            # CRITICAL: Wait for response to fully stabilize
            print("  Stabilizing...")
            time.sleep(stabilization_wait)

            # Check if the LATEST MESSAGE is still changing (wait until stable)
            stable_count = 0
            last_message_length = 0

            for stability_check in range(max_stability_checks):
                try:
                    # Get the latest message text length (not entire page)
                    latest_message_js = """
                    var selectors = [
                        'div[data-test-render-count]',
                        'div[class*="Message"]',
                        'div[class*="message"]',
                        'div[role="article"]'
                    ];

                    var latestMsg = null;
                    var maxLength = 0;

                    for (var i = 0; i < selectors.length; i++) {
                        var elements = document.querySelectorAll(selectors[i]);
                        if (elements.length > 0) {
                            var lastElement = elements[elements.length - 1];
                            var text = lastElement.innerText || lastElement.textContent || '';
                            if (text.length > maxLength) {
                                maxLength = text.length;
                                latestMsg = text;
                            }
                        }
                    }

                    return latestMsg ? latestMsg.length : 0;
                    """
                    current_message_length = self.driver.execute_script(latest_message_js)

                    if current_message_length == last_message_length and current_message_length > 0:
                        stable_count += 1
                        if stable_count >= stability_threshold:
                            print(f"  Response stable ({current_message_length} chars, {stable_count} checks)")
                            break
                    else:
                        if current_message_length > last_message_length:
                            print(f"  Still generating... ({current_message_length} chars)")
                        stable_count = 0

                    last_message_length = current_message_length
                    time.sleep(stability_check_interval)
                except Exception as e:
                    print(f"  Stability check error: {e}")
                    time.sleep(5)

            # Final wait for DOM to settle and any final rendering
            print("  Final stabilization...")
            time.sleep(8)  # Increased from 5 to 8 seconds for extra safety

            # Use JavaScript to extract response - MUCH more reliable!
            response_text = ""
            extraction_attempts = 5

            for extract_attempt in range(extraction_attempts):
                if extract_attempt > 0:
                    time.sleep(3)

                # JavaScript approach - scan the DOM and extract last message
                # Only filter out the prompt at JS level (don't filter previous content here)
                prompt_start = prompt[:50].replace("'", "\\'").replace("\n", " ")

                js_extract_script = f"""
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
                var promptStart = '{prompt_start}';

                for (var i = 0; i < selectors.length; i++) {{
                    var elements = document.querySelectorAll(selectors[i]);
                    for (var j = 0; j < elements.length; j++) {{
                        // Scroll element into view to ensure all content is loaded (for lazy-loading)
                        try {{
                            elements[j].scrollIntoView({{behavior: 'instant', block: 'nearest'}});
                        }} catch (e) {{}}

                        // Get text using multiple methods and pick the longest
                        var text1 = elements[j].innerText || '';
                        var text2 = elements[j].textContent || '';
                        var text = text1.length > text2.length ? text1 : text2;

                        // CRITICAL: Skip if this contains the user's prompt
                        if (text && text.indexOf(promptStart) !== -1) {{
                            continue;
                        }}

                        if (text && text.length > 20) {{
                            allMessages.push({{
                                text: text.trim(),
                                length: text.length,
                                selector: selectors[i],
                                index: j
                            }});
                        }}
                    }}
                }}

                // Return the LONGEST message (likely the full response)
                if (allMessages.length > 0) {{
                    // Sort by length descending to get longest message
                    allMessages.sort(function(a, b) {{ return b.length - a.length; }});
                    var longestMsg = allMessages[0];
                    return JSON.stringify({{
                        success: true,
                        text: longestMsg.text,
                        method: longestMsg.selector,
                        count: allMessages.length
                    }});
                }}

                return JSON.stringify({{success: false, text: '', count: 0}});
                """

                try:
                    result_json = self.driver.execute_script(js_extract_script)
                    result = json.loads(result_json)

                    if result.get('success') and result.get('text'):
                        response_text = result['text'].strip()
                        break

                except:
                    pass

                # Fallback: Try direct Selenium element finding
                if not response_text:
                    all_divs = self.driver.find_elements(By.TAG_NAME, "div")

                    for div in reversed(all_divs):
                        try:
                            text = div.text.strip()
                            # REMOVED 5000 char limit - scripts can be 40,000+ characters!
                            if text and len(text) > 20:
                                # Don't include if it contains the prompt
                                if prompt[:30] not in text:
                                    response_text = text
                                    break
                        except:
                            continue

                if response_text:
                    break  # Got a response, stop retrying

            if response_text:
                print(f"  Response captured ({len(response_text)} chars)\n")
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

    def extract_generated_content(self, response: str, extract_all: bool = False, filter_hashtags: bool = False, filter_previous_content: str = "") -> str:
        """
        Extract the actual generated content from Claude's response,
        filtering out thinking, searching, and explanatory text.

        Args:
            response: The raw response from Claude
            extract_all: If True, return ALL content lines (for scripts).
                        If False, return only the last line (for titles/descriptions).
            filter_hashtags: If True, filter out lines containing hashtags (for premises).
                           If False, keep hashtags (for descriptions).
            filter_previous_content: Previous content to filter out (e.g., description text when extracting premise).
        """
        # Remove common Claude prefixes/explanations
        lines = response.split('\n')

        # Filter out lines that are clearly Claude's internal process or call-to-action
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
            'results',
            'Show working file',
            'TEXT',
            'relevant sections',
            'Reading the',
            'Reading another',
            'Now I understand',
            '👉',  # Filter out emoji-based call-to-actions
            'Subscribe',
            'turn on notifications',
            'Drop a comment',
            'never miss'
        ]

        # Collect candidate lines (not process text)
        candidates = []

        # If we have previous content to filter, split it into lines for comparison
        previous_lines = []
        if filter_previous_content:
            previous_lines = [l.strip() for l in filter_previous_content.split('\n') if l.strip()]

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

            # Skip hashtag lines only if filter_hashtags is True (for premises)
            if filter_hashtags and (line_stripped.startswith('#') or (line_stripped.count('#') > 2)):
                continue

            # CRITICAL: Skip lines that match previous content (e.g., description when extracting premise)
            if filter_previous_content:
                # Check if this line matches any line from previous content
                is_previous_content = False
                for prev_line in previous_lines:
                    # Check if line is similar to previous content (allow some flexibility)
                    if len(prev_line) > 20 and prev_line[:50] in line_stripped:
                        is_previous_content = True
                        break
                    if len(line_stripped) > 20 and line_stripped[:50] in prev_line:
                        is_previous_content = True
                        break

                if is_previous_content:
                    continue

            if not is_process and len(line_stripped) > 15:
                candidates.append(line_stripped)

        # Return based on extract_all parameter
        if candidates:
            if extract_all:
                # For scripts: return ALL candidate lines joined together
                result = '\n\n'.join(candidates)
                return result
            else:
                # For titles/descriptions: return only the LAST line
                result = candidates[-1].strip('"\'')
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
                        return first_line

        # Last resort: Return the whole response cleaned up
        return response.strip().strip('"\'')

    def generate_title_browser(self) -> str:
        """Generate video title using Claude.ai Project with approval loop"""
        print("\n=== STEP 1: Generating Video Title ===")

        while True:
            # Use character name if available, otherwise fall back to "a doctor"
            host_identity = f"The host is {self.character_name}" if self.character_name else "The host is a doctor"

            prompt = f"""Generate a YouTube video title in PURE ENGLISH.

Use the "korean video titles.txt" file in this project as reference for:
- Topics to cover (HEALTH and LIFESTYLE for seniors 60+, NO FINANCE)
- Title structure and format
- Tone and urgency level
- Use of numbers and specific details

{host_identity}, so focus on health and lifestyle topics only.

LANGUAGE REQUIREMENTS:
- Write ENTIRELY in ENGLISH - NO Korean words or phrases
- Use ONLY English vocabulary

Create ONE title in pure English following that style.

JUST OUTPUT THE TITLE. No explanations."""

            response = self.send_prompt_and_wait(
                prompt,
                wait_time=90,
                stabilization_wait=25,
                max_stability_checks=20
            )

            # Parse the response to extract JUST the title (not Claude's thinking/searching)
            title = self.extract_generated_content(response)

            print(f"\nGenerated Title:\n{title}\n")

            # Get user approval
            choice = input("Options: [a]pprove, [d]eny (regenerate), [m]odify, [p]aste: ").lower().strip()

            if choice == 'a':
                print(f"\nTitle approved\n")
                return title
            elif choice == 'd':
                print("\nRegenerating...")
                continue
            elif choice == 'm':
                modification = input("\nWhat would you like to change? ")
                print("\nModifying...")

                modify_prompt = f"""Current title: "{title}"

User wants this change: {modification}

Generate the modified title. JUST OUTPUT THE NEW TITLE."""

                response = self.send_prompt_and_wait(
                    modify_prompt,
                    wait_time=90,
                    stabilization_wait=25,
                    max_stability_checks=20
                )
                title = self.extract_generated_content(response)
                print(f"\nModified Title:\n{title}\n")

                # Ask for approval again
                if input("Approve this version? [y/n]: ").lower() == 'y':
                    print("\nTitle approved\n")
                    return title
                else:
                    print("\nStarting over...")
                    continue
            elif choice == 'p':
                print("\nPaste the correct title below:")
                pasted_title = input("Title: ").strip()
                if pasted_title:
                    print(f"\nPasted Title:\n{pasted_title}\n")
                    if input("Use this title? [y/n]: ").lower() == 'y':
                        print("\nTitle approved\n")
                        return pasted_title
                    else:
                        print("\nCancelled...")
                        continue
                else:
                    print("\nNo title provided, starting over...")
                    continue
            else:
                print("Invalid choice. Please enter 'a', 'd', 'm', or 'p'")
                continue

    def generate_description_browser(self, title: str) -> str:
        """Generate video description using Claude.ai Project with approval loop"""
        print("\n=== STEP 2: Generating Video Description ===")

        while True:
            prompt = f"""Generate a DETAILED, COMPREHENSIVE video description for this title: "{title}"

Use the "korean video descriptions.txt" file in this project as reference for:
- Description format and structure
- Tone and urgency
- How to create curiosity
- Call to action style

REQUIREMENTS:
- Write a LONG, DETAILED description (aim for 500-1000+ words)
- CRITICAL: You MUST keep the description under 5000 characters total
- Write a complete, compelling description that naturally fits within this limit
- DO NOT exceed 5000 characters - plan your content to fit within this constraint
- Include multiple paragraphs
- Explain what viewers will learn
- Build curiosity and urgency
- Include specific benefits and takeaways
- Use emotional hooks
- End with strong call to action

LANGUAGE REQUIREMENTS - CRITICAL:
- Write ENTIRELY in ENGLISH language only
- NO Korean words, phrases, or greetings
- Use ONLY English vocabulary throughout
- NO fabricated quotes or testimonials

Write in pure English following that style.

JUST OUTPUT THE DESCRIPTION IN PURE ENGLISH. Make it DETAILED and COMPREHENSIVE, but stay under 5000 characters."""

            response = self.send_prompt_and_wait(
                prompt,
                wait_time=180,  # 3 minutes for long descriptions
                stabilization_wait=30,  # Extra long initial wait
                max_stability_checks=30  # More checks to ensure completion
            )
            description = self.extract_generated_content(response, extract_all=True, filter_hashtags=False)  # Get full description WITH hashtags

            # Show character count
            char_count = len(description)
            print(f"\nGenerated Description ({char_count} characters):\n{description}\n")

            if char_count > 5000:
                print(f"⚠ WARNING: Description is {char_count} characters (exceeds 5000 limit)\n")

            choice = input("Options: [a]pprove, [d]eny (regenerate), [m]odify, [p]aste: ").lower().strip()

            if choice == 'a':
                print("\nDescription approved\n")
                return description
            elif choice == 'd':
                print("\nRegenerating...")
                continue
            elif choice == 'm':
                modification = input("\nWhat would you like to change? ")
                modify_prompt = f"""Current description: "{description}"

User wants this change: {modification}

Generate the modified description. CRITICAL: Keep it under 5000 characters. JUST OUTPUT THE NEW DESCRIPTION."""

                response = self.send_prompt_and_wait(
                    modify_prompt,
                    wait_time=180,
                    stabilization_wait=30,
                    max_stability_checks=30
                )
                description = self.extract_generated_content(response, extract_all=True, filter_hashtags=False)  # Get full description WITH hashtags
                char_count = len(description)
                print(f"\nModified Description ({char_count} characters):\n{description}\n")

                if char_count > 5000:
                    print(f"⚠ WARNING: Description is {char_count} characters (exceeds 5000 limit)\n")

                if input("Approve this version? [y/n]: ").lower() == 'y':
                    print("\nDescription approved\n")
                    return description
                else:
                    print("\nStarting over...")
                    continue
            elif choice == 'p':
                print("\nPaste the correct description below (press Enter twice when done):")
                print("Description:")
                lines = []
                while True:
                    line = input()
                    if line == "" and len(lines) > 0 and lines[-1] == "":
                        lines.pop()  # Remove the last empty line
                        break
                    lines.append(line)
                pasted_description = "\n".join(lines).strip()

                if pasted_description:
                    char_count = len(pasted_description)
                    print(f"\nPasted Description ({char_count} characters):\n{pasted_description}\n")
                    if char_count > 5000:
                        print(f"⚠ WARNING: Description is {char_count} characters (exceeds 5000 limit)\n")
                    if input("Use this description? [y/n]: ").lower() == 'y':
                        print("\nDescription approved\n")
                        return pasted_description
                    else:
                        print("\nCancelled...")
                        continue
                else:
                    print("\nNo description provided, starting over...")
                    continue
            else:
                print("Invalid choice. Please enter 'a', 'd', 'm', or 'p'")
                continue

    def generate_premise_browser(self, title: str, description: str = "") -> str:
        """Generate video premise using Claude.ai Project with approval loop"""
        print("\n=== STEP 3: Generating Video Premise ===")

        while True:
            # Use character name if available
            expert_intro = f"Introduce {self.character_name}" if self.character_name else "Introduce the expert/authority"

            prompt = f"""Generate a video premise based on this title: "{title}"

Write 2-3 sentences in PURE ENGLISH that:
- {expert_intro} with years of experience
- State the main discovery/solution with specific details
- Preview the key benefits viewers will learn

LANGUAGE REQUIREMENTS:
- Write ENTIRELY in ENGLISH - NO Korean words or phrases
- NO fabricated quotes or testimonials
- Describe the premise directly without quotation marks

JUST OUTPUT THE PREMISE IN PURE ENGLISH."""

            response = self.send_prompt_and_wait(
                prompt,
                wait_time=90,
                stabilization_wait=25,
                max_stability_checks=20,
                previous_content_to_filter=""  # Don't filter at JS level - filter at content level instead
            )
            premise = self.extract_generated_content(response, extract_all=True, filter_hashtags=False)  # Extract ALL lines for 2-3 sentence premise

            print(f"\nGenerated Premise:\n{premise}\n")

            choice = input("Options: [a]pprove, [d]eny (regenerate), [m]odify, [p]aste: ").lower().strip()

            if choice == 'a':
                print("\nPremise approved\n")
                return premise
            elif choice == 'd':
                print("\nRegenerating...")
                continue
            elif choice == 'm':
                modification = input("\nWhat would you like to change? ")
                modify_prompt = f"""Current premise: "{premise}"

User wants this change: {modification}

Generate the modified premise. JUST OUTPUT THE NEW PREMISE."""

                response = self.send_prompt_and_wait(
                    modify_prompt,
                    wait_time=90,
                    stabilization_wait=25,
                    max_stability_checks=20,
                    previous_content_to_filter=""  # Don't filter at JS level - filter at content level instead
                )
                premise = self.extract_generated_content(response, extract_all=True, filter_hashtags=False)  # Extract ALL lines for 2-3 sentence premise
                print(f"\nModified Premise:\n{premise}\n")

                if input("Approve this version? [y/n]: ").lower() == 'y':
                    print("\nPremise approved\n")
                    return premise
                else:
                    print("\nStarting over...")
                    continue
            elif choice == 'p':
                print("\nPaste the correct premise below (press Enter twice when done):")
                print("Premise:")
                lines = []
                while True:
                    line = input()
                    if line == "" and len(lines) > 0 and lines[-1] == "":
                        lines.pop()  # Remove the last empty line
                        break
                    lines.append(line)
                pasted_premise = "\n".join(lines).strip()

                if pasted_premise:
                    print(f"\nPasted Premise:\n{pasted_premise}\n")
                    if input("Use this premise? [y/n]: ").lower() == 'y':
                        print("\nPremise approved\n")
                        return pasted_premise
                    else:
                        print("\nCancelled...")
                        continue
                else:
                    print("\nNo premise provided, starting over...")
                    continue
            else:
                print("Invalid choice. Please enter 'a', 'd', 'm', or 'p'")
                continue

    def generate_script_segment_browser(self, title: str, premise: str, segment_num: int, total_segments: int) -> str:
        """Generate one segment of the script using Claude.ai Project"""
        print(f"  Generating segment {segment_num}/{total_segments}...")

        # Use character name if available
        doctor_identity = f"The doctor is {self.character_name}, from KOREA" if self.character_name else "The doctor is from KOREA"

        prompt = f"""Write script segment {segment_num} of {total_segments} for this video.

Title: "{title}"
Premise: {premise}

Target: {6500 // total_segments} words for this segment

SEGMENT FOCUS:
{self._get_segment_focus(segment_num, total_segments)}

WRITING STYLE - Reference the Korean .txt script files in this project:
- Use their dramatic storytelling style
- Copy their structure (opening hooks, patient stories, expert credibility, solutions, timelines)
- Match their tone for seniors (60+)
- Include specific numbers, ages, measurements like they do
- Use "you" language and conversational style
- Scientific explanations in simple terms

CRITICAL - KOREAN CONTEXT ONLY:
- {doctor_identity} (not America)
- ALL patient stories must be Korean patients with Korean names (Kim, Park, Lee, Choi, etc.)
- ALL locations must be in Korea (Seoul, Busan, hospitals in Korea, etc.)
- Use Korean cultural context and references
- Mention Korean healthcare system when relevant
- NO American names, cities, or locations
- The doctor practices in Korea and treats Korean patients

LANGUAGE REQUIREMENTS - CRITICAL:
- Write ENTIRELY in ENGLISH language only
- DO NOT include ANY Korean words, phrases, or greetings
- DO NOT mix Korean and English (no "여러분", "안녕하세요", etc.)
- Use ONLY English vocabulary throughout the entire script
- Korean context (names, places) is fine, but ALL text must be in English

NO FABRICATED CONTENT:
- DO NOT invent fake quotes or testimonials
- DO NOT create fabricated patient dialogue
- Patient STORIES are okay, but NO direct quotes
- Describe what happened without using quotation marks

JUST WRITE THE SCRIPT SEGMENT IN PURE ENGLISH. NO explanations, NO "here's the segment", JUST THE SCRIPT."""

        # EXTRA LONG waits for script segments (they're 1625+ words)
        response = self.send_prompt_and_wait(
            prompt,
            wait_time=300,  # 5 minutes max wait (up from 4)
            stabilization_wait=45,  # 45 seconds initial stabilization (up from 30)
            max_stability_checks=30  # 30 checks = up to 150 more seconds (up from 20)
        )
        segment_text = self.extract_generated_content(response, extract_all=True)  # Get ALL lines for scripts

        word_count = len(segment_text.split())
        print(f"  Segment {segment_num} complete (~{word_count} words)\n")
        return segment_text

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
        print("\n=== STEP 4: Generating Full Video Script ===")
        print("Target: 6000-7000 words\n")

        num_segments = 4
        segments = []

        for i in range(1, num_segments + 1):
            segment = self.generate_script_segment_browser(title, premise, i, num_segments)
            segments.append(segment)

            # Wait between segments to avoid rate limits
            if i < num_segments:
                time.sleep(10)

        # Combine segments
        full_script = "\n\n".join(segments)
        total_words = len(full_script.split())

        print(f"Total word count: {total_words}")

        # Adjust if needed
        if total_words < 6000:
            print(f"Below target - generating additional content...")
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

            additional = self.send_prompt_and_wait(
                additional_prompt,
                wait_time=240,
                stabilization_wait=35,
                max_stability_checks=30
            )
            full_script += "\n\n" + additional
            total_words = len(full_script.split())
            print(f"Updated word count: {total_words}")

        if total_words > 7000:
            print(f"Trimming to ~7000 words...")
            words = full_script.split()
            trimmed_text = " ".join(words[:7000])

            # Find the last complete sentence (ending with . ! or ?)
            last_period = max(
                trimmed_text.rfind('.'),
                trimmed_text.rfind('!'),
                trimmed_text.rfind('?')
            )

            if last_period > 0:
                # Keep text up to and including the sentence-ending punctuation
                full_script = trimmed_text[:last_period + 1]
                total_words = len(full_script.split())
            else:
                # Fallback: just use 7000 words if no sentence ending found
                full_script = trimmed_text
                total_words = 7000

        print(f"\nFinal script: {total_words} words")

        # Show preview and get approval
        while True:
            print("\nScript Preview (start and end):")

            # Split into sentences and show first + last
            import re
            sentences = re.split(r'(?<=[.!?])\s+', full_script)
            sentences = [s.strip() for s in sentences if s.strip()]

            # Get first 3 and last 3 sentences
            num_preview_sentences = 3
            if len(sentences) > num_preview_sentences * 2:
                first_sentences = ' '.join(sentences[:num_preview_sentences])
                last_sentences = ' '.join(sentences[-num_preview_sentences:])
                print(f"{first_sentences}")
                print("\n[... middle of script ...]\n")
                print(f"{last_sentences}\n")
            else:
                # If script is short, just show it all
                print(full_script + "\n")

            # Show last 20 words for validation
            words = full_script.strip().split()
            last_20_words = ' '.join(words[-20:])
            print(f"Last 20 words: ...{last_20_words}\n")

            choice = input("Options: [a]pprove, [d]eny (regenerate all), [m]odify, [p]aste: ").lower().strip()

            if choice == 'a':
                print("\nScript approved\n")
                return full_script
            elif choice == 'd':
                print("\nRegenerating entire script...")
                # Recursive call to regenerate
                return self.generate_full_script_browser(title, premise)
            elif choice == 'm':
                modification = input("\nWhat would you like to change in the script? ")
                print("\nModifying script...")

                modify_prompt = f"""Current script ({total_words} words):

{full_script[:2000]}... [script continues]

User wants this change: {modification}

Generate the modified FULL script incorporating this change. Keep it 6000-7000 words.

JUST OUTPUT THE COMPLETE MODIFIED SCRIPT."""

                response = self.send_prompt_and_wait(
                    modify_prompt,
                    wait_time=300,
                    stabilization_wait=40,
                    max_stability_checks=35
                )
                full_script = response.strip()
                total_words = len(full_script.split())

                print(f"\nModified script: {total_words} words")
                print("\nModified Script Preview:")
                print(full_script[:500] + "...\n")

                if input("Approve this version? [y/n]: ").lower() == 'y':
                    print("\nScript approved\n")
                    return full_script
                else:
                    print("\nContinuing with modifications...")
                    continue
            elif choice == 'p':
                print("\nFor long scripts, you can:")
                print("1. Type/paste directly (press Enter twice when done)")
                print("2. Provide a file path to read from")
                choice_method = input("\nChoose method [t]ype or [f]ile: ").lower().strip()

                if choice_method == 't':
                    print("\nPaste the correct script below (press Enter twice when done):")
                    print("Script:")
                    lines = []
                    while True:
                        line = input()
                        if line == "" and len(lines) > 0 and lines[-1] == "":
                            lines.pop()  # Remove the last empty line
                            break
                        lines.append(line)
                    pasted_script = "\n".join(lines).strip()
                elif choice_method == 'f':
                    file_path = input("\nEnter file path: ").strip()
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            pasted_script = f.read().strip()
                        print(f"✓ Loaded script from file ({len(pasted_script.split())} words)")
                    except Exception as e:
                        print(f"✗ Error reading file: {e}")
                        print("\nStarting over...")
                        continue
                else:
                    print("Invalid choice. Starting over...")
                    continue

                if pasted_script:
                    script_words = len(pasted_script.split())
                    print(f"\nPasted Script ({script_words} words)")
                    print(f"Preview: {pasted_script[:300]}...\n")
                    if input("Use this script? [y/n]: ").lower() == 'y':
                        print("\nScript approved\n")
                        return pasted_script
                    else:
                        print("\nCancelled...")
                        continue
                else:
                    print("\nNo script provided, starting over...")
                    continue
            else:
                print("Invalid choice. Please enter 'a', 'd', 'm', or 'p'")
                continue

    def translate_to_korean_browser(self, text: str, content_type: str = "text") -> str:
        """Translate text to Korean using ONLY local Opus-MT translator (offline, no API calls)"""
        if not self.local_translator:
            raise RuntimeError("Local Opus-MT translator not available! Cannot translate without it.")

        # Use local translator ONLY (offline, no API calls)
        return self.local_translator.translate(text, content_type)

    def translate_script_to_korean_browser(self, script_file_path: str) -> str:
        """Translate full script to Korean using ONLY local Opus-MT translator (offline, no API calls)"""
        print("\n=== Translating Full Script to Korean ===")

        if not self.local_translator:
            raise RuntimeError("Local Opus-MT translator not available! Cannot translate without it.")

        # Read the English script from file
        with open(script_file_path, 'r', encoding='utf-8') as f:
            english_script = f.read()

        # Use local translator with chunking (offline, no API calls, smaller chunks for better quality)
        print("  (Using local Opus-MT translator - no API calls!)")
        korean_script = self.local_translator.translate_in_chunks(english_script, chunk_size=500, label="script")

        # Show character count and word estimate
        char_count = len(korean_script)
        word_estimate = char_count // 2  # Korean characters are roughly 2 chars per word
        print(f"Script translated: {char_count} chars (~{word_estimate} Korean chars)\n")

        # Warning if translation seems too short
        if char_count < 15000:
            print(f"⚠ WARNING: Translation seems short ({char_count} chars). Expected ~20,000+ for full script.\n")

        return korean_script

    # === CHARACTER SELECTION ===

    def select_character(self) -> Tuple[str, str, Optional[str]]:
        """Let user select which character to use - returns (folder, video_file, character_name)"""
        characters_base = Path(self.config.get("characters_base_path", "./characters"))

        if not characters_base.exists():
            print(f"Error: Characters folder not found: {characters_base}")
            sys.exit(1)

        # Find all character folders
        character_folders = [f for f in characters_base.iterdir() if f.is_dir()]

        if not character_folders:
            print(f"Error: No character folders found in {characters_base}")
            sys.exit(1)

        print("\n" + "="*50)
        print("CHARACTER SELECTION")
        print(f"\nFound {len(character_folders)} character(s):\n")

        for i, folder in enumerate(character_folders, 1):
            # Check for video file
            video_files = list(folder.glob("*.mp4"))
            has_video = "✓" if video_files else "✗"

            # Count images
            image_files = list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg")) + \
                         list(folder.glob("*.png")) + list(folder.glob("*.webp"))
            num_images = len(image_files)

            print(f"{i}. {folder.name} - Video: {has_video} | Images: {num_images}")

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

        # Read character name from character_name.txt
        character_name_file = selected_folder / "character_name.txt"
        character_name = None
        if character_name_file.exists():
            try:
                with open(character_name_file, 'r', encoding='utf-8') as f:
                    character_name = f.read().strip()
                print(f"\nSelected: {selected_folder.name}")
                print(f"Character: {character_name}")
            except:
                print(f"\nSelected: {selected_folder.name}")
        else:
            print(f"\nSelected: {selected_folder.name}")

        return str(selected_folder), str(video_file), character_name

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

        print(f"\nSelected {num_to_select} images from {len(image_files)} available")

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

        print(f"\nGenerating voiceover ({len(korean_script)} chars)...")
        print("This may take a few minutes...")

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
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            task_data = response.json()
            task_id = task_data.get("id")

            print(f"Task created: {task_id}")

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

                if progress % 20 == 0 or status == "completed":  # Only show every 20%
                    print(f"Progress: {progress}%")

                if status == "completed":
                    result_url = task_info.get("result")

                    if not result_url:
                        print("Error: No result URL")
                        return None

                    # Fix relative URL if needed
                    if not result_url.startswith('http'):
                        result_url = f"https://genaipro.vn{result_url}"

                    print("Downloading...")

                    # Download
                    audio_response = requests.get(result_url)
                    audio_response.raise_for_status()

                    with open(output_path, 'wb') as f:
                        f.write(audio_response.content)

                    file_size = Path(output_path).stat().st_size / (1024 * 1024)
                    print(f"Voiceover complete ({file_size:.2f} MB)\n")

                    return output_path

                elif status == "failed":
                    error = task_info.get("error", "Unknown error")
                    print(f"Task failed: {error}")
                    return None

            print("Task timed out after 15 minutes")
            return None

        except Exception as e:
            print(f"Error generating voiceover: {e}")
            return None

    def generate_subtitles(self, korean_script: str, output_path: str, duration: float = 300.0) -> str:
        """Generate SRT subtitle file from Korean script"""
        print("\n=== Generating Subtitles ===")

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

        print(f"Subtitles created ({len(sentences)} entries, {duration:.1f}s)\n")

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
        print("\n=== STEP 8: Editing Video ===")

        # Get voiceover duration
        voiceover_duration = self.get_audio_duration(voiceover_path)
        print(f"Duration: {voiceover_duration:.2f}s")
        print(f"Images: {len(image_paths)}\n")

        # IMPORTANT: Resolve all paths to absolute before os.chdir() to avoid path duplication
        working_dir = Path(output_path).parent.resolve()
        temp_looped = (working_dir / "temp_looped.mp4").resolve()
        temp_concat_list = (working_dir / "concat_list.txt").resolve()
        temp_concatenated = (working_dir / "temp_concatenated.mp4").resolve()
        temp_with_subs = (working_dir / "temp_with_subs.mp4").resolve()

        try:
            # Step 1: Create boomerang (ping-pong) effect for the talking person video
            temp_forward = (working_dir / "temp_forward.mp4").resolve()
            temp_reverse = (working_dir / "temp_reverse.mp4").resolve()
            temp_pingpong = (working_dir / "temp_pingpong.mp4").resolve()
            pingpong_list = (working_dir / "pingpong_list.txt").resolve()

            print("[1/7] Creating boomerang effect...")

            # Create forward version (no audio)
            forward_cmd = [
                'ffmpeg', '-y',
                '-i', self.selected_character_video,
                '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
                '-an',  # No audio
                str(temp_forward)
            ]
            subprocess.run(forward_cmd, capture_output=True, check=True)

            # Create reverse version
            reverse_cmd = [
                'ffmpeg', '-y',
                '-i', self.selected_character_video,
                '-vf', 'reverse',
                '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
                '-an',  # No audio
                str(temp_reverse)
            ]
            subprocess.run(reverse_cmd, capture_output=True, check=True)

            # Concatenate forward + reverse to create ping-pong effect
            with open(pingpong_list, 'w', encoding='utf-8') as f:
                f.write(f"file '{temp_forward}'\n")
                f.write(f"file '{temp_reverse}'\n")

            pingpong_cmd = [
                'ffmpeg', '-y',
                '-f', 'concat', '-safe', '0',
                '-i', str(pingpong_list),
                '-c', 'copy',
                str(temp_pingpong)
            ]
            subprocess.run(pingpong_cmd, capture_output=True, check=True)

            # Step 2: Loop the boomerang video to 90 seconds
            print("[2/7] Looping boomerang to 90s...")
            loop_cmd = [
                'ffmpeg', '-y',
                '-stream_loop', '-1',  # Loop indefinitely
                '-i', str(temp_pingpong),
                '-t', '90',  # 90 seconds
                '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
                '-an',  # No audio
                str(temp_looped)
            ]
            subprocess.run(loop_cmd, capture_output=True, check=True)

            # Step 3: Create video segments from images
            print(f"[3/7] Creating image segments...")

            remaining_duration = voiceover_duration - 90
            if remaining_duration <= 0:
                image_segments = []
            else:
                duration_per_image = remaining_duration / len(image_paths)

                image_segments = []
                for i, img_path in enumerate(image_paths, 1):
                    temp_img_video = (working_dir / f"temp_image_{i}.mp4").resolve()

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

            # Step 4: Concatenate all segments
            print("[4/7] Concatenating segments...")

            # Create concat list
            with open(temp_concat_list, 'w', encoding='utf-8') as f:
                f.write(f"file '{temp_looped}'\n")
                for seg in image_segments:
                    f.write(f"file '{seg}'\n")

            concat_cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(temp_concat_list),
                '-c', 'copy',
                str(temp_concatenated)
            ]
            subprocess.run(concat_cmd, capture_output=True, check=True)

            # Step 5: Add subtitles
            print("[5/7] Burning subtitles...")

            # Use a different approach: copy subtitles to working dir with simple name to avoid path escaping issues
            simple_subtitle_path = (working_dir / "subs.srt").resolve()
            import shutil
            shutil.copy(subtitle_path, simple_subtitle_path)

            # For FFmpeg filter syntax, we need to escape special characters
            # Using a simple filename avoids Windows path escaping issues entirely
            subtitle_filter = f"subtitles={simple_subtitle_path.name}:force_style='FontName=Arial,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,Outline=2,Shadow=1,MarginV=40'"

            # Run FFmpeg from the working directory so it can find the subtitle file
            import os
            original_cwd = os.getcwd()
            os.chdir(working_dir)

            try:
                subtitle_cmd = [
                    'ffmpeg', '-y',
                    '-i', str(temp_concatenated),
                    '-vf', subtitle_filter,
                    '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
                    '-c:a', 'copy',
                    str(temp_with_subs)
                ]
                subprocess.run(subtitle_cmd, capture_output=True, check=True)
            finally:
                os.chdir(original_cwd)
                # Clean up temporary subtitle copy
                simple_subtitle_path.unlink(missing_ok=True)

            # Step 6: Add voiceover
            print("[6/7] Adding voiceover...")

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

            # Step 7: Cleanup
            print("[7/7] Cleaning up...")
            temp_forward.unlink(missing_ok=True)
            temp_reverse.unlink(missing_ok=True)
            temp_pingpong.unlink(missing_ok=True)
            pingpong_list.unlink(missing_ok=True)
            temp_looped.unlink(missing_ok=True)
            temp_concat_list.unlink(missing_ok=True)
            temp_concatenated.unlink(missing_ok=True)
            temp_with_subs.unlink(missing_ok=True)
            for seg in image_segments:
                seg.unlink(missing_ok=True)

            # Show result
            file_size = Path(output_path).stat().st_size / (1024 * 1024)
            print(f"\nVideo complete ({voiceover_duration:.2f}s, {file_size:.2f} MB)\n")

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
        print(f"\nOpening video...")
        try:
            if sys.platform == 'win32':
                os.startfile(video_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', video_path])
            else:  # Linux
                subprocess.run(['xdg-open', video_path])
        except Exception as e:
            print(f"Could not auto-open: {e}")
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

        # Truncate to reasonable length (reduced from 100 to 60 to accommodate long base paths)
        max_length = 60
        if len(filename) > max_length:
            filename = filename[:max_length].strip()

        # Default if empty
        if not filename:
            filename = "untitled_video"

        return filename

    def run(self):
        """Main execution flow - browser automation for content, API for media"""
        try:
            print("\n" + "="*50)
            print("AI VIDEO GENERATION MACRO")
            print("="*50)

            # === CHARACTER SELECTION ===
            self.selected_character_folder, self.selected_character_video, self.character_name = self.select_character()

            # === INITIALIZE BROWSER ===
            self.init_browser()
            self.navigate_to_project()

            # === PHASE 1: GENERATE ENGLISH CONTENT (Browser) ===
            print("="*50)
            print("PHASE 1: GENERATE ENGLISH CONTENT")
            print("="*50)

            # STEP 1: Generate and save title immediately
            english_title = self.generate_title_browser()

            # Create output folder immediately after title is approved
            folder_name = self.sanitize_filename(english_title)
            self.working_dir = self.base_output_dir / folder_name
            self.working_dir.mkdir(exist_ok=True)
            print(f"\nOutput folder: {self.working_dir}")

            # Save English title immediately
            title_path = self.working_dir / "video_title_english.txt"
            with open(title_path, 'w', encoding='utf-8') as f:
                f.write(english_title)
            print(f"✓ Saved: {title_path.name}\n")

            time.sleep(5)

            # STEP 2: Generate and save description immediately
            english_description = self.generate_description_browser(english_title)

            # Save English description immediately
            description_path = self.working_dir / "video_description_english.txt"
            with open(description_path, 'w', encoding='utf-8') as f:
                f.write(english_description)
            print(f"✓ Saved: {description_path.name}\n")

            time.sleep(5)

            # STEP 3: Generate premise (no save needed, just used for script generation)
            english_premise = self.generate_premise_browser(english_title, english_description)
            time.sleep(5)

            # STEP 4: Generate and save script immediately
            english_script = self.generate_full_script_browser(english_title, english_premise)

            # Validate English script was fully captured
            print("\n=== Validating English Script Capture ===")
            script_words = english_script.strip().split()
            script_chars = len(english_script)
            last_30_words = ' '.join(script_words[-30:])

            print(f"Script stats:")
            print(f"  Total words: {len(script_words)}")
            print(f"  Total characters: {script_chars}")
            print(f"  Last 30 words: ...{last_30_words}")

            # Verify it's not truncated by checking it ends with a sentence-ending punctuation
            if english_script.strip()[-1] not in '.!?':
                print("\n⚠ WARNING: Script doesn't end with sentence-ending punctuation!")
                print("This might indicate truncation.")
                choice = input("Continue anyway? [y/n]: ").lower()
                if choice != 'y':
                    print("Script rejected. Please regenerate.")
                    if self.driver:
                        self.driver.quit()
                    return
            else:
                print("✓ Script appears complete (ends with proper punctuation)\n")

            # Save English script immediately
            script_path = self.working_dir / "video_script_english.txt"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(english_script)
            print(f"✓ Saved: {script_path.name}\n")

            print("All English files saved")

            # === PHASE 2: TRANSLATE TO KOREAN (Local Opus-MT) ===
            print("\n" + "="*50)
            print("PHASE 2: TRANSLATE TO KOREAN (using Opus-MT)")
            print("="*50 + "\n")

            # Translate title from file
            print("Translating title from video_title_english.txt...")
            with open(title_path, 'r', encoding='utf-8') as f:
                english_title_text = f.read()
            korean_title = self.translate_to_korean_browser(english_title_text, "title")
            korean_title_path = self.working_dir / "video_title_korean.txt"
            with open(korean_title_path, 'w', encoding='utf-8') as f:
                f.write(korean_title)
            print(f"✓ Saved: {korean_title_path.name}\n")
            time.sleep(3)

            # Translate description from file
            print("Translating description from video_description_english.txt...")
            with open(description_path, 'r', encoding='utf-8') as f:
                english_description_text = f.read()
            korean_description = self.translate_to_korean_browser(english_description_text, "description")
            korean_description_path = self.working_dir / "video_description_korean.txt"
            with open(korean_description_path, 'w', encoding='utf-8') as f:
                f.write(korean_description)
            print(f"✓ Saved: {korean_description_path.name}\n")
            time.sleep(3)

            # Translate script from file
            print("Translating script from video_script_english.txt...")
            korean_script = self.translate_script_to_korean_browser(str(script_path))
            korean_script_path = self.working_dir / "video_script_korean.txt"
            with open(korean_script_path, 'w', encoding='utf-8') as f:
                f.write(korean_script)
            print(f"✓ Saved: {korean_script_path.name}\n")

            print("All Korean files saved")

            # === CLOSE BROWSER ===
            print("Closing browser...")
            self.driver.quit()
            print("Browser closed\n")

            # === PHASE 3: GENERATE MEDIA (API + FFmpeg) ===
            print("="*50)
            print("PHASE 3: GENERATE MEDIA")
            print("="*50)

            # Generate voiceover
            voiceover_path = self.working_dir / "voiceover.mp3"
            voiceover_result = self.generate_voiceover_genaipro(korean_script, str(voiceover_path))

            if not voiceover_result:
                print("Voiceover generation failed. Exiting.")
                return

            # Get voiceover duration for subtitles
            duration = self.get_audio_duration(str(voiceover_path))

            # Generate subtitles
            subtitle_path = self.working_dir / "subtitles.srt"
            self.generate_subtitles(korean_script, str(subtitle_path), duration)

            # Load images
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
                print("Video editing failed. Exiting.")
                return

            # === COMPLETION ===
            print("="*50)
            print("VIDEO GENERATION COMPLETE")
            print("="*50)
            print(f"\nEnglish Title: {english_title}")
            print(f"Korean Title: {korean_title}")
            print(f"\nAll files: {self.working_dir}")

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
