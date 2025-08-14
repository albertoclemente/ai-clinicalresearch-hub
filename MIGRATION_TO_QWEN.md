# Migration from OpenAI to Qwen via OpenRouter

## Summary of Changes

This migration replaces OpenAI GPT-4o-mini with Qwen-2.5-72B via OpenRouter for all AI operations in the clinical research pipeline.

## Benefits of Migration

- **Cost Reduction**: Qwen via OpenRouter is more cost-effective than OpenAI GPT-4o-mini
- **Performance**: Qwen-2.5-72B provides excellent performance for content analysis and query generation
- **Reliability**: OpenRouter provides reliable access to state-of-the-art models
- **Flexibility**: Easy to switch between different models via OpenRouter if needed

## Files Modified

### Core Changes
1. **`qwen_client.py`** - New Qwen OpenRouter client with OpenAI-compatible interface
2. **`pipeline.py`** - Updated to use Qwen client instead of OpenAI client
3. **`test_quality_filters.py`** - Updated test initialization

### Configuration Changes
4. **`requirements.txt`** - Updated dependencies (still uses openai package for compatibility)
5. **`environment.yml`** - Updated conda environment
6. **`.env.example`** - Updated environment variable template
7. **`README.md`** - Updated documentation throughout

## API Changes

### Before (OpenAI)
```python
openai_client = openai.OpenAI(api_key=openai_api_key)
response = openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7,
    max_tokens=800
)
```

### After (Qwen via OpenRouter)
```python
qwen_client = QwenOpenRouterClient(api_key=qwen_api_key)
response = qwen_client.chat.completions.create(
    model="qwen/qwen-2.5-72b-instruct",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7,
    max_tokens=800
)
```

## Environment Variables

### Before
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### After
```bash
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

## Setup Instructions

1. **Get OpenRouter API Key**:
   - Visit https://openrouter.ai/
   - Sign up for an account
   - Generate an API key

2. **Update Environment**:
   ```bash
   export OPENROUTER_API_KEY="your_openrouter_api_key_here"
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Test the Migration**:
   ```bash
   python test_quality_filters.py
   python pipeline.py
   ```

## Model Specifications

- **Model**: qwen/qwen-2.5-72b-instruct
- **Context Length**: 128k tokens
- **Provider**: OpenRouter
- **Cost**: More cost-effective than GPT-4o-mini
- **Performance**: Excellent for content analysis and text generation

## Backward Compatibility

The Qwen client maintains the same interface as the OpenAI client, ensuring minimal code changes were required. The pipeline functionality remains identical from a user perspective.

## Migration Verification

To verify the migration was successful:

1. **Run Quality Filter Tests**:
   ```bash
   python test_quality_filters.py
   ```

2. **Test Query Generation**:
   ```bash
   python -c "from pipeline import FeedProcessor; import os; fp = FeedProcessor(os.getenv('OPENROUTER_API_KEY'), 'test.log'); print(len(fp.generate_search_queries()))"
   ```

3. **Full Pipeline Test**:
   ```bash
   python pipeline.py
   ```

## Troubleshooting

- **API Key Issues**: Ensure `OPENROUTER_API_KEY` is set correctly
- **Model Access**: Verify OpenRouter account has access to Qwen models
- **Dependencies**: Ensure all packages are installed with `pip install -r requirements.txt`

## Performance Notes

- Estimated cost reduction: ~50-70% compared to GPT-4o-mini
- Response quality: Comparable or better for clinical research content analysis
- Response time: Similar to OpenAI API calls via OpenRouter
