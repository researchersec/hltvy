#!/usr/bin/env python3
"""
Generate data quality report with visualizations.
"""

import json
import os
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import logging

# Try to import optional dependencies
try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    logging.warning("Visualization libraries not available. Generating text-only report.")

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

def analyze_data_quality():
    """Analyze data quality metrics."""
    upcoming = load_json_safe('upcoming.json')
    results = load_json_safe('results.json')
    
    quality_metrics = {
        'timestamp': datetime.now().isoformat(),
        'upcoming': {
            'total_matches': len(upcoming),
            'complete_odds': 0,
            'partial_odds': 0,
            'no_odds': 0,
            'bookmaker_coverage': defaultdict(int),
            'team_frequency': Counter()
        },
        'results': {
            'total_matches': len(results),
            'enriched_matches': 0,
            'date_coverage': defaultdict(int),
            'event_distribution': Counter(),
            'map_statistics': Counter(),
            'completeness_score': 0
        }
    }
    
    # Analyze upcoming matches
    for match in upcoming:
        bookmakers = ['leovegas', 'nordic', 'unibet']
        odds_count = 0
        
        for bookmaker in bookmakers:
            has_odds = (match.get(f'{bookmaker}1', 'N/A') != 'N/A' or 
                       match.get(f'{bookmaker}2', 'N/A') != 'N/A')
            if has_odds:
                quality_metrics['upcoming']['bookmaker_coverage'][bookmaker] += 1
                odds_count += 1
        
        if odds_count == 0:
            quality_metrics['upcoming']['no_odds'] += 1
        elif odds_count == len(bookmakers):
            quality_metrics['upcoming']['complete_odds'] += 1
        else:
            quality_metrics['upcoming']['partial_odds'] += 1
        
        # Track team frequency
        teams = [match.get('team1', ''), match.get('team2', '')]
        quality_metrics['upcoming']['team_frequency'].update(teams)
    
    # Analyze results
    for match in results:
        # Check enrichment level
        enrichment_score = 0
        if match.get('maps'):
            enrichment_score += 3
        if match.get('format'):
            enrichment_score += 1
        if match.get('veto'):
            enrichment_score += 1
        
        if enrichment_score >= 3:
            quality_metrics['results']['enriched_matches'] += 1
        
        # Date coverage
        if match.get('date'):
            quality_metrics['results']['date_coverage'][match['date']] += 1
        
        # Event distribution
        event = match.get('event', 'Unknown')
        quality_metrics['results']['event_distribution'][event] += 1
        
        # Map statistics
        for map_data in match.get('maps', []):
            map_name = map_data.get('map', 'Unknown')
            quality_metrics['results']['map_statistics'][map_name] += 1
    
    # Calculate completeness score
    if quality_metrics['results']['total_matches'] > 0:
        quality_metrics['results']['completeness_score'] = (
            quality_metrics['results']['enriched_matches'] / 
            quality_metrics['results']['total_matches'] * 100
        )
    
    return quality_metrics

