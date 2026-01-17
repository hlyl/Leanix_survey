"""
Generate JSON Schema from Pydantic models for use in documentation and external tools.
"""

import json
from pathlib import Path

from src.leanix_survey_models import SurveyInput


def generate_json_schema():
    """Generate and save JSON Schema for SurveyInput model"""
    schema = SurveyInput.model_json_schema()

    # Add additional metadata
    schema["$schema"] = "http://json-schema.org/draft-07/schema#"
    schema["$id"] = "https://leanix.com/schemas/survey-input-v1.json"

    # Save to file
    output_path = Path(__file__).parent / "survey_input_schema.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)

    print(f"JSON Schema saved to: {output_path}")
    print(f"Schema size: {len(json.dumps(schema))} bytes")

    return schema


if __name__ == "__main__":
    schema = generate_json_schema()
    print("\nSchema generated successfully!")
    print(f"Title: {schema.get('title', 'N/A')}")
    print(f"Required fields: {schema.get('required', [])}")
