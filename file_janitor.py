#!/usr/bin/env python3
"""
Intelligent File Janitor - AI-powered file organization tool
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import stat
import shutil
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
            
            # Initialize text model (Gemini 2.5 Flash)
            self.model = genai.GenerativeModel(
                'gemini-2.0-flash-lite',
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            # Initialize vision model (Gemini 2.5 Flash)
            self.vision_model = genai.GenerativeModel(
                'gemini-2.0-flash-lite',
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


class OrganizationPlanner:
    """Creates file organization plans based on AI analysis"""
    
    def __init__(self):
        self.plan = None
    
    def create_plan(self, files: List[Dict], ai_analysis: Dict) -> Dict:
        """
        Create a comprehensive organization plan based on AI analysis
        
        Args:
            files: List of file information dictionaries
            ai_analysis: AI clustering/analysis results
            
        Returns:
            Dictionary containing the organization plan
        """
        try:
            # Extract clusters from AI analysis
            clusters = ai_analysis.get('clusters', [])
            
            if not clusters:
                return {
                    'folders_to_create': [],
                    'file_operations': [],
                    'summary': 'No clusters found in AI analysis',
                    'error': 'No valid clusters to organize'
                }
            
            # Generate folder structure
            folders_to_create = self.generate_folder_structure(clusters)
            
            # Create file operations based on clusters
            file_operations = []
            file_name_map = {f['name']: f for f in files}
            
            for cluster in clusters:
                category = cluster.get('category', 'Uncategorized')
                suggested_folder = cluster.get('suggested_folder', category.lower().replace(' ', '_'))
                cluster_files = cluster.get('files', [])
                
                for filename in cluster_files:
                    # Find the full file info
                    file_info = file_name_map.get(filename)
                    
                    if not file_info:
                        continue
                    
                    # Create file operation
                    operation = {
                        'action': 'move',
                        'source': file_info['path'],
                        'destination_folder': suggested_folder,
                        'original_name': filename,
                        'new_name': filename,  # Will be updated if rename is suggested
                        'category': category
                    }
                    
                    file_operations.append(operation)
            
            # Handle naming conflicts
            file_operations = self._resolve_naming_conflicts(file_operations)
            
            # Create summary
            summary = self._generate_summary(folders_to_create, file_operations)
            
            # Store the plan
            self.plan = {
                'folders_to_create': folders_to_create,
                'file_operations': file_operations,
                'summary': summary,
                'error': None
            }
            
            return self.plan
            
        except Exception as e:
            return {
                'folders_to_create': [],
                'file_operations': [],
                'summary': f'Failed to create plan: {str(e)}',
                'error': str(e)
            }
    
    def generate_folder_structure(self, clusters: List[Dict]) -> List[str]:
        """
        Generate folder structure based on AI clusters
        
        Args:
            clusters: List of cluster dictionaries from AI analysis
            
        Returns:
            List of folder paths to create
        """
        folders = []
        
        for cluster in clusters:
            suggested_folder = cluster.get('suggested_folder', '')
            
            if not suggested_folder:
                # Fallback to category name
                category = cluster.get('category', 'Uncategorized')
                suggested_folder = category.lower().replace(' ', '_')
            
            # Clean folder name (remove invalid characters)
            suggested_folder = self._sanitize_folder_name(suggested_folder)
            
            if suggested_folder and suggested_folder not in folders:
                folders.append(suggested_folder)
        
        return sorted(folders)
    
    def suggest_renames(self, files: List[Dict], analysis: Dict) -> Dict[str, str]:
        """
        Generate rename suggestions based on AI content analysis
        
        Args:
            files: List of file information dictionaries
            analysis: AI analysis results with content insights
            
        Returns:
            Dictionary mapping original filenames to suggested new names
        """
        rename_suggestions = {}
        
        # This method is designed to work with detailed content analysis
        # For now, it returns an empty dict as content analysis happens per-file
        # and is integrated into the file operations during plan creation
        
        return rename_suggestions
    
    def _sanitize_folder_name(self, folder_name: str) -> str:
        """
        Clean folder name by removing invalid characters
        
        Args:
            folder_name: Original folder name
            
        Returns:
            Sanitized folder name
        """
        # Remove or replace invalid characters for Windows/Unix
        invalid_chars = '<>:"/\\|?*'
        
        for char in invalid_chars:
            folder_name = folder_name.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        folder_name = folder_name.strip('. ')
        
        # Replace multiple underscores with single underscore
        while '__' in folder_name:
            folder_name = folder_name.replace('__', '_')
        
        # Ensure it's not empty
        if not folder_name:
            folder_name = 'organized_files'
        
        return folder_name
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Clean filename by removing invalid characters
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Split name and extension
        path_obj = Path(filename)
        name = path_obj.stem
        ext = path_obj.suffix
        
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        
        for char in invalid_chars:
            name = name.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        name = name.strip('. ')
        
        # Replace multiple underscores with single underscore
        while '__' in name:
            name = name.replace('__', '_')
        
        # Ensure it's not empty
        if not name:
            name = 'file'
        
        return name + ext
    
    def _resolve_naming_conflicts(self, file_operations: List[Dict]) -> List[Dict]:
        """
        Resolve naming conflicts by appending numbers to duplicate filenames
        
        Args:
            file_operations: List of file operation dictionaries
            
        Returns:
            Updated list with resolved naming conflicts
        """
        # Track filenames per destination folder
        folder_files = defaultdict(list)
        
        # Group operations by destination folder
        for operation in file_operations:
            dest_folder = operation.get('destination_folder', '')
            new_name = operation.get('new_name', operation.get('original_name', ''))
            folder_files[dest_folder].append(new_name)
        
        # Find duplicates and resolve them
        for dest_folder, filenames in folder_files.items():
            # Count occurrences of each filename
            name_counts = defaultdict(int)
            name_indices = defaultdict(int)
            
            for filename in filenames:
                name_counts[filename] += 1
            
            # Update operations with conflict resolution
            for operation in file_operations:
                if operation.get('destination_folder') != dest_folder:
                    continue
                
                new_name = operation.get('new_name', operation.get('original_name', ''))
                
                # If this filename appears multiple times, add a number
                if name_counts[new_name] > 1:
                    name_indices[new_name] += 1
                    
                    # Split name and extension
                    path_obj = Path(new_name)
                    name = path_obj.stem
                    ext = path_obj.suffix
                    
                    # Append number
                    numbered_name = f"{name}_{name_indices[new_name]}{ext}"
                    operation['new_name'] = numbered_name
                    operation['conflict_resolved'] = True
        
        return file_operations
    
    def _generate_summary(self, folders: List[str], operations: List[Dict]) -> str:
        """
        Generate a human-readable summary of the organization plan
        
        Args:
            folders: List of folders to create
            operations: List of file operations
            
        Returns:
            Summary string
        """
        total_files = len(operations)
        total_folders = len(folders)
        
        # Count operations by type
        moves = sum(1 for op in operations if op.get('action') == 'move')
        renames = sum(1 for op in operations if op.get('action') == 'rename')
        move_and_renames = sum(1 for op in operations if op.get('action') == 'move_and_rename')
        
        # Count conflicts resolved
        conflicts_resolved = sum(1 for op in operations if op.get('conflict_resolved', False))
        
        summary_parts = [
            f"Organization Plan Summary:",
            f"  • {total_folders} folder(s) will be created",
            f"  • {total_files} file(s) will be organized",
        ]
        
        if moves > 0:
            summary_parts.append(f"  • {moves} file(s) will be moved")
        
        if renames > 0:
            summary_parts.append(f"  • {renames} file(s) will be renamed")
        
        if move_and_renames > 0:
            summary_parts.append(f"  • {move_and_renames} file(s) will be moved and renamed")
        
        if conflicts_resolved > 0:
            summary_parts.append(f"  • {conflicts_resolved} naming conflict(s) resolved")
        
        return '\n'.join(summary_parts)
    
    def get_plan(self) -> Optional[Dict]:
        """
        Get the current organization plan
        
        Returns:
            Plan dictionary or None if no plan exists
        """
        return self.plan


class PlanExecutor:
    """Executes file organization plans with safety features"""
    
    def __init__(self):
        self.execution_log = []
        self.errors = []
    
    def execute_plan(self, plan: Dict, base_path: str, dry_run: bool = True, progress_callback=None) -> Dict:
        """
        Execute the organization plan with optional dry-run mode
        
        Args:
            plan: Organization plan dictionary from OrganizationPlanner
            base_path: Base directory path where operations will be performed
            dry_run: If True, simulate operations without making changes
            progress_callback: Optional callback function(current, total) for progress updates
            
        Returns:
            Dictionary with execution results
        """
        self.execution_log = []
        self.errors = []
        self.progress_callback = progress_callback
        
        try:
            if not plan:
                return {
                    'success': False,
                    'error': 'No plan provided',
                    'operations_completed': 0,
                    'operations_failed': 0,
                    'log': []
                }
            
            folders_to_create = plan.get('folders_to_create', [])
            file_operations = plan.get('file_operations', [])
            
            # Step 1: Create folders
            folders_created = 0
            total_operations = len(folders_to_create) + len(file_operations)
            current_operation = 0
            
            for folder in folders_to_create:
                if self.create_folder(base_path, folder, dry_run):
                    folders_created += 1
                current_operation += 1
                if self.progress_callback:
                    self.progress_callback(current_operation, total_operations)
            
            # Step 2: Execute file operations
            operations_completed = 0
            operations_failed = 0
            
            for operation in file_operations:
                success = self._execute_file_operation(base_path, operation, dry_run)
                if success:
                    operations_completed += 1
                else:
                    operations_failed += 1
                current_operation += 1
                if self.progress_callback:
                    self.progress_callback(current_operation, total_operations)
            
            # Generate result summary
            result = {
                'success': operations_failed == 0,
                'dry_run': dry_run,
                'folders_created': folders_created,
                'operations_completed': operations_completed,
                'operations_failed': operations_failed,
                'total_operations': len(file_operations),
                'log': self.execution_log.copy(),
                'errors': self.errors.copy()
            }
            
            return result
            
        except Exception as e:
            self.errors.append(f"Critical error during execution: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'operations_completed': 0,
                'operations_failed': len(file_operations) if 'file_operations' in locals() else 0,
                'log': self.execution_log.copy(),
                'errors': self.errors.copy()
            }
    
    def create_folder(self, base_path: str, folder_name: str, dry_run: bool = True) -> bool:
        """
        Create a folder in the base path
        
        Args:
            base_path: Base directory path
            folder_name: Name of folder to create
            dry_run: If True, simulate without creating
            
        Returns:
            True if successful (or would be successful in dry-run)
        """
        try:
            folder_path = Path(base_path) / folder_name
            
            if dry_run:
                # Simulate folder creation
                if folder_path.exists():
                    self.execution_log.append(f"[DRY-RUN] Folder already exists: {folder_name}")
                else:
                    self.execution_log.append(f"[DRY-RUN] Would create folder: {folder_name}")
                return True
            else:
                # Actually create the folder
                if folder_path.exists():
                    self.execution_log.append(f"Folder already exists: {folder_name}")
                    return True
                
                folder_path.mkdir(parents=True, exist_ok=True)
                self.execution_log.append(f"Created folder: {folder_name}")
                return True
                
        except PermissionError as e:
            error_msg = f"Permission denied creating folder '{folder_name}'. Please check folder permissions."
            self.errors.append(error_msg)
            self.execution_log.append(f"[ERROR] {error_msg}")
            return False
        except OSError as e:
            error_msg = f"System error creating folder '{folder_name}': Invalid path or disk full"
            self.errors.append(error_msg)
            self.execution_log.append(f"[ERROR] {error_msg}")
            return False
        except Exception as e:
            error_msg = f"Unexpected error creating folder '{folder_name}': {str(e)}"
            self.errors.append(error_msg)
            self.execution_log.append(f"[ERROR] {error_msg}")
            return False
    
    def move_file(self, source_path: str, destination_path: str, dry_run: bool = True) -> bool:
        """
        Move a file from source to destination
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            dry_run: If True, simulate without moving
            
        Returns:
            True if successful (or would be successful in dry-run)
        """
        try:
            source = Path(source_path)
            destination = Path(destination_path)
            
            # Validate source exists
            if not source.exists():
                error_msg = f"Source file not found: {source.name}"
                self.errors.append(error_msg)
                self.execution_log.append(f"[ERROR] {error_msg}")
                return False
            
            # Check if destination already exists
            if destination.exists():
                error_msg = f"Destination already exists: {destination.name}"
                self.errors.append(error_msg)
                self.execution_log.append(f"[ERROR] {error_msg}")
                return False
            
            if dry_run:
                # Simulate move
                self.execution_log.append(f"[DRY-RUN] Would move: {source.name} -> {destination}")
                return True
            else:
                # Ensure destination directory exists
                destination.parent.mkdir(parents=True, exist_ok=True)
                
                # Actually move the file
                shutil.move(str(source), str(destination))
                self.execution_log.append(f"Moved: {source.name} -> {destination}")
                return True
                
        except PermissionError:
            error_msg = f"Permission denied: Cannot move '{source.name}'. Check file permissions."
            self.errors.append(error_msg)
            self.execution_log.append(f"[ERROR] {error_msg}")
            return False
        except OSError as e:
            if "cross-device" in str(e).lower():
                error_msg = f"Cannot move '{source.name}' across different drives. Try copying instead."
            else:
                error_msg = f"System error moving '{source.name}': Disk may be full or path invalid"
            self.errors.append(error_msg)
            self.execution_log.append(f"[ERROR] {error_msg}")
            return False
        except Exception as e:
            error_msg = f"Unexpected error moving '{source.name}': {str(e)}"
            self.errors.append(error_msg)
            self.execution_log.append(f"[ERROR] {error_msg}")
            return False
    
    def rename_file(self, file_path: str, new_name: str, dry_run: bool = True) -> bool:
        """
        Rename a file
        
        Args:
            file_path: Current file path
            new_name: New filename (not full path, just the name)
            dry_run: If True, simulate without renaming
            
        Returns:
            True if successful (or would be successful in dry-run)
        """
        try:
            source = Path(file_path)
            destination = source.parent / new_name
            
            # Validate source exists
            if not source.exists():
                error_msg = f"Source file not found: {source.name}"
                self.errors.append(error_msg)
                self.execution_log.append(f"[ERROR] {error_msg}")
                return False
            
            # Check if destination already exists
            if destination.exists() and destination != source:
                error_msg = f"File already exists with name: {new_name}"
                self.errors.append(error_msg)
                self.execution_log.append(f"[ERROR] {error_msg}")
                return False
            
            if dry_run:
                # Simulate rename
                self.execution_log.append(f"[DRY-RUN] Would rename: {source.name} -> {new_name}")
                return True
            else:
                # Actually rename the file
                source.rename(destination)
                self.execution_log.append(f"Renamed: {source.name} -> {new_name}")
                return True
                
        except PermissionError:
            error_msg = f"Permission denied: Cannot rename '{source.name}'. File may be in use."
            self.errors.append(error_msg)
            self.execution_log.append(f"[ERROR] {error_msg}")
            return False
        except OSError as e:
            error_msg = f"System error renaming '{source.name}': Invalid filename or disk error"
            self.errors.append(error_msg)
            self.execution_log.append(f"[ERROR] {error_msg}")
            return False
        except Exception as e:
            error_msg = f"Unexpected error renaming '{source.name}': {str(e)}"
            self.errors.append(error_msg)
            self.execution_log.append(f"[ERROR] {error_msg}")
            return False
    
    def _execute_file_operation(self, base_path: str, operation: Dict, dry_run: bool = True) -> bool:
        """
        Execute a single file operation
        
        Args:
            base_path: Base directory path
            operation: File operation dictionary
            dry_run: If True, simulate without executing
            
        Returns:
            True if successful
        """
        try:
            action = operation.get('action', 'move')
            source_path = operation.get('source', '')
            destination_folder = operation.get('destination_folder', '')
            original_name = operation.get('original_name', '')
            new_name = operation.get('new_name', original_name)
            
            if not source_path:
                self.errors.append("Operation missing source path")
                return False
            
            # Build destination path
            dest_folder_path = Path(base_path) / destination_folder
            dest_file_path = dest_folder_path / new_name
            
            # Determine operation type
            needs_rename = new_name != original_name
            needs_move = Path(source_path).parent != dest_folder_path
            
            if needs_move and needs_rename:
                # Move and rename in one operation
                return self.move_file(source_path, str(dest_file_path), dry_run)
            elif needs_move:
                # Just move
                return self.move_file(source_path, str(dest_file_path), dry_run)
            elif needs_rename:
                # Just rename
                return self.rename_file(source_path, new_name, dry_run)
            else:
                # No operation needed
                self.execution_log.append(f"[SKIP] File already in correct location: {original_name}")
                return True
                
        except Exception as e:
            error_msg = f"Failed to execute operation: {str(e)}"
            self.errors.append(error_msg)
            self.execution_log.append(f"[ERROR] {error_msg}")
            return False
    
    def get_execution_log(self) -> List[str]:
        """
        Get the execution log
        
        Returns:
            List of log messages
        """
        return self.execution_log.copy()
    
    def get_errors(self) -> List[str]:
        """
        Get the list of errors
        
        Returns:
            List of error messages
        """
        return self.errors.copy()


class ToolTip:
    """Simple tooltip class for Tkinter widgets"""
    
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        """Display the tooltip"""
        if self.tooltip_window or not self.text:
            return
        
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("Arial", 9))
        label.pack(ipadx=5, ipady=3)
    
    def hide_tooltip(self, event=None):
        """Hide the tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class FileJanitorApp:
    """Main application class for the Intelligent File Janitor"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.selected_folder = None
        self.scanner = FileScanner()
        self.planner = OrganizationPlanner()
        self.executor = PlanExecutor()
        self.scanned_files = []
        self.current_plan = None
        self.is_processing = False  # Track if operation is in progress
        
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
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.select_folder())
        self.root.bind('<Control-a>', lambda e: self.analyze_files() if self.analyze_button['state'] == tk.NORMAL else None)
        self.root.bind('<Control-e>', lambda e: self.execute_plan() if self.execute_button['state'] == tk.NORMAL else None)
        self.root.bind('<F5>', lambda e: self.analyze_files() if self.analyze_button['state'] == tk.NORMAL else None)
        
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
        
        # Folder selection button and display with tooltip
        self.browse_button = ttk.Button(main_frame, text="Browse Folder (Ctrl+O)", 
                  command=self.select_folder)
        self.browse_button.grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self._create_tooltip(self.browse_button, "Select a folder to organize (Ctrl+O)")
        
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
        
        self.analyze_button = ttk.Button(button_frame, text="Analyze Files (Ctrl+A / F5)", 
                                       command=self.analyze_files, state=tk.DISABLED)
        self.analyze_button.grid(row=0, column=0, padx=(0, 10))
        self._create_tooltip(self.analyze_button, "Scan and analyze files in the selected folder (Ctrl+A or F5)")
        
        self.execute_button = ttk.Button(button_frame, text="Execute Plan (Ctrl+E)", 
                                       command=self.execute_plan, state=tk.DISABLED)
        self.execute_button.grid(row=0, column=1)
        self._create_tooltip(self.execute_button, "Execute the organization plan (Ctrl+E)\nWarning: This will move/rename files!")
        
        # Progress bar (initially hidden)
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), 
                                pady=(10, 0))
        self.progress_frame.columnconfigure(0, weight=1)
        
        self.progress_label = ttk.Label(self.progress_frame, text="")
        self.progress_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate', 
                                           length=300)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Hide progress bar initially
        self.progress_frame.grid_remove()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Select a folder to begin")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                             relief="sunken", anchor=tk.W)
        status_bar.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), 
                       pady=(10, 0))
    
    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        ToolTip(widget, text)
    
    def _update_button_states(self, analyzing=False, executing=False):
        """
        Update button states based on current operation
        
        Args:
            analyzing: True if analysis is in progress
            executing: True if execution is in progress
        """
        if analyzing or executing:
            self.browse_button.config(state=tk.DISABLED)
            self.analyze_button.config(state=tk.DISABLED)
            self.execute_button.config(state=tk.DISABLED)
            self.is_processing = True
        else:
            self.browse_button.config(state=tk.NORMAL)
            self.analyze_button.config(state=tk.NORMAL if self.selected_folder else tk.DISABLED)
            self.execute_button.config(state=tk.NORMAL if self.current_plan and not self.current_plan.get('error') else tk.DISABLED)
            self.is_processing = False
    
    def select_folder(self):
        """Handle folder selection"""
        if self.is_processing:
            return
        
        folder = filedialog.askdirectory(title="Select folder to organize")
        if folder:
            self.selected_folder = folder
            self.folder_label.config(text=folder, foreground="black")
            self._update_button_states()
            self.status_var.set(f"✓ Folder selected: {os.path.basename(folder)}")
            
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
        
        self.current_plan = None
        self._update_button_states()
    
    def analyze_files(self):
        """Scan and analyze files in the selected directory"""
        if not self.selected_folder:
            messagebox.showerror("Error", "Please select a folder first")
            return
        
        if self.is_processing:
            return
        
        # Update button states to disabled during analysis
        self._update_button_states(analyzing=True)
        
        self.status_var.set("⏳ Scanning files...")
        self.root.update()  # Update GUI to show status
        
        try:
            # Scan the directory
            self.scanned_files = self.scanner.scan_directory(self.selected_folder)
            
            if not self.scanned_files:
                self.status_var.set("⚠ No files found in selected folder")
                self._update_button_states()
                messagebox.showinfo("No Files", "No files were found in the selected folder.")
                return
            
            self.status_var.set(f"⏳ Analyzing {len(self.scanned_files)} files...")
            self.root.update()
            
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
                self.status_var.set(f"⚠ Analysis complete with {len(errors)} warning(s)")
            
            # Perform AI-based filename analysis if service is available
            if self.ai_service and len(self.scanned_files) > 0:
                self.status_var.set("🤖 Running AI analysis on filenames...")
                self.root.update()
                self.perform_ai_filename_analysis()
            
            self.status_var.set(f"✓ Analysis complete - Found {len(self.scanned_files)} files")
            
        except Exception as e:
            messagebox.showerror("Scan Error", f"An error occurred during scanning:\n\n{str(e)}")
            self.status_var.set("❌ Scan failed")
        finally:
            # Re-enable buttons
            self._update_button_states()
    
    def perform_ai_filename_analysis(self):
        """Perform AI-based filename clustering analysis"""
        try:
            # Extract just the filenames
            filenames = [file_info['name'] for file_info in self.scanned_files]
            
            # Limit to first 100 files for initial analysis
            files_to_analyze = self.scanned_files[:100] if len(self.scanned_files) > 100 else self.scanned_files
            filenames_to_analyze = [f['name'] for f in files_to_analyze]
            
            if len(self.scanned_files) > 100:
                self.status_var.set(f"🤖 Analyzing first 100 of {len(self.scanned_files)} files...")
                self.root.update()
            
            # Call AI service
            result = self.ai_service.analyze_filenames(filenames_to_analyze)
            
            # Create organization plan based on AI analysis
            if not result.get('error') and result.get('clusters'):
                self.status_var.set("📋 Creating organization plan...")
                self.root.update()
                
                self.current_plan = self.planner.create_plan(files_to_analyze, result)
                
                # Display the plan
                self.display_organization_plan(self.current_plan)
                
                # Update button states
                self._update_button_states()
            else:
                # Display clustering results without plan
                self.display_ai_clusters(result)
                self.status_var.set("⚠ AI analysis completed with errors")
            
        except Exception as e:
            self.plan_text.config(state=tk.NORMAL)
            self.plan_text.insert(tk.END, f"\n⚠️ AI Analysis Error: {str(e)}\n")
            self.plan_text.config(state=tk.DISABLED)
            self.status_var.set("❌ AI analysis failed")
    
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
    
    def display_organization_plan(self, plan: Dict):
        """
        Display the complete organization plan in the plan text area
        
        Args:
            plan: Organization plan dictionary from OrganizationPlanner
        """
        self.plan_text.config(state=tk.NORMAL)
        self.plan_text.delete(1.0, tk.END)
        
        if plan.get('error'):
            self.plan_text.insert(tk.END, f"ORGANIZATION PLAN ERROR\n")
            self.plan_text.insert(tk.END, f"{'='*60}\n\n")
            self.plan_text.insert(tk.END, f"Error: {plan['error']}\n")
            self.plan_text.insert(tk.END, f"\n{plan.get('summary', '')}\n")
        else:
            # Display header
            self.plan_text.insert(tk.END, f"FILE ORGANIZATION PLAN\n")
            self.plan_text.insert(tk.END, f"{'='*60}\n\n")
            
            # Display summary
            summary = plan.get('summary', '')
            self.plan_text.insert(tk.END, f"{summary}\n\n")
            
            # Display folder structure
            folders = plan.get('folders_to_create', [])
            if folders:
                self.plan_text.insert(tk.END, f"FOLDERS TO CREATE:\n")
                self.plan_text.insert(tk.END, f"{'-'*40}\n")
                for folder in folders:
                    self.plan_text.insert(tk.END, f"📁 {folder}/\n")
                self.plan_text.insert(tk.END, "\n")
            
            # Display file operations grouped by destination folder
            operations = plan.get('file_operations', [])
            if operations:
                self.plan_text.insert(tk.END, f"FILE OPERATIONS:\n")
                self.plan_text.insert(tk.END, f"{'-'*40}\n\n")
                
                # Group operations by destination folder
                ops_by_folder = defaultdict(list)
                for op in operations:
                    dest_folder = op.get('destination_folder', 'root')
                    ops_by_folder[dest_folder].append(op)
                
                # Display operations for each folder
                for folder, folder_ops in sorted(ops_by_folder.items()):
                    category = folder_ops[0].get('category', 'Files') if folder_ops else 'Files'
                    self.plan_text.insert(tk.END, f"📁 {folder}/ ({len(folder_ops)} files)\n")
                    self.plan_text.insert(tk.END, f"   Category: {category}\n\n")
                    
                    # Show first 10 operations for this folder
                    display_count = min(10, len(folder_ops))
                    for op in folder_ops[:display_count]:
                        original_name = op.get('original_name', 'unknown')
                        new_name = op.get('new_name', original_name)
                        action = op.get('action', 'move')
                        
                        # Determine the operation symbol
                        if action == 'move_and_rename' or (new_name != original_name):
                            self.plan_text.insert(tk.END, f"   📄 {original_name}\n")
                            self.plan_text.insert(tk.END, f"      → Rename to: {new_name}\n")
                            if op.get('conflict_resolved'):
                                self.plan_text.insert(tk.END, f"      ⚠️  Conflict resolved\n")
                        else:
                            self.plan_text.insert(tk.END, f"   📄 {original_name}\n")
                    
                    if len(folder_ops) > display_count:
                        self.plan_text.insert(tk.END, f"   ... and {len(folder_ops) - display_count} more files\n")
                    
                    self.plan_text.insert(tk.END, "\n")
            
            # Display action prompt
            self.plan_text.insert(tk.END, f"{'='*60}\n")
            self.plan_text.insert(tk.END, f"💡 Review the plan above and click 'Execute Plan' to proceed.\n")
            self.plan_text.insert(tk.END, f"⚠️  WARNING: File operations cannot be undone!\n")
        
        self.plan_text.config(state=tk.DISABLED)
    
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
        """Execute the organization plan with safety confirmations"""
        if not self.current_plan:
            messagebox.showerror("No Plan", "No organization plan available to execute.")
            return
        
        if self.current_plan.get('error'):
            messagebox.showerror("Invalid Plan", 
                               f"Cannot execute plan with errors:\n\n{self.current_plan.get('error')}")
            return
        
        if not self.selected_folder:
            messagebox.showerror("No Folder", "No folder selected for organization.")
            return
        
        if self.is_processing:
            return
        
        # Show mandatory safety confirmation dialog
        file_count = len(self.current_plan.get('file_operations', []))
        folder_count = len(self.current_plan.get('folders_to_create', []))
        
        confirmation_message = (
            "⚠️  WARNING: FILE OPERATIONS CANNOT BE UNDONE! ⚠️\n\n"
            f"This will:\n"
            f"  • Create {folder_count} new folder(s)\n"
            f"  • Move/rename {file_count} file(s)\n\n"
            f"Target directory: {self.selected_folder}\n\n"
            "Are you absolutely sure you want to proceed?\n\n"
            "Click 'Yes' to execute the plan.\n"
            "Click 'No' to cancel."
        )
        
        response = messagebox.askyesno(
            "⚠️  Confirm File Operations", 
            confirmation_message,
            icon='warning'
        )
        
        if not response:
            self.status_var.set("⚠ Plan execution cancelled by user")
            return
        
        # Update button states to disabled during execution
        self._update_button_states(executing=True)
        
        # Show progress bar
        self.progress_frame.grid()
        self.progress_label.config(text="⏳ Executing plan...")
        self.progress_bar['value'] = 0
        self.progress_bar['maximum'] = file_count + folder_count
        self.root.update_idletasks()
        
        # Define progress callback to update progress bar
        def update_progress(current, total):
            self.progress_bar['value'] = current
            percentage = int((current / total) * 100) if total > 0 else 0
            self.progress_label.config(text=f"⏳ Executing plan... {percentage}% ({current}/{total})")
            self.root.update_idletasks()
        
        try:
            self.status_var.set("⏳ Executing file operations...")
            
            # Execute the plan (not dry-run) with progress callback
            result = self.executor.execute_plan(
                self.current_plan, 
                self.selected_folder, 
                dry_run=False,
                progress_callback=update_progress
            )
            
            # Update progress bar to completion
            self.progress_bar['value'] = self.progress_bar['maximum']
            self.progress_label.config(text=f"✓ Execution complete!")
            self.root.update_idletasks()
            
            # Display execution results
            self._display_execution_results(result)
            
            # Show summary dialog
            if result.get('success'):
                summary_message = (
                    f"✅ Plan executed successfully!\n\n"
                    f"Folders created: {result.get('folders_created', 0)}\n"
                    f"Files organized: {result.get('operations_completed', 0)}\n"
                    f"Operations failed: {result.get('operations_failed', 0)}\n\n"
                    "Check the plan area for detailed execution log."
                )
                messagebox.showinfo("Execution Complete", summary_message)
                self.status_var.set(
                    f"✓ Plan executed: {result.get('operations_completed', 0)} files organized"
                )
            else:
                error_count = result.get('operations_failed', 0)
                summary_message = (
                    f"⚠️  Plan executed with errors\n\n"
                    f"Folders created: {result.get('folders_created', 0)}\n"
                    f"Files organized: {result.get('operations_completed', 0)}\n"
                    f"Operations failed: {error_count}\n\n"
                    "Check the plan area for detailed error log."
                )
                messagebox.showwarning("Execution Completed with Errors", summary_message)
                self.status_var.set(
                    f"⚠ Plan executed with {error_count} error(s)"
                )
            
        except Exception as e:
            messagebox.showerror(
                "Execution Error", 
                f"An unexpected error occurred during execution:\n\n{str(e)}"
            )
            self.status_var.set("❌ Plan execution failed")
        
        finally:
            # Hide progress bar
            self.progress_frame.grid_remove()
            
            # Clear current plan to prevent re-execution
            self.current_plan = None
            
            # Re-enable buttons
            self._update_button_states()
    
    def _display_execution_results(self, result: Dict):
        """
        Display execution results in the plan text area
        
        Args:
            result: Execution result dictionary from PlanExecutor
        """
        self.plan_text.config(state=tk.NORMAL)
        self.plan_text.delete(1.0, tk.END)
        
        # Header
        self.plan_text.insert(tk.END, "=" * 60 + "\n")
        self.plan_text.insert(tk.END, "EXECUTION RESULTS\n")
        self.plan_text.insert(tk.END, "=" * 60 + "\n\n")
        
        # Summary
        self.plan_text.insert(tk.END, "Summary:\n")
        self.plan_text.insert(tk.END, f"  Status: {'✅ Success' if result.get('success') else '⚠️  Completed with errors'}\n")
        self.plan_text.insert(tk.END, f"  Folders created: {result.get('folders_created', 0)}\n")
        self.plan_text.insert(tk.END, f"  Operations completed: {result.get('operations_completed', 0)}\n")
        self.plan_text.insert(tk.END, f"  Operations failed: {result.get('operations_failed', 0)}\n")
        self.plan_text.insert(tk.END, f"  Total operations: {result.get('total_operations', 0)}\n\n")
        
        # Execution log
        execution_log = result.get('log', [])
        if execution_log:
            self.plan_text.insert(tk.END, "Execution Log:\n")
            self.plan_text.insert(tk.END, "-" * 60 + "\n")
            for log_entry in execution_log:
                self.plan_text.insert(tk.END, f"{log_entry}\n")
            self.plan_text.insert(tk.END, "\n")
        
        # Errors
        errors = result.get('errors', [])
        if errors:
            self.plan_text.insert(tk.END, "Errors:\n")
            self.plan_text.insert(tk.END, "-" * 60 + "\n")
            for error in errors:
                self.plan_text.insert(tk.END, f"❌ {error}\n")
            self.plan_text.insert(tk.END, "\n")
        
        self.plan_text.insert(tk.END, "=" * 60 + "\n")
        
        self.plan_text.config(state=tk.DISABLED)
    
    def _initialize_ai_service(self):
        """Initialize AI service based on current provider and API key"""
        try:
            api_key = AIConfig.get_api_key(self.ai_provider, self.config)
            
            if api_key:
                self.status_var.set("⏳ Connecting to AI service...")
                self.root.update()
                
                self.ai_service = AIServiceFactory.create_service(
                    self.ai_provider, 
                    api_key
                )
                
                # Test the connection
                if self.ai_service.test_connection():
                    provider_name = self.ai_provider.value.capitalize()
                    self.status_var.set(f"✓ Connected to {provider_name} AI service - Ready")
                else:
                    self.status_var.set(f"⚠ Warning: Could not verify AI connection")
            else:
                self.ai_service = None
                self.status_var.set("⚠ No AI API key configured - Select a folder to begin")
                
        except Exception as e:
            messagebox.showwarning(
                "AI Service Warning", 
                f"Could not initialize AI service:\n\n{str(e)}\n\n"
                "Please configure your API key in ai_config.json or set environment variable."
            )
            self.ai_service = None
            self.status_var.set("⚠ AI service initialization failed - Select a folder to begin")
    
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