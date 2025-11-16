#!/usr/bin/env python3

"""
AI System Integration for Dynamic Database Management
Automatically updates the AI agent when database changes occur
"""

import json
import threading
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import logging

class AISystemIntegrator:
    """
    Handles real-time integration between database changes and the AI system
    """
    
    def __init__(self, dynamic_db_manager, enhanced_sql_agent):
        self.db_manager = dynamic_db_manager
        self.sql_agent = enhanced_sql_agent
        
        # Change monitoring
        self.last_check_time = datetime.now().isoformat()
        self.monitoring_active = False
        self.monitor_thread = None
        
        # AI agent update configurations
        self.keyword_mapping = self.load_keyword_mapping()
        
        self.logger = logging.getLogger(__name__)
    
    def load_keyword_mapping(self) -> Dict[str, List[str]]:
        """
        Load database keyword mapping for AI agent auto-detection
        """
        default_mapping = {
            'earthquake': ['earthquake', 'seismic', 'magnitude', 'tsunami', 'geological', 'tremor', 'quake'],
            'main': ['pcos', 'patient', 'medical', 'health', 'syndrome', 'ovarian', 'hormone', 'polycystic'],
            'sql_agent': ['agent', 'sql', 'database', 'query', 'main'],
            'analytics_data': ['analytics', 'performance', 'metrics', 'analysis'],
            'sales_reports': ['sales', 'revenue', 'profit', 'orders', 'customers', 'products'],
            'customer-info': ['customer', 'client', 'contact', 'demographics']
        }
        
        # Try to load from file, use default if not found
        config_path = Path("ai_keyword_mapping.json")
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load keyword mapping: {e}, using defaults")
        
        return default_mapping
    
    def save_keyword_mapping(self):
        """
        Save current keyword mapping to file
        """
        config_path = Path("ai_keyword_mapping.json")
        try:
            with open(config_path, 'w') as f:
                json.dump(self.keyword_mapping, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save keyword mapping: {e}")
    
    def analyze_table_content_for_keywords(self, database_name: str, table_name: str) -> List[str]:
        """
        Analyze table content to automatically generate keywords for AI detection
        """
        keywords = []
        
        try:
            # Get table schema
            tables = self.db_manager.get_tables_in_database(database_name)
            table_info = next((t for t in tables if t['name'] == table_name), None)
            
            if not table_info:
                return keywords
            
            # Extract keywords from column names
            for column in table_info['columns']:
                col_name = column['name'].lower()
                # Split on underscores and add meaningful parts
                parts = col_name.replace('_', ' ').split()
                for part in parts:
                    if len(part) > 2:  # Avoid very short words
                        keywords.append(part)
            
            # Get sample data for content analysis
            sample_result = self.db_manager.view_data(database_name, table_name, limit=10)
            if sample_result['success'] and sample_result['data']:
                # Analyze text content in sample data
                for record in sample_result['data']:
                    for key, value in record.items():
                        if isinstance(value, str) and len(value) > 2:
                            # Extract meaningful words from text fields
                            words = value.lower().replace('_', ' ').split()
                            for word in words:
                                if len(word) > 3 and word.isalpha():
                                    keywords.append(word)
            
            # Remove duplicates and common words
            common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            keywords = list(set(keywords) - common_words)
            
        except Exception as e:
            self.logger.error(f"Error analyzing content for keywords: {e}")
        
        return keywords[:10]  # Limit to top 10 keywords
    
    def update_ai_agent_database_detection(self):
        """
        Update the AI agent's auto_detect_databases method with current database info
        """
        try:
            # Get all current databases
            databases = self.db_manager.get_all_databases()
            
            # Update keyword mapping for new databases
            for db_name, db_info in databases.items():
                if db_name not in self.keyword_mapping:
                    # Auto-generate keywords for new database
                    keywords = []
                    
                    # Add database name variants
                    keywords.append(db_name)
                    keywords.extend(db_name.replace('_', ' ').split())
                    
                    # Analyze tables for content-based keywords
                    for table in db_info['tables']:
                        table_keywords = self.analyze_table_content_for_keywords(db_name, table['name'])
                        keywords.extend(table_keywords)
                    
                    # Remove duplicates
                    self.keyword_mapping[db_name] = list(set(keywords))[:10]
            
            # Remove mappings for deleted databases
            existing_dbs = set(databases.keys())
            to_remove = [db for db in self.keyword_mapping.keys() if db not in existing_dbs]
            for db in to_remove:
                del self.keyword_mapping[db]
            
            # Update the AI agent's auto_detect_databases method if it exists
            if hasattr(self.sql_agent, 'auto_detect_databases'):
                # Create new method dynamically
                def new_auto_detect_databases(question: str) -> List[str]:
                    question_lower = question.lower()
                    detected_databases = []
                    
                    # Check for keyword matches
                    for db_name, keywords in self.keyword_mapping.items():
                        if any(keyword in question_lower for keyword in keywords):
                            # Verify database exists
                            available_dbs = self.sql_agent.multi_db_manager.get_databases()
                            if db_name in available_dbs:
                                detected_databases.append(db_name)
                    
                    # If no specific database detected, return main as default
                    if not detected_databases:
                        detected_databases = ['main'] if 'main' in self.sql_agent.multi_db_manager.get_databases() else ['sql_agent']
                    
                    return detected_databases
                
                # Replace the method
                self.sql_agent.auto_detect_databases = new_auto_detect_databases
            
            # Save updated mapping
            self.save_keyword_mapping()
            
            self.logger.info(f"Updated AI agent database detection for {len(databases)} databases")
            
        except Exception as e:
            self.logger.error(f"Error updating AI agent database detection: {e}")
    
    def refresh_ai_agent_schemas(self):
        """
        Refresh all schema information in the AI agent
        """
        try:
            if hasattr(self.sql_agent, 'refresh_all_schemas'):
                self.sql_agent.refresh_all_schemas()
            
            # Update multi-database manager if available
            if hasattr(self.sql_agent, 'multi_db_manager'):
                self.sql_agent.multi_db_manager.refresh_database_info()
            
            self.logger.info("Refreshed AI agent schemas")
            
        except Exception as e:
            self.logger.error(f"Error refreshing AI agent schemas: {e}")
    
    def process_database_changes(self):
        """
        Process recent database changes and update AI system accordingly
        """
        try:
            # Get changes since last check
            changes = self.db_manager.get_change_log(since=self.last_check_time)
            
            if not changes:
                return
            
            self.logger.info(f"Processing {len(changes)} database changes")
            
            schema_update_needed = False
            detection_update_needed = False
            
            for change in changes:
                operation = change['operation']
                
                # Determine what updates are needed
                if operation in ['CREATE_DATABASE', 'DELETE_DATABASE']:
                    detection_update_needed = True
                    schema_update_needed = True
                elif operation in ['CREATE_TABLE', 'DELETE_TABLE', 'MOVE_TABLE']:
                    schema_update_needed = True
                elif operation in ['DELETE_COLUMN', 'CUSTOM_QUERY']:
                    schema_update_needed = True
            
            # Apply updates
            if detection_update_needed:
                self.update_ai_agent_database_detection()
            
            if schema_update_needed:
                self.refresh_ai_agent_schemas()
            
            # Update last check time
            self.last_check_time = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.error(f"Error processing database changes: {e}")
    
    def force_full_update(self):
        """
        Force a complete update of the AI system with current database state
        """
        self.logger.info("Forcing full AI system update...")
        
        # Refresh database info
        self.db_manager.refresh_all_database_info()
        
        # Update detection system
        self.update_ai_agent_database_detection()
        
        # Refresh schemas
        self.refresh_ai_agent_schemas()
        
        self.logger.info("Full AI system update completed")
    
    def add_custom_keywords(self, database_name: str, keywords: List[str]):
        """
        Add custom keywords for a database
        """
        if database_name not in self.keyword_mapping:
            self.keyword_mapping[database_name] = []
        
        # Add new keywords, avoiding duplicates
        current_keywords = set(self.keyword_mapping[database_name])
        new_keywords = [k for k in keywords if k not in current_keywords]
        
        self.keyword_mapping[database_name].extend(new_keywords)
        
        # Update AI agent
        self.update_ai_agent_database_detection()
        
        self.logger.info(f"Added {len(new_keywords)} keywords to database {database_name}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current status of the AI integration system
        """
        databases = self.db_manager.get_all_databases()
        recent_changes = self.db_manager.get_change_log(limit=10)
        
        return {
            'monitoring_active': self.monitoring_active,
            'last_check_time': self.last_check_time,
            'databases_count': len(databases),
            'keyword_mappings': len(self.keyword_mapping),
            'recent_changes_count': len(recent_changes),
            'databases': list(databases.keys()),
            'keyword_mapping': self.keyword_mapping
        }