#!/usr/bin/env python3
"""
Enhanced logging system for the automation framework.
"""

import logging
import json
import os
from datetime import datetime
from pathlib import Path

class AutomationLogger:
    def __init__(self, name="automation", log_level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        # Create logs directory if it doesn't exist
        Path("logs").mkdir(exist_ok=True)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(f'logs/{name}_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # Error tracking
        self.errors = []
        self.warnings = []
        self.metrics = {
            'start_time': datetime.now().isoformat(),
            'operations': [],
            'performance': {}
        }
    
    def info(self, message, operation=None):
        """Log info message and track operation."""
        self.logger.info(message)
        if operation:
            self.metrics['operations'].append({
                'timestamp': datetime.now().isoformat(),
                'operation': operation,
                'status': 'info',
                'message': message
            })
    
    def warning(self, message, operation=None):
        """Log warning message and track it."""
        self.logger.warning(message)
        self.warnings.append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'operation': operation
        })
        if operation:
            self.metrics['operations'].append({
                'timestamp': datetime.now().isoformat(),
                'operation': operation,
                'status': 'warning',
                'message': message
            })
    
    def error(self, message, operation=None, exception=None):
        """Log error message and track it."""
        if exception:
            self.logger.error(f"{message}: {exception}", exc_info=True)
        else:
            self.logger.error(message)
        
        self.errors.append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'operation': operation,
            'exception': str(exception) if exception else None
        })
        
        if operation:
            self.metrics['operations'].append({
                'timestamp': datetime.now().isoformat(),
                'operation': operation,
                'status': 'error',
                'message': message,
                'exception': str(exception) if exception else None
            })
    
    def debug(self, message):
        """Log debug message."""
        self.logger.debug(message)
    
    def track_performance(self, operation, duration_seconds, details=None):
        """Track performance metrics."""
        self.metrics['performance'][operation] = {
            'duration_seconds': duration_seconds,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        self.info(f"Performance: {operation} took {duration_seconds:.2f}s", operation)
    
    def get_summary(self):
        """Get execution summary."""
        self.metrics['end_time'] = datetime.now().isoformat()
        self.metrics['summary'] = {
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'total_operations': len(self.metrics['operations']),
            'success_rate': (
                (len(self.metrics['operations']) - len(self.errors)) / 
                max(len(self.metrics['operations']), 1) * 100
            )
        }
        return self.metrics
    
    def save_execution_log(self, filename=None):
        """Save execution log to file."""
        if not filename:
            filename = f"logs/execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        summary = self.get_summary()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.info(f"Execution log saved to {filename}")
        return filename

def get_logger(name="automation", log_level=logging.INFO):
    """Get configured logger instance."""
    return AutomationLogger(name, log_level)