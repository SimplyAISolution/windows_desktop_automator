"""
Unit tests for DSL (Domain Specific Language) components.
Tests recipe loading, validation, and schema compliance.
"""

import pytest
from pydantic import ValidationError

from automator.core.dsl import (
    Recipe, ActionStep, ActionType, Target, ElementSelector, WindowSelector,
    RecipeValidator, RecipeValidationError, load_recipe_from_dict, create_minimal_recipe
)


class TestElementSelector:
    """Test ElementSelector validation and functionality."""
    
    def test_valid_element_selector(self):
        """Test creating valid element selector."""
        selector = ElementSelector(
            automation_id="btn_submit",
            control_type="Button",
            name="Submit"
        )
        
        assert selector.automation_id == "btn_submit"
        assert selector.control_type == "Button"
        assert selector.name == "Submit"
        assert selector.index == 0  # Default value
    
    def test_element_selector_entropy_score(self):
        """Test entropy scoring for element selectors."""
        # High entropy selector (AutomationId)
        high_entropy = ElementSelector(automation_id="unique_id")
        assert high_entropy.get_selector_entropy_score() == 10
        
        # Medium entropy selector (ControlType + Name)
        medium_entropy = ElementSelector(
            control_type="Button",
            name="Submit",
            class_name="btn-class"
        )
        assert medium_entropy.get_selector_entropy_score() == 10  # 5+2+3
        
        # Low entropy selector (Name only)
        low_entropy = ElementSelector(name="Submit")
        assert low_entropy.get_selector_entropy_score() == 2
        
        # No selectors
        empty_selector = ElementSelector()
        assert empty_selector.get_selector_entropy_score() == 0
    
    def test_has_selectors(self):
        """Test selector existence check."""
        with_selector = ElementSelector(name="Test")
        assert with_selector.has_selectors() is True
        
        empty_selector = ElementSelector()
        assert empty_selector.has_selectors() is False


class TestWindowSelector:
    """Test WindowSelector validation."""
    
    def test_valid_window_selector(self):
        """Test creating valid window selector."""
        selector = WindowSelector(
            name="Calculator",
            class_name="ApplicationFrameWindow"
        )
        
        assert selector.name == "Calculator"
        assert selector.class_name == "ApplicationFrameWindow"
    
    def test_window_name_validation(self):
        """Test window name validation."""
        # Valid name
        valid_selector = WindowSelector(name="Valid Window Name")
        assert valid_selector.name == "Valid Window Name"
        
        # Invalid name (too short)
        with pytest.raises(ValidationError):
            WindowSelector(name="A")


class TestTarget:
    """Test Target validation and functionality."""
    
    def test_valid_target(self):
        """Test creating valid target."""
        target = Target(
            app="notepad.exe",
            window=WindowSelector(name="Notepad"),
            element=ElementSelector(control_type="Edit"),
            text="Hello World"
        )
        
        assert target.app == "notepad.exe"
        assert target.text == "Hello World"
        assert target.window is not None
        assert target.element is not None
    
    def test_file_path_validation(self):
        """Test file path validation."""
        valid_target = Target(file_path="C:\\temp\\test.txt")
        assert valid_target.file_path == "C:\\temp\\test.txt"
        
        # Invalid file path type
        with pytest.raises(ValidationError):
            Target(file_path=123)
    
    def test_region_validation(self):
        """Test screen region validation."""
        # Valid region
        valid_target = Target(region={"x": 100, "y": 200, "width": 300, "height": 400})
        assert valid_target.region == {"x": 100, "y": 200, "width": 300, "height": 400}
        
        # Invalid region (missing keys)
        with pytest.raises(ValidationError):
            Target(region={"x": 100, "y": 200})
        
        # Invalid region (negative values)
        with pytest.raises(ValidationError):
            Target(region={"x": -10, "y": 20, "width": 100, "height": 200})


