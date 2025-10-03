#!/usr/bin/env python3
"""
Intelligent File Janitor - AI-powered file organization tool
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import stat
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from abc import ABC, abstractmethod
from enum import Enum
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import json
from PIL import Image


class AIProvider(Enum):
    """Enum for supported AI providers"""
    GEMINI = "gemini"
    CLAUDE = "claude"


class AIConfig:
    """Configuration management for AI services"""
    
    CONFIG_FILE = "ai_config.json"
    
    @staticmethod
    def load_config() -> Dict:
        """
        Load AI configuration from file or environment variables
        
        Returns:
            Dictionary with configuration settings
        """
        config = {
            'provider': 'gemini',
            'gemini_api_key': '',
            'claude_api_key': ''
        }
        
        # Try to load from config file
        try:
            if os.path.exists(AIConfig.CONFIG_FILE):
                with open(AIConfig.CONFIG_FILE, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
        except Exception as e:
            print(f"Warning: Could not load config file: {str(e)}")
        
        # Override with environment variables if present
        if os.environ.get('GEMINI_API_KEY'):
            config['gemini_api_key'] = os.environ.get('GEMINI_API_KEY')
        if os.environ.get('CLAUDE_API_KEY'):
            config['claude_api_key'] = os.environ.get('CLAUDE_API_KEY')
        if os.environ.get('AI_PROVIDER'):
            config['provider'] = os.environ.get('AI_PROVIDER')
        
        return config
    
    @staticmethod
    def save_config(config: Dict) -> bool:
        """
        Save AI configuration to file
        
        Args:
            config: Configuration dictionary to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(AIConfig.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {str(e)}")
            return False
    
    @staticmethod
    def get_api_key(provider: AIProvider, config: Dict) -> Optional[str]:
        """
        Get API key for specified provider
        
        Args:
            provider: AIProvider enum value
            config: Configuration dictionary
            
        Returns:
            API key string or None if not found
        """
        if provider == AIProvider.GEMINI:
            return config.get('gemini_api_key', '')
        elif provider == AIProvider.CLAUDE:
            return config.get('claude_api_key', '')
        return None


class AIServiceInterface(ABC):
    """Abstract base class for AI service providers"""
    
    @abstractmethod
    def analyze_filenames(self, filenames: List[str]) -> Dict:
        """
        Analyze a batch of filenames and group them into logical clusters
        
        Args:
            filenames: List of filenames to analyze
            
        Returns:
            Dictionary with cluster information
        """
        pass
    
    @abstractmethod
    def analyze_text_content(self, filename: str, text_preview: str) -> Dict:
        """
        Analyze text content to determine file purpose and suggest better name
        
        Args:
            filename: Original filename
            text_preview: Preview of text content
            
        Returns:
            Dictionary with analysis results and name suggestions
        """
        pass
    
    @abstractmethod
    def analyze_image(self, image_path: str) -> Dict:
        """
        Analyze image content using vision capabilities
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with scene description and name suggestions
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if the API connection is working
        
        Returns:
            True if connection successful, False otherwise
        """
        pass


class GeminiService(AIServiceInterface):
    """Google Gemini AI service implementation"""
    
    def __init__(self, api_key: str):
        """
        Initialize Gemini service
        
        Args:
            api_key: Google Gemini API key
        """
        self.api_key = api_key
        self.model = None
        self.vision_model = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Gemini API client"""
        try:
            # Configure the API key
            genai.configure(api_key=self.api_key)
            
            # Initialize text model (Gemini Pro)
            self.model = genai.GenerativeModel(
                'gemini-1.5-flash',
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            # Initialize vision model (Gemini Pro Vision)
            self.vision_model = genai.GenerativeModel(
                'gemini-1.5-flash',
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Gemini client: {str(e)}")
    
    def analyze_filenames(self, filenames: List[str]) -> Dict:
        """
        Analyze filenames using Gemini API
        
        Args:
            filenames: List of filenames to analyze
            
        Returns:
            Dictionary with cluster information
        """
        try:
            if not self.model:
                return {
                    'clusters': [],
                    'error': 'Model not initialized'
                }
            
            # Limit batch size to avoid token limits
            batch_size = 100
            if len(filenames) > batch_size:
                filenames = filenames[:batch_size]
            
            # Create prompt for filename clustering
            prompt = f"""Analyze these {len(filenames)} filenames and group them into logical categories based on their names, patterns, and likely content.

Filenames:
{chr(10).join(f"- {name}" for name in filenames)}

Please organize these files into 3-7 meaningful clusters. For each cluster:
1. Give it a descriptive category name
2. List which files belong to it
3. Provide a brief explanation of why they're grouped together

Format your response as JSON with this structure:
{{
  "clusters": [
    {{
      "category": "Category Name",
      "files": ["file1.txt", "file2.txt"],
      "description": "Brief explanation",
      "suggested_folder": "suggested_folder_name"
    }}
  ]
}}"""
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                return {
                    'clusters': [],
                    'error': 'Empty response from API'
                }
            
            # Parse JSON response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            return {
                'clusters': result.get('clusters', []),
                'total_files': len(filenames),
                'error': None
            }
            
        except json.JSONDecodeError as e:
            return {
                'clusters': [],
                'error': f'Failed to parse AI response: {str(e)}',
                'raw_response': response.text if response else None
            }
        except Exception as e:
            return {
                'clusters': [],
                'error': f'Analysis failed: {str(e)}'
            }
    
    def analyze_text_content(self, filename: str, text_preview: str) -> Dict:
        """
        Analyze text content using Gemini API
        
        Args:
            filename: Original filename
            text_preview: Preview of text content
            
        Returns:
            Dictionary with analysis results
        """
        try:
            if not self.model:
                return {
                    'purpose': 'Unknown',
                    'suggested_name': filename,
                    'error': 'Model not initialized'
                }
            
            # Create prompt for content analysis
            prompt = f"""Analyze this document and suggest a better, more descriptive filename.

Current filename: {filename}

Document content preview:
{text_preview[:2000]}

Based on the content, provide:
1. The main purpose/topic of this document
2. A suggested descriptive filename (keep extension, use underscores or hyphens, be concise but clear)
3. A brief explanation of why this name is better

Format your response as JSON:
{{
  "purpose": "Brief description of document purpose",
  "suggested_name": "better_filename.ext",
  "explanation": "Why this name is better",
  "confidence": "high/medium/low"
}}"""
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                return {
                    'purpose': 'Unknown',
                    'suggested_name': filename,
                    'error': 'Empty response from API'
                }
            
            # Parse JSON response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            return {
                'purpose': result.get('purpose', 'Unknown'),
                'suggested_name': result.get('suggested_name', filename),
                'explanation': result.get('explanation', ''),
                'confidence': result.get('confidence', 'medium'),
                'error': None
            }
            
        except json.JSONDecodeError as e:
            return {
                'purpose': 'Unknown',
                'suggested_name': filename,
                'error': f'Failed to parse AI response: {str(e)}',
                'raw_response': response.text if response else None
            }
        except Exception as e:
            return {
                'purpose': 'Unknown',
                'suggested_name': filename,
                'error': f'Analysis failed: {str(e)}'
            }
    
    def analyze_image(self, image_path: str) -> Dict:
        """
        Analyze image using Gemini Vision API
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with scene description and suggestions
        """
        try:
            if not self.vision_model:
                return {
                    'description': 'Unknown',
                    'suggested_name': Path(image_path).name,
                    'error': 'Vision model not initialized'
                }
            
            # Load the image
            try:
                img = Image.open(image_path)
            except Exception as e:
                return {
                    'description': 'Unknown',
                    'suggested_name': Path(image_path).name,
                    'error': f'Could not open image: {str(e)}'
                }
            
            # Get current filename
            current_name = Path(image_path).name
            extension = Path(image_path).suffix
            
            # Create prompt for image analysis
            prompt = f"""Analyze this image and suggest a descriptive filename.

Current filename: {current_name}

Please provide:
1. A detailed description of what's in the image (main subject, setting, notable features)
2. A suggested descriptive filename (keep the {extension} extension, use underscores or hyphens, be concise but clear)
3. Key elements that make this image unique

Format your response as JSON:
{{
  "description": "Detailed description of the image",
  "suggested_name": "descriptive_name{extension}",
  "key_elements": ["element1", "element2", "element3"],
  "confidence": "high/medium/low"
}}"""
            
            # Generate response with image
            response = self.vision_model.generate_content([prompt, img])
            
            if not response or not response.text:
                return {
                    'description': 'Unknown',
                    'suggested_name': current_name,
                    'error': 'Empty response from API'
                }
            
            # Parse JSON response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            return {
                'description': result.get('description', 'Unknown'),
                'suggested_name': result.get('suggested_name', current_name),
                'key_elements': result.get('key_elements', []),
                'confidence': result.get('confidence', 'medium'),
                'error': None
            }
            
        except json.JSONDecodeError as e:
            return {
                'description': 'Unknown',
                'suggested_name': Path(image_path).name,
                'error': f'Failed to parse AI response: {str(e)}',
                'raw_response': response.text if response else None
            }
        except Exception as e:
            return {
                'description': 'Unknown',
                'suggested_name': Path(image_path).name,
                'error': f'Image analysis failed: {str(e)}'
            }
    
    def test_connection(self) -> bool:
        """
        Test Gemini API connection
        
        Returns:
            True if connection successful
        """
        try:
            if not self.model:
                return False
            
            # Send a simple test prompt
            response = self.model.generate_content("Hello, respond with 'OK' if you can read this.")
            
            # Check if we got a valid response
            if response and response.text:
                return True
            return False
            
        except Exception as e:
            print(f"Gemini connection test failed: {str(e)}")
            return False


class ClaudeService(AIServiceInterface):
    """Anthropic Claude AI service implementation (stub for future migration)"""
    
    def __init__(self, api_key: str):
        """
        Initialize Claude service
        
        Args:
            api_key: Anthropic Claude API key
        """
        self.api_key = api_key
        self.client = None
        # Claude initialization will be implemented when migrating from Gemini
    
    def analyze_filenames(self, filenames: List[str]) -> Dict:
        """
        Analyze filenames using Claude API (stub)
        
        Args:
            filenames: List of filenames to analyze
            
        Returns:
            Dictionary with cluster information
        """
        return {
            'clusters': [],
            'error': 'Claude service not yet implemented'
        }
    
    def analyze_text_content(self, filename: str, text_preview: str) -> Dict:
        """
        Analyze text content using Claude API (stub)
        
        Args:
            filename: Original filename
            text_preview: Preview of text content
            
        Returns:
            Dictionary with analysis results
        """
        return {
            'purpose': 'Unknown',
            'suggested_name': filename,
            'error': 'Claude service not yet implemented'
        }
    
    def analyze_image(self, image_path: str) -> Dict:
        """
        Analyze image using Claude Vision API (stub)
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with scene description and suggestions
        """
        return {
            'description': 'Unknown',
            'suggested_name': Path(image_path).name,
            'error': 'Claude service not yet implemented'
        }
    
    def test_connection(self) -> bool:
        """
        Test Claude API connection (stub)
        
        Returns:
            False (not implemented)
        """
        return False


class AIServiceFactory:
    """Factory class for creating AI service instances"""
    
    @staticmethod
    def create_service(provider: AIProvider, api_key: str) -> AIServiceInterface:
        """
        Create an AI service instance based on provider
        
        Args:
            provider: AIProvider enum value
            api_key: API key for the provider
            
        Returns:
            AIServiceInterface implementation
            
        Raises:
            ValueError: If provider is not supported
        """
        if provider == AIProvider.GEMINI:
            return GeminiService(api_key)
        elif provider == AIProvider.CLAUDE:
            return ClaudeService(api_key)
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")


class FileScanner:
    """Handles directory scanning and file metadata extraction"""
    
    def __init__(self):
        self.scan_errors = []
    
    def extract_text_preview(self, file_path: str, max_chars: int = 2000) -> Optional[str]:
        """
        Extract text preview from common document formats
        
        Args:
            file_path: Path to the file
            max_chars: Maximum characters to extract
            
        Returns:
            Text preview string or None if extraction fails
        """
        try:
            path_obj = Path(file_path)
            extension = path_obj.suffix.lower()
            
            # Text-based formats that can be read directly
            text_extensions = {'.txt', '.md', '.csv', '.json', '.xml', '.html', '.htm', 
                             '.py', '.js', '.java', '.cpp', '.c', '.h', '.css', '.sql',
                             '.log', '.ini', '.cfg', '.yaml', '.yml', '.toml'}
            
            if extension in text_extensions:
                # Try different encodings
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read(max_chars)
                            return content
                    except UnicodeDecodeError:
                        continue
                    except Exception:
                        break
            
            # For other formats, return None (could be extended with libraries like python-docx, PyPDF2, etc.)
            return None
            
        except Exception as e:
            self.scan_errors.append(f"Could not extract text from {file_path}: {str(e)}")
            return None
    
    def scan_directory(self, path: str) -> List[Dict]:
        """
        Scan directory recursively and return list of file information dictionaries
        
        Args:
            path: Directory path to scan
            
        Returns:
            List of dictionaries containing file metadata
        """
        self.scan_errors = []  # Reset errors for new scan
        files = []
        
        try:
            root_path = Path(path)
            if not root_path.exists():
                self.scan_errors.append(f"Directory does not exist: {path}")
                return files
            
            if not root_path.is_dir():
                self.scan_errors.append(f"Path is not a directory: {path}")
                return files
            
            # Recursively scan all files
            for file_path in root_path.rglob('*'):
                if file_path.is_file():
                    file_info = self.get_file_info(str(file_path))
                    if file_info:  # Only add if we successfully got file info
                        files.append(file_info)
                        
        except PermissionError as e:
            self.scan_errors.append(f"Permission denied accessing directory: {path} - {str(e)}")
        except Exception as e:
            self.scan_errors.append(f"Unexpected error scanning directory: {path} - {str(e)}")
        
        return files
    
    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """
        Extract metadata from a single file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file metadata or None if error occurred
        """
        try:
            path_obj = Path(file_path)
            
            # Get file stats
            file_stats = path_obj.stat()
            
            # Extract basic information
            file_info = {
                'path': str(path_obj.absolute()),
                'name': path_obj.name,
                'extension': path_obj.suffix.lower(),
                'size': file_stats.st_size,
                'modified_date': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                'created_date': datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                'type': self._categorize_file_type(path_obj.suffix.lower())
            }
            
            return file_info
            
        except PermissionError:
            self.scan_errors.append(f"Permission denied accessing file: {file_path}")
            return None
        except FileNotFoundError:
            self.scan_errors.append(f"File not found: {file_path}")
            return None
        except OSError as e:
            self.scan_errors.append(f"OS error accessing file: {file_path} - {str(e)}")
            return None
        except Exception as e:
            self.scan_errors.append(f"Unexpected error processing file: {file_path} - {str(e)}")
            return None
    
    def _categorize_file_type(self, extension: str) -> str:
        """
        Categorize file based on extension
        
        Args:
            extension: File extension (with dot)
            
        Returns:
            Category string: 'document', 'image', 'video', or 'other'
        """
        document_extensions = {
            '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', 
            '.ppt', '.pptx', '.csv', '.md', '.html', '.htm', '.xml', '.json'
        }
        
        image_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.svg', 
            '.webp', '.ico', '.raw', '.cr2', '.nef', '.arw'
        }
        
        video_extensions = {
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', 
            '.mpg', '.mpeg', '.3gp', '.ogv'
        }
        
        if extension in document_extensions:
            return 'document'
        elif extension in image_extensions:
            return 'image'
        elif extension in video_extensions:
            return 'video'
        else:
            return 'other'
    
    def group_by_type(self, files: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group files by their type category
        
        Args:
            files: List of file information dictionaries
            
        Returns:
            Dictionary with type categories as keys and file lists as values
        """
        grouped = {
            'document': [],
            'image': [],
            'video': [],
            'other': []
        }
        
        for file_info in files:
            file_type = file_info.get('type', 'other')
            grouped[file_type].append(file_info)
        
        return grouped
    
    def get_file_type_stats(self, files: List[Dict]) -> Dict[str, Dict]:
        """
        Get detailed statistics for each file type category
        
        Args:
            files: List of file information dictionaries
            
        Returns:
            Dictionary with type categories and their statistics
        """
        grouped = self.group_by_type(files)
        stats = {}
        
        for file_type, file_list in grouped.items():
            if not file_list:
                continue
                
            total_size = sum(f['size'] for f in file_list)
            extensions = defaultdict(int)
            
            for file_info in file_list:
                ext = file_info['extension'] or 'no extension'
                extensions[ext] += 1
            
            # Get most common extensions (top 3)
            common_extensions = sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:3]
            
            stats[file_type] = {
                'count': len(file_list),
                'total_size': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'common_extensions': common_extensions,
                'files': file_list
            }
        
        return stats
    
    def get_date_based_suggestions(self, files: List[Dict]) -> List[Dict]:
        """
        Generate date-based filtering suggestions for intelligent organization
        
        Args:
            files: List of file information dictionaries
            
        Returns:
            List of suggestion dictionaries with filtering options
        """
        if not files:
            return []
        
        suggestions = []
        now = datetime.now()
        
        # Group files by time periods
        recent_files = []  # Last 30 days
        this_month_files = []
        last_month_files = []
        older_files = []
        
        for file_info in files:
            try:
                modified_date = datetime.fromisoformat(file_info['modified_date'])
                days_ago = (now - modified_date).days
                
                if days_ago <= 30:
                    recent_files.append(file_info)
                
                if modified_date.year == now.year and modified_date.month == now.month:
                    this_month_files.append(file_info)
                elif modified_date.year == now.year and modified_date.month == (now.month - 1 if now.month > 1 else 12):
                    last_month_files.append(file_info)
                elif days_ago > 30:
                    older_files.append(file_info)
                    
            except (ValueError, KeyError):
                # Skip files with invalid dates
                older_files.append(file_info)
        
        # Create suggestions based on file counts
        if len(recent_files) > 0:
            suggestions.append({
                'title': f'Recent files (last 30 days)',
                'description': f'{len(recent_files)} files to organize',
                'file_count': len(recent_files),
                'files': recent_files,
                'priority': 'high' if len(recent_files) < 100 else 'medium'
            })
        
        if len(this_month_files) > 0 and len(this_month_files) != len(recent_files):
            month_name = now.strftime('%B %Y')
            suggestions.append({
                'title': f'This month ({month_name})',
                'description': f'{len(this_month_files)} files from current month',
                'file_count': len(this_month_files),
                'files': this_month_files,
                'priority': 'medium'
            })
        
        if len(last_month_files) > 0:
            last_month_date = now.replace(month=now.month-1 if now.month > 1 else 12, 
                                        year=now.year if now.month > 1 else now.year-1)
            month_name = last_month_date.strftime('%B %Y')
            suggestions.append({
                'title': f'Last month ({month_name})',
                'description': f'{len(last_month_files)} files from previous month',
                'file_count': len(last_month_files),
                'files': last_month_files,
                'priority': 'medium'
            })
        
        # For large collections, suggest breaking down by clusters
        if len(older_files) > 200:
            suggestions.append({
                'title': f'Older files (large collection)',
                'description': f'{len(older_files)} files - consider processing in smaller batches',
                'file_count': len(older_files),
                'files': older_files,
                'priority': 'low'
            })
        elif len(older_files) > 0:
            suggestions.append({
                'title': f'Older files',
                'description': f'{len(older_files)} files older than 30 days',
                'file_count': len(older_files),
                'files': older_files,
                'priority': 'low'
            })
        
        # Sort suggestions by priority and file count
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        suggestions.sort(key=lambda x: (priority_order[x['priority']], -x['file_count']))
        
        return suggestions
    
    def get_scan_errors(self) -> List[str]:
        """
        Get list of errors that occurred during the last scan
        
        Returns:
            List of error messages
        """
        return self.scan_errors.copy()


