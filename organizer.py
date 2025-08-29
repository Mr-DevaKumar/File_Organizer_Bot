# organizer.py
import os
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
import yaml
from typing import List, Dict, Any, Optional
import re

class FileOrganizer:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self.load_config(config_path)
        self.setup_logging()
        
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Expand user directory (~)
            config['target_directory'] = os.path.expanduser(config['target_directory'])
            return config
        except FileNotFoundError:
            logging.error(f"Config file {config_path} not found")
            raise
        except yaml.YAMLError as e:
            logging.error(f"Error parsing config file: {e}")
            raise
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_file = self.config.get('log_file', 'organizer.log')
        log_dir = os.path.dirname(log_file)
        
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def get_date_group(self, file_path: Path) -> str:
        """Categorize file based on modification date"""
        try:
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            now = datetime.now()
            days_diff = (now - mod_time).days
            
            date_groups = self.config.get('date_groups', {})
            
            if days_diff <= date_groups.get('last_week', 7):
                return "Last_Week"
            elif days_diff <= date_groups.get('last_month', 30):
                return "Last_Month"
            else:
                return "Older"
        except OSError as e:
            logging.warning(f"Could not get file stats for {file_path}: {e}")
            return "Unknown"
    
    def should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed"""
        # Skip directories, hidden files, and system files
        if (file_path.is_dir() or 
            file_path.name.startswith('.') or 
            file_path.name.startswith('~$')):
            return False
        
        # Skip files that are currently in use (Windows)
        try:
            with open(file_path, 'a'):
                pass
            return True
        except (OSError, IOError):
            logging.warning(f"File {file_path} is locked or inaccessible")
            return False
    
    def resolve_conflict(self, source: Path, destination: Path) -> Optional[Path]:
        """Handle file naming conflicts"""
        resolution = self.config.get('conflict_resolution', 'rename')
        
        if not destination.exists():
            return destination
        
        if resolution == 'skip':
            logging.info(f"Skipping {source.name} - destination exists")
            return None
        elif resolution == 'overwrite':
            logging.warning(f"Overwriting {destination}")
            return destination
        elif resolution == 'rename':
            # Add timestamp to filename
            stem = destination.stem
            suffix = destination.suffix
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_destination = destination.with_name(f"{stem}_{timestamp}{suffix}")
            logging.info(f"Renaming {source.name} to {new_destination.name}")
            return new_destination
        
        return None
    
    def create_subfolder_path(self, file_path: Path, pattern: Optional[str]) -> str:
        """Create subfolder path based on pattern"""
        if not pattern:
            return ""
        
        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        
        # Replace pattern placeholders
        folder_path = pattern
        folder_path = folder_path.replace('YYYY', mod_time.strftime('%Y'))
        folder_path = folder_path.replace('MM', mod_time.strftime('%m'))
        folder_path = folder_path.replace('DD', mod_time.strftime('%d'))
        folder_path = folder_path.replace('HH', mod_time.strftime('%H'))
        folder_path = folder_path.replace('MI', mod_time.strftime('%M'))
        
        return folder_path
    
    def process_file(self, file_path: Path, dry_run: bool = False) -> bool:
        """Process a single file based on rules"""
        if not self.should_process_file(file_path):
            return False
        
        file_processed = False
        
        for rule in self.config.get('rules', []):
            for condition in rule.get('conditions', []):
                # Check extension match
                extensions = condition.get('extension', [])
                filename_contains = condition.get('filename_contains', [])
                
                matches_extension = (
                    '*' in extensions or 
                    file_path.suffix.lower() in [ext.lower() for ext in extensions]
                )
                
                matches_filename = (
                    not filename_contains or
                    any(pattern.lower() in file_path.name.lower() 
                        for pattern in filename_contains)
                )
                
                if matches_extension and matches_filename:
                    destination_dir = condition.get('destination', '')
                    
                    # Replace placeholders in destination path
                    destination_dir = destination_dir.replace(
                        '{extension_group}', file_path.suffix[1:].upper()
                    )
                    destination_dir = destination_dir.replace(
                        '{date_group}', self.get_date_group(file_path)
                    )
                    destination_dir = destination_dir.replace(
                        '{filename_prefix}', file_path.stem.split('_')[0]
                    )
                    
                    # Create subfolder path if pattern specified
                    subfolder_pattern = condition.get('subfolder_pattern')
                    subfolder_path = self.create_subfolder_path(file_path, subfolder_pattern)
                    
                    if subfolder_path:
                        destination_dir = os.path.join(destination_dir, subfolder_path)
                    
                    # Create full destination path
                    full_destination = Path(self.config['target_directory']) / destination_dir
                    full_destination.mkdir(parents=True, exist_ok=True)
                    
                    destination_file = full_destination / file_path.name
                    
                    # Handle conflicts
                    destination_file = self.resolve_conflict(file_path, destination_file)
                    if destination_file is None:
                        continue
                    
                    # Move or log the action
                    if dry_run:
                        logging.info(f"DRY RUN: Would move {file_path} to {destination_file}")
                    else:
                        try:
                            shutil.move(str(file_path), str(destination_file))
                            logging.info(f"Moved {file_path} to {destination_file}")
                        except (OSError, shutil.Error) as e:
                            logging.error(f"Error moving {file_path}: {e}")
                            continue
                    
                    file_processed = True
                    break  # Stop checking other conditions in this rule
        
        return file_processed
    
    def organize_files(self, dry_run: bool = None):
        """Main method to organize files"""
        if dry_run is None:
            dry_run = self.config.get('dry_run', False)
        
        target_dir = Path(self.config['target_directory'])
        
        if not target_dir.exists():
            logging.error(f"Target directory {target_dir} does not exist")
            return
        
        logging.info(f"Starting organization of {target_dir} (dry_run: {dry_run})")
        
        files_processed = 0
        files_skipped = 0
        
        # Process files (not directories)
        for file_path in target_dir.iterdir():
            if self.process_file(file_path, dry_run):
                files_processed += 1
            else:
                files_skipped += 1
        
        logging.info(f"Organization complete. Processed: {files_processed}, Skipped: {files_skipped}")
        
        return files_processed, files_skipped