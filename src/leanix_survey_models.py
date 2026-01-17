"""
LeanIX Survey/Poll Creation Models

Pydantic models for validating JSON input for creating LeanIX surveys.
Based on LeanIX Poll API v2.0.0 OpenAPI specification.
"""

from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

# ============================================================================
# Enums
# ============================================================================


class SubscriptionType(str, Enum):
    """User subscription types for role-based filtering"""

    RESPONSIBLE = "RESPONSIBLE"
    OBSERVER = "OBSERVER"
    ACCOUNTABLE = "ACCOUNTABLE"
    ALL = "ALL"


class AllowedPermissionStatus(str, Enum):
    """Permission levels for poll participants"""

    ACTIVE_ONLY = "ACTIVE_ONLY"
    ACTIVE_AND_INVITED = "ACTIVE_AND_INVITED"
    ACTIVE_AND_INVITED_AND_CONTACTS = "ACTIVE_AND_INVITED_AND_CONTACTS"


class DateFilterType(str, Enum):
    """Date filter types for fact sheet queries"""

    POINT = "POINT"
    RANGE = "RANGE"
    TODAY = "TODAY"
    END_OF_MONTH = "END_OF_MONTH"
    END_OF_YEAR = "END_OF_YEAR"
    RANGE_STARTS = "RANGE_STARTS"
    RANGE_ENDS = "RANGE_ENDS"


class FacetFilterOperator(str, Enum):
    """Logical operators for combining filters"""

    AND = "AND"
    OR = "OR"
    NOR = "NOR"


# ============================================================================
# Supporting Models
# ============================================================================


class ElementProperty(BaseModel):
    """Property definition for fact sheet elements"""

    name: str


class FactSheetElement(BaseModel):
    """
    Fact sheet element configuration for questions that map to fact sheet fields.
    Used when a question should update/read from a specific fact sheet field.
    """

    type: str | None = None
    tag_group_id: str | None = Field(None, alias="tagGroupId")
    subscription: dict[str, Any] | None = None
    fact_sheet_field_name: str | None = Field(None, alias="factSheetFieldName")
    fact_sheet_field_type: str | None = Field(None, alias="factSheetFieldType")
    tag_group_mode: str | None = Field(None, alias="tagGroupMode")
    fact_sheet_field_view_type: str | None = Field(None, alias="factSheetFieldViewType")
    properties: list[ElementProperty] | None = None

    class Config:
        populate_by_name = True


class DependencySettings(BaseModel):
    """
    Configuration for conditional question dependencies.
    Allows questions to be shown/hidden based on answers to parent questions.
    """

    parent_id: str = Field(..., alias="parentId", description="ID of the parent question")
    condition: dict[str, Any] = Field(
        ..., description="Condition object defining when this question should be shown"
    )

    class Config:
        populate_by_name = True


class QuestionSettings(BaseModel):
    """
    Advanced settings for questions including metrics, formulas, and dependencies.
    All fields are optional to support simple and complex question configurations.
    """

    metrics: dict[str, str] | None = Field(
        None, description="Metrics configuration for the question"
    )
    version: int | None = Field(None, description="Settings version number")
    hide_in_results: bool | None = Field(None, alias="hideInResults")
    is_conditional: bool | None = Field(None, alias="isConditional")
    fs_sections: dict[str, Any] | None = Field(None, alias="fsSections")
    formula: str | None = Field(None, description="Formula for calculated questions")
    dependency: DependencySettings | None = Field(
        None, description="Dependency configuration for conditional questions"
    )
    is_mandatory: bool | None = Field(None, alias="isMandatory")

    class Config:
        populate_by_name = True


class QuestionOption(BaseModel):
    """
    Option for multiple choice questions.
    Each option can have an optional comment field.
    """

    id: str = Field(..., description="Unique identifier for this option")
    label: str = Field(..., description="Display text for the option")
    comment: str | None = Field(None, description="Optional comment/help text")


