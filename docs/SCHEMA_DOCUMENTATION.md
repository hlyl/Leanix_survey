# LeanIX Survey JSON Schema Documentation

## Overview

This document provides detailed information about the JSON schema for creating LeanIX surveys programmatically.

## Schema Structure

### Root Object: `SurveyInput`

The root object that defines a complete survey.

**Required Fields:**
- `title` (string): Survey title
- `questionnaire` (Questionnaire): Survey questions

**Optional Fields:**
- `introductionText` (string): Introduction text shown to recipients
- `introductionSubject` (string): Email subject line
- `sendChangeNotifications` (boolean): Enable change notifications
- `allowedPermissionStatus` (enum): Who can participate
- `userQuery` (UserQuery): Define recipients by role
- `factSheetQuery` (FactSheetQuery): Define target fact sheets

### Questionnaire

Container for survey questions.

```json
{
  "questions": [Question]
}
```

### Question

Individual survey question with support for various types and conditional logic.

**Required Fields:**
- `id` (string): Unique identifier
- `label` (string): Question text
- `type` (string): Question type

**Question Types:**
- `text`: Single-line text input
- `textarea`: Multi-line text input
- `singlechoice`: Single selection from options
- `multiplechoice`: Multiple selections from options
- `number`: Numeric input
- `date`: Date picker
- `factsheet`: Fact sheet field mapping

**Optional Fields:**
- `descriptiveText` (string): Help text
- `options` (QuestionOption[]): For choice questions
- `children` (Question[]): Nested questions
- `settings` (QuestionSettings): Advanced configuration
- `factSheetElement` (FactSheetElement): Field mapping

### Question Options

For choice-based questions (singlechoice, multiplechoice):

```json
{
  "id": "option_id",
  "label": "Option Label",
  "comment": "Optional help text"
}
```

### Question Settings

Advanced question configuration:

```json
{
  "isMandatory": true,
  "isConditional": true,
  "hideInResults": false,
  "dependency": {
    "parentId": "parent_question_id",
    "condition": {
      "parent_option_id": true
    }
  }
}
```

### User Query

Select survey recipients based on roles:

```json
{
  "roles": [
    {
      "subscriptionType": "RESPONSIBLE"
    },
    {
      "subscriptionType": "ACCOUNTABLE"
    }
  ]
}
```

**Subscription Types:**
- `RESPONSIBLE`: Users responsible for fact sheets
- `ACCOUNTABLE`: Users accountable for fact sheets
- `OBSERVER`: Users observing fact sheets
- `ALL`: All subscribed users

### Fact Sheet Query

Select target fact sheets using filters:

```json
{
  "filter": {
    "fsType": "Application",
    "facetFilter": [
      {
        "facetKey": "lifecycle",
        "keys": ["active"],
        "operator": "OR"
      }
    ]
  }
}
```

Or specify explicit IDs:

```json
{
  "ids": ["uuid1", "uuid2"]
}
```

## Complete Examples

### Example 1: Simple Survey

```json
{
  "title": "Quick Application Check",
  "questionnaire": {
    "questions": [
      {
        "id": "q1",
        "label": "Is this application still active?",
        "type": "singlechoice",
        "options": [
          {"id": "yes", "label": "Yes"},
          {"id": "no", "label": "No"}
        ],
        "settings": {
          "isMandatory": true
        }
      }
    ]
  },
  "userQuery": {
    "roles": [
      {"subscriptionType": "RESPONSIBLE"}
    ]
  }
}
```

### Example 2: Conditional Questions

```json
{
  "title": "Application Lifecycle Survey",
  "questionnaire": {
    "questions": [
      {
        "id": "q1_status",
        "label": "Current lifecycle status?",
        "type": "singlechoice",
        "options": [
          {"id": "active", "label": "Active"},
          {"id": "phaseout", "label": "Phase Out"},
          {"id": "endoflife", "label": "End of Life"}
        ]
      },
      {
        "id": "q2_reason",
        "label": "Why is it being phased out?",
        "type": "textarea",
        "settings": {
          "isConditional": true,
          "dependency": {
            "parentId": "q1_status",
            "condition": {
              "phaseout": true
            }
          }
        }
      }
    ]
  },
  "userQuery": {
    "roles": [
      {"subscriptionType": "RESPONSIBLE"}
    ]
  }
}
```

### Example 3: Fact Sheet Field Mapping

```json
{
  "title": "Update Application Description",
  "questionnaire": {
    "questions": [
      {
        "id": "q1_desc",
        "label": "Application Description",
        "type": "textarea",
        "factSheetElement": {
          "type": "description",
          "factSheetFieldName": "description",
          "factSheetFieldType": "TEXT"
        }
      },
      {
        "id": "q2_lifecycle",
        "label": "Lifecycle Phase",
        "type": "singlechoice",
        "options": [
          {"id": "plan", "label": "Plan"},
          {"id": "active", "label": "Active"},
          {"id": "phaseout", "label": "Phase Out"}
        ],
        "factSheetElement": {
          "type": "lifecycle",
          "factSheetFieldName": "lifecycle",
          "factSheetFieldType": "SINGLE_SELECT"
        }
      }
    ]
  },
  "userQuery": {
    "roles": [
      {"subscriptionType": "RESPONSIBLE"}
    ]
  }
}
```

