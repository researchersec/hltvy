#!/usr/bin/env python3
"""
Recovery helper script for data collection issues.
"""

import json
import os
import logging
from datetime import datetime
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def analyze_current_state():
    """Analyze current state and data files."""
    analysis = {
        'timestamp': datetime.now().isoformat(),
        'files': {},
        'state': {},
        'recommendations': []
    }
    
    # Check results.json
    if os.path.exists('results.json'):
        try:
            with open('results.json', 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            analysis['files']['results.json'] = {
                'exists': True,
                'size_mb': round(os.path.getsize('results.json') / 1024 / 1024, 2),
                'count': len(results) if isinstance(results, list) else 0,
                'valid': isinstance(results, list)
            }
            
            if isinstance(results, list) and results:
                # Analyze data quality
                match_ids = [r.get('match-id') for r in results if r.get('match-id')]
                unique_ids = set(match_ids)
                
                enriched_count = sum(1 for r in results if r.get('maps') or r.get('format'))
                
                analysis['files']['results.json'].update({
                    'unique_matches': len(unique_ids),
                    'duplicates': len(match_ids) - len(unique_ids),
                    'enriched_matches': enriched_count,
                    'enrichment_rate': enriched_count / len(results) * 100 if results else 0,
                    'date_range': {
                        'earliest': min([r.get('date', '9999-12-31') for r in results if r.get('date')], default=None),
                        'latest': max([r.get('date', '0000-01-01') for r in results if r.get('date')], default=None)
                    }
                })
                
                if analysis['files']['results.json']['duplicates'] > 0:
                    analysis['recommendations'].append(f"Remove {analysis['files']['results.json']['duplicates']} duplicate matches")
        
        except Exception as e:
            analysis['files']['results.json'] = {
                'exists': True,
                'error': str(e),
                'valid': False
            }
            analysis['recommendations'].append("Fix corrupted results.json file")
    else:
        analysis['files']['results.json'] = {'exists': False}
        analysis['recommendations'].append("Create empty results.json file")
    
    # Check scrape_state.json
    if os.path.exists('scrape_state.json'):
        try:
            with open('scrape_state.json', 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            analysis['state'] = {
                'exists': True,
                'results_offset': state.get('results_offset', 0),
                'enriched_count': len(state.get('enriched_match_ids', {})),
                'valid': isinstance(state, dict)
            }
            
            # Check if offset is reasonable
            if state.get('results_offset', 0) > 50000:
                analysis['recommendations'].append("Reset high results_offset (may be stuck)")
            
        except Exception as e:
            analysis['state'] = {
                'exists': True,
                'error': str(e),
                'valid': False
            }
            analysis['recommendations'].append("Fix corrupted scrape_state.json file")
    else:
        analysis['state'] = {'exists': False}
        analysis['recommendations'].append("Create initial scrape_state.json file")
    
    # Check upcoming.json
    if os.path.exists('upcoming.json'):
        try:
            with open('upcoming.json', 'r', encoding='utf-8') as f:
                upcoming = json.load(f)
            
            analysis['files']['upcoming.json'] = {
                'exists': True,
                'count': len(upcoming) if isinstance(upcoming, list) else 0,
                'valid': isinstance(upcoming, list)
            }
        except Exception as e:
            analysis['files']['upcoming.json'] = {
                'exists': True,
                'error': str(e),
                'valid': False
            }
    else:
        analysis['files']['upcoming.json'] = {'exists': False}
    
    return analysis

def fix_duplicate_matches():
    """Remove duplicate matches from results.json."""
    if not os.path.exists('results.json'):
        logging.error("results.json not found")
        return False
    
    try:
        with open('results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        if not isinstance(results, list):
            logging.error("results.json is not a list")
            return False
        
        original_count = len(results)
        
        # Remove duplicates based on match-id
        seen_ids = set()
        unique_results = []
        
        for match in results:
            match_id = match.get('match-id')
            if match_id and match_id not in seen_ids:
                seen_ids.add(match_id)
                unique_results.append(match)
            elif not match_id:
                # Keep matches without ID but log warning
                unique_results.append(match)
                logging.warning("Found match without match-id")
        
        # Sort by match-id for consistency
        unique_results.sort(key=lambda x: x.get('match-id', 0), reverse=True)
        
        # Save cleaned results
        with open('results.json', 'w', encoding='utf-8') as f:
            json.dump(unique_results, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Removed duplicates: {original_count} -> {len(unique_results)} matches")
        return True
        
    except Exception as e:
        logging.error(f"Failed to fix duplicates: {e}")
        return False

def reset_scrape_state(reset_offset=False, reset_enriched=False):
    """Reset scrape state to recover from stuck state."""
    try:
        if os.path.exists('scrape_state.json'):
            with open('scrape_state.json', 'r', encoding='utf-8') as f:
                state = json.load(f)
        else:
            state = {}
        
        if reset_offset:
            old_offset = state.get('results_offset', 0)
            state['results_offset'] = 0
            logging.info(f"Reset results_offset from {old_offset} to 0")
        
        if reset_enriched:
            old_count = len(state.get('enriched_match_ids', {}))
            state['enriched_match_ids'] = {}
            logging.info(f"Reset enriched_match_ids (was {old_count} entries)")
        
        # Ensure required fields exist
        state.setdefault('results_offset', 0)
        state.setdefault('enriched_match_ids', {})
        
        with open('scrape_state.json', 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        
        logging.info("Scrape state reset successfully")
        return True
        
    except Exception as e:
        logging.error(f"Failed to reset scrape state: {e}")
        return False

def create_missing_files():
    """Create missing data files with default content."""
    files_created = []
    
    # Create results.json if missing
    if not os.path.exists('results.json'):
        with open('results.json', 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        files_created.append('results.json')
    
    # Create upcoming.json if missing
    if not os.path.exists('upcoming.json'):
        with open('upcoming.json', 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        files_created.append('upcoming.json')
    
    # Create scrape_state.json if missing
    if not os.path.exists('scrape_state.json'):
        with open('scrape_state.json', 'w', encoding='utf-8') as f:
            json.dump({
                'results_offset': 0,
                'enriched_match_ids': {}
            }, f, indent=2)
        files_created.append('scrape_state.json')
    
    if files_created:
        logging.info(f"Created missing files: {', '.join(files_created)}")
    
    return files_created

def backup_current_data():
    """Create backup of current data files."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f"backup_{timestamp}"
    
    try:
        os.makedirs(backup_dir, exist_ok=True)
        
        files_to_backup = ['results.json', 'upcoming.json', 'scrape_state.json']
        backed_up = []
        
        for filename in files_to_backup:
            if os.path.exists(filename):
                backup_path = os.path.join(backup_dir, filename)
                with open(filename, 'r', encoding='utf-8') as src:
                    with open(backup_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                backed_up.append(filename)
        
        logging.info(f"Backup created in {backup_dir}: {', '.join(backed_up)}")
        return backup_dir
        
    except Exception as e:
        logging.error(f"Failed to create backup: {e}")
        return None

def main():
    """Main recovery function."""
    import sys
    
    # Check for auto-fix argument
    auto_fix = '--auto-fix' in sys.argv
    
    if auto_fix:
        print("🔧 Running automatic recovery...")
        
        # Analyze current state
        analysis = analyze_current_state()
        
        # Auto-fix common issues
        fixed_issues = []
        
        # Create missing files
        created_files = create_missing_files()
        if created_files:
            fixed_issues.append(f"Created missing files: {', '.join(created_files)}")
        
        # Fix duplicates if found
        results_info = analysis['files'].get('results.json', {})
        if results_info.get('duplicates', 0) > 0:
            if fix_duplicate_matches():
                fixed_issues.append(f"Removed {results_info['duplicates']} duplicate matches")
        
        # Reset offset if too high
        state_info = analysis['state']
        if state_info.get('results_offset', 0) > 50000:
            if reset_scrape_state(reset_offset=True):
                fixed_issues.append("Reset high results_offset")
        
        if fixed_issues:
            print("✅ Auto-fix completed:")
            for issue in fixed_issues:
                print(f"  - {issue}")
        else:
            print("ℹ️ No issues found that could be auto-fixed")
        
        return
    
    print("🔧 Data Collection Recovery Helper")
    print("=" * 40)
    
    # Analyze current state
    analysis = analyze_current_state()
    
    print(f"\n📊 Current State Analysis:")
    print(f"Timestamp: {analysis['timestamp']}")
    
    # Results file
    results_info = analysis['files'].get('results.json', {})
    if results_info.get('exists'):
        print(f"✅ results.json: {results_info.get('count', 0)} matches, {results_info.get('size_mb', 0)} MB")
        if results_info.get('duplicates', 0) > 0:
            print(f"⚠️  Found {results_info['duplicates']} duplicate matches")
        if results_info.get('enrichment_rate', 0) > 0:
            print(f"📈 Enrichment rate: {results_info['enrichment_rate']:.1f}%")
    else:
        print("❌ results.json: Missing")
    
    # State file
    state_info = analysis['state']
    if state_info.get('exists'):
        print(f"✅ scrape_state.json: Offset {state_info.get('results_offset', 0)}, {state_info.get('enriched_count', 0)} enriched")
    else:
        print("❌ scrape_state.json: Missing")
    
    # Recommendations
    if analysis['recommendations']:
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(analysis['recommendations'], 1):
            print(f"{i}. {rec}")
    
    # Interactive recovery options
    print(f"\n🛠️ Recovery Options:")
    print("1. Create missing files")
    print("2. Fix duplicate matches")
    print("3. Reset scrape offset (if stuck)")
    print("4. Reset enrichment state")
    print("5. Create backup of current data")
    print("6. Full recovery (all of the above)")
    print("0. Exit")
    
    try:
        choice = input("\nSelect option (0-6): ").strip()
        
        if choice == '0':
            print("Exiting...")
            return
        
        # Create backup first for destructive operations
        if choice in ['2', '3', '4', '6']:
            print("\n📦 Creating backup first...")
            backup_dir = backup_current_data()
            if backup_dir:
                print(f"✅ Backup created: {backup_dir}")
            else:
                print("⚠️ Backup failed, continuing anyway...")
        
        if choice == '1' or choice == '6':
            print("\n📁 Creating missing files...")
            create_missing_files()
        
        if choice == '2' or choice == '6':
            print("\n🔄 Fixing duplicate matches...")
            fix_duplicate_matches()
        
        if choice == '3' or choice == '6':
            print("\n🔄 Resetting scrape offset...")
            reset_scrape_state(reset_offset=True)
        
        if choice == '4' or choice == '6':
            print("\n🔄 Resetting enrichment state...")
            reset_scrape_state(reset_enriched=True)
        
        if choice == '5':
            print("\n📦 Creating backup...")
            backup_dir = backup_current_data()
            if backup_dir:
                print(f"✅ Backup created: {backup_dir}")
        
        print("\n✅ Recovery operations completed!")
        print("You can now run the data collection scripts again.")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Recovery failed: {e}")

if __name__ == "__main__":
    main()