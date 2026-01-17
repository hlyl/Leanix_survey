"""
Validation utilities for LeanIX survey JSON files.
"""

import json
import sys
from pathlib import Path

from pydantic import ValidationError

from src.leanix_survey_models import SurveyInput


def validate_survey_json(json_path: Path) -> tuple[bool, SurveyInput | None, str]:
    """
    Validate a survey JSON file against the schema.

    Args:
        json_path: Path to the JSON file

    Returns:
        Tuple of (is_valid, survey_input, error_message)
    """
    try:
        # Read JSON file
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        # Validate against schema
        survey_input = SurveyInput.model_validate(data)

        return True, survey_input, ""

    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON: {str(e)}"

    except ValidationError as e:
        error_msg = "Validation errors:\n"
        for error in e.errors():
            location = " -> ".join(str(loc) for loc in error["loc"])
            error_msg += f"  • {location}: {error['msg']}\n"
        return False, None, error_msg

    except Exception as e:
        return False, None, f"Unexpected error: {str(e)}"


def validate_json_string(json_string: str) -> tuple[bool, SurveyInput | None, str]:
    """
    Validate a survey JSON string against the schema.

    Args:
        json_string: JSON string to validate

    Returns:
        Tuple of (is_valid, survey_input, error_message)
    """
    try:
        data = json.loads(json_string)
        survey_input = SurveyInput.model_validate(data)
        return True, survey_input, ""

    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON: {str(e)}"

    except ValidationError as e:
        error_msg = "Validation errors:\n"
        for error in e.errors():
            location = " -> ".join(str(loc) for loc in error["loc"])
            error_msg += f"  • {location}: {error['msg']}\n"
        return False, None, error_msg

    except Exception as e:
        return False, None, f"Unexpected error: {str(e)}"


def main() -> None:
    """CLI for validating survey JSON files"""
    if len(sys.argv) < 2:
        print("Usage: python validate_survey.py <json_file>")
        sys.exit(1)

    json_path = Path(sys.argv[1])

    if not json_path.exists():
        print(f"Error: File not found: {json_path}")
        sys.exit(1)

    print(f"Validating: {json_path}")
    print("=" * 60)

    is_valid, survey_input, error_msg = validate_survey_json(json_path)

    if is_valid:
        print("✓ Validation successful!")
        print(f"\nSurvey title: {survey_input.title}")
        print(f"Number of questions: {len(survey_input.questionnaire.questions)}")

        if survey_input.user_query:
            print(f"User query roles: {len(survey_input.user_query.roles)}")

        if survey_input.fact_sheet_query:
            print("Fact sheet query: Present")

        # Count question types
        question_types = {}
        for q in survey_input.questionnaire.questions:
            question_types[q.type] = question_types.get(q.type, 0) + 1

        print("\nQuestion types:")
        for qtype, count in sorted(question_types.items()):
            print(f"  • {qtype}: {count}")

    else:
        print("✗ Validation failed!")
        print(f"\n{error_msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
