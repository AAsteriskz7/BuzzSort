# AI Provider Switching Guide

This guide explains how to switch between different AI providers (Google Gemini and Anthropic Claude) in the Intelligent File Janitor application.

## Current Status

- **Gemini**: ✅ Fully implemented and tested
- **Claude**: ⚠️ Stub implementation (ready for migration)

## Architecture Overview

The application uses an abstraction layer that makes switching providers seamless:

```
AIServiceInterface (Abstract Base Class)
    ├── GeminiService (Implemented)
    └── ClaudeService (Stub)
```

All AI operations go through the `AIServiceInterface`, which defines:
- `analyze_filenames()` - Cluster files by name patterns
- `analyze_text_content()` - Analyze document content
- `analyze_image()` - Analyze image content with vision
- `test_connection()` - Verify API connectivity

## Switching from Gemini to Claude

### Step 1: Get Claude API Key

1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-ant-`)

### Step 2: Update Configuration

Edit `ai_config.json`:

```json
{
  "provider": "claude",
  "gemini_api_key": "your_existing_gemini_key",
  "claude_api_key": "sk-ant-your-claude-key-here"
}
```

Or set environment variable:

```bash
export AI_PROVIDER=claude
export CLAUDE_API_KEY=sk-ant-your-key-here
```

### Step 3: Implement Claude Service (Required)

Currently, `ClaudeService` is a stub. To complete the migration:

1. Install the Anthropic SDK (already in requirements.txt):
   ```bash
   pip install anthropic
   ```

2. Implement the Claude service methods in `file_janitor.py`:

```python
import anthropic

class ClaudeService(AIServiceInterface):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"  # Latest model
    
    def analyze_filenames(self, filenames: List[str]) -> Dict:
        # Implement using Claude's Messages API
        # Similar structure to GeminiService but using Claude's API
        pass
    
    def analyze_text_content(self, filename: str, text_preview: str) -> Dict:
        # Implement text analysis with Claude
        pass
    
    def analyze_image(self, image_path: str) -> Dict:
        # Implement image analysis with Claude Vision
        pass
    
    def test_connection(self) -> bool:
        # Test Claude API connection
        pass
```

### Step 4: Test the Migration

Run the test suite to verify:

```bash
python test_workflow.py
```

## Implementation Guide for Claude

### Claude Messages API Structure

Claude uses a different API structure than Gemini:

```python
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Your prompt here"}
    ]
)

response_text = message.content[0].text
```

### Key Differences: Gemini vs Claude

| Feature | Gemini | Claude |
|---------|--------|--------|
| **API Style** | `generate_content()` | `messages.create()` |
| **Response** | `response.text` | `message.content[0].text` |
| **Vision** | Built into model | Separate vision model |
| **Safety** | `safety_settings` | `system` parameter |
| **Streaming** | `stream=True` | `stream=True` |

### Example: Filename Analysis with Claude

```python
def analyze_filenames(self, filenames: List[str]) -> Dict:
    try:
        prompt = f"""Analyze these {len(filenames)} filenames and group them into logical categories.

Filenames:
{chr(10).join(f"- {name}" for name in filenames)}

Organize into 3-7 meaningful clusters. Format as JSON:
{{
  "clusters": [
    {{
      "category": "Category Name",
      "files": ["file1.txt"],
      "description": "Brief explanation",
      "suggested_folder": "folder_name"
    }}
  ]
}}"""
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text
        
        # Parse JSON response (same as Gemini)
        result = json.loads(response_text)
        
        return {
            'clusters': result.get('clusters', []),
            'total_files': len(filenames),
            'error': None
        }
        
    except Exception as e:
        return {
            'clusters': [],
            'error': f'Analysis failed: {str(e)}'
        }