class Question(BaseModel):
    """
    Survey question definition with support for various question types.

    Question Types (common values, not exhaustive):
    - text: Free text input
    - textarea: Multi-line text input
    - singlechoice: Single selection from options
    - multiplechoice: Multiple selections from options
    - number: Numeric input
    - date: Date picker
    - factsheet: Fact sheet field mapping
    """

    id: str = Field(..., description="Unique identifier for this question")
    label: str = Field(..., description="Question text displayed to users")
    descriptive_text: str | None = Field(
        None, alias="descriptiveText", description="Additional help text or description"
    )
    type: str = Field(..., description="Question type (text, singlechoice, multiplechoice, etc.)")
    element: str | None = Field(None, description="Element type identifier")
    options: list[QuestionOption] | None = Field(
        None, description="Available options for choice-based questions"
    )
    answer_options: str | None = Field(None, alias="answerOptions")
    children: list["Question"] | None = Field(
        None, description="Nested child questions (for hierarchical structures)"
    )
    powerfeature: bool | None = Field(None, description="Whether this is a power user feature")
    disabled: bool | None = Field(None, description="Whether the question is disabled")
    fact_sheet_element: FactSheetElement | None = Field(
        None, alias="factSheetElement", description="Fact sheet field mapping configuration"
    )
    settings: QuestionSettings | None = Field(None, description="Advanced question settings")

    class Config:
        populate_by_name = True

    @model_validator(mode="after")
    def check_choice_questions_have_options(self):
        """Ensure choice questions have options"""
        if self.type in ["singlechoice", "multiplechoice"]:
            if not self.options:
                raise ValueError(f"Questions of type '{self.type}' must have at least one option")
        return self

    @field_validator("options")
    @classmethod
    def validate_options_for_choice_questions(
        cls, v: list[QuestionOption], info
    ) -> list[QuestionOption]:
        """Ensure choice questions have options"""
        if info.data.get("type") in ["singlechoice", "multiplechoice"] and not v:
            raise ValueError(f"Questions of type {info.data.get('type')} must have options")
        return v


# Enable forward references for recursive Question model
Question.model_rebuild()


class Questionnaire(BaseModel):
    """
    Container for survey questions.
    The questionnaire ID will be auto-generated by LeanIX.
    """

    questions: list[Question] = Field(..., description="List of questions in the survey")


class DateFilter(BaseModel):
    """Date-based filtering for fact sheet queries"""

    from_date: date | None = Field(None, alias="from")
    to_date: date | None = Field(None, alias="to")
    type: DateFilterType

    class Config:
        populate_by_name = True


class SubscriptionFilter(BaseModel):
    """Filter fact sheets by user subscription/role"""

    type: SubscriptionType
    role_id: str | None = Field(None, alias="roleId")

    class Config:
        populate_by_name = True


class FacetFilter(BaseModel):
    """
    Flexible filtering system for fact sheets.
    Supports nested filters with logical operators.
    """

    facet_key: str | None = Field(None, alias="facetKey")
    keys: list[str] | None = None
    operator: FacetFilterOperator | None = None
    date_filter: DateFilter | None = Field(None, alias="dateFilter")
    subscription_filter: SubscriptionFilter | None = Field(None, alias="subscriptionFilter")
    sub_filter: list["FacetFilter"] | None = Field(None, alias="subFilter")

    class Config:
        populate_by_name = True


# Enable forward references for recursive FacetFilter
FacetFilter.model_rebuild()


class QueryFilter(BaseModel):
    """Filter configuration for fact sheet queries"""

    fs_type: str | None = Field(None, alias="fsType", description="Fact sheet type to filter")
    facet_filter: list[FacetFilter] | None = Field(None, alias="facetFilter")
    full_text_search_term: str | None = Field(None, alias="fullTextSearchTerm")

    class Config:
        populate_by_name = True


class FactSheetQuery(BaseModel):
    """
    Query definition for selecting which fact sheets to include in the survey.
    Can use either filter-based selection or explicit ID list.
    """

    filter: QueryFilter | None = Field(None, description="Filter-based selection of fact sheets")
    ids: list[str] | None = Field(None, description="Explicit list of fact sheet IDs to include")


class UserRoleDetails(BaseModel):
    """Details about a specific user role"""

    name: str = Field(..., description="Role name")
    id: str = Field(..., description="Role ID")


class UserRole(BaseModel):
    """
    User role configuration for selecting survey recipients.
    Defines which users should receive the survey based on their role/subscription.
    """

    subscription_type: SubscriptionType = Field(..., alias="subscriptionType")
    role_details: list[UserRoleDetails] | None = Field(None, alias="roleDetails")

    class Config:
        populate_by_name = True


class UserQuery(BaseModel):
    """
    Query definition for selecting which users should receive the survey.
    Based on their roles and subscriptions to fact sheets.
    """

    roles: list[UserRole] = Field(
        ..., description="List of role-based filters for selecting recipients"
    )


# ============================================================================
# Main Survey Input Model
# ============================================================================


