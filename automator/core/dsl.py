"""
DSL (Domain Specific Language) for automation recipes.
Defines Pydantic models for recipe structure, validation, and execution.
"""

import re
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class SelectorType(str, Enum):
    """Types of UI element selectors."""
    AUTOMATION_ID = "automationId"
    CONTROL_TYPE = "controlType"
    CLASS_NAME = "className"
    NAME = "name"
    VALUE = "value"
    HELP_TEXT = "helpText"
    ACCESSIBLE_NAME = "accessibleName"


class ActionType(str, Enum):
    """Types of automation actions."""
    LAUNCH = "launch"
    WAIT_FOR = "wait_for"
    CLICK = "click"
    TYPE = "type"
    HOTKEY = "hotkey"
    VERIFY = "verify"
    READ_TEXT = "read_text"
    FILE_WRITE = "file_write"
    FILE_READ = "file_read"
    FILE_COPY = "file_copy"
    SCREENSHOT = "screenshot"
    OCR_TEXT = "ocr_text"


class WindowSelector(BaseModel):
    """Selector for targeting application windows."""
    name: Optional[str] = Field(None, description="Window title or partial title")
    class_name: Optional[str] = Field(None, description="Window class name")
    process_id: Optional[int] = Field(None, description="Process ID")
    
    @validator('name')
    def validate_name(cls, v):
        if v and len(v) < 2:
            raise ValueError("Window name must be at least 2 characters long")
        return v


class ElementSelector(BaseModel):
    """Selector for targeting UI elements within windows."""
    automation_id: Optional[str] = Field(None, description="UIA AutomationId property")
    control_type: Optional[str] = Field(None, description="UIA ControlType")
    class_name: Optional[str] = Field(None, description="Element class name")
    name: Optional[str] = Field(None, description="Element name/title")
    value: Optional[str] = Field(None, description="Element value")
    help_text: Optional[str] = Field(None, description="Element help text")
    accessible_name: Optional[str] = Field(None, description="Accessible name")
    index: Optional[int] = Field(0, description="Element index when multiple matches")
    
    def get_selector_entropy_score(self) -> int:
        """Calculate selector entropy score - higher is more specific."""
        score = 0
        # AutomationId is most specific
        if self.automation_id:
            score += 10
        # ControlType + other attributes are moderately specific
        if self.control_type:
            score += 5
        if self.class_name:
            score += 3
        if self.name:
            score += 2
        if self.value:
            score += 2
        if self.help_text:
            score += 1
        if self.accessible_name:
            score += 1
        return score
    
    def has_selectors(self) -> bool:
        """Check if any selectors are defined."""
        return any([
            self.automation_id, self.control_type, self.class_name,
            self.name, self.value, self.help_text, self.accessible_name
        ])


class Target(BaseModel):
    """Target specification for automation actions."""
    app: Optional[str] = Field(None, description="Application executable name")
    window: Optional[WindowSelector] = Field(None, description="Window selector")
    element: Optional[ElementSelector] = Field(None, description="Element selector")
    file_path: Optional[str] = Field(None, description="File path for file operations")
    text: Optional[str] = Field(None, description="Text content for operations")
    region: Optional[Dict[str, int]] = Field(None, description="Screen region (x, y, width, height)")
    
    @validator('file_path')
    def validate_file_path(cls, v):
        if v and not isinstance(v, str):
            raise ValueError("File path must be a string")
        return v
    
    @validator('region')
    def validate_region(cls, v):
        if v:
            required_keys = {'x', 'y', 'width', 'height'}
            if not all(k in v for k in required_keys):
                raise ValueError(f"Region must contain keys: {required_keys}")
            if not all(isinstance(v[k], int) and v[k] >= 0 for k in required_keys):
                raise ValueError("Region values must be non-negative integers")
        return v


class ActionStep(BaseModel):
    """Individual automation step within a recipe."""
    name: str = Field(..., description="Human-readable step name")
    action: ActionType = Field(..., description="Action to perform")
    target: Target = Field(..., description="Target for the action")
    timeout: int = Field(10, description="Timeout in seconds")
    retry_attempts: int = Field(3, description="Number of retry attempts")
    retry_delay: float = Field(1.0, description="Delay between retries in seconds")
    verify_after: bool = Field(True, description="Whether to verify action success")
    continue_on_failure: bool = Field(False, description="Continue recipe if step fails")
    
    @validator('timeout')
    def validate_timeout(cls, v):
        if v < 1 or v > 300:
            raise ValueError("Timeout must be between 1 and 300 seconds")
        return v
    
    @validator('retry_attempts')
    def validate_retry_attempts(cls, v):
        if v < 1 or v > 10:
            raise ValueError("Retry attempts must be between 1 and 10")
        return v


