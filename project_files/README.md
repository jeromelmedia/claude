# Project Files Folder

## What Is This Folder?

This is where you put all the reference files from your Claude Project so the macro can use them!

## What to Put Here

Download ALL the files you uploaded to your Claude Project (ID: 0199f815-e36a-75cc-8a99-e6aace1ac274) and paste them into this folder.

**Your files might include:**
- Writing style examples
- Video script templates
- Topic guidelines
- Brand voice documents
- Example titles
- Sample scripts
- Reference materials

## Supported File Types

The macro will automatically load these file types:
- `.txt` - Text files
- `.md` - Markdown files
- `.json` - JSON data
- `.csv` - CSV data
- `.py` - Python code
- `.js` - JavaScript code
- `.html` - HTML files
- `.css` - CSS files

## How to Add Your Files

### Step 1: Download from Claude Project

1. Go to https://claude.ai
2. Open your project (ID: 0199f815-e36a-75cc-8a99-e6aace1ac274)
3. Download each file you uploaded there

### Step 2: Paste Files Here

Just drag and drop all downloaded files into **THIS FOLDER** (`project_files/`)

### Step 3: Run the Macro

Double-click `RUN_ME.bat` or run:
```bash
python run_video_macro.py
```

The macro will automatically:
- Find all files in this folder
- Load their content
- Include them in Claude's system prompt
- Use them when generating titles and scripts!

## Example Structure

After you add your files, this folder might look like:

```
project_files/
├── README.md (this file - you can delete it if you want)
├── writing_style_guide.txt
├── video_script_examples.md
├── topic_guidelines.txt
├── brand_voice.md
└── example_titles.txt
```

You can also organize into subfolders:

```
project_files/
├── style/
│   ├── writing_guide.md
│   └── brand_voice.txt
├── examples/
│   ├── good_titles.txt
│   └── sample_scripts.md
└── topics/
    └── content_topics.txt
```

## What Happens When You Run the Macro?

You'll see output like:

```
✓ Loading 5 project file(s) from: ./project_files
  - writing_style_guide.txt
  - video_script_examples.md
  - topic_guidelines.txt
  - brand_voice.md
  - example_titles.txt
✓ Project knowledge loaded (12,345 chars)
```

Now Claude has access to ALL your reference material when generating content!

## Tips

- **Include examples** - The more examples you provide, the better Claude understands your style
- **Be specific** - Clear guidelines help Claude match your exact requirements
- **Keep it organized** - Use subfolders if you have many files
- **Update anytime** - Just edit files here and re-run the macro

## Need Help?

See the full guide: `HOW_TO_USE_PROJECT_FILES.md` in the main folder

## Ready to Go!

1. Paste your Claude Project files into this folder
2. Run `RUN_ME.bat`
3. The macro will use your files automatically!

**That's it! No configuration needed - just add your files here.** 🚀