class SurveyInput(BaseModel):
    """
    Main input model for creating a LeanIX survey/poll.

    This represents the JSON structure that users will provide.
    UI-collected fields (dueDate, language, etc.) will be merged with this.
    """

    title: str = Field(..., description="Survey title", min_length=1)
    questionnaire: Questionnaire = Field(..., description="Survey questions")

    # Optional configuration
    introduction_text: str | None = Field(
        None, alias="introductionText", description="Introduction text shown to survey recipients"
    )
    introduction_subject: str | None = Field(
        None, alias="introductionSubject", description="Email subject line for survey invitation"
    )
    additional_fact_sheet_subject: str | None = Field(None, alias="additionalFactSheetSubject")
    additional_fact_sheet_text: str | None = Field(None, alias="additionalFactSheetText")
    additional_fact_sheet_check_enabled: bool | None = Field(
        None, alias="additionalFactSheetCheckEnabled"
    )
    repeat_interval: int | None = Field(
        None,
        alias="repeatInterval",
        description="Repeat interval in milliseconds (for recurring surveys)",
    )
    time_frame: int | None = Field(
        None, alias="timeFrame", description="Time frame in milliseconds"
    )
    send_change_notifications: bool | None = Field(
        None,
        alias="sendChangeNotifications",
        description="Send notifications when fact sheets change",
    )
    allowed_permission_status: AllowedPermissionStatus | None = Field(
        None, alias="allowedPermissionStatus", description="Who can participate in the survey"
    )
    dynamic_scope_check_enabled: bool | None = Field(
        None, alias="dynamicScopeCheckEnabled", description="Enable dynamic scope checking"
    )

    # Query definitions (at least one should be provided)
    fact_sheet_query: FactSheetQuery | None = Field(
        None, alias="factSheetQuery", description="Query for selecting which fact sheets to survey"
    )
    user_query: UserQuery | None = Field(
        None, alias="userQuery", description="Query for selecting survey recipients"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "examples": [
                {
                    "title": "Q1 Application Health Check",
                    "introductionText": "Please review and update information about your applications.",
                    "questionnaire": {
                        "questions": [
                            {
                                "id": "q1",
                                "label": "What is the current lifecycle status?",
                                "type": "singlechoice",
                                "options": [
                                    {"id": "active", "label": "Active"},
                                    {"id": "phaseout", "label": "Phase Out"},
                                    {"id": "endoflife", "label": "End of Life"},
                                ],
                            }
                        ]
                    },
                    "userQuery": {"roles": [{"subscriptionType": "RESPONSIBLE"}]},
                }
            ]
        }

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Ensure title is not empty or whitespace only"""
        if not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip()


class PollCreate(BaseModel):
    """
    Complete poll creation request combining user input with UI-collected data.
    This is what gets sent to the LeanIX API.
    """

    title: str
    language: str = Field(..., description="Language code (e.g., 'en', 'de', 'fr')")
    fact_sheet_type: str = Field(
        ..., alias="factSheetType", description="Type of fact sheet to survey"
    )
    questionnaire: Questionnaire
    due_date: date | None = Field(None, alias="dueDate")
    introduction_text: str | None = Field(None, alias="introductionText")
    introduction_subject: str | None = Field(None, alias="introductionSubject")
    additional_fact_sheet_subject: str | None = Field(None, alias="additionalFactSheetSubject")
    additional_fact_sheet_text: str | None = Field(None, alias="additionalFactSheetText")
    additional_fact_sheet_check_enabled: bool | None = Field(
        None, alias="additionalFactSheetCheckEnabled"
    )
    repeat_interval: int | None = Field(None, alias="repeatInterval")
    time_frame: int | None = Field(None, alias="timeFrame")
    send_change_notifications: bool | None = Field(None, alias="sendChangeNotifications")
    allowed_permission_status: AllowedPermissionStatus | None = Field(
        None, alias="allowedPermissionStatus"
    )
    dynamic_scope_check_enabled: bool | None = Field(None, alias="dynamicScopeCheckEnabled")
    fact_sheet_query: FactSheetQuery | None = Field(None, alias="factSheetQuery")
    user_query: UserQuery | None = Field(None, alias="userQuery")

    class Config:
        populate_by_name = True

    @classmethod
    def from_survey_input(
        cls,
        survey_input: SurveyInput,
        language: str,
        fact_sheet_type: str,
        due_date: date | None = None,
    ) -> "PollCreate":
        """
        Create a PollCreate instance from SurveyInput and UI-collected data.

        Args:
            survey_input: Validated survey definition from JSON
            language: Language code from UI
            fact_sheet_type: Fact sheet type from UI
            due_date: Optional due date from UI

        Returns:
            PollCreate instance ready to send to LeanIX API
        """
        return cls(
            title=survey_input.title,
            language=language,
            factSheetType=fact_sheet_type,
            questionnaire=survey_input.questionnaire,
            dueDate=due_date,
            introductionText=survey_input.introduction_text,
            introductionSubject=survey_input.introduction_subject,
            additionalFactSheetSubject=survey_input.additional_fact_sheet_subject,
            additionalFactSheetText=survey_input.additional_fact_sheet_text,
            additionalFactSheetCheckEnabled=survey_input.additional_fact_sheet_check_enabled,
            repeatInterval=survey_input.repeat_interval,
            timeFrame=survey_input.time_frame,
            sendChangeNotifications=survey_input.send_change_notifications,
            allowedPermissionStatus=survey_input.allowed_permission_status,
            dynamicScopeCheckEnabled=survey_input.dynamic_scope_check_enabled,
            factSheetQuery=survey_input.fact_sheet_query,
            userQuery=survey_input.user_query,
        )
