#!/usr/bin/env python3
"""
Data validation script for betting odds and results JSON files.
"""

import json
import os
import sys
from datetime import datetime
import logging
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def validate_upcoming_odds(self, data: List[Dict]) -> bool:
        """Validate upcoming odds data structure."""
        if not isinstance(data, list):
            self.errors.append("upcoming.json must contain a list")
            return False
            
        required_fields = ['team1', 'team2', 'href']
        bookmaker_fields = ['leovegas1', 'leovegas2', 'nordic1', 'nordic2', 'unibet1', 'unibet2']
        
        for i, match in enumerate(data):
            if not isinstance(match, dict):
                self.errors.append(f"Match {i}: Must be a dictionary")
                continue
                
            # Check required fields
            for field in required_fields:
                if field not in match:
                    self.errors.append(f"Match {i}: Missing required field '{field}'")
                elif not match[field]:
                    self.warnings.append(f"Match {i}: Empty value for '{field}'")
            
            # Validate team names
            if 'team1' in match and 'team2' in match:
                if match['team1'] == match['team2']:
                    self.errors.append(f"Match {i}: team1 and team2 cannot be the same")
            
            # Check bookmaker odds format
            for field in bookmaker_fields:
                if field in match and match[field] not in ['N/A', None]:
                    try:
                        float(match[field])
                    except (ValueError, TypeError):
                        self.warnings.append(f"Match {i}: Invalid odds format for '{field}': {match[field]}")
            
            # Validate href format
            if 'href' in match and match['href']:
                if not match['href'].startswith('/matches/'):
                    self.warnings.append(f"Match {i}: Unexpected href format: {match['href']}")
        
        return len(self.errors) == 0
    
    def validate_results(self, data: List[Dict]) -> bool:
        """Validate results data structure."""
        if not isinstance(data, list):
            self.errors.append("results.json must contain a list")
            return False
            
        required_fields = ['match-id', 'url']
        
        match_ids = set()
        
        for i, match in enumerate(data):
            if not isinstance(match, dict):
                self.errors.append(f"Result {i}: Must be a dictionary")
                continue
            
            # Check required fields
            for field in required_fields:
                if field not in match:
                    self.errors.append(f"Result {i}: Missing required field '{field}'")
            
            # Validate match ID uniqueness
            match_id = match.get('match-id')
            if match_id:
                if match_id in match_ids:
                    self.errors.append(f"Result {i}: Duplicate match-id {match_id}")
                match_ids.add(match_id)
            
            # Validate date format
            if 'date' in match and match['date']:
                try:
                    datetime.strptime(match['date'], '%Y-%m-%d')
                except ValueError:
                    self.errors.append(f"Result {i}: Invalid date format '{match['date']}', expected YYYY-MM-DD")
            
            # Validate scores
            for score_field in ['team1score', 'team2score']:
                if score_field in match and match[score_field] is not None:
                    if not isinstance(match[score_field], int) or match[score_field] < 0:
                        self.errors.append(f"Result {i}: Invalid score for '{score_field}': {match[score_field]}")
            
            # Validate maps data if present
            if 'maps' in match and match['maps']:
                self.validate_maps_data(match['maps'], i)
        
        return len(self.errors) == 0
    
    def validate_maps_data(self, maps: List[Dict], match_index: int):
        """Validate maps data structure."""
        if not isinstance(maps, list):
            self.errors.append(f"Result {match_index}: maps must be a list")
            return
        
        for j, map_data in enumerate(maps):
            if not isinstance(map_data, dict):
                self.errors.append(f"Result {match_index}, Map {j}: Must be a dictionary")
                continue
            
            # Validate map name
            if 'map' not in map_data:
                self.errors.append(f"Result {match_index}, Map {j}: Missing map name")
            
            # Validate team data
            for team_key in ['team1', 'team2']:
                if team_key in map_data:
                    team = map_data[team_key]
                    if isinstance(team, dict):
                        if 'score' in team:
                            try:
                                int(team['score'])
                            except (ValueError, TypeError):
                                self.warnings.append(f"Result {match_index}, Map {j}: Invalid score for {team_key}: {team['score']}")
    
    def validate_file(self, filepath: str, validator_func) -> bool:
        """Validate a single JSON file."""
        if not os.path.exists(filepath):
            self.warnings.append(f"File {filepath} does not exist")
            return True  # Not an error if file doesn't exist yet
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in {filepath}: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading {filepath}: {e}")
            return False
        
        return validator_func(data)
    
    def generate_summary(self) -> str:
        """Generate validation summary."""
        summary = []
        
        if not self.errors and not self.warnings:
            summary.append("✅ All data validation checks passed!")
        else:
            if self.errors:
                summary.append(f"❌ **{len(self.errors)} Error(s) Found:**")
                for error in self.errors:
                    summary.append(f"  - {error}")
                summary.append("")
            
            if self.warnings:
                summary.append(f"⚠️ **{len(self.warnings)} Warning(s):**")
                for warning in self.warnings:
                    summary.append(f"  - {warning}")
        
        return "\n".join(summary)

def main():
    """Main validation function."""
    validator = DataValidator()
    
    logging.info("Starting data validation...")
    
    # Validate upcoming odds
    upcoming_valid = validator.validate_file('upcoming.json', validator.validate_upcoming_odds)
    
    # Validate results
    results_valid = validator.validate_file('results.json', validator.validate_results)
    
    # Generate summary
    summary = validator.generate_summary()
    
    # Write summary to file for GitHub Actions
    with open('validation_summary.txt', 'w', encoding='utf-8') as f:
        f.write(summary)
    
    # Print summary
    print(summary)
    
    # Exit with error code if validation failed
    if validator.errors:
        logging.error(f"Validation failed with {len(validator.errors)} errors")
        sys.exit(1)
    else:
        logging.info("Validation completed successfully")
        if validator.warnings:
            logging.warning(f"Validation completed with {len(validator.warnings)} warnings")

if __name__ == "__main__":
    main()