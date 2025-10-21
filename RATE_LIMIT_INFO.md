# Rate Limit Information

## What Happened?

You encountered a **rate limit error** from the Anthropic API:
```
Error code: 429 - rate_limit_error
This request would exceed the rate limit for your organization of 50,000 input tokens per minute.
```

## Why This Happened

The macro loads your project files (83,114 characters) to give Claude context about your video style. With each API call that uses this context:

- **~20,000+ tokens** are sent (project files + your request)
- **Rate limit**: 50,000 tokens/minute
- **Result**: You can only make 2-3 calls per minute before hitting the limit

## What I Fixed

I've added **automatic rate limit handling**:

1. **Exponential Backoff Retry**
   - If rate limit is hit, the macro automatically waits and retries
   - Wait times: 2s → 4s → 8s → 16s → 32s
   - Up to 5 retry attempts for translations

2. **Automatic Delays Between Calls**
   - 2-second delay after each translation
   - Spreads out API usage over time

3. **Smart Retry for Heavy Calls**
   - Description generation has retry logic
   - Waits: 5s → 10s → 20s if rate limited

## What This Means for You

**You don't need to do anything!** The macro will now:
- ✅ Automatically wait and retry if rate limited
- ✅ Show you progress messages like "⚠ Rate limit hit. Waiting 5 seconds before retry..."
- ✅ Space out API calls to avoid hitting limits

**Just be patient** - the macro will handle rate limits automatically and continue working.

## If You Still See Errors

If you're making many videos in quick succession, you might need to:

1. **Wait between runs** - Give it 1-2 minutes between video generations
2. **Reduce project files** - If you have many reference files, consider keeping only the most relevant ones
3. **Upgrade your API plan** - Contact Anthropic for higher rate limits

## Understanding Your Rate Limit

- **Current limit**: 50,000 tokens/minute
- **With your project files**: ~2-3 API calls per minute
- **The macro spaces these out automatically now**

## Quick Test

To test if your API is working, run:
```
python test_api_access.py
```

This will show you which models you can access and won't count against heavy rate limits.

---

**Bottom line**: Just re-run the macro! It will automatically handle rate limits with waits and retries.
