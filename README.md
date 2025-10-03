# 🐝 Buzz Sort

**AI-Powered File Organization • Georgia Tech Yellow Jacket Edition**

Buzz Sort is an intelligent desktop application that automatically organizes cluttered directories using advanced AI content analysis. Powered by Claude AI, Buzz Sort understands your files and creates smart organization plans with the precision and efficiency of a Yellow Jacket.

## Features

- **Smart File Scanning**: Recursively scans directories and extracts comprehensive metadata
- **AI-Powered Analysis**: Uses Claude 3.5 Sonnet to analyze file content and suggest intelligent organization
- **Two-Pass Triage**: Efficiently handles large volumes of files with intelligent clustering
- **Multimodal Content Analysis**: 
  - Text content analysis for documents
  - Image recognition for photos
  - Metadata-based categorization for all file types
- **Safe Execution**: Dry-run mode and confirmation dialogs prevent accidental changes
- **Comprehensive Logging**: Track all operations with detailed logs
- **Yellow Jacket UI**: Stunning Georgia Tech-themed interface with official GT colors
- **Modern Design**: Professional interface with color-coded results and intuitive controls

## Requirements

- Python 3.9 or higher
- Windows, macOS, or Linux
- Internet connection (for AI API calls)
- Anthropic Claude API key

## Installation

### 1. Clone or Download the Repository

```bash
git clone <repository-url>
cd buzz-sort
```

### 2. Create a Virtual Environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Key

Create an `ai_config.json` file in the project root:

```json
{
  "provider": "claude",
  "claude_api_key": "YOUR_CLAUDE_API_KEY_HERE"
}
```

**Getting Your API Key:**
- Visit [Anthropic Console](https://console.anthropic.com/)
- Sign up or log in
- Navigate to API Keys
- Create a new API key
- Copy and paste it into `ai_config.json`

### 5. Verify Installation

Run the verification script to ensure everything is set up correctly:

```bash
python verify_installation.py
```

This will check:
- Python version compatibility
- All required dependencies
- Configuration file and API keys

## Usage

### Running the Application

```bash
python file_janitor.py
```

### Basic Workflow

1. **Select Folder**: Click "Select Folder" and choose the directory you want to organize
2. **Scan Files**: The application automatically scans and categorizes files
3. **AI Analysis**: Files are analyzed using AI to create intelligent clusters
4. **Review Plan**: Review the proposed organization plan showing:
   - New folder structure
   - File moves and renames
   - Operation summary
5. **Execute Plan**: Click "Execute Plan" to apply the changes (with safety confirmation)

### Features in Detail

#### File Scanning
- Recursively scans all files and subdirectories
- Extracts metadata: name, size, dates, type
- Groups files by category (documents, images, videos, etc.)
- Handles permission errors gracefully

#### AI Analysis (Two-Pass System)
- **Pass 1**: Analyzes filenames to create logical clusters
- **Pass 2**: Deep content analysis for each cluster
  - Text extraction from documents
  - Image recognition for photos
  - Smart rename suggestions

#### Organization Planning
- Creates descriptive folder names based on content
- Suggests meaningful file renames (e.g., `IMG_1234.jpg` → `beach_sunset_hawaii.jpg`)
- Handles naming conflicts automatically
- Shows complete plan before execution

#### Safe Execution
- **Dry-Run Mode**: Preview operations without making changes
- **Confirmation Dialog**: Mandatory warning before execution
- **Progress Tracking**: Real-time progress bar
- **Error Handling**: Continues on errors, reports all issues
- **Operation Logging**: Complete log of all changes

## Configuration

### Switching AI Providers

To switch from Gemini to Claude, update `ai_config.json`:

```json
{
  "provider": "claude",
  "gemini_api_key": "your_gemini_key",
  "claude_api_key": "YOUR_CLAUDE_API_KEY_HERE"
}
```

**Note**: Claude integration is currently a stub. Full implementation coming soon.

### Environment Variables

You can also configure the application using environment variables:

```bash
export AI_PROVIDER=gemini
export GEMINI_API_KEY=your_key_here
export CLAUDE_API_KEY=your_key_here
```

Environment variables take precedence over `ai_config.json`.

## Testing

Run the comprehensive test suite:

```bash
python test_workflow.py
```

The test suite includes:
- File scanning functionality
- AI service integration
- Organization plan generation
- Plan execution (dry-run and actual)
- Error handling scenarios
- Logging system

## Logging

All operations are logged to `logs/file_janitor.log`:
- File scans and analysis
- AI API calls and responses
- File operations (moves, renames, folder creation)
- Errors and warnings

View logs to troubleshoot issues or audit changes.

## Project Structure

```
intelligent-file-janitor/
├── file_janitor.py              # Main application
├── test_workflow.py             # Integration tests
├── verify_installation.py       # Installation verification
├── requirements.txt             # Python dependencies
├── ai_config.json              # API configuration
├── .env.example                # Configuration template
├── README.md                   # Main documentation
├── PROVIDER_SWITCHING.md       # AI provider switching guide
├── CHANGELOG.md                # Version history
├── logs/                       # Operation logs
│   ├── file_janitor.log
│   └── README.md
└── .kiro/                      # Kiro spec files
    └── specs/
        └── intelligent-file-janitor/
            ├── requirements.md
            ├── design.md
            └── tasks.md
```

## Troubleshooting

### API Key Issues

**Error**: "API authentication failed"
- Verify your API key is correct in `ai_config.json`
- Check that the key has proper permissions
- Ensure you're using the correct provider setting

### Permission Errors

**Error**: "Permission denied"
- Run the application with appropriate permissions
- Check folder and file permissions
- On Windows, try running as Administrator if needed

### Network Issues

**Error**: "Network error" or "Connection failed"
- Check your internet connection
- Verify firewall settings allow Python to access the internet
- Try again if API service is temporarily unavailable

### API Quota Exceeded

**Error**: "API quota exceeded"
- Check your API usage limits
- Wait for quota reset (usually daily)
- Consider upgrading your API plan for higher limits

## Best Practices

1. **Start Small**: Test with a small folder first to understand the workflow
2. **Review Plans**: Always review the organization plan before executing
3. **Backup Important Files**: Make backups before organizing critical directories
4. **Check Logs**: Review logs after execution to verify all operations
5. **Use Dry-Run**: Test with dry-run mode first for large operations

## Limitations

- **API Costs**: AI analysis requires API calls (check provider pricing)
- **File Types**: Some file types may not support deep content analysis
- **Large Directories**: Very large directories (1000+ files) may take time to process
- **Network Required**: Requires internet connection for AI features

## Future Enhancements

- Full Claude AI integration
- Batch processing for very large directories
- Custom organization rules and templates
- Undo functionality
- Support for more file types (PDFs, Office documents)
- Local AI models for offline operation

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues, questions, or suggestions:
- Check the logs in `logs/file_janitor.log`
- Review this README and troubleshooting section
- [Add contact/support information]

---

**🐝 Buzz Sort - Made with Yellow Jacket Pride at Georgia Tech**

*Powered by Claude AI • Themed in Tech Gold & Navy Blue*
