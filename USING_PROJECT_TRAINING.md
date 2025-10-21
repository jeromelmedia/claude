# How to Use Your Claude Project's Training

## The Problem

The macro was generating generic titles and scripts that didn't match your Claude Project's training because it wasn't accessing your project's custom instructions and knowledge base.

## The Solution

You need to copy your Claude Project's custom instructions into the `config.json` file so the macro can use them.

## Step-by-Step Instructions

### 1. Go to Your Claude Project

1. Open https://claude.ai
2. Click on "Projects" in the sidebar
3. Open your trained project

### 2. Get Your Custom Instructions

**Option A: If you have Custom Instructions set:**
1. Click the project settings (gear icon or Settings)
2. Look for "Custom Instructions" or "System Prompt"
3. Copy ALL the text from this field

**Option B: If you uploaded training files:**
- Create custom instructions that reference your training:
```
You are a video script writer creating content about [YOUR SPECIFIC TOPIC].

Writing Style:
- [Describe your desired tone: educational, entertaining, formal, casual, etc.]
- [Describe structure: how you want videos organized]
- [Any specific requirements: length, format, etc.]

Content Focus:
- [Main topics you cover]
- [Target audience]
- [Key themes or messages]

Use the examples and knowledge from the project files to:
- Generate titles in the same style as the examples
- Write scripts that match the tone and format you've learned
- Focus on the topics and themes present in the training data

Always maintain consistency with the project's established voice and style.
```

### 3. Add to config.json

Edit your `config.json` and add/update the `custom_instructions` field:

```json
{
  "anthropic_api_key": "sk-ant-xxxxx",
  "claude_project_id": "your-project-id",
  "claude_model": "claude-3-haiku-20240307",
  "custom_instructions": "PASTE YOUR CUSTOM INSTRUCTIONS HERE - You are creating video content about... [your full instructions]",
  "tts_voice": "ko-KR-SunHiNeural",
  "video_clip_path": "C:/path/to/talking_person.mp4"
}
```

### Example Full config.json

```json
{
  "anthropic_api_key": "sk-ant-api01-xxxxx",
  "claude_project_id": "proj_xxxxx",
  "claude_model": "claude-3-haiku-20240307",
  "custom_instructions": "You are creating educational video content about artificial intelligence and machine learning. Your writing style is informative yet accessible, breaking down complex topics for a general audience. Videos follow this structure: 1) Hook with a real-world example, 2) Explain the core concept, 3) Provide practical applications, 4) Conclude with key takeaways. Tone is professional but conversational. Target audience is tech-interested individuals without formal CS background. Use analogies and real-world examples frequently. Generate titles that are clear, specific, and highlight the practical value.",
  "tts_voice": "ko-KR-SunHiNeural",
  "video_clip_path": "C:/Users/yourname/Videos/talking_person.mp4",
  "target_min_words": 6000,
  "target_max_words": 7000,
  "num_script_segments": 4,
  "num_images": 4,
  "video_loop_duration_seconds": 90
}
```

## What This Does

When you add custom instructions to the config:

- **Title Generation**: Uses your instructions to generate titles matching your project's style
- **Premise Generation**: Creates premises aligned with your topic and tone
- **Script Generation**: Writes full scripts in your trained writing style
- **Consistency**: All content follows your project's guidelines

## Testing Your Instructions

After updating `config.json`:

1. Run the macro: `python run_video_macro.py`
2. Generate a few titles and check if they match your desired style
3. If not matching, refine your custom instructions and try again

## Tips for Good Custom Instructions

### Be Specific About:
- **Topic/Niche**: "creating content about [specific topic]"
- **Target Audience**: "for [specific audience]"
- **Tone**: "professional/casual/educational/entertaining"
- **Structure**: "videos should follow [specific format]"
- **Length**: "scripts should be approximately [X] words"

### Include Examples:
```
Example titles:
- "How AI is Revolutionizing Healthcare: 3 Real-World Applications"
- "Understanding Neural Networks: A Simple Visual Guide"

Writing style should match these examples in tone and structure.
```

### Reference Your Training Data:
```
Use the writing style, topics, and formats demonstrated in the project's knowledge base files. Follow the patterns established in the example scripts provided.
```

## Troubleshooting

### Still Getting Generic Content?

1. **Check your instructions are detailed enough**
   - Too vague: "Write good content"
   - Better: "Write educational content about AI for non-technical audiences using simple analogies"

2. **Make sure instructions are in config.json**
   - The `custom_instructions` field must be in your actual config.json, not just the example

3. **Test with different models**
   - Try `claude-3-opus-20240229` for better following of instructions
   - Or `claude-3-5-sonnet-20241022` if you have access

### Example vs Reality Check

Run the macro and compare:
- **Generated Title** vs **Expected Title Style**
- **Generated Script** vs **Your Training Examples**

If they don't match, your instructions need to be more specific about what makes your style unique.

## Need Help?

If your titles/scripts still don't match after adding detailed instructions:

1. Check that custom instructions are actually in `config.json`
2. Verify the instructions match what you want
3. Try being even more specific about style, tone, and format
4. Include actual examples in your instructions

The more specific and detailed your instructions, the better the results!
