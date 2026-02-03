#!/usr/bin/env python3
"""
Optimize JSON files for size and performance.
"""

import json
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def optimize_json_file(filepath, compact=False):
    """Optimize a JSON file by removing unnecessary whitespace and sorting keys."""
    if not os.path.exists(filepath):
        return False
    
    try:
        # Load the JSON data
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Get original size
        original_size = os.path.getsize(filepath)
        
        # Save optimized version
        indent = None if compact else 2
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False, sort_keys=True, separators=(',', ':') if compact else (',', ': '))
        
        # Get new size
        new_size = os.path.getsize(filepath)
        
        logging.info(f"Optimized {filepath}: {original_size} -> {new_size} bytes ({((original_size - new_size) / original_size * 100):.1f}% reduction)")
        return True
        
    except Exception as e:
        logging.error(f"Error optimizing {filepath}: {e}")
        return False

def main():
    """Main optimization function."""
    logging.info("Starting JSON optimization...")
    
    # Files to optimize (compact=True for smaller files, False for readability)
    files_to_optimize = [
        ('results.json', True),      # Large file, prioritize size
        ('upcoming.json', False),    # Smaller file, keep readable
        ('scrape_state.json', True), # Internal file, prioritize size
        ('data_summary.json', False), # Summary file, keep readable
        ('quality_metrics.json', False) # Report file, keep readable
    ]
    
    optimized_count = 0
    
    for filepath, compact in files_to_optimize:
        if optimize_json_file(filepath, compact):
            optimized_count += 1
    
    logging.info(f"Optimization completed: {optimized_count} files processed")

if __name__ == "__main__":
    main()