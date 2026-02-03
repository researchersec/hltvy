#!/usr/bin/env python3
"""
Data cleanup and maintenance script.
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_json_safe(filepath):
    """Safely load JSON file."""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"Error loading {filepath}: {e}")
    return []

def save_json(data, filepath):
    """Save data to JSON file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logging.error(f"Error saving {filepath}: {e}")
        return False

def cleanup_results_data():
    """Clean up and deduplicate results data."""
    results = load_json_safe('results.json')
    
    if not results:
        logging.info("No results data to clean up")
        return
    
    original_count = len(results)
    
    # Remove duplicates based on match-id
    seen_ids = set()
    cleaned_results = []
    
    for match in results:
        match_id = match.get('match-id')
        if match_id and match_id not in seen_ids:
            seen_ids.add(match_id)
            cleaned_results.append(match)
        elif not match_id:
            # Keep matches without ID but log warning
            cleaned_results.append(match)
            logging.warning("Found match without match-id")
    
    # Sort by date (newest first) and match-id
    def sort_key(match):
        date_str = match.get('date', '1900-01-01')
        match_id = match.get('match-id', 0)
        return (date_str, match_id)
    
    cleaned_results.sort(key=sort_key, reverse=True)
    
    # Limit to reasonable size (keep last 10,000 matches)
    if len(cleaned_results) > 10000:
        logging.info(f"Limiting results to 10,000 most recent matches (was {len(cleaned_results)})")
        cleaned_results = cleaned_results[:10000]
    
    if save_json(cleaned_results, 'results.json'):
        logging.info(f"Results cleanup completed: {original_count} -> {len(cleaned_results)} matches")
    
    return cleaned_results

def cleanup_upcoming_data():
    """Clean up upcoming matches data."""
    upcoming = load_json_safe('upcoming.json')
    
    if not upcoming:
        logging.info("No upcoming data to clean up")
        return
    
    original_count = len(upcoming)
    
    # Remove matches without essential data
    cleaned_upcoming = []
    
    for match in upcoming:
        # Must have team names and href
        if (match.get('team1') and match.get('team2') and 
            match.get('href') and match['team1'] != match['team2']):
            cleaned_upcoming.append(match)
        else:
            logging.warning(f"Removing invalid match: {match}")
    
    # Remove duplicates based on href
    seen_hrefs = set()
    final_upcoming = []
    
    for match in cleaned_upcoming:
        href = match.get('href')
        if href not in seen_hrefs:
            seen_hrefs.add(href)
            final_upcoming.append(match)
    
    if save_json(final_upcoming, 'upcoming.json'):
        logging.info(f"Upcoming cleanup completed: {original_count} -> {len(final_upcoming)} matches")
    
    return final_upcoming

def cleanup_state_files():
    """Clean up state and log files."""
    
    # Clean up scrape state
    if os.path.exists('scrape_state.json'):
        state = load_json_safe('scrape_state.json')
        
        # Reset offset if it's too high (prevents infinite loops)
        if state.get('results_offset', 0) > 50000:
            logging.info("Resetting high results_offset")
            state['results_offset'] = 0
        
        # Clean up old enriched match IDs (keep only recent ones)
        enriched_ids = state.get('enriched_match_ids', {})
        if len(enriched_ids) > 5000:
            logging.info(f"Cleaning up enriched_match_ids: {len(enriched_ids)} -> 5000")
            # Keep only the most recent 5000 entries
            sorted_ids = sorted(enriched_ids.items(), key=lambda x: x[0], reverse=True)
            state['enriched_match_ids'] = dict(sorted_ids[:5000])
        
        save_json(state, 'scrape_state.json')
    
    # Clean up failed URLs log
    if os.path.exists('failed_urls.json'):
        try:
            with open('failed_urls.json', 'r') as f:
                lines = f.readlines()
            
            if len(lines) > 500:
                logging.info(f"Trimming failed_urls.json: {len(lines)} -> 500 lines")
                with open('failed_urls.json', 'w') as f:
                    f.writelines(lines[-500:])  # Keep last 500 lines
        except Exception as e:
            logging.error(f"Error cleaning failed_urls.json: {e}")

def generate_cleanup_report():
    """Generate cleanup report."""
    report = {
        'cleanup_timestamp': datetime.now().isoformat(),
        'files_processed': [],
        'statistics': {}
    }
    
    # Check file sizes and record statistics
    for filename in ['results.json', 'upcoming.json', 'scrape_state.json']:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            with open(filename, 'r') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        count = len(data)
                    elif isinstance(data, dict):
                        count = len(data)
                    else:
                        count = 1
                except:
                    count = 0
            
            report['files_processed'].append({
                'filename': filename,
                'size_bytes': size,
                'size_mb': round(size / 1024 / 1024, 2),
                'record_count': count
            })
    
    # Save report
    save_json(report, 'cleanup_report.json')
    logging.info("Cleanup report generated")
    
    return report

def main():
    """Main cleanup function."""
    logging.info("Starting data cleanup process...")
    
    # Perform cleanup operations
    cleanup_results_data()
    cleanup_upcoming_data()
    cleanup_state_files()
    
    # Generate report
    report = generate_cleanup_report()
    
    # Log summary
    total_size = sum(f['size_bytes'] for f in report['files_processed'])
    logging.info(f"Cleanup completed. Total data size: {total_size / 1024 / 1024:.2f} MB")
    
    for file_info in report['files_processed']:
        logging.info(f"{file_info['filename']}: {file_info['record_count']} records, {file_info['size_mb']} MB")

if __name__ == "__main__":
    main()