class TestActionStep:
    """Test ActionStep validation."""
    
    def test_valid_action_step(self):
        """Test creating valid action step."""
        step = ActionStep(
            name="Click Submit Button",
            action=ActionType.CLICK,
            target=Target(
                element=ElementSelector(automation_id="btn_submit")
            ),
            timeout=10,
            retry_attempts=3
        )
        
        assert step.name == "Click Submit Button"
        assert step.action == ActionType.CLICK
        assert step.timeout == 10
        assert step.retry_attempts == 3
        assert step.verify_after is True  # Default value
    
    def test_timeout_validation(self):
        """Test timeout validation."""
        # Valid timeout
        step = ActionStep(
            name="Test",
            action=ActionType.CLICK,
            target=Target(),
            timeout=30
        )
        assert step.timeout == 30
        
        # Invalid timeout (too low)
        with pytest.raises(ValidationError):
            ActionStep(
                name="Test",
                action=ActionType.CLICK,
                target=Target(),
                timeout=0
            )
        
        # Invalid timeout (too high)
        with pytest.raises(ValidationError):
            ActionStep(
                name="Test",
                action=ActionType.CLICK,
                target=Target(),
                timeout=500
            )
    
    def test_retry_attempts_validation(self):
        """Test retry attempts validation."""
        # Valid retry attempts
        step = ActionStep(
            name="Test",
            action=ActionType.CLICK,
            target=Target(),
            retry_attempts=5
        )
        assert step.retry_attempts == 5
        
        # Invalid retry attempts (too low)
        with pytest.raises(ValidationError):
            ActionStep(
                name="Test",
                action=ActionType.CLICK,
                target=Target(),
                retry_attempts=0
            )
        
        # Invalid retry attempts (too high)
        with pytest.raises(ValidationError):
            ActionStep(
                name="Test",
                action=ActionType.CLICK,
                target=Target(),
                retry_attempts=20
            )


class TestRecipe:
    """Test Recipe validation and functionality."""
    
    def test_valid_recipe(self):
        """Test creating valid recipe."""
        recipe = Recipe(
            name="test_recipe",
            description="A test recipe",
            steps=[
                ActionStep(
                    name="Test step",
                    action=ActionType.CLICK,
                    target=Target()
                )
            ]
        )
        
        assert recipe.name == "test_recipe"
        assert recipe.description == "A test recipe"
        assert recipe.version == "1.0"  # Default value
        assert len(recipe.steps) == 1
    
    def test_recipe_name_validation(self):
        """Test recipe name validation."""
        # Valid names
        valid_names = ["test_recipe", "MyRecipe-123", "recipe1"]
        for name in valid_names:
            recipe = Recipe(
                name=name,
                description="Test",
                steps=[ActionStep(name="Test", action=ActionType.CLICK, target=Target())]
            )
            assert recipe.name == name
        
        # Invalid names
        invalid_names = ["123recipe", "recipe with spaces", "recipe@special"]
        for name in invalid_names:
            with pytest.raises(ValidationError):
                Recipe(
                    name=name,
                    description="Test",
                    steps=[ActionStep(name="Test", action=ActionType.CLICK, target=Target())]
                )
    
    def test_steps_validation(self):
        """Test steps validation."""
        # Valid recipe with steps
        recipe = Recipe(
            name="test",
            description="Test",
            steps=[
                ActionStep(name="Step1", action=ActionType.CLICK, target=Target()),
                ActionStep(name="Step2", action=ActionType.TYPE, target=Target())
            ]
        )
        assert len(recipe.steps) == 2
        
        # Invalid recipe (no steps)
        with pytest.raises(ValidationError):
            Recipe(name="test", description="Test", steps=[])
        
        # Invalid recipe (too many steps)
        too_many_steps = [
            ActionStep(name=f"Step{i}", action=ActionType.CLICK, target=Target())
            for i in range(101)
        ]
        with pytest.raises(ValidationError):
            Recipe(name="test", description="Test", steps=too_many_steps)
    
    def test_get_variable(self):
        """Test variable retrieval."""
        recipe = Recipe(
            name="test",
            description="Test",
            steps=[ActionStep(name="Test", action=ActionType.CLICK, target=Target())],
            variables={"var1": "value1", "var2": 42}
        )
        
        assert recipe.get_variable("var1") == "value1"
        assert recipe.get_variable("var2") == 42
        assert recipe.get_variable("nonexistent") is None
        assert recipe.get_variable("nonexistent", "default") == "default"
    
    def test_substitute_variables(self):
        """Test variable substitution."""
        recipe = Recipe(
            name="test",
            description="Test",
            steps=[ActionStep(name="Test", action=ActionType.CLICK, target=Target())],
            variables={"name": "World", "count": "5"}
        )
        
        # Test substitution
        result = recipe.substitute_variables("Hello ${name}!")
        assert result == "Hello World!"
        
        # Test multiple substitutions
        result = recipe.substitute_variables("${name} has ${count} items")
        assert result == "World has 5 items"
        
        # Test missing variable (should remain unchanged)
        result = recipe.substitute_variables("Hello ${missing}!")
        assert result == "Hello ${missing}!"
        
        # Test non-string input
        result = recipe.substitute_variables(123)
        assert result == 123