class Recipe(BaseModel):
    """Complete automation recipe specification."""
    name: str = Field(..., description="Recipe name")
    description: str = Field(..., description="Recipe description")
    version: str = Field("1.0", description="Recipe version")
    author: Optional[str] = Field(None, description="Recipe author")
    tags: List[str] = Field(default_factory=list, description="Recipe tags")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Recipe variables")
    steps: List[ActionStep] = Field(..., description="Automation steps")
    
    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', v):
            raise ValueError("Recipe name must start with letter and contain only letters, numbers, underscores, and hyphens")
        return v
    
    @validator('steps')
    def validate_steps(cls, v):
        if not v:
            raise ValueError("Recipe must contain at least one step")
        if len(v) > 100:
            raise ValueError("Recipe cannot contain more than 100 steps")
        return v
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get recipe variable value."""
        return self.variables.get(key, default)
    
    def substitute_variables(self, text: str) -> str:
        """Substitute variables in text using ${variable} syntax."""
        if not isinstance(text, str):
            return text
        
        def replace_var(match):
            var_name = match.group(1)
            return str(self.variables.get(var_name, match.group(0)))
        
        return re.sub(r'\$\{([^}]+)\}', replace_var, text)


class RecipeValidationError(Exception):
    """Exception raised when recipe validation fails."""
    pass


class RecipeValidator:
    """Validator for automation recipes with advanced checks."""
    
    @staticmethod
    def validate_recipe(recipe: Recipe) -> List[str]:
        """Validate recipe and return list of warnings/issues."""
        warnings = []
        
        # Check for duplicate step names
        step_names = [step.name for step in recipe.steps]
        duplicates = [name for name in set(step_names) if step_names.count(name) > 1]
        if duplicates:
            warnings.append(f"Duplicate step names found: {duplicates}")
        
        # Check for unrealistic timeouts
        long_timeouts = [step.name for step in recipe.steps if step.timeout > 60]
        if long_timeouts:
            warnings.append(f"Steps with long timeouts (>60s): {long_timeouts}")
        
        # Check for selector quality
        weak_selectors = []
        for step in recipe.steps:
            if step.target.element and step.target.element.has_selectors():
                score = step.target.element.get_selector_entropy_score()
                if score < 5:  # Low entropy threshold
                    weak_selectors.append(step.name)
        
        if weak_selectors:
            warnings.append(f"Steps with weak selectors (consider using AutomationId): {weak_selectors}")
        
        # Check for missing verification
        no_verify = [step.name for step in recipe.steps if not step.verify_after and step.action in [ActionType.CLICK, ActionType.TYPE]]
        if no_verify:
            warnings.append(f"Steps without verification: {no_verify}")
        
        return warnings
    
    @staticmethod
    def validate_selector_fallbacks(element: ElementSelector) -> List[ElementSelector]:
        """Generate fallback selectors for self-healing automation."""
        fallbacks = []
        
        if element.automation_id:
            # Fallback 1: ControlType + Name
            if element.control_type and element.name:
                fallbacks.append(ElementSelector(
                    control_type=element.control_type,
                    name=element.name,
                    index=element.index
                ))
            
            # Fallback 2: ClassName + Name
            if element.class_name and element.name:
                fallbacks.append(ElementSelector(
                    class_name=element.class_name,
                    name=element.name,
                    index=element.index
                ))
        
        return fallbacks


def load_recipe_from_dict(data: Dict[str, Any]) -> Recipe:
    """Load recipe from dictionary with validation."""
    try:
        recipe = Recipe(**data)
        warnings = RecipeValidator.validate_recipe(recipe)
        if warnings:
            # Log warnings but don't fail validation
            print(f"Recipe validation warnings: {warnings}")
        return recipe
    except Exception as e:
        raise RecipeValidationError(f"Invalid recipe format: {e}")


def create_minimal_recipe(name: str, steps: List[Dict[str, Any]]) -> Recipe:
    """Create a minimal recipe from basic step definitions."""
    recipe_steps = []
    for step_data in steps:
        step = ActionStep(
            name=step_data.get('name', f"Step {len(recipe_steps) + 1}"),
            action=ActionType(step_data['action']),
            target=Target(**step_data['target'])
        )
        recipe_steps.append(step)
    
    return Recipe(
        name=name,
        description=f"Auto-generated recipe: {name}",
        steps=recipe_steps
    )