## Validation Rules

### Title
- Must not be empty
- Whitespace-only titles are invalid

### Questions
- Choice questions (singlechoice, multiplechoice) must have `options`
- Each question must have unique `id`
- Conditional questions must reference valid parent question

### Dependencies
- `parentId` must reference existing question
- Parent question must appear before dependent question
- Condition keys should match parent question option IDs

### User/Fact Sheet Query
- At least one query type should be provided
- Both can be used together for complex targeting

## Best Practices

### Question IDs
Use descriptive, hierarchical IDs:
```
q1_lifecycle
q2_phaseout_reason
q3_business_criticality
```

### Question Labels
- Be clear and concise
- Use action verbs for clarity
- Avoid jargon when possible

### Options
- Provide exhaustive option sets
- Include "Other" or "N/A" when appropriate
- Order logically (alphabetically, by frequency, etc.)

### Conditional Logic
- Keep dependency chains shallow (max 2-3 levels)
- Document complex dependencies
- Test all condition paths

### Fact Sheet Mapping
- Verify field names match workspace configuration
- Check field types are compatible
- Consider data validation requirements

## Common Patterns

### Rating Scale

```json
{
  "id": "rating",
  "label": "How would you rate this?",
  "type": "singlechoice",
  "options": [
    {"id": "1", "label": "1 - Poor"},
    {"id": "2", "label": "2"},
    {"id": "3", "label": "3 - Average"},
    {"id": "4", "label": "4"},
    {"id": "5", "label": "5 - Excellent"}
  ]
}
```

### Yes/No with Follow-up

```json
{
  "id": "needs_update",
  "label": "Does this need updating?",
  "type": "singlechoice",
  "options": [
    {"id": "yes", "label": "Yes"},
    {"id": "no", "label": "No"}
  ]
},
{
  "id": "update_details",
  "label": "What needs to be updated?",
  "type": "textarea",
  "settings": {
    "isConditional": true,
    "dependency": {
      "parentId": "needs_update",
      "condition": {"yes": true}
    }
  }
}
```

### Multi-select with "Other"

```json
{
  "id": "technologies",
  "label": "Which technologies are used?",
  "type": "multiplechoice",
  "options": [
    {"id": "java", "label": "Java"},
    {"id": "python", "label": "Python"},
    {"id": "nodejs", "label": "Node.js"},
    {"id": "other", "label": "Other"}
  ]
},
{
  "id": "technologies_other",
  "label": "Please specify other technologies",
  "type": "text",
  "settings": {
    "isConditional": true,
    "dependency": {
      "parentId": "technologies",
      "condition": {"other": true}
    }
  }
}
```

## Error Handling

### Validation Errors

**Missing required field:**
```
ValidationError: title: field required
```

**Invalid question type:**
```
ValidationError: questionnaire -> questions -> 0: Questions of type singlechoice must have options
```

**Invalid dependency:**
```
ValidationError: settings -> dependency -> parentId: Referenced question does not exist
```

## Migration Guide

### From Manual Creation to JSON

1. **Export existing survey** (if possible)
2. **Map fields to JSON schema**
3. **Add question IDs** (auto-generated in manual creation)
4. **Convert options** to structured format
5. **Document dependencies** as JSON conditions
6. **Validate** using schema validator

### Updating Existing Surveys

To update an existing survey:
1. Get current survey via API
2. Modify JSON
3. Create new version (surveys are immutable)
4. Migrate results if needed

## Troubleshooting

### Schema Validation Fails

**Check:**
- JSON syntax (trailing commas, quotes)
- Required fields present
- Question IDs are unique
- Option IDs are unique within question
- Dependency references are valid

### Survey Creation Fails in LeanIX

**Check:**
- Fact sheet type exists in workspace
- Field names match workspace configuration
- User has survey creation permissions
- Workspace ID is correct

## API Integration

### Using with LeanIX API

```python
import httpx

# Validate JSON
survey_data = SurveyInput.model_validate(json_data)

# Convert to API format
poll_data = PollCreate.from_survey_input(
    survey_input=survey_data,
    language="en",
    fact_sheet_type="Application"
)

# Send to LeanIX
response = httpx.post(
    f"{leanix_url}/services/poll/v2/polls",
    params={"workspaceId": workspace_id},
    headers={"Authorization": f"Bearer {token}"},
    json=poll_data.model_dump(by_alias=True, exclude_none=True)
)
```

## Version History

- **v1.0.0**: Initial schema based on LeanIX Poll API v2.0.0

## Resources

- LeanIX API Documentation: https://docs.leanix.net
- JSON Schema Specification: https://json-schema.org
- Pydantic Documentation: https://docs.pydantic.dev
