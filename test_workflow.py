#!/usr/bin/env python3
"""
Integration test for Intelligent File Janitor
Tests the complete workflow with sample directories
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
import tempfile

# Import the main application components
from file_janitor import (
    FileScanner, 
    GeminiService, 
    OrganizationPlanner, 
    PlanExecutor,
    AIConfig,
    AIProvider,
    AIServiceFactory,
    OperationLogger
)


class WorkflowTester:
    """Test the complete file organization workflow"""
    
    def __init__(self):
        self.test_dir = None
        self.logger = OperationLogger()
        self.results = {
            'tests_passed': 0,
            'tests_failed': 0,
            'errors': []
        }
    
    def setup_test_directory(self):
        """Create a temporary test directory with sample files"""
        print("\n" + "="*60)
        print("Setting up test directory...")
        print("="*60)
        
        # Create temporary directory
        self.test_dir = Path(tempfile.mkdtemp(prefix="file_janitor_test_"))
        print(f"Test directory: {self.test_dir}")
        
        # Create sample files with various types
        test_files = {
            # Documents
            'report_2024.txt': 'Annual financial report for 2024\nRevenue: $1M\nExpenses: $500K',
            'meeting_notes.txt': 'Team meeting notes from January\nAttendees: John, Jane, Bob',
            'project_plan.md': '# Project Plan\n## Goals\n- Complete phase 1\n- Launch beta',
            
            # Generic names that need renaming
            'document1.txt': 'This is a recipe for chocolate cake\nIngredients: flour, sugar, cocoa',
            'file.txt': 'Travel itinerary for Paris trip\nDay 1: Eiffel Tower\nDay 2: Louvre',
            'untitled.txt': 'Shopping list\n- Milk\n- Bread\n- Eggs',
            
            # Code files
            'script.py': 'def hello():\n    print("Hello World")',
            'config.json': '{"setting": "value", "debug": true}',
            
            # Mixed content
            'IMG_001.txt': 'Photo description: Sunset at the beach',
            'IMG_002.txt': 'Photo description: Mountain hiking trail',
            'data_export.csv': 'name,age,city\nJohn,30,NYC\nJane,25,LA',
        }
        
        for filename, content in test_files.items():
            file_path = self.test_dir / filename
            file_path.write_text(content, encoding='utf-8')
        
        print(f"Created {len(test_files)} test files")
        return True
    
    def test_file_scanning(self):
        """Test 1: File scanning functionality"""
        print("\n" + "="*60)
        print("TEST 1: File Scanning")
        print("="*60)
        
        try:
            scanner = FileScanner()
            files = scanner.scan_directory(str(self.test_dir))
            
            print(f"✓ Scanned directory successfully")
            print(f"✓ Found {len(files)} files")
            
            # Verify metadata extraction
            if files:
                sample_file = files[0]
                required_keys = ['path', 'name', 'extension', 'size', 'modified_date', 'type']
                missing_keys = [key for key in required_keys if key not in sample_file]
                
                if missing_keys:
                    raise AssertionError(f"Missing metadata keys: {missing_keys}")
                
                print(f"✓ File metadata extraction working")
                print(f"  Sample: {sample_file['name']} ({sample_file['type']}, {sample_file['size']} bytes)")
            
            # Test file type categorization
            file_types = scanner.group_by_type(files)
            print(f"✓ File categorization working")
            print(f"  Categories: {list(file_types.keys())}")
            
            self.results['tests_passed'] += 1
            return True
            
        except Exception as e:
            print(f"✗ File scanning test failed: {str(e)}")
            self.results['tests_failed'] += 1
            self.results['errors'].append(f"File scanning: {str(e)}")
            return False
    
    def test_ai_service(self):
        """Test 2: AI service integration"""
        print("\n" + "="*60)
        print("TEST 2: AI Service Integration")
        print("="*60)
        
        try:
            # Load configuration
            config = AIConfig.load_config()
            api_key = AIConfig.get_api_key(AIProvider.GEMINI, config)
            
            if not api_key or len(api_key.strip()) == 0:
                print("⚠ Skipping AI test: No API key configured")
                print("  To test AI features, add your API key to ai_config.json")
                return True
            
            # Create AI service
            ai_service = AIServiceFactory.create_service(AIProvider.GEMINI, api_key)
            
            # Test connection
            print("Testing API connection...")
            if ai_service.test_connection():
                print("✓ AI service connection successful")
            else:
                raise Exception("AI service connection failed")
            
            # Test filename analysis
            print("\nTesting filename analysis...")
            test_filenames = [
                'report_2024.txt',
                'meeting_notes.txt',
                'IMG_001.txt',
                'IMG_002.txt',
                'script.py'
            ]
            
            result = ai_service.analyze_filenames(test_filenames)
            
            if result.get('error'):
                raise Exception(f"Filename analysis failed: {result['error']}")
            
            clusters = result.get('clusters', [])
            print(f"✓ Filename analysis successful")
            print(f"  Generated {len(clusters)} clusters")
            
            for i, cluster in enumerate(clusters[:3], 1):  # Show first 3
                print(f"  Cluster {i}: {cluster.get('category', 'Unknown')} ({len(cluster.get('files', []))} files)")
            
            # Test text content analysis
            print("\nTesting text content analysis...")
            sample_text = "This is a recipe for chocolate cake. Ingredients: flour, sugar, cocoa powder."
            text_result = ai_service.analyze_text_content('document1.txt', sample_text)
            
            if text_result.get('error'):
                print(f"⚠ Text analysis warning: {text_result['error']}")
            else:
                print(f"✓ Text content analysis successful")
                print(f"  Purpose: {text_result.get('purpose', 'Unknown')}")
                print(f"  Suggested name: {text_result.get('suggested_name', 'N/A')}")
            
            self.results['tests_passed'] += 1
            return True
            
        except Exception as e:
            print(f"✗ AI service test failed: {str(e)}")
            self.results['tests_failed'] += 1
            self.results['errors'].append(f"AI service: {str(e)}")
            return False
    
    def test_organization_planning(self):
        """Test 3: Organization plan generation"""
        print("\n" + "="*60)
        print("TEST 3: Organization Plan Generation")
        print("="*60)
        
        try:
            # Scan files
            scanner = FileScanner()
            files = scanner.scan_directory(str(self.test_dir))
            
            # Create mock AI analysis
            mock_analysis = {
                'clusters': [
                    {
                        'category': 'Documents',
                        'files': ['report_2024.txt', 'meeting_notes.txt', 'project_plan.md'],
                        'suggested_folder': 'Documents'
                    },
                    {
                        'category': 'Code',
                        'files': ['script.py', 'config.json'],
                        'suggested_folder': 'Code'
                    },
                    {
                        'category': 'Images',
                        'files': ['IMG_001.txt', 'IMG_002.txt'],
                        'suggested_folder': 'Images'
                    }
                ]
            }
            
            # Create organization plan
            planner = OrganizationPlanner()
            plan = planner.create_plan(files, mock_analysis)
            
            print(f"✓ Organization plan created")
            print(f"  Folders to create: {len(plan.get('folders_to_create', []))}")
            print(f"  File operations: {len(plan.get('file_operations', []))}")
            
            # Verify plan structure
            if 'folders_to_create' not in plan:
                raise AssertionError("Plan missing 'folders_to_create'")
            if 'file_operations' not in plan:
                raise AssertionError("Plan missing 'file_operations'")
            
            # Show sample operations
            operations = plan.get('file_operations', [])
            if operations:
                print(f"\n  Sample operations:")
                for op in operations[:3]:
                    print(f"    - {op.get('action', 'unknown')}: {Path(op.get('source', '')).name}")
            
            self.results['tests_passed'] += 1
            return True
            
        except Exception as e:
            print(f"✗ Organization planning test failed: {str(e)}")
            self.results['tests_failed'] += 1
            self.results['errors'].append(f"Organization planning: {str(e)}")
            return False
    
    def test_plan_execution(self):
        """Test 4: Plan execution (dry-run and actual)"""
        print("\n" + "="*60)
        print("TEST 4: Plan Execution")
        print("="*60)
        
        try:
            # Scan files
            scanner = FileScanner()
            files = scanner.scan_directory(str(self.test_dir))
            
            # Create simple plan (matching the expected format)
            plan = {
                'folders_to_create': ['Documents', 'Code'],
                'file_operations': [
                    {
                        'action': 'move',
                        'source': str(self.test_dir / 'report_2024.txt'),
                        'destination_folder': 'Documents',
                        'original_name': 'report_2024.txt',
                        'new_name': 'report_2024.txt'
                    },
                    {
                        'action': 'move',
                        'source': str(self.test_dir / 'script.py'),
                        'destination_folder': 'Code',
                        'original_name': 'script.py',
                        'new_name': 'script.py'
                    }
                ]
            }
            
            executor = PlanExecutor()
            
            # Test dry-run
            print("\nTesting dry-run mode...")
            dry_result = executor.execute_plan(plan, str(self.test_dir), dry_run=True)
            
            print(f"✓ Dry-run completed")
            print(f"  Would create {dry_result.get('folders_created', 0)} folders")
            print(f"  Would perform {dry_result.get('operations_completed', 0)} operations")
            
            # Verify no actual changes were made
            if (self.test_dir / 'Documents').exists():
                raise AssertionError("Dry-run created actual folders!")
            
            print(f"✓ Dry-run did not modify filesystem")
            
            # Test actual execution
            print("\nTesting actual execution...")
            actual_result = executor.execute_plan(plan, str(self.test_dir), dry_run=False)
            
            print(f"✓ Execution completed")
            print(f"  Created {actual_result.get('folders_created', 0)} folders")
            print(f"  Completed {actual_result.get('operations_completed', 0)} operations")
            print(f"  Failed {actual_result.get('operations_failed', 0)} operations")
            
            # Verify changes were made
            if not (self.test_dir / 'Documents').exists():
                raise AssertionError("Execution did not create folders")
            
            if not (self.test_dir / 'Documents' / 'report_2024.txt').exists():
                raise AssertionError("Execution did not move files")
            
            print(f"✓ Files were moved correctly")
            
            self.results['tests_passed'] += 1
            return True
            
        except Exception as e:
            print(f"✗ Plan execution test failed: {str(e)}")
            self.results['tests_failed'] += 1
            self.results['errors'].append(f"Plan execution: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test 5: Error handling scenarios"""
        print("\n" + "="*60)
        print("TEST 5: Error Handling")
        print("="*60)
        
        try:
            scanner = FileScanner()
            
            # Test with non-existent directory
            print("Testing non-existent directory...")
            files = scanner.scan_directory('/nonexistent/path/12345')
            if scanner.scan_errors:
                print(f"✓ Error properly caught: {scanner.scan_errors[0][:50]}...")
            else:
                print("⚠ No error reported for non-existent directory")
            
            # Test with invalid file operations
            print("\nTesting invalid file operations...")
            executor = PlanExecutor()
            invalid_plan = {
                'folders_to_create': [],
                'file_operations': [
                    {
                        'action': 'move',
                        'source': '/nonexistent/file.txt',
                        'destination': str(self.test_dir / 'file.txt')
                    }
                ]
            }
            
            result = executor.execute_plan(invalid_plan, str(self.test_dir), dry_run=False)
            if result.get('operations_failed', 0) > 0:
                print(f"✓ Invalid operations properly handled")
                print(f"  Failed operations: {result['operations_failed']}")
            else:
                print("⚠ Invalid operations not detected")
            
            self.results['tests_passed'] += 1
            return True
            
        except Exception as e:
            print(f"✗ Error handling test failed: {str(e)}")
            self.results['tests_failed'] += 1
            self.results['errors'].append(f"Error handling: {str(e)}")
            return False
    
    def test_logging(self):
        """Test 6: Logging functionality"""
        print("\n" + "="*60)
        print("TEST 6: Logging System")
        print("="*60)
        
        try:
            logger = OperationLogger()
            
            # Test basic logging
            logger.log_operation('test', 'Test operation', success=True)
            logger.log_scan('/test/path', 10)
            logger.log_ai_analysis(5, 2, success=True)
            
            # Get operation history
            history = logger.get_operation_history()
            
            print(f"✓ Logging system working")
            print(f"  Operations logged: {len(history)}")
            print(f"  Log file: {logger.get_log_file_path()}")
            
            # Verify log file exists
            log_path = Path(logger.get_log_file_path())
            if log_path.exists():
                print(f"✓ Log file created successfully")
            else:
                print(f"⚠ Log file not found")
            
            self.results['tests_passed'] += 1
            return True
            
        except Exception as e:
            print(f"✗ Logging test failed: {str(e)}")
            self.results['tests_failed'] += 1
            self.results['errors'].append(f"Logging: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up test directory"""
        print("\n" + "="*60)
        print("Cleaning up...")
        print("="*60)
        
        try:
            if self.test_dir and self.test_dir.exists():
                shutil.rmtree(self.test_dir)
                print(f"✓ Test directory removed: {self.test_dir}")
        except Exception as e:
            print(f"⚠ Could not remove test directory: {str(e)}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Tests passed: {self.results['tests_passed']}")
        print(f"Tests failed: {self.results['tests_failed']}")
        
        if self.results['errors']:
            print("\nErrors:")
            for error in self.results['errors']:
                print(f"  - {error}")
        
        total_tests = self.results['tests_passed'] + self.results['tests_failed']
        if total_tests > 0:
            success_rate = (self.results['tests_passed'] / total_tests) * 100
            print(f"\nSuccess rate: {success_rate:.1f}%")
        
        print("="*60)
        
        return self.results['tests_failed'] == 0
    
    def run_all_tests(self):
        """Run all workflow tests"""
        print("\n" + "="*60)
        print("INTELLIGENT FILE JANITOR - WORKFLOW TESTS")
        print("="*60)
        
        # Setup
        if not self.setup_test_directory():
            print("Failed to set up test directory")
            return False
        
        # Run tests
        self.test_file_scanning()
        self.test_ai_service()
        self.test_organization_planning()
        self.test_plan_execution()
        self.test_error_handling()
        self.test_logging()
        
        # Cleanup
        self.cleanup()
        
        # Summary
        return self.print_summary()


def main():
    """Main test entry point"""
    tester = WorkflowTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
