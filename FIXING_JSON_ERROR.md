# Fixing "Invalid \escape" JSON Error

## The Problem

If you see this error:
```
json.decoder.JSONDecodeError: Invalid \escape: line 6 column 25
```

It means you have **Windows backslashes** in your `config.json` file that need to be fixed.

## The Solution

In JSON files, backslashes (`\`) are special characters and must be escaped. You have **two options**:

### Option 1: Use Forward Slashes (EASIEST)

Windows accepts forward slashes in paths, so just use `/` instead of `\`:

```json
{
  "chrome_profile_path": "C:/Users/YourName/AppData/Local/Google/Chrome/User Data/Default",
  "video_clip_path": "C:/Users/YourName/Videos/talking_person.mp4"
}
```

✓ **This is the easiest and recommended approach!**

### Option 2: Double the Backslashes

If you prefer backslashes, you must **double them** (`\\` instead of `\`):

```json
{
  "chrome_profile_path": "C:\\Users\\YourName\\AppData\\Local\\Google\\Chrome\\User Data\\Default",
  "video_clip_path": "C:\\Users\\YourName\\Videos\\talking_person.mp4"
}
```

## Example: What NOT to Do

❌ **WRONG** (will cause error):
```json
{
  "chrome_profile_path": "C:\Users\YourName\AppData\Local\Google\Chrome\User Data\Default"
}
```

## Example: Correct config.json

```json
{
  "anthropic_api_key": "sk-ant-xxxxx",
  "claude_project_id": "your-project-id",
  "voice_id": "your-voice-id",
  "genaipro_api_key": "",
  "video_clip_path": "C:/Users/alexh/Videos/talking_person.mp4",
  "chrome_profile_path": "C:/Users/alexh/AppData/Local/Google/Chrome/User Data/Default",
  "target_min_words": 6000,
  "target_max_words": 7000,
  "num_script_segments": 4,
  "num_images": 4,
  "video_loop_duration_seconds": 90
}
```

## Quick Fix Steps

1. Open your `config.json` in a text editor (Notepad, VS Code, etc.)
2. Find any paths with backslashes like `C:\Users\...`
3. Replace all `\` with `/`
4. Save the file
5. Run the macro again

## Still Getting Errors?

Use an online JSON validator to check your file:
- https://jsonlint.com/
- Copy/paste your config.json content
- It will show you exactly what's wrong

## Why Does This Happen?

In JSON (and many programming languages), backslash is an "escape character" used for special characters like:
- `\n` = newline
- `\t` = tab
- `\"` = quote
- `\\` = actual backslash

So when JSON sees `C:\Users`, it thinks `\U` is trying to be a special character, which doesn't exist - hence the error.

**Solution**: Use forward slashes `/` which work perfectly fine on Windows!
