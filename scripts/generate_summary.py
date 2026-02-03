#!/usr/bin/env python3
"""
Generate data summary and statistics for the betting data collection.
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_json_safe(filepath):
    """Safely load JSON file, return empty list if file doesn't exist or is invalid."""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.warning(f"Could not load {filepath}: {e}")
    return []

def analyze_upcoming_matches():
    """Analyze upcoming matches data."""
    upcoming = load_json_safe('upcoming.json')
    
    stats = {
        'total_matches': len(upcoming),
        'matches_with_odds': 0,
        'bookmakers': defaultdict(int),
        'teams': Counter(),
        'last_updated': datetime.now().isoformat()
    }
    
    for match in upcoming:
        teams = [match.get('team1', ''), match.get('team2', '')]
        stats['teams'].update(teams)
        
        # Check which bookmakers have odds
        has_odds = False
        for bookmaker in ['leovegas', 'nordic', 'unibet']:
            if (match.get(f'{bookmaker}1', 'N/A') != 'N/A' or 
                match.get(f'{bookmaker}2', 'N/A') != 'N/A'):
                stats['bookmakers'][bookmaker] += 1
                has_odds = True
        
        if has_odds:
            stats['matches_with_odds'] += 1
    
    # Convert Counter to regular dict for JSON serialization
    stats['teams'] = dict(stats['teams'].most_common(20))
    stats['bookmakers'] = dict(stats['bookmakers'])
    
    return stats

def analyze_results():
    """Analyze historical results data."""
    results = load_json_safe('results.json')
    
    stats = {
        'total_matches': len(results),
        'enriched_matches': 0,
        'events': Counter(),
        'teams': Counter(),
        'date_range': {'earliest': None, 'latest': None},
        'maps_played': Counter(),
        'last_updated': datetime.now().isoformat()
    }
    
    dates = []
    
    for match in results:
        # Count enriched matches (those with detailed data)
        if match.get('maps') or match.get('format'):
            stats['enriched_matches'] += 1
        
        # Event statistics
        event = match.get('event', 'Unknown')
        stats['events'][event] += 1
        
        # Team statistics
        teams = [match.get('team1', ''), match.get('team2', '')]
        stats['teams'].update(teams)
        
        # Date range
        if match.get('date'):
            dates.append(match['date'])
        
        # Map statistics
        for map_data in match.get('maps', []):
            map_name = map_data.get('map', 'Unknown')
            stats['maps_played'][map_name] += 1
    
    if dates:
        stats['date_range']['earliest'] = min(dates)
        stats['date_range']['latest'] = max(dates)
    
    # Convert Counters to regular dicts for JSON serialization
    stats['events'] = dict(stats['events'].most_common(10))
    stats['teams'] = dict(stats['teams'].most_common(20))
    stats['maps_played'] = dict(stats['maps_played'].most_common(10))
    
    return stats

def generate_readme_stats():
    """Generate statistics section for README."""
    upcoming_stats = analyze_upcoming_matches()
    results_stats = analyze_results()
    
    readme_content = f"""# CS:GO/CS2 Betting Data Collection

🤖 **Automated data collection system for CS:GO/CS2 match odds and results**

## 📊 Current Statistics

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

### Upcoming Matches
- **Total matches with odds:** {upcoming_stats['matches_with_odds']}/{upcoming_stats['total_matches']}
- **Active bookmakers:** {', '.join(upcoming_stats['bookmakers'].keys()) if upcoming_stats['bookmakers'] else 'None'}
- **Most frequent teams:** {', '.join(list(upcoming_stats['teams'].keys())[:5]) if upcoming_stats['teams'] else 'None'}

### Historical Results  
- **Total matches collected:** {results_stats['total_matches']:,}
- **Enriched with details:** {results_stats['enriched_matches']:,} ({results_stats['enriched_matches']/max(results_stats['total_matches'], 1)*100:.1f}%)
- **Date range:** {results_stats['date_range']['earliest']} to {results_stats['date_range']['latest']}
- **Top events:** {', '.join(list(results_stats['events'].keys())[:3]) if results_stats['events'] else 'None'}
- **Most played maps:** {', '.join(list(results_stats['maps_played'].keys())[:3]) if results_stats['maps_played'] else 'None'}

## 🔄 Automation

This repository automatically collects data every 4 hours using GitHub Actions:
- **Odds collection** from HLTV betting section
- **Results scraping** with detailed match statistics  
- **Data validation** and error handling
- **Automatic commits** when new data is available

## 📁 Data Files

- `upcoming.json` - Current matches with betting odds
- `results.json` - Historical match results with detailed statistics
- `scrape_state.json` - Scraping progress state (auto-generated)
- `failed_urls.json` - Failed URL log for debugging (auto-generated)

## 🛠️ Technical Details

**Dependencies:**
- Python 3.11+
- FlareSolverr (Docker container for Cloudflare bypass)
- BeautifulSoup4 for HTML parsing
- Requests for HTTP handling

**Data Sources:**
- HLTV.org betting odds
- HLTV.org match results and statistics

---
*This README is automatically updated by the data collection system.*
"""
    
    return readme_content

def main():
    """Main function to generate all summaries."""
    logging.info("Generating data summaries...")
    
    # Generate individual stats files
    upcoming_stats = analyze_upcoming_matches()
    results_stats = analyze_results()
    
    # Save detailed statistics
    with open('data_summary.json', 'w', encoding='utf-8') as f:
        json.dump({
            'upcoming': upcoming_stats,
            'results': results_stats,
            'generated_at': datetime.now().isoformat()
        }, f, indent=2, ensure_ascii=False)
    
    # Generate and save README
    readme_content = generate_readme_stats()
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    logging.info("Summary generation completed")
    logging.info(f"Upcoming matches: {upcoming_stats['total_matches']}")
    logging.info(f"Historical results: {results_stats['total_matches']}")

if __name__ == "__main__":
    main()