#!/usr/bin/env python3
"""
Simple recipe validator that doesn't require external dependencies.
Tests recipe YAML structure and basic validation.
"""

import yaml
import sys
import os

def validate_recipe_structure(recipe_path):
    """Validate recipe structure without importing full automation stack."""
    
    print(f"🔍 Validating recipe: {recipe_path}")
    
    try:
        with open(recipe_path, 'r', encoding='utf-8') as f:
            recipe_data = yaml.safe_load(f)
        
        # Basic structure validation
        required_fields = ['name', 'description', 'steps']
        for field in required_fields:
            if field not in recipe_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate steps
        steps = recipe_data['steps']
        if not isinstance(steps, list) or len(steps) == 0:
            raise ValueError("Recipe must have at least one step")
        
        print(f"✅ Recipe structure is valid!")
        print(f"   Name: {recipe_data['name']}")
        print(f"   Description: {recipe_data['description']}")
        print(f"   Steps: {len(steps)}")
        
        # Validate each step has required fields
        for i, step in enumerate(steps, 1):
            step_required = ['name', 'action', 'target']
            for field in step_required:
                if field not in step:
                    print(f"   ⚠️  Step {i} missing field: {field}")
                else:
                    print(f"   ✅ Step {i}: {step['name']} ({step['action']})")
        
        # Check for variables
        if 'variables' in recipe_data:
            vars_count = len(recipe_data['variables'])
            print(f"   Variables: {vars_count}")
            for var_name, var_value in recipe_data['variables'].items():
                print(f"     - {var_name}: {var_value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Recipe validation failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_recipe.py <recipe_path>")
        sys.exit(1)
    
    recipe_path = sys.argv[1]
    if not os.path.exists(recipe_path):
        print(f"❌ Recipe file not found: {recipe_path}")
        sys.exit(1)
    
    success = validate_recipe_structure(recipe_path)
    sys.exit(0 if success else 1)