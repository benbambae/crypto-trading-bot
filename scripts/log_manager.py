#!/usr/bin/env python3
"""
Log Management Script for Cryptocurrency Trading Bot
Handles log rotation, archiving, and cleanup operations
"""

import os
import shutil
import datetime
import glob
import gzip
from pathlib import Path
import argparse

class LogManager:
    def __init__(self, base_log_dir="/Users/benjamin/Desktop/bencryptobot/logs"):
        self.base_log_dir = Path(base_log_dir)
        self.archived_dir = self.base_log_dir / "archived"
        
    def archive_old_logs(self, days_old=30):
        """Archive logs older than specified days"""
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_old)
        archived_count = 0
        
        # Get current year for archiving
        current_year = datetime.datetime.now().year
        archive_year_dir = self.archived_dir / str(current_year)
        archive_year_dir.mkdir(exist_ok=True)
        
        for log_file in self.base_log_dir.rglob("*.log"):
            # Skip already archived files
            if "archived" in str(log_file):
                continue
                
            # Check file modification time
            file_mtime = datetime.datetime.fromtimestamp(log_file.stat().st_mtime)
            
            if file_mtime < cutoff_date:
                # Create archive subdirectory structure
                relative_path = log_file.relative_to(self.base_log_dir)
                archive_dest = archive_year_dir / relative_path.parent
                archive_dest.mkdir(parents=True, exist_ok=True)
                
                # Compress and move file
                compressed_name = archive_dest / f"{log_file.stem}_{file_mtime.strftime('%Y%m%d')}.log.gz"
                
                with open(log_file, 'rb') as f_in:
                    with gzip.open(compressed_name, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                log_file.unlink()  # Remove original
                archived_count += 1
                print(f"Archived: {log_file} -> {compressed_name}")
        
        print(f"Archived {archived_count} log files")
        return archived_count
    
    def cleanup_empty_logs(self):
        """Remove empty log files"""
        removed_count = 0
        
        for log_file in self.base_log_dir.rglob("*.log"):
            if log_file.stat().st_size == 0:
                log_file.unlink()
                removed_count += 1
                print(f"Removed empty log: {log_file}")
        
        print(f"Removed {removed_count} empty log files")
        return removed_count
    
    def rotate_large_logs(self, max_size_mb=10):
        """Rotate logs larger than specified size"""
        max_size_bytes = max_size_mb * 1024 * 1024
        rotated_count = 0
        
        for log_file in self.base_log_dir.rglob("*.log"):
            if "archived" in str(log_file):
                continue
                
            if log_file.stat().st_size > max_size_bytes:
                # Create rotated filename
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                rotated_name = log_file.parent / f"{log_file.stem}_{timestamp}.log"
                
                # Rename current log
                log_file.rename(rotated_name)
                
                # Create new empty log file
                log_file.touch()
                
                rotated_count += 1
                print(f"Rotated large log: {log_file} -> {rotated_name}")
        
        print(f"Rotated {rotated_count} large log files")
        return rotated_count
    
    def organize_logs_by_date(self):
        """Organize logs with timestamps in their names by date"""
        organized_count = 0
        
        # Pattern for logs with dates in filename
        for log_file in self.base_log_dir.rglob("*202*.log"):
            if "archived" in str(log_file):
                continue
                
            # Extract date from filename
            filename = log_file.name
            try:
                # Look for date patterns like 20250615, 20250615_123456, etc.
                import re
                date_match = re.search(r'(\d{8})', filename)
                if date_match:
                    date_str = date_match.group(1)
                    date_obj = datetime.datetime.strptime(date_str, '%Y%m%d')
                    
                    # Create date-based directory
                    date_dir = log_file.parent / date_obj.strftime('%Y-%m')
                    date_dir.mkdir(exist_ok=True)
                    
                    # Move file to date directory
                    new_path = date_dir / log_file.name
                    if not new_path.exists():
                        log_file.rename(new_path)
                        organized_count += 1
                        print(f"Organized: {log_file} -> {new_path}")
                        
            except (ValueError, AttributeError):
                continue
        
        print(f"Organized {organized_count} log files by date")
        return organized_count
    
    def generate_log_summary(self):
        """Generate a summary of log structure and sizes"""
        print("\n" + "="*60)
        print("LOG DIRECTORY SUMMARY")
        print("="*60)
        
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(self.base_log_dir):
            if not files:
                continue
                
            root_path = Path(root)
            relative_path = root_path.relative_to(self.base_log_dir)
            
            section_size = 0
            section_files = 0
            
            for file in files:
                file_path = root_path / file
                if file_path.suffix in ['.log', '.gz']:
                    size = file_path.stat().st_size
                    section_size += size
                    total_size += size
                    section_files += 1
                    file_count += 1
            
            if section_files > 0:
                print(f"\n{relative_path if str(relative_path) != '.' else 'Root'}:")
                print(f"  Files: {section_files}")
                print(f"  Size: {self._format_size(section_size)}")
                
                # Show recent files
                log_files = list(root_path.glob("*.log"))
                if log_files:
                    recent_files = sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]
                    print(f"  Recent files: {', '.join([f.name for f in recent_files])}")
        
        print(f"\nTOTAL: {file_count} files, {self._format_size(total_size)}")
        print("="*60)
    
    def _format_size(self, size_bytes):
        """Format byte size to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

def main():
    parser = argparse.ArgumentParser(description='Manage trading bot logs')
    parser.add_argument('--archive', type=int, metavar='DAYS', 
                       help='Archive logs older than DAYS (default: 30)')
    parser.add_argument('--cleanup', action='store_true', 
                       help='Remove empty log files')
    parser.add_argument('--rotate', type=int, metavar='MB', 
                       help='Rotate logs larger than MB (default: 10)')
    parser.add_argument('--organize', action='store_true', 
                       help='Organize logs by date')
    parser.add_argument('--summary', action='store_true', 
                       help='Show log directory summary')
    parser.add_argument('--all', action='store_true', 
                       help='Run all maintenance operations')
    
    args = parser.parse_args()
    
    log_manager = LogManager()
    
    if args.all:
        print("Running all log maintenance operations...")
        log_manager.cleanup_empty_logs()
        log_manager.rotate_large_logs(10)
        log_manager.organize_logs_by_date()
        log_manager.archive_old_logs(30)
        log_manager.generate_log_summary()
    else:
        if args.cleanup:
            log_manager.cleanup_empty_logs()
        
        if args.rotate is not None:
            log_manager.rotate_large_logs(args.rotate)
        
        if args.organize:
            log_manager.organize_logs_by_date()
        
        if args.archive is not None:
            log_manager.archive_old_logs(args.archive)
        
        if args.summary:
            log_manager.generate_log_summary()
    
    if not any(vars(args).values()):
        log_manager.generate_log_summary()

if __name__ == "__main__":
    main()