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


class FileScanner:
    """Handles directory scanning and file metadata extraction"""
    
    def __init__(self):
        self.scan_errors = []
    
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
        self.setup_gui()
    
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
            
            self.status_var.set(f"Analysis complete - Found {len(self.scanned_files)} files")
            
        except Exception as e:
            messagebox.showerror("Scan Error", f"An error occurred during scanning: {str(e)}")
            self.status_var.set("Scan failed")
    
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
    
    def run(self):
        """Start the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = FileJanitorApp()
    app.run()