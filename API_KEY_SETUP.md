# Setting Up Your OpenAI API Key

## Quick Start (Recommended)

1. **Edit the `.env` file** in your project root:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

2. **Test your API key**:
   ```bash
   python test_api_key.py
   ```

3. **Run the pipeline**:
   ```bash
   python pipeline.py
   ```

## Options for Setting Your API Key

### Option 1: .env File (Recommended - Most Secure)
- Edit `.env` file in project root
- Replace `your-api-key-here` with your actual key
- The file is already protected by `.gitignore`

### Option 2: Environment Variable (Terminal Session)
```bash
export OPENAI_API_KEY="sk-your-actual-api-key-here"
python pipeline.py
```

### Option 3: Permanent Environment Variable
Add to your shell profile (`~/.zshrc` or `~/.bash_profile`):
```bash
echo 'export OPENAI_API_KEY="sk-your-actual-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

## Testing Your Setup

After setting your API key, run:
```bash
python test_api_key.py
```

This will:
- ✅ Check if your API key is set
- ✅ Verify the key format 
- ✅ Test an actual API call
- ✅ Confirm everything is working

## Running the Full Pipeline

Once your API key is working:
```bash
python pipeline.py
```

This will:
- Fetch RSS feeds from 7 clinical research sources
- Use OpenAI to score, summarize, and comment on each article
- Select the top 8-10 articles
- Generate HTML and PDF outputs
- Create detailed logs

## Security Notes

- ✅ Your `.env` file is already in `.gitignore`
- ✅ Never commit your API key to version control
- ✅ Keep your API key private and secure
- ✅ The pipeline loads the key automatically from `.env`

## Troubleshooting

If you get authentication errors:
1. Check that your API key starts with `sk-`
2. Verify you have credits in your OpenAI account
3. Ensure the key hasn't expired
4. Run `python test_api_key.py` to diagnose issues
