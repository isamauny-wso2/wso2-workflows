#!/usr/bin/env python3
"""
Generic property validation script for extracted API properties.
Reads properties from a JSON file (GitHub Actions step output) and validates against configurable rules.
Returns appropriate exit codes for GitHub Actions workflow control.
"""

import yaml
import sys
import json
import argparse
from typing import Dict, Any


class PropertyValidator:
    def __init__(self, config_file: str = "property-validation-config.yaml"):
        self.config = self._load_config(config_file)
        self.validation_rules = self.config.get("validation_rules", {})
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load validation configuration from YAML file."""
        try:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"::error::Configuration file '{config_file}' not found")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"::error::Invalid YAML in configuration file: {e}")
            sys.exit(1)
    
    def load_properties_from_json(self, json_file: str) -> Dict[str, str]:
        """Load properties from JSON file."""
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                # Handle different JSON structures
                if isinstance(data, dict):
                    return data
                return {}
        except FileNotFoundError:
            print(f"::error::Properties file '{json_file}' not found")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"::error::Invalid JSON in properties file: {e}")
            sys.exit(1)
    
    def validate_property(self, property_name: str, property_value: str) -> Dict[str, Any]:
        """Validate a single property against the rules."""
        if property_name not in self.validation_rules:
            return {
                "valid": False,
                "error": f"Property '{property_name}' is not defined in validation rules"
            }
        
        rule = self.validation_rules[property_name]
        valid_values = rule.get("valid_values", [])
        
        if property_value not in valid_values:
            return {
                "valid": False,
                "error": f"Property '{property_name}' has invalid value '{property_value}'. Valid values are: {valid_values}"
            }
        
        return {"valid": True}
    
    def validate_all_properties(self, properties: Dict[str, str]) -> Dict[str, Any]:
        """Validate all properties and return validation results."""
        results = {
            "overall_valid": True,
            "property_results": {},
            "missing_required": [],
            "errors": [],
            "unknown_properties": []
        }
        
        # Check for missing required properties
        for property_name, rule in self.validation_rules.items():
            if rule.get("required", False) and property_name not in properties:
                results["missing_required"].append(property_name)
                results["overall_valid"] = False
        
        # Validate provided properties
        for property_name, property_value in properties.items():
            if property_name not in self.validation_rules:
                results["unknown_properties"].append(property_name)
                continue
                
            validation_result = self.validate_property(property_name, property_value)
            results["property_results"][property_name] = validation_result
            
            if not validation_result["valid"]:
                results["overall_valid"] = False
                results["errors"].append(validation_result["error"])
        
        return results
    
    def print_github_actions_output(self, results: Dict[str, Any], properties: Dict[str, str]):
        """Print GitHub Actions formatted output with appropriate annotations."""
        
        # Print GitHub Actions group for better organization
        print("::group::Property Validation Report")
        
        if results["overall_valid"]:
            print("✅ VALIDATION PASSED")
        else:
            print("❌ VALIDATION FAILED")
        
        print(f"\nExtracted Properties ({len(properties)}):")
        for prop_name, prop_value in properties.items():
            print(f"   {prop_name}: {prop_value}")
        
        # Print validation results
        if results["property_results"]:
            print(f"\nProperty Validation Results:")
            for prop_name, result in results["property_results"].items():
                status = "✅" if result["valid"] else "❌"
                prop_value = properties.get(prop_name, "N/A")
                print(f"   {status} {prop_name}: {prop_value}")
        
        # Print unknown properties as warnings
        if results["unknown_properties"]:
            for prop in results["unknown_properties"]:
                print(f"::warning::Unknown property '{prop}' with value '{properties[prop]}' (not in validation rules)")
        
        # Print missing required properties as errors
        for prop in results["missing_required"]:
            valid_values = self.validation_rules[prop].get("valid_values", [])
            print(f"::error::Missing required property '{prop}'. Valid values are: {valid_values}")
        
        # Print validation errors
        for error in results["errors"]:
            print(f"::error::{error}")
        
        print("::endgroup::")
        
        # Summary for GitHub Actions
        if results["overall_valid"]:
            print("::notice::Property validation completed successfully")
        else:
            error_count = len(results["errors"]) + len(results["missing_required"])
            print(f"::error::Property validation failed with {error_count} error(s)")


def main():
    parser = argparse.ArgumentParser(description="Validate API properties against configured rules")
    parser.add_argument("--config", default="property-validation-config.yaml", 
                       help="Path to validation configuration file")
    parser.add_argument("--properties-file", required=True,
                       help="JSON file containing extracted properties")
    
    args = parser.parse_args()
    
    validator = PropertyValidator(args.config)
    
    # Load properties from JSON file
    properties = validator.load_properties_from_json(args.properties_file)
    
    if not properties:
        print("::warning::No properties found in input file")
    
    # Validate properties
    results = validator.validate_all_properties(properties)
    
    # Print GitHub Actions formatted output
    validator.print_github_actions_output(results, properties)
    
    # Exit with appropriate code for GitHub Actions
    # Exit code 0 = success, Exit code 1 = failure
    exit_code = 0 if results["overall_valid"] else 1
    print(f"::debug::Exiting with code {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()