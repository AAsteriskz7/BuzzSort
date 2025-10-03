#!/usr/bin/env python3
"""
Test script for the logging functionality
"""

import os
import sys
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the OperationLogger class
from file_janitor import OperationLogger

def test_operation_logger():
    """Test the OperationLogger functionality"""
    print("Testing OperationLogger...")
    print("-" * 60)
    
    # Create logger instance
    logger = OperationLogger()
    print(f"✓ Logger initialized")
    print(f"  Log file: {logger.get_log_file_path()}")
    
    # Test logging various operations
    print("\n1. Testing scan operation logging...")
    logger.log_scan("/test/folder", 150, ["Error 1", "Error 2"])
    print("  ✓ Scan logged")
    
    print("\n2. Testing AI analysis logging...")
    logger.log_ai_analysis(150, 5, success=True)
    print("  ✓ AI analysis logged (success)")
    
    logger.log_ai_analysis(100, 0, success=False, error="API quota exceeded")
    print("  ✓ AI analysis logged (failure)")
    
    print("\n3. Testing plan creation logging...")
    logger.log_plan_creation(5, 150, success=True)
    print("  ✓ Plan creation logged")
    
    print("\n4. Testing plan execution logging...")
    test_result = {
        'dry_run': False,
        'folders_created': 5,
        'operations_completed': 145,
        'operations_failed': 5,
        'log': [
            'Created folder: documents',
            'Moved: file1.txt -> documents/file1.txt',
            '[ERROR] Failed to move file2.txt'
        ]
    }
    logger.log_plan_execution(test_result)
    print("  ✓ Plan execution logged")
    
    print("\n5. Testing error logging...")
    logger.log_error('test_error', 'This is a test error message')
    print("  ✓ Error logged")
    
    print("\n6. Testing operation history retrieval...")
    history = logger.get_operation_history()
    print(f"  ✓ Retrieved {len(history)} operations from history")
    
    print("\n7. Displaying operation history:")
    print("-" * 60)
    for i, op in enumerate(history, 1):
        status = "✓" if op['success'] else "✗"
        print(f"  {i}. [{status}] {op['type']}: {op['details'][:60]}...")
    
    print("\n" + "=" * 60)
    print("✓ All logging tests passed!")
    print(f"✓ Log file created at: {logger.get_log_file_path()}")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        test_operation_logger()
        print("\n✓ Test completed successfully!")
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
