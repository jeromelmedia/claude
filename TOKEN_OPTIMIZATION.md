# Token Optimization Explained

## How the Macro Saves Tokens

The macro is **already optimized** to minimize token usage while still maintaining quality. Here's how:

## API Call Types

### 🔴 Heavy Calls (WITH Project Files - ~25,000 tokens)
These calls send your 83K+ characters of project files for context:

1. **Title Generation** - Needs project files to match your video style
2. **Description Generation** - Needs project files for format/style reference
3. **Premise Generation** - Needs project files for topic/style guidance
4. **Script Generation** - Needs project files for content style and structure

**Total Heavy Calls:** ~4-6 per video (depending on approvals/regenerations)

### 🟢 Lightweight Calls (NO Project Files - ~500-3,000 tokens)
These calls do simple tasks that don't need the full context:

1. **Translation (short)** - Title, description, premise translations
2. **Translation (chunks)** - Full script translation (split into ~3-4 chunks)
3. **Subtitle Generation** - No translation needed, just formatting

**Total Lightweight Calls:** ~6-10 per video

## Token Usage Breakdown

### Example: Full Video Generation

```
CREATIVE TASKS (with project files):
  Title generation:        ~25,000 tokens ✓ Needs style
  Description generation:  ~25,000 tokens ✓ Needs format
  Premise generation:      ~25,000 tokens ✓ Needs guidance
  Script generation:       ~30,000 tokens ✓ Needs full context
  Script expansion (if needed): ~30,000 tokens ✓ Needs context
  ────────────────────────────────────────
  Subtotal:                ~135,000 tokens

SIMPLE TASKS (without project files):
  Title translation:       ~300 tokens ✓ No context needed
  Description translation: ~500 tokens ✓ No context needed
  Premise translation:     ~400 tokens ✓ No context needed
  Script translation (3 chunks): ~9,000 tokens ✓ No context needed
  ────────────────────────────────────────
  Subtotal:                ~10,200 tokens

TOTAL FOR ONE VIDEO:       ~145,200 tokens
```

### Without Optimization (if we sent project files everywhere):
```
Same tasks but ALL with project files: ~210,000 tokens
```

**Savings: ~65,000 tokens per video (31% reduction)** 🎉

## Rate Limit Management

With your current limit of **50,000 tokens/minute**:

### Optimized Approach (Current):
- Creative tasks use heavy calls (spread over time)
- Translations use lightweight calls (fast and efficient)
- Automatic 2-second delays between calls
- Retry logic with exponential backoff
- **Result**: Video completes in 10-15 minutes smoothly

### If We Sent Project Files Everywhere:
- Every call would be heavy
- Hit rate limits constantly
- Need 4-5 minutes of waiting between calls
- **Result**: Video would take 30-45 minutes

## How to Verify Optimization

When you run the macro, watch for these messages:

```
✓ Good - Heavy call (needs project files):
"=== STEP 1: Generating Video Title (English) ==="

✓ Good - Lightweight call:
"Translating title to Korean..."
"  (Using lightweight API call without project files)"

✓ Good - Retry handling:
"⚠ Rate limit hit. Waiting 5 seconds before retry..."
```

## Understanding the Code

### Heavy Call Example:
```python
message = self.claude_client.messages.create(
    model=self.model,
    max_tokens=500,
    system=self.custom_instructions,  # ← Project files sent here!
    messages=[...]
)
```

### Lightweight Call Example:
```python
message = self.claude_client.messages.create(
    model=self.model,
    max_tokens=1000,
    # No system= parameter = no project files!
    messages=[...]
)
```

## Why We Can't Access Your Claude Project Directly

You asked: "I already have all those files in my Claude Project, can't we use that?"

**Unfortunately, no.** Here's why:

1. **Anthropic API vs Claude.ai are different**
   - Claude.ai (website) = Has Projects feature
   - Anthropic API (what this macro uses) = No Projects feature
   - The API cannot access your web-based Projects

2. **Why We Download Project Files Locally**
   - The macro loads files from `project_files/` folder
   - These get combined into `self.custom_instructions`
   - Only sent with creative tasks (title, description, script)
   - Not sent with simple tasks (translation)

3. **This Is Actually Better**
   - You have full control over what files are included
   - No dependency on internet connection to Claude.ai
   - Faster (local file reads vs API calls)
   - More reliable

## Further Optimization Ideas

If you still hit rate limits frequently:

### 1. Use Claude Haiku for Translations
```python
# In translate_to_korean_simple():
model="claude-3-haiku-20240307",  # Faster, cheaper, separate rate limit
```

### 2. Reduce Project File Size
- Keep only the most relevant reference videos
- Remove duplicate examples
- Current: 83K chars → Target: 30-40K chars

### 3. Cache Translations
- Save common phrases/terms
- Reuse across multiple videos
- Reduce translation calls

### 4. Batch Operations
- Translate all short texts (title + description + premise) in one call
- Reduces number of API calls

## Summary

✅ **The macro is already optimized!**

- Creative tasks (4-6 calls) use project files
- Simple tasks (6-10 calls) skip project files
- 31% token savings over non-optimized approach
- Automatic retry and delay handling
- Smooth operation within rate limits

**You don't need to do anything** - just run the macro and it handles token optimization automatically!
