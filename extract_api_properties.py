#!/usr/bin/env python3
"""
Extract properties from WSO2 APIM api.yaml file.
Specifically extracts additionalProperties array and outputs them in multiple formats.
"""

import yaml
import json
import argparse
import sys
import os
from pathlib import Path


def extract_properties_from_yaml(yaml_file_path):
    """
    Extract properties from api.yaml file.
    
    Args:
        yaml_file_path (str): Path to the api.yaml file
        
    Returns:
        dict: Dictionary of extracted properties
    """
    try:
        with open(yaml_file_path, 'r') as file:
            data = yaml.safe_load(file)
        
        properties = {}
        
        # Extract from additionalProperties array
        if 'data' in data and 'additionalProperties' in data['data']:
            for prop in data['data']['additionalProperties']:
                if 'name' in prop and 'value' in prop:
                    properties[prop['name']] = prop['value']
        
        return properties
        
    except FileNotFoundError:
        print(f"Error: File not found: {yaml_file_path}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def output_properties(properties, output_format, output_file=None):
    """
    Output properties in the specified format.
    
    Args:
        properties (dict): Dictionary of properties to output
        output_format (str): Format to output ('json', 'env', 'yaml', 'console')
        output_file (str): Optional output file path
    """
    output_content = ""
    
    if output_format == 'json':
        output_content = json.dumps(properties, indent=2)
    elif output_format == 'env':
        output_content = '\n'.join([f"{k.upper()}={v}" for k, v in properties.items()])
    elif output_format == 'yaml':
        output_content = yaml.dump(properties, default_flow_style=False)
    elif output_format == 'github':
        # Special format for GitHub Actions outputs (lowercase keys)
        output_content = '\n'.join([f"{k.lower()}={v}" for k, v in properties.items()])
    elif output_format == 'console':
        output_content = '\n'.join([f"{k}: {v}" for k, v in properties.items()])
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(output_content)
        print(f"Properties written to: {output_file}")
    else:
        print(output_content)


def main():
    parser = argparse.ArgumentParser(description='Extract properties from WSO2 APIM api.yaml file')
    parser.add_argument('yaml_file', help='Path to the api.yaml file')
    parser.add_argument('--format', '-f', 
                        choices=['json', 'env', 'yaml', 'github', 'console'], 
                        default='console',
                        help='Output format (default: console)')
    parser.add_argument('--output', '-o', help='Output file path (default: stdout)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        print(f"Extracting properties from: {args.yaml_file}", file=sys.stderr)
    
    # Extract properties
    properties = extract_properties_from_yaml(args.yaml_file)
    
    if not properties:
        print("No properties found in additionalProperties section", file=sys.stderr)
        sys.exit(0)
    
    if args.verbose:
        print(f"Found {len(properties)} properties", file=sys.stderr)
    
    # Output properties
    output_properties(properties, args.format, args.output)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())