class TestRecipeValidator:
    """Test RecipeValidator functionality."""
    
    def test_validate_recipe_warnings(self):
        """Test recipe validation warnings."""
        # Recipe with issues
        recipe = Recipe(
            name="test",
            description="Test recipe with issues",
            steps=[
                ActionStep(
                    name="Long timeout step",
                    action=ActionType.WAIT_FOR,
                    target=Target(element=ElementSelector(name="weak_selector")),
                    timeout=120  # Long timeout
                ),
                ActionStep(
                    name="Duplicate name",
                    action=ActionType.CLICK,
                    target=Target(),
                    verify_after=False  # No verification
                ),
                ActionStep(
                    name="Duplicate name",  # Duplicate name
                    action=ActionType.TYPE,
                    target=Target()
                )
            ]
        )
        
        warnings = RecipeValidator.validate_recipe(recipe)
        
        # Should have warnings about duplicates, long timeouts, weak selectors, and no verify
        assert len(warnings) > 0
        
        # Check specific warning types
        warning_text = " ".join(warnings)
        assert "Duplicate step names" in warning_text
        assert "long timeouts" in warning_text
        assert "weak selectors" in warning_text
        assert "without verification" in warning_text
    
    def test_validate_selector_fallbacks(self):
        """Test selector fallback generation."""
        # Primary selector with fallback options
        primary_selector = ElementSelector(
            automation_id="primary_id",
            control_type="Button",
            class_name="btn-class",
            name="Submit"
        )
        
        fallbacks = RecipeValidator.validate_selector_fallbacks(primary_selector)
        
        # Should generate fallback selectors
        assert len(fallbacks) >= 2
        
        # First fallback should be ControlType + Name
        first_fallback = fallbacks[0]
        assert first_fallback.control_type == "Button"
        assert first_fallback.name == "Submit"
        assert first_fallback.automation_id is None
        
        # Second fallback should be ClassName + Name
        second_fallback = fallbacks[1]
        assert second_fallback.class_name == "btn-class"
        assert second_fallback.name == "Submit"
        assert second_fallback.automation_id is None


class TestRecipeLoading:
    """Test recipe loading functions."""
    
    def test_load_recipe_from_dict(self):
        """Test loading recipe from dictionary."""
        recipe_data = {
            "name": "test_recipe",
            "description": "Test recipe",
            "steps": [
                {
                    "name": "Test step",
                    "action": "click",
                    "target": {
                        "element": {
                            "automation_id": "btn_test"
                        }
                    }
                }
            ]
        }
        
        recipe = load_recipe_from_dict(recipe_data)
        
        assert recipe.name == "test_recipe"
        assert recipe.description == "Test recipe"
        assert len(recipe.steps) == 1
        assert recipe.steps[0].action == ActionType.CLICK
        assert recipe.steps[0].target.element.automation_id == "btn_test"
    
    def test_load_invalid_recipe(self):
        """Test loading invalid recipe."""
        invalid_data = {
            "name": "123invalid",  # Invalid name
            "description": "Test",
            "steps": []  # No steps
        }
        
        with pytest.raises(RecipeValidationError):
            load_recipe_from_dict(invalid_data)
    
    def test_create_minimal_recipe(self):
        """Test creating minimal recipe."""
        steps_data = [
            {
                "name": "Click button",
                "action": "click",
                "target": {
                    "element": {"automation_id": "btn1"}
                }
            },
            {
                "action": "type",  # No name provided
                "target": {
                    "text": "Hello"
                }
            }
        ]
        
        recipe = create_minimal_recipe("minimal_test", steps_data)
        
        assert recipe.name == "minimal_test"
        assert len(recipe.steps) == 2
        assert recipe.steps[0].name == "Click button"
        assert recipe.steps[1].name == "Step 2"  # Auto-generated name
        assert recipe.steps[0].action == ActionType.CLICK
        assert recipe.steps[1].action == ActionType.TYPE


if __name__ == "__main__":
    pytest.main([__file__])