```

### Example: Image Analysis with Claude

```python
def analyze_image(self, image_path: str) -> Dict:
    try:
        # Read and encode image
        import base64
        with open(image_path, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')
        
        # Determine media type
        extension = Path(image_path).suffix.lower()
        media_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        media_type = media_types.get(extension, 'image/jpeg')
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": "Analyze this image and suggest a descriptive filename. Format as JSON: {\"description\": \"...\", \"suggested_name\": \"...\", \"key_elements\": [...], \"confidence\": \"high/medium/low\"}"
                        }
                    ]
                }
            ]
        )
        
        response_text = message.content[0].text
        result = json.loads(response_text)
        
        return {
            'description': result.get('description', 'Unknown'),
            'suggested_name': result.get('suggested_name', Path(image_path).name),
            'key_elements': result.get('key_elements', []),
            'confidence': result.get('confidence', 'medium'),
            'error': None
        }
        
    except Exception as e:
        return {
            'description': 'Unknown',
            'suggested_name': Path(image_path).name,
            'error': f'Image analysis failed: {str(e)}'
        }
```

## Testing Provider Switching

### 1. Test Configuration Loading

```python
from file_janitor import AIConfig, AIProvider

config = AIConfig.load_config()
print(f"Provider: {config['provider']}")
print(f"Gemini key present: {bool(config.get('gemini_api_key'))}")
print(f"Claude key present: {bool(config.get('claude_api_key'))}")
```

### 2. Test Service Creation

```python
from file_janitor import AIServiceFactory, AIProvider

provider = AIProvider.CLAUDE
api_key = "your-claude-key"

service = AIServiceFactory.create_service(provider, api_key)
print(f"Service type: {type(service).__name__}")
print(f"Connection test: {service.test_connection()}")
```

### 3. Run Full Test Suite

```bash
# Update ai_config.json to use Claude
python test_workflow.py
```

## Cost Comparison

### Google Gemini Pricing (as of 2024)
- **Gemini 2.0 Flash**: Free tier available
- **Input**: ~$0.075 per 1M tokens
- **Output**: ~$0.30 per 1M tokens

### Anthropic Claude Pricing (as of 2024)
- **Claude 3.5 Sonnet**: 
- **Input**: $3.00 per 1M tokens
- **Output**: $15.00 per 1M tokens

**Note**: Prices subject to change. Check provider websites for current pricing.

## Recommendations

### When to Use Gemini
- ✅ Cost-sensitive projects
- ✅ Free tier for testing
- ✅ Good balance of speed and quality
- ✅ Built-in vision capabilities

### When to Use Claude
- ✅ Need highest quality analysis
- ✅ Complex reasoning tasks
- ✅ Better at following instructions
- ✅ More consistent JSON output

## Troubleshooting

### Provider Not Switching

1. Check `ai_config.json` is properly formatted
2. Verify environment variables are set correctly
3. Restart the application after config changes
4. Check logs for configuration errors

### Claude Service Not Working

1. Verify Claude API key is valid
2. Check that `anthropic` package is installed
3. Ensure ClaudeService methods are implemented
4. Review error messages in logs

### API Rate Limits

Both providers have rate limits:
- **Gemini**: 60 requests per minute (free tier)
- **Claude**: Varies by plan

If you hit rate limits:
- Add delays between requests
- Reduce batch sizes
- Upgrade to paid tier

## Migration Checklist

- [ ] Get Claude API key
- [ ] Update `ai_config.json` with Claude key
- [ ] Implement `ClaudeService` methods
- [ ] Test connection with `test_connection()`
- [ ] Test filename analysis
- [ ] Test text content analysis
- [ ] Test image analysis
- [ ] Run full test suite
- [ ] Update documentation
- [ ] Monitor costs and performance

## Support

For issues with provider switching:
1. Check this guide
2. Review logs in `logs/file_janitor.log`
3. Verify API keys are valid
4. Test with simple examples first

---

**Note**: The abstraction layer makes it easy to add more providers in the future (OpenAI GPT-4, local models, etc.)
