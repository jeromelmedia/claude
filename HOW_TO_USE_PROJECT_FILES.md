# How to Use Your Claude Project Files in the Macro

## The Problem

You have uploaded files and training resources to your Claude Project (ID: `0199f815-e36a-75cc-8a99-e6aace1ac274`), but the Anthropic Messages API **cannot directly access Claude.ai Projects**.

Projects are a web interface feature for organizing conversations - the API doesn't have access to them.

## The Solution

Download your project files locally and let the macro load them automatically!

## Step-by-Step Setup

### 1. Create Project Files Folder

In the same directory as the macro, create a folder:

```bash
mkdir project_files
```

### 2. Download Your Project Files

Go to your Claude Project on claude.ai and download ALL the files you uploaded:

1. Open https://claude.ai
2. Go to your project (ID: 0199f815-e36a-75cc-8a99-e6aace1ac274)
3. In the "Knowledge" or "Files" section, download each file
4. Save them ALL into the `project_files` folder

**Example structure:**
```
claude/
├── ai_video_generation_macro.py
├── run_video_macro.py
├── config.json
└── project_files/
    ├── writing_style_examples.txt
    ├── video_script_template.md
    ├── topic_guidelines.txt
    ├── brand_voice.md
    └── example_titles.txt
```

### 3. Run the Macro

```bash
python run_video_macro.py
```

The macro will automatically:
- ✓ Find all files in `project_files/`
- ✓ Load their content
- ✓ Include them in the system prompt
- ✓ Use them for generating titles and scripts

You'll see output like:
```
✓ Loading 5 project file(s) from: ./project_files
  - writing_style_examples.txt
  - video_script_template.md
  - topic_guidelines.txt
  - brand_voice.md
  - example_titles.txt
✓ Project knowledge loaded (15,234 chars)
```

## Supported File Types

The macro automatically loads:
- `.txt` - Text files
- `.md` - Markdown files
- `.json` - JSON data
- `.csv` - CSV data
- `.py` - Python code
- `.js` - JavaScript code
- `.html` - HTML files
- `.css` - CSS files

## What Gets Included

Each file is loaded with a header:
```
=== File: writing_style_examples.txt ===

[Your file content here]

=== End of writing_style_examples.txt ===
```

Claude can then reference these files when generating content!

## Example: Writing Style File

Create `project_files/writing_style.txt`:

```
WRITING STYLE GUIDELINES

Video Structure:
1. Hook (first 10 seconds) - Start with a question or bold statement
2. Introduction (30 seconds) - Set context and promise value
3. Main Content (4-5 minutes) - 3-5 key points with examples
4. Conclusion (1 minute) - Recap and call-to-action

Tone:
- Conversational but authoritative
- Use "you" to address viewer directly
- Avoid jargon unless explaining it
- Include personal anecdotes when relevant

Title Format:
- [Number] + [Benefit] + [Topic]
- Examples:
  * "5 Proven Strategies to Double Your Productivity"
  * "The Ultimate Guide to Starting Your First Business"
  * "3 Simple Habits That Changed My Life"

Script Style:
- Short sentences (10-15 words average)
- Active voice
- Transitions between sections
- Include viewer engagement prompts
```

## Example: Topic Guidelines

Create `project_files/topics.txt`:

```
PRIMARY TOPICS

1. Productivity & Time Management
   - Focus on practical, actionable tips
   - Include specific tools and techniques
   - Share personal productivity systems

2. Personal Development
   - Mindset and habit formation
   - Goal setting frameworks
   - Success principles

3. Business & Entrepreneurship
   - Starting and growing businesses
   - Marketing strategies
   - Revenue generation

AVOID:
- Political content
- Controversial social issues
- Get-rich-quick schemes
- Unproven health claims
```

## Example: Example Titles

Create `project_files/example_titles.txt`:

```
EXAMPLE VIDEO TITLES (Follow This Style)

How I Built a $10K/Month Side Hustle in 6 Months
The Morning Routine That Transformed My Productivity
5 Business Lessons I Learned the Hard Way
Why Most People Fail at Goal Setting (And How to Succeed)
The Simple Framework That 10X'd My Output
3 Books That Completely Changed My Mindset
How to Find Your Passion (When You Have No Idea What You Want)
```

## Custom Instructions + Project Files

You can use BOTH custom instructions AND project files!

**config.json:**
```json
{
  "anthropic_api_key": "sk-ant-xxxxx",
  "claude_project_id": "0199f815-e36a-75cc-8a99-e6aace1ac274",
  "claude_model": "claude-3-haiku-20240307",
  "custom_instructions": "You are creating motivational and educational video content for entrepreneurs and professionals looking to level up their careers and businesses.",
  "project_files_dir": "./project_files",
  "tts_voice": "ko-KR-SunHiNeural",
  "video_clip_path": "C:/path/to/talking_person.mp4"
}
```

The macro will:
1. Load your custom instructions
2. Load all files from `project_files/`
3. Combine them into one comprehensive system prompt
4. Use it for all content generation

## Advanced: Organize by Category

You can organize files into subdirectories:

```
project_files/
├── style/
│   ├── writing_guidelines.md
│   └── brand_voice.txt
├── examples/
│   ├── good_titles.txt
│   └── sample_scripts.md
└── topics/
    ├── productivity.txt
    └── business.txt
```

The macro will load **all** files recursively!

## Testing Your Setup

Run this test script to see what's loaded:

```bash
python project_loader.py
```

Output:
```
=== PROJECT KNOWLEDGE LOADER ===

Found 8 file(s):

  - style/writing_guidelines.md
  - style/brand_voice.txt
  - examples/good_titles.txt
  - examples/sample_scripts.md
  - topics/productivity.txt
  - topics/business.txt

============================================================
Sample System Prompt (first 500 chars):
============================================================

You are creating motivational and educational...
=== PROJECT KNOWLEDGE BASE ===
...
```

## Benefits

✓ **Use your exact project files** - No need to manually copy content
✓ **Easy updates** - Just edit files in `project_files/`, no config changes
✓ **Organized** - Keep files separate and organized
✓ **Versioned** - Can track changes with git
✓ **Flexible** - Add/remove files anytime
✓ **Powerful** - Claude has full access to all your reference material

## Checklist

Before running the macro:

- [ ] Created `project_files` folder
- [ ] Downloaded ALL files from your Claude Project
- [ ] Placed files in `project_files/`
- [ ] Added custom instructions to `config.json` (optional but recommended)
- [ ] Tested with `python project_loader.py`
- [ ] Ready to run: `python run_video_macro.py`

## Troubleshooting

### "No project files found"

Make sure:
1. Folder is named exactly `project_files` (or update `project_files_dir` in config.json)
2. Files are directly in the folder (or subfolders)
3. Files have supported extensions (.txt, .md, .json, etc.)

### "Still not matching my style"

1. Check files actually contain your style guidelines
2. Make files more specific and detailed
3. Include MORE examples in your project files
4. Add a `custom_instructions` field in config.json with additional context

### "Too much content, API errors"

If you have MANY large files:
1. Keep only the most important reference files
2. Summarize long documents
3. Use more concise examples

## Next Steps

1. Download your Claude Project files
2. Put them in `project_files/`
3. Run the macro
4. Generate a title and check if it matches your style
5. If not perfect, add more specific examples to your project files!

The more specific examples and guidelines you include, the better the results! 🚀
