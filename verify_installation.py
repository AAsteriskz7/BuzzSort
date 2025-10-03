#!/usr/bin/env python3
"""
Verify that all dependencies are installed correctly
"""

import sys

def check_imports():
    """Check that all required packages can be imported"""
    print("Checking dependencies...")
    print("=" * 60)
    
    errors = []
    
    # Check tkinter (built-in)
    try:
        import tkinter as tk
        print("✓ tkinter (GUI framework)")
    except ImportError as e:
        errors.append(f"✗ tkinter: {str(e)}")
        print(f"✗ tkinter: Not available")
    
    # Check google-generativeai
    try:
        import google.generativeai as genai
        print("✓ google-generativeai (Gemini AI)")
    except ImportError as e:
        errors.append(f"✗ google-generativeai: {str(e)}")
        print(f"✗ google-generativeai: Not installed")
    
    # Check anthropic
    try:
        import anthropic
        print("✓ anthropic (Claude AI)")
    except ImportError as e:
        errors.append(f"✗ anthropic: {str(e)}")
        print(f"✗ anthropic: Not installed")
    
    # Check Pillow
    try:
        from PIL import Image
        print("✓ Pillow (Image processing)")
    except ImportError as e:
        errors.append(f"✗ Pillow: {str(e)}")
        print(f"✗ Pillow: Not installed")
    
    # Check standard library modules
    try:
        import pathlib
        import shutil
        import json
        import logging
        print("✓ Standard library modules")
    except ImportError as e:
        errors.append(f"✗ Standard library: {str(e)}")
        print(f"✗ Standard library: Missing modules")
    
    print("=" * 60)
    
    if errors:
        print(f"\n❌ {len(errors)} error(s) found:")
        for error in errors:
            print(f"  {error}")
        print("\nPlease install missing dependencies:")
        print("  pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All dependencies are installed correctly!")
        return True

def check_config():
    """Check if configuration file exists"""
    print("\nChecking configuration...")
    print("=" * 60)
    
    import os
    from pathlib import Path
    
    config_file = Path("ai_config.json")
    
    if config_file.exists():
        print("✓ ai_config.json found")
        
        try:
            import json
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            provider = config.get('provider', 'not set')
            has_gemini = bool(config.get('gemini_api_key', '').strip())
            has_claude = bool(config.get('claude_api_key', '').strip())
            
            print(f"  Provider: {provider}")
            print(f"  Gemini API key: {'✓ configured' if has_gemini else '✗ not set'}")
            print(f"  Claude API key: {'✓ configured' if has_claude else '✗ not set'}")
            
            if provider == 'gemini' and not has_gemini:
                print("\n⚠ Warning: Gemini provider selected but no API key configured")
            elif provider == 'claude' and not has_claude:
                print("\n⚠ Warning: Claude provider selected but no API key configured")
            
        except Exception as e:
            print(f"✗ Error reading config: {str(e)}")
    else:
        print("✗ ai_config.json not found")
        print("\n⚠ Please create ai_config.json with your API keys")
        print("  See .env.example for template")
    
    print("=" * 60)

def check_python_version():
    """Check Python version"""
    print("\nChecking Python version...")
    print("=" * 60)
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    print(f"Python version: {version_str}")
    
    if version.major >= 3 and version.minor >= 9:
        print("✓ Python version is compatible (3.9+)")
        return True
    else:
        print("✗ Python 3.9 or higher is required")
        return False
    
    print("=" * 60)

def main():
    """Main verification function"""
    print("\n" + "=" * 60)
    print("INTELLIGENT FILE JANITOR - INSTALLATION VERIFICATION")
    print("=" * 60)
    
    # Check Python version
    python_ok = check_python_version()
    
    # Check imports
    imports_ok = check_imports()
    
    # Check configuration
    check_config()
    
    # Final summary
    print("\n" + "=" * 60)
    if python_ok and imports_ok:
        print("✅ Installation verified successfully!")
        print("\nYou can now run the application:")
        print("  python file_janitor.py")
        print("\nOr run tests:")
        print("  python test_workflow.py")
    else:
        print("❌ Installation verification failed")
        print("\nPlease fix the issues above and try again")
    print("=" * 60)
    
    return python_ok and imports_ok

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
