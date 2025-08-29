# utils.py
import json
import yaml
from pathlib import Path
from typing import Dict, Any

def create_sample_config(config_path: str = "config.yaml"):
    """Create a sample configuration file"""
    sample_config = {
        'target_directory': "~/Downloads",
        'log_file': "logs/organizer.log",
        'dry_run': False,
        'rules': [
            {
                'name': "Organize by file type",
                'conditions': [
                    {
                        'extension': [".pdf", ".doc", ".docx", ".txt"],
                        'destination': "Documents/{extension_group}",
                        'subfolder_pattern': None
                    }
                ]
            }
        ],
        'date_groups': {
            'last_week': 7,
            'last_month': 30,
            'older': 365
        },
        'conflict_resolution': "rename"
    }
    
    config_dir = Path(config_path).parent
    config_dir.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        yaml.dump(sample_config, f, default_flow_style=False, sort_keys=False)
    
    print(f"Sample config created at {config_path}")

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration structure"""
    required_keys = ['target_directory', 'rules']
    
    for key in required_keys:
        if key not in config:
            print(f"Missing required config key: {key}")
            return False
    
    # Validate rules structure
    for rule in config.get('rules', []):
        if 'conditions' not in rule:
            print("Rule missing 'conditions' key")
            return False
        
        for condition in rule['conditions']:
            if 'destination' not in condition:
                print("Condition missing 'destination' key")
                return False
    
    return True

if __name__ == "__main__":
    create_sample_config()