def generate_visualizations(metrics):
    """Generate quality visualizations if libraries are available."""
    if not VISUALIZATION_AVAILABLE:
        return
    
    plt.style.use('seaborn-v0_8')
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Data Quality Report', fontsize=16, fontweight='bold')
    
    # 1. Bookmaker coverage
    ax1 = axes[0, 0]
    bookmakers = list(metrics['upcoming']['bookmaker_coverage'].keys())
    coverage = list(metrics['upcoming']['bookmaker_coverage'].values())
    
    if bookmakers:
        ax1.bar(bookmakers, coverage, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
        ax1.set_title('Bookmaker Coverage (Upcoming Matches)')
        ax1.set_ylabel('Number of Matches')
        ax1.tick_params(axis='x', rotation=45)
    
    # 2. Odds completeness
    ax2 = axes[0, 1]
    odds_labels = ['Complete Odds', 'Partial Odds', 'No Odds']
    odds_values = [
        metrics['upcoming']['complete_odds'],
        metrics['upcoming']['partial_odds'],
        metrics['upcoming']['no_odds']
    ]
    colors = ['#2ca02c', '#ff7f0e', '#d62728']
    
    if sum(odds_values) > 0:
        ax2.pie(odds_values, labels=odds_labels, colors=colors, autopct='%1.1f%%')
        ax2.set_title('Odds Completeness Distribution')
    
    # 3. Results enrichment over time
    ax3 = axes[1, 0]
    dates = sorted(metrics['results']['date_coverage'].keys())[-30:]  # Last 30 days
    counts = [metrics['results']['date_coverage'][date] for date in dates]
    
    if dates:
        ax3.plot(range(len(dates)), counts, marker='o', linewidth=2, markersize=4)
        ax3.set_title('Match Results Over Time (Last 30 Days)')
        ax3.set_ylabel('Number of Matches')
        ax3.set_xlabel('Days')
        ax3.grid(True, alpha=0.3)
    
    # 4. Top events
    ax4 = axes[1, 1]
    top_events = dict(metrics['results']['event_distribution'].most_common(8))
    
    if top_events:
        events = list(top_events.keys())
        counts = list(top_events.values())
        ax4.barh(events, counts, color='#9467bd')
        ax4.set_title('Top Events by Match Count')
        ax4.set_xlabel('Number of Matches')
    
    plt.tight_layout()
    plt.savefig('data_quality_charts.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    logging.info("Quality visualizations saved to data_quality_charts.png")

def generate_html_report(metrics):
    """Generate HTML quality report."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Data Quality Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
            .metric-card {{ background: white; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; margin: 15px 0; }}
            .metric-title {{ font-size: 18px; font-weight: bold; color: #495057; margin-bottom: 10px; }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
            .metric-description {{ color: #6c757d; margin-top: 5px; }}
            .quality-score {{ font-size: 32px; font-weight: bold; }}
            .good {{ color: #28a745; }}
            .warning {{ color: #ffc107; }}
            .danger {{ color: #dc3545; }}
            .table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            .table th, .table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
            .table th {{ background-color: #f8f9fa; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Data Quality Report</h1>
            <p><strong>Generated:</strong> {metrics['timestamp']}</p>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">Overall Data Quality Score</div>
            <div class="metric-value quality-score {'good' if metrics['results']['completeness_score'] >= 80 else 'warning' if metrics['results']['completeness_score'] >= 60 else 'danger'}">
                {metrics['results']['completeness_score']:.1f}%
            </div>
            <div class="metric-description">Based on data enrichment and completeness</div>
        </div>
        
        <h2>📈 Upcoming Matches Analysis</h2>
        
        <div class="metric-card">
            <div class="metric-title">Total Upcoming Matches</div>
            <div class="metric-value">{metrics['upcoming']['total_matches']}</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">Odds Coverage</div>
            <table class="table">
                <tr><th>Category</th><th>Count</th><th>Percentage</th></tr>
                <tr><td>Complete Odds (All Bookmakers)</td><td>{metrics['upcoming']['complete_odds']}</td><td>{metrics['upcoming']['complete_odds']/max(metrics['upcoming']['total_matches'], 1)*100:.1f}%</td></tr>
                <tr><td>Partial Odds</td><td>{metrics['upcoming']['partial_odds']}</td><td>{metrics['upcoming']['partial_odds']/max(metrics['upcoming']['total_matches'], 1)*100:.1f}%</td></tr>
                <tr><td>No Odds Available</td><td>{metrics['upcoming']['no_odds']}</td><td>{metrics['upcoming']['no_odds']/max(metrics['upcoming']['total_matches'], 1)*100:.1f}%</td></tr>
            </table>
        </div>
        
        <h2>📋 Historical Results Analysis</h2>
        
        <div class="metric-card">
            <div class="metric-title">Total Historical Matches</div>
            <div class="metric-value">{metrics['results']['total_matches']:,}</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">Enriched Matches</div>
            <div class="metric-value">{metrics['results']['enriched_matches']:,}</div>
            <div class="metric-description">{metrics['results']['completeness_score']:.1f}% of matches have detailed statistics</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">Top Events</div>
            <table class="table">
                <tr><th>Event</th><th>Matches</th></tr>
    """
    
    for event, count in metrics['results']['event_distribution'].most_common(10):
        html_content += f"<tr><td>{event}</td><td>{count}</td></tr>"
    
    html_content += """
            </table>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">Most Played Maps</div>
            <table class="table">
                <tr><th>Map</th><th>Times Played</th></tr>
    """
    
    for map_name, count in metrics['results']['map_statistics'].most_common(10):
        html_content += f"<tr><td>{map_name}</td><td>{count}</td></tr>"
    
    html_content += """
            </table>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">Data Collection Recommendations</div>
            <ul>
    """
    
    # Add recommendations based on metrics
    if metrics['upcoming']['no_odds'] > metrics['upcoming']['complete_odds']:
        html_content += "<li>⚠️ Many matches lack betting odds - consider checking data source availability</li>"
    
    if metrics['results']['completeness_score'] < 70:
        html_content += "<li>⚠️ Low enrichment rate - consider optimizing the detailed data collection process</li>"
    
    if metrics['results']['total_matches'] < 100:
        html_content += "<li>📈 Consider extending the historical data collection period</li>"
    
    html_content += """
            </ul>
        </div>
    </body>
    </html>
    """
    
    return html_content

def main():
    """Main function to generate quality report."""
    logging.info("Generating data quality report...")
    
    # Analyze data quality
    metrics = analyze_data_quality()
    
    # Generate visualizations if possible
    if VISUALIZATION_AVAILABLE:
        generate_visualizations(metrics)
    
    # Generate HTML report
    html_report = generate_html_report(metrics)
    with open('data_quality_report.html', 'w', encoding='utf-8') as f:
        f.write(html_report)
    
    # Save metrics as JSON
    with open('quality_metrics.json', 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, default=str)
    
    logging.info("Quality report generated successfully")
    logging.info(f"Overall quality score: {metrics['results']['completeness_score']:.1f}%")

if __name__ == "__main__":
    main()