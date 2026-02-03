#!/usr/bin/env python3
"""
System monitoring script for data collection automation.
"""

import json
import os
from datetime import datetime, timedelta
import logging
import requests
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SystemMonitor:
    def __init__(self):
        self.alerts = []
        self.metrics = {
            'timestamp': datetime.now().isoformat(),
            'data_freshness': {},
            'file_sizes': {},
            'system_health': {},
            'recommendations': []
        }
    
    def check_data_freshness(self):
        """Check if data files are fresh."""
        files_to_check = {
            'upcoming.json': 6,    # Should be updated every 6 hours
            'results.json': 24,   # Should be updated daily
            'scrape_state.json': 12  # Should be updated every 12 hours
        }
        
        current_time = datetime.now()
        
        for filename, max_age_hours in files_to_check.items():
            if os.path.exists(filename):
                file_time = datetime.fromtimestamp(os.path.getmtime(filename))
                age_hours = (current_time - file_time).total_seconds() / 3600
                
                self.metrics['data_freshness'][filename] = {
                    'last_modified': file_time.isoformat(),
                    'age_hours': round(age_hours, 2),
                    'is_stale': age_hours > max_age_hours
                }
                
                if age_hours > max_age_hours:
                    self.alerts.append(f"⚠️ {filename} is stale ({age_hours:.1f}h old, max: {max_age_hours}h)")
                    self.metrics['recommendations'].append(f"Update {filename} - last modified {age_hours:.1f} hours ago")
            else:
                self.metrics['data_freshness'][filename] = {
                    'exists': False,
                    'is_stale': True
                }
                self.alerts.append(f"❌ {filename} is missing")
                self.metrics['recommendations'].append(f"Create missing file: {filename}")
    
    def check_file_sizes(self):
        """Check file sizes for anomalies."""
        expected_sizes = {
            'upcoming.json': {'min': 100, 'max': 1000000},      # 100B to 1MB
            'results.json': {'min': 1000, 'max': 100000000},    # 1KB to 100MB
            'scrape_state.json': {'min': 50, 'max': 10000}      # 50B to 10KB
        }
        
        for filename, size_limits in expected_sizes.items():
            if os.path.exists(filename):
                size = os.path.getsize(filename)
                self.metrics['file_sizes'][filename] = {
                    'size_bytes': size,
                    'size_mb': round(size / 1024 / 1024, 2)
                }
                
                if size < size_limits['min']:
                    self.alerts.append(f"⚠️ {filename} is unusually small ({size} bytes)")
                    self.metrics['recommendations'].append(f"Investigate small file size: {filename}")
                elif size > size_limits['max']:
                    self.alerts.append(f"⚠️ {filename} is unusually large ({size / 1024 / 1024:.1f} MB)")
                    self.metrics['recommendations'].append(f"Consider cleaning up large file: {filename}")
    
    def check_data_quality(self):
        """Check data quality metrics."""
        try:
            # Check upcoming matches
            if os.path.exists('upcoming.json'):
                with open('upcoming.json', 'r') as f:
                    upcoming = json.load(f)
                
                if isinstance(upcoming, list):
                    matches_with_odds = sum(1 for match in upcoming 
                                          if any(match.get(f'{bm}1', 'N/A') != 'N/A' 
                                               for bm in ['leovegas', 'nordic', 'unibet']))
                    
                    self.metrics['system_health']['upcoming_matches'] = len(upcoming)
                    self.metrics['system_health']['matches_with_odds'] = matches_with_odds
                    self.metrics['system_health']['odds_coverage'] = (
                        matches_with_odds / max(len(upcoming), 1) * 100
                    )
                    
                    if len(upcoming) == 0:
                        self.alerts.append("❌ No upcoming matches found")
                        self.metrics['recommendations'].append("Check HLTV data source availability")
                    elif matches_with_odds / max(len(upcoming), 1) < 0.5:
                        self.alerts.append("⚠️ Low odds coverage (<50%)")
                        self.metrics['recommendations'].append("Investigate betting odds collection issues")
            
            # Check results data
            if os.path.exists('results.json'):
                with open('results.json', 'r') as f:
                    results = json.load(f)
                
                if isinstance(results, list):
                    enriched_count = sum(1 for match in results if match.get('maps'))
                    
                    self.metrics['system_health']['total_results'] = len(results)
                    self.metrics['system_health']['enriched_results'] = enriched_count
                    self.metrics['system_health']['enrichment_rate'] = (
                        enriched_count / max(len(results), 1) * 100
                    )
                    
                    if enriched_count / max(len(results), 1) < 0.3:
                        self.alerts.append("⚠️ Low enrichment rate (<30%)")
                        self.metrics['recommendations'].append("Optimize detailed data collection process")
        
        except Exception as e:
            self.alerts.append(f"❌ Error checking data quality: {e}")
            self.metrics['recommendations'].append("Fix data quality check errors")
    
    def check_external_dependencies(self):
        """Check external service availability."""
        services = {
            'HLTV Main': 'https://www.hltv.org',
            'HLTV Betting': 'https://www.hltv.org/betting/money',
            'HLTV Results': 'https://www.hltv.org/results'
        }
        
        self.metrics['system_health']['external_services'] = {}
        
        for service_name, url in services.items():
            try:
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                is_available = response.status_code == 200
                self.metrics['system_health']['external_services'][service_name] = {
                    'available': is_available,
                    'status_code': response.status_code,
                    'response_time_ms': round(response.elapsed.total_seconds() * 1000, 2)
                }
                
                if not is_available:
                    self.alerts.append(f"❌ {service_name} is not available (HTTP {response.status_code})")
                    self.metrics['recommendations'].append(f"Check {service_name} service status")
                
            except Exception as e:
                self.metrics['system_health']['external_services'][service_name] = {
                    'available': False,
                    'error': str(e)
                }
                self.alerts.append(f"❌ Cannot reach {service_name}: {e}")
                self.metrics['recommendations'].append(f"Investigate connectivity to {service_name}")
    
    def generate_health_score(self):
        """Generate overall system health score."""
        score = 100
        
        # Deduct points for various issues
        for filename, data in self.metrics['data_freshness'].items():
            if data.get('is_stale', False):
                score -= 20
        
        if self.metrics['system_health'].get('odds_coverage', 100) < 50:
            score -= 15
        
        if self.metrics['system_health'].get('enrichment_rate', 100) < 30:
            score -= 15
        
        unavailable_services = sum(1 for service in self.metrics['system_health'].get('external_services', {}).values()
                                 if not service.get('available', True))
        score -= unavailable_services * 10
        
        self.metrics['system_health']['overall_score'] = max(0, score)
        
        if score < 70:
            self.alerts.append(f"⚠️ System health score is low: {score}/100")
            self.metrics['recommendations'].append("Address system health issues to improve reliability")
    
    def save_monitoring_report(self):
        """Save monitoring report to files."""
        # Save detailed metrics
        with open('monitoring_metrics.json', 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)
        
        # Save alerts summary
        if self.alerts:
            with open('monitoring_alerts.txt', 'w') as f:
                f.write('\n'.join(self.alerts))
        
        # Save recommendations
        if self.metrics['recommendations']:
            with open('monitoring_recommendations.txt', 'w') as f:
                f.write('\n'.join(self.metrics['recommendations']))
    
    def run_monitoring(self):
        """Run complete monitoring check."""
        logging.info("Starting system monitoring...")
        
        self.check_data_freshness()
        self.check_file_sizes()
        self.check_data_quality()
        self.check_external_dependencies()
        self.generate_health_score()
        
        self.save_monitoring_report()
        
        # Log summary
        health_score = self.metrics['system_health']['overall_score']
        logging.info(f"Monitoring completed. Health score: {health_score}/100")
        
        if self.alerts:
            logging.warning(f"Found {len(self.alerts)} alerts")
            for alert in self.alerts:
                logging.warning(alert)
        else:
            logging.info("No alerts found - system is healthy")
        
        return health_score >= 70

def main():
    """Main monitoring function."""
    monitor = SystemMonitor()
    is_healthy = monitor.run_monitoring()
    
    if not is_healthy:
        logging.error("System health check failed")
        exit(1)
    else:
        logging.info("System health check passed")

if __name__ == "__main__":
    main()