class FileJanitorApp:
    """Main application class for the Intelligent File Janitor"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.selected_folder = None
        self.scanner = FileScanner()
        self.scanned_files = []
        
        # Load AI configuration
        self.config = AIConfig.load_config()
        
        # AI service configuration
        provider_str = self.config.get('provider', 'gemini')
        self.ai_provider = AIProvider.GEMINI if provider_str == 'gemini' else AIProvider.CLAUDE
        self.ai_service = None  # Will be initialized when API key is provided
        
        self.setup_gui()
        self._initialize_ai_service()
    
    def setup_gui(self):
        """Set up the basic Tkinter GUI framework"""
        # Configure main window
        self.root.title("Intelligent File Janitor")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for responsive layout
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Folder selection section
        ttk.Label(main_frame, text="Select Folder to Organize:", 
                 font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, 
                                                  sticky=tk.W, pady=(0, 10))
        
        # Folder selection button and display
        ttk.Button(main_frame, text="Browse Folder", 
                  command=self.select_folder).grid(row=1, column=0, 
                                                  sticky=tk.W, padx=(0, 10))
        
        self.folder_label = ttk.Label(main_frame, text="No folder selected", 
                                     foreground="gray")
        self.folder_label.grid(row=1, column=1, sticky=(tk.W, tk.E))
        
        # Analysis results section
        ttk.Label(main_frame, text="Analysis Results:", 
                 font=('Arial', 12, 'bold')).grid(row=2, column=0, columnspan=2, 
                                                  sticky=(tk.W, tk.N), pady=(20, 5))
        
        # Analysis results display area
        self.analysis_frame = ttk.Frame(main_frame, relief="sunken", borderwidth=1)
        self.analysis_frame.grid(row=3, column=0, columnspan=2, 
                               sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        self.analysis_frame.columnconfigure(0, weight=1)
        self.analysis_frame.rowconfigure(0, weight=1)
        
        # Scrollable text widget for analysis results
        analysis_scroll = ttk.Scrollbar(self.analysis_frame)
        analysis_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.analysis_text = tk.Text(self.analysis_frame, wrap=tk.WORD, 
                                   yscrollcommand=analysis_scroll.set,
                                   state=tk.DISABLED, height=8)
        self.analysis_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        analysis_scroll.config(command=self.analysis_text.yview)
        
        # Organization plan section
        ttk.Label(main_frame, text="Organization Plan:", 
                 font=('Arial', 12, 'bold')).grid(row=4, column=0, columnspan=2, 
                                                  sticky=(tk.W, tk.N), pady=(0, 5))
        
        # Organization plan display area
        self.plan_frame = ttk.Frame(main_frame, relief="sunken", borderwidth=1)
        self.plan_frame.grid(row=5, column=0, columnspan=2, 
                           sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        self.plan_frame.columnconfigure(0, weight=1)
        self.plan_frame.rowconfigure(0, weight=1)
        
        # Scrollable text widget for organization plan
        plan_scroll = ttk.Scrollbar(self.plan_frame)
        plan_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.plan_text = tk.Text(self.plan_frame, wrap=tk.WORD, 
                               yscrollcommand=plan_scroll.set,
                               state=tk.DISABLED, height=8)
        self.plan_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        plan_scroll.config(command=self.plan_text.yview)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(10, 0))
        
        self.analyze_button = ttk.Button(button_frame, text="Analyze Files", 
                                       command=self.analyze_files, state=tk.DISABLED)
        self.analyze_button.grid(row=0, column=0, padx=(0, 10))
        
        self.execute_button = ttk.Button(button_frame, text="Execute Plan", 
                                       command=self.execute_plan, state=tk.DISABLED)
        self.execute_button.grid(row=0, column=1)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Select a folder to begin")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                             relief="sunken", anchor=tk.W)
        status_bar.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), 
                       pady=(10, 0))
    
    def select_folder(self):
        """Handle folder selection"""
        folder = filedialog.askdirectory(title="Select folder to organize")
        if folder:
            self.selected_folder = folder
            self.folder_label.config(text=folder, foreground="black")
            self.analyze_button.config(state=tk.NORMAL)
            self.status_var.set(f"Folder selected: {os.path.basename(folder)}")
            
            # Clear previous results
            self.clear_display_areas()
    
    def clear_display_areas(self):
        """Clear the analysis and plan display areas"""
        self.analysis_text.config(state=tk.NORMAL)
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.config(state=tk.DISABLED)
        
        self.plan_text.config(state=tk.NORMAL)
        self.plan_text.delete(1.0, tk.END)
        self.plan_text.config(state=tk.DISABLED)
        
        self.execute_button.config(state=tk.DISABLED)
    
    def analyze_files(self):
        """Scan and analyze files in the selected directory"""
        if not self.selected_folder:
            messagebox.showerror("Error", "Please select a folder first")
            return
        
        self.status_var.set("Scanning files...")
        self.root.update()  # Update GUI to show status
        
        try:
            # Scan the directory
            self.scanned_files = self.scanner.scan_directory(self.selected_folder)
            
            # Get detailed file type statistics
            file_type_stats = self.scanner.get_file_type_stats(self.scanned_files)
            
            # Get date-based filtering suggestions
            date_suggestions = self.scanner.get_date_based_suggestions(self.scanned_files)
            
            # Display results
            self.display_analysis_results(file_type_stats, date_suggestions)
            
            # Check for errors
            errors = self.scanner.get_scan_errors()
            if errors:
                self.display_scan_errors(errors)
            
            # Perform AI-based filename analysis if service is available
            if self.ai_service and len(self.scanned_files) > 0:
                self.status_var.set("Running AI analysis on filenames...")
                self.root.update()
                self.perform_ai_filename_analysis()
            
            self.status_var.set(f"Analysis complete - Found {len(self.scanned_files)} files")
            
        except Exception as e:
            messagebox.showerror("Scan Error", f"An error occurred during scanning: {str(e)}")
            self.status_var.set("Scan failed")
    
    def perform_ai_filename_analysis(self):
        """Perform AI-based filename clustering analysis"""
        try:
            # Extract just the filenames
            filenames = [file_info['name'] for file_info in self.scanned_files]
            
            # Limit to first 100 files for initial analysis
            if len(filenames) > 100:
                filenames = filenames[:100]
                self.status_var.set(f"Analyzing first 100 of {len(self.scanned_files)} files...")
                self.root.update()
            
            # Call AI service
            result = self.ai_service.analyze_filenames(filenames)
            
            # Display clustering results
            self.display_ai_clusters(result)
            
        except Exception as e:
            self.plan_text.config(state=tk.NORMAL)
            self.plan_text.insert(tk.END, f"\n⚠️ AI Analysis Error: {str(e)}\n")
            self.plan_text.config(state=tk.DISABLED)
    
    def perform_content_analysis(self, file_info: Dict) -> Dict:
        """
        Perform content-based analysis on a single file
        
        Args:
            file_info: File information dictionary
            
        Returns:
            Analysis result dictionary
        """
        try:
            if not self.ai_service:
                return {
                    'error': 'AI service not available'
                }
            
            # Check file type
            file_type = file_info.get('type', 'other')
            
            # For images, use image analysis
            if file_type == 'image':
                result = self.ai_service.analyze_image(file_info['path'])
                return result
            
            # For documents, use text content analysis
            elif file_type == 'document':
                # Extract text preview
                text_preview = self.scanner.extract_text_preview(file_info['path'])
                
                if not text_preview:
                    return {
                        'error': 'Could not extract text content'
                    }
                
                # Analyze content
                result = self.ai_service.analyze_text_content(
                    file_info['name'],
                    text_preview
                )
                
                return result
            
            else:
                return {
                    'error': f'Content analysis not supported for file type: {file_type}'
                }
            
        except Exception as e:
            return {
                'error': f'Content analysis failed: {str(e)}'
            }
    
    def display_ai_clusters(self, result: Dict):
        """Display AI clustering results in the plan text area"""
        self.plan_text.config(state=tk.NORMAL)
        self.plan_text.delete(1.0, tk.END)
        
        if result.get('error'):
            self.plan_text.insert(tk.END, f"AI ANALYSIS ERROR\n")
            self.plan_text.insert(tk.END, f"{'='*60}\n\n")
            self.plan_text.insert(tk.END, f"Error: {result['error']}\n")
            
            if result.get('raw_response'):
                self.plan_text.insert(tk.END, f"\nRaw response:\n{result['raw_response'][:500]}\n")
        else:
            clusters = result.get('clusters', [])
            total_files = result.get('total_files', 0)
            
            self.plan_text.insert(tk.END, f"AI-POWERED FILE ORGANIZATION PLAN\n")
            self.plan_text.insert(tk.END, f"{'='*60}\n\n")
            self.plan_text.insert(tk.END, f"Analyzed {total_files} files and identified {len(clusters)} categories:\n\n")
            
            for i, cluster in enumerate(clusters, 1):
                category = cluster.get('category', 'Unknown')
                files = cluster.get('files', [])
                description = cluster.get('description', 'No description')
                suggested_folder = cluster.get('suggested_folder', category.lower().replace(' ', '_'))
                
                self.plan_text.insert(tk.END, f"📁 Category {i}: {category}\n")
                self.plan_text.insert(tk.END, f"   Suggested folder: {suggested_folder}/\n")
                self.plan_text.insert(tk.END, f"   Files: {len(files)}\n")
                self.plan_text.insert(tk.END, f"   Description: {description}\n")
                
                # Show first few files as examples
                example_count = min(5, len(files))
                if example_count > 0:
                    self.plan_text.insert(tk.END, f"   Examples:\n")
                    for file in files[:example_count]:
                        self.plan_text.insert(tk.END, f"      • {file}\n")
                    
                    if len(files) > example_count:
                        self.plan_text.insert(tk.END, f"      ... and {len(files) - example_count} more\n")
                
                self.plan_text.insert(tk.END, "\n")
            
            self.plan_text.insert(tk.END, f"\n💡 TIP: Review these suggestions and use 'Execute Plan' to organize files.\n")
        
        self.plan_text.config(state=tk.DISABLED)
    
    def display_analysis_results(self, file_type_stats: Dict[str, Dict], date_suggestions: List[Dict]):
        """Display the enhanced analysis results in the analysis text area"""
        self.analysis_text.config(state=tk.NORMAL)
        self.analysis_text.delete(1.0, tk.END)
        
        # Summary
        total_files = sum(stats['count'] for stats in file_type_stats.values())
        total_size_mb = sum(stats['total_size_mb'] for stats in file_type_stats.values())
        
        self.analysis_text.insert(tk.END, f"FILE ANALYSIS RESULTS\n")
        self.analysis_text.insert(tk.END, f"{'='*60}\n\n")
        self.analysis_text.insert(tk.END, f"Total files found: {total_files:,}\n")
        self.analysis_text.insert(tk.END, f"Total size: {total_size_mb:.1f} MB\n\n")
        
        # Enhanced file type breakdown
        self.analysis_text.insert(tk.END, "FILE TYPE BREAKDOWN:\n")
        self.analysis_text.insert(tk.END, f"{'-'*40}\n")
        
        # Sort file types by count (descending)
        sorted_types = sorted(file_type_stats.items(), key=lambda x: x[1]['count'], reverse=True)
        
        for file_type, stats in sorted_types:
            if stats['count'] == 0:
                continue
                
            count = stats['count']
            size_mb = stats['total_size_mb']
            percentage = (count / total_files) * 100 if total_files > 0 else 0
            
            self.analysis_text.insert(tk.END, f"\n📁 {file_type.upper()}: {count:,} files ({percentage:.1f}%)\n")
            self.analysis_text.insert(tk.END, f"   Size: {size_mb:.1f} MB\n")
            
            # Show common extensions
            if stats['common_extensions']:
                ext_text = ", ".join([f"{ext} ({cnt})" for ext, cnt in stats['common_extensions']])
                self.analysis_text.insert(tk.END, f"   Common types: {ext_text}\n")
            
            # Show example files (up to 3)
            examples = stats['files'][:3]
            for file_info in examples:
                file_size_mb = file_info['size'] / (1024 * 1024)
                self.analysis_text.insert(tk.END, f"   • {file_info['name']} ({file_size_mb:.2f} MB)\n")
            
            if len(stats['files']) > 3:
                self.analysis_text.insert(tk.END, f"   ... and {len(stats['files']) - 3} more files\n")
        
        # Date-based filtering suggestions
        if date_suggestions:
            self.analysis_text.insert(tk.END, f"\n\nSMART ORGANIZATION SUGGESTIONS:\n")
            self.analysis_text.insert(tk.END, f"{'-'*40}\n")
            self.analysis_text.insert(tk.END, "Based on file dates, consider organizing in these batches:\n\n")
            
            for i, suggestion in enumerate(date_suggestions, 1):
                priority_icon = "🔥" if suggestion['priority'] == 'high' else "⭐" if suggestion['priority'] == 'medium' else "📋"
                
                self.analysis_text.insert(tk.END, f"{priority_icon} {suggestion['title']}\n")
                self.analysis_text.insert(tk.END, f"   {suggestion['description']}\n")
                
                if suggestion['priority'] == 'high':
                    self.analysis_text.insert(tk.END, f"   💡 Recommended: Good size for AI analysis\n")
                elif suggestion['file_count'] > 200:
                    self.analysis_text.insert(tk.END, f"   ⚠️  Large batch - consider smaller groups for better results\n")
                
                self.analysis_text.insert(tk.END, "\n")
        
        self.analysis_text.config(state=tk.DISABLED)
    
    def display_scan_errors(self, errors: List[str]):
        """Display scan errors to the user"""
        if not errors:
            return
        
        self.analysis_text.config(state=tk.NORMAL)
        self.analysis_text.insert(tk.END, f"\nSCAN WARNINGS/ERRORS:\n")
        self.analysis_text.insert(tk.END, f"{'-'*30}\n")
        
        for error in errors[:10]:  # Show up to 10 errors
            self.analysis_text.insert(tk.END, f"⚠ {error}\n")
        
        if len(errors) > 10:
            self.analysis_text.insert(tk.END, f"... and {len(errors) - 10} more errors\n")
        
        self.analysis_text.config(state=tk.DISABLED)
    
    def execute_plan(self):
        """Placeholder for plan execution functionality"""
        self.status_var.set("Plan execution functionality will be implemented in future tasks")
        messagebox.showinfo("Not Implemented", 
                          "Plan execution will be implemented in task 5.")
    
    def _initialize_ai_service(self):
        """Initialize AI service based on current provider and API key"""
        try:
            api_key = AIConfig.get_api_key(self.ai_provider, self.config)
            
            if api_key:
                self.ai_service = AIServiceFactory.create_service(
                    self.ai_provider, 
                    api_key
                )
                
                # Test the connection
                if self.ai_service.test_connection():
                    provider_name = self.ai_provider.value.capitalize()
                    self.status_var.set(f"Connected to {provider_name} AI service")
                else:
                    self.status_var.set(f"Warning: Could not verify AI connection")
            else:
                self.ai_service = None
                self.status_var.set("No AI API key configured")
                
        except Exception as e:
            messagebox.showwarning(
                "AI Service Warning", 
                f"Could not initialize AI service: {str(e)}\n\n"
                "Please configure your API key in Settings or set environment variable."
            )
            self.ai_service = None
            self.status_var.set("AI service initialization failed")
    
    def switch_ai_provider(self, provider: AIProvider):
        """
        Switch between AI providers
        
        Args:
            provider: AIProvider enum value to switch to
        """
        self.ai_provider = provider
        self._initialize_ai_service()
        
        if self.ai_service:
            provider_name = provider.value.capitalize()
            self.status_var.set(f"Switched to {provider_name} AI provider")
        else:
            self.status_var.set(f"Failed to switch provider - check API key")
    
    def run(self):
        """Start the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = FileJanitorApp()
    app.run()