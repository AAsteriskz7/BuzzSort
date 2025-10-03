#!/usr/bin/env python3
"""
Test Claude AI integration
"""

import sys
from file_janitor import ClaudeService, AIConfig, AIProvider

def test_claude():
    """Test Claude service"""
    print("=" * 60)
    print("CLAUDE AI SERVICE TEST")
    print("=" * 60)
    
    # Load config
    config = AIConfig.load_config()
    claude_key = config.get('claude_api_key', '')
    
    if not claude_key or len(claude_key.strip()) == 0:
        print("\n❌ No Claude API key found!")
        print("\nPlease add your Claude API key to ai_config.json:")
        print('  "claude_api_key": "sk-ant-your-key-here"')
        print("\nOr set environment variable:")
        print("  export CLAUDE_API_KEY=sk-ant-your-key-here")
        return False
    
    print(f"\n✓ Claude API key found (length: {len(claude_key)})")
    
    # Initialize service
    print("\nInitializing Claude service...")
    try:
        service = ClaudeService(claude_key)
        print("✓ Claude service initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {str(e)}")
        return False
    
    # Test connection
    print("\nTesting API connection...")
    try:
        if service.test_connection():
            print("✓ Connection successful!")
        else:
            print("❌ Connection failed")
            return False
    except Exception as e:
        print(f"❌ Connection test error: {str(e)}")
        return False
    
    # Test filename analysis
    print("\nTesting filename analysis...")
    test_files = [
        'report_2024.txt',
        'meeting_notes.txt',
        'IMG_001.jpg',
        'IMG_002.jpg',
        'script.py',
        'data.csv'
    ]
    
    try:
        result = service.analyze_filenames(test_files)
        
        if result.get('error'):
            print(f"❌ Analysis failed: {result['error']}")
            return False
        
        clusters = result.get('clusters', [])
        print(f"✓ Analysis successful!")
        print(f"  Generated {len(clusters)} clusters")
        
        for i, cluster in enumerate(clusters, 1):
            print(f"\n  Cluster {i}: {cluster.get('category', 'Unknown')}")
            print(f"    Files: {len(cluster.get('files', []))}")
            print(f"    Folder: {cluster.get('suggested_folder', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Filename analysis error: {str(e)}")
        return False
    
    # Test text content analysis
    print("\n" + "=" * 60)
    print("Testing text content analysis...")
    sample_text = "This is a recipe for chocolate cake. Ingredients: flour, sugar, cocoa powder, eggs."
    
    try:
        result = service.analyze_text_content('document1.txt', sample_text)
        
        if result.get('error'):
            print(f"❌ Text analysis failed: {result['error']}")
        else:
            print(f"✓ Text analysis successful!")
            print(f"  Purpose: {result.get('purpose', 'Unknown')}")
            print(f"  Suggested name: {result.get('suggested_name', 'N/A')}")
            print(f"  Confidence: {result.get('confidence', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Text analysis error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ Claude integration test complete!")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    success = test_claude()
    sys.exit(0 if success else 1)
