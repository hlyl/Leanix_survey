"""
Tests for LeanIX survey models and validation.
"""

import json
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.leanix_survey_models import (
    AllowedPermissionStatus,
    PollCreate,
    Question,
    Questionnaire,
    QuestionOption,
    SubscriptionType,
    SurveyInput,
    UserQuery,
    UserRole,
)

# ============================================================================
# Test Data
# ============================================================================


@pytest.fixture
def simple_question():
    """Simple text question"""
    return Question(id="q1", label="What is your name?", type="text")


@pytest.fixture
def choice_question():
    """Multiple choice question"""
    return Question(
        id="q2",
        label="Select your preference",
        type="singlechoice",
        options=[
            QuestionOption(id="opt1", label="Option 1"),
            QuestionOption(id="opt2", label="Option 2"),
        ],
    )


@pytest.fixture
def conditional_question():
    """Question with dependency"""
    return Question(
        id="q3",
        label="Why?",
        type="textarea",
        settings={
            "isConditional": True,
            "dependency": {"parentId": "q2", "condition": {"opt1": True}},
        },
    )


@pytest.fixture
def simple_survey(choice_question):
    """Minimal valid survey"""
    return SurveyInput(
        title="Test Survey",
        questionnaire=Questionnaire(questions=[choice_question]),
        userQuery=UserQuery(roles=[UserRole(subscriptionType=SubscriptionType.RESPONSIBLE)]),
    )


# ============================================================================
# Question Tests
# ============================================================================


def test_simple_question_creation(simple_question):
    """Test creating a basic question"""
    assert simple_question.id == "q1"
    assert simple_question.label == "What is your name?"
    assert simple_question.type == "text"


def test_choice_question_requires_options():
    """Test that choice questions must have options"""
    with pytest.raises(ValidationError) as exc_info:
        Question(
            id="q1",
            label="Choose one",
            type="singlechoice",
            # Missing options
        )

    errors = exc_info.value.errors()
    assert any("option" in str(error).lower() for error in errors)


def test_choice_question_with_options(choice_question):
    """Test choice question with options"""
    assert len(choice_question.options) == 2
    assert choice_question.options[0].label == "Option 1"


def test_conditional_question(conditional_question):
    """Test question with conditional logic"""
    assert conditional_question.settings.is_conditional is True
    assert conditional_question.settings.dependency.parent_id == "q2"


def test_nested_questions():
    """Test questions with children"""
    parent = Question(
        id="parent",
        label="Parent question",
        type="singlechoice",
        options=[
            QuestionOption(id="yes", label="Yes"),
            QuestionOption(id="no", label="No"),
        ],
        children=[Question(id="child1", label="Child question", type="text")],
    )

    assert len(parent.children) == 1
    assert parent.children[0].id == "child1"


# ============================================================================
# Survey Input Tests
# ============================================================================


def test_minimal_survey(simple_survey):
    """Test creating a minimal valid survey"""
    assert simple_survey.title == "Test Survey"
    assert len(simple_survey.questionnaire.questions) == 1
    assert simple_survey.user_query is not None


def test_survey_requires_title():
    """Test that survey requires a title"""
    with pytest.raises(ValidationError):
        SurveyInput(questionnaire=Questionnaire(questions=[]), userQuery=UserQuery(roles=[]))


def test_survey_title_validation():
    """Test title cannot be empty or whitespace"""
    with pytest.raises(ValidationError):
        SurveyInput(
            title="   ",  # Whitespace only
            questionnaire=Questionnaire(questions=[]),
            userQuery=UserQuery(roles=[]),
        )


def test_survey_with_multiple_questions():
    """Test survey with multiple questions"""
    survey = SurveyInput(
        title="Multi-question Survey",
        questionnaire=Questionnaire(
            questions=[
                Question(id="q1", label="Question 1", type="text"),
                Question(id="q2", label="Question 2", type="textarea"),
                Question(
                    id="q3",
                    label="Question 3",
                    type="singlechoice",
                    options=[
                        QuestionOption(id="a", label="A"),
                        QuestionOption(id="b", label="B"),
                    ],
                ),
            ]
        ),
        userQuery=UserQuery(roles=[UserRole(subscriptionType=SubscriptionType.RESPONSIBLE)]),
    )

    assert len(survey.questionnaire.questions) == 3


# ============================================================================
# User Query Tests
# ============================================================================


def test_user_query_with_single_role():
    """Test user query with one role"""
    query = UserQuery(roles=[UserRole(subscriptionType=SubscriptionType.RESPONSIBLE)])

    assert len(query.roles) == 1
    assert query.roles[0].subscription_type == SubscriptionType.RESPONSIBLE


def test_user_query_with_multiple_roles():
    """Test user query with multiple roles"""
    query = UserQuery(
        roles=[
            UserRole(subscriptionType=SubscriptionType.RESPONSIBLE),
            UserRole(subscriptionType=SubscriptionType.ACCOUNTABLE),
            UserRole(subscriptionType=SubscriptionType.OBSERVER),
        ]
    )

    assert len(query.roles) == 3


# ============================================================================
# Poll Create Tests
# ============================================================================


def test_poll_create_from_survey_input(simple_survey):
    """Test creating PollCreate from SurveyInput"""
    poll = PollCreate.from_survey_input(
        survey_input=simple_survey,
        language="en",
        fact_sheet_type="Application",
        due_date=date(2024, 12, 31),
    )

    assert poll.title == "Test Survey"
    assert poll.language == "en"
    assert poll.fact_sheet_type == "Application"
    assert poll.due_date == date(2024, 12, 31)
    assert poll.questionnaire == simple_survey.questionnaire


def test_poll_create_with_optional_fields():
    """Test PollCreate with all optional fields"""
    survey = SurveyInput(
        title="Complete Survey",
        questionnaire=Questionnaire(questions=[Question(id="q1", label="Q1", type="text")]),
        introductionText="Welcome!",
        sendChangeNotifications=True,
        allowedPermissionStatus=AllowedPermissionStatus.ACTIVE_AND_INVITED,
        userQuery=UserQuery(roles=[UserRole(subscriptionType=SubscriptionType.RESPONSIBLE)]),
    )

    poll = PollCreate.from_survey_input(
        survey_input=survey, language="de", fact_sheet_type="ITComponent"
    )

    assert poll.introduction_text == "Welcome!"
    assert poll.send_change_notifications is True
    assert poll.allowed_permission_status == AllowedPermissionStatus.ACTIVE_AND_INVITED


# ============================================================================
# JSON Serialization Tests
# ============================================================================


def test_survey_to_json(simple_survey):
    """Test serializing survey to JSON"""
    json_str = simple_survey.model_dump_json(by_alias=True, exclude_none=True)
    data = json.loads(json_str)

    assert data["title"] == "Test Survey"
    assert "questionnaire" in data
    assert "userQuery" in data


def test_survey_from_json():
    """Test deserializing survey from JSON"""
    json_data = {
        "title": "JSON Survey",
        "questionnaire": {"questions": [{"id": "q1", "label": "Test Question", "type": "text"}]},
        "userQuery": {"roles": [{"subscriptionType": "RESPONSIBLE"}]},
    }

    survey = SurveyInput.model_validate(json_data)

    assert survey.title == "JSON Survey"
    assert len(survey.questionnaire.questions) == 1


def test_poll_create_json_with_aliases():
    """Test that PollCreate uses correct field aliases"""
    survey = SurveyInput(
        title="Test",
        questionnaire=Questionnaire(questions=[Question(id="q1", label="Q", type="text")]),
        userQuery=UserQuery(roles=[UserRole(subscriptionType=SubscriptionType.RESPONSIBLE)]),
    )

    poll = PollCreate.from_survey_input(
        survey_input=survey, language="en", fact_sheet_type="Application"
    )

    json_data = poll.model_dump(by_alias=True, exclude_none=True)

    # Should use camelCase aliases
    assert "factSheetType" in json_data
    assert "userQuery" in json_data
    # Should not use snake_case
    assert "fact_sheet_type" not in json_data


# ============================================================================
# Example File Tests
# ============================================================================


@pytest.mark.parametrize(
    "example_file",
    [
        "example_survey_simple.json",
        "example_survey_comprehensive.json",
        "example_survey_factsheet_mapping.json",
    ],
)
def test_example_files_are_valid(example_file):
    """Test that all example files validate correctly"""
    file_path = Path(__file__).parent / example_file

    if not file_path.exists():
        pytest.skip(f"Example file not found: {example_file}")

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    # Should validate without errors
    survey = SurveyInput.model_validate(data)

    assert survey.title
    assert len(survey.questionnaire.questions) > 0


# ============================================================================
# Edge Cases
# ============================================================================


def test_question_with_all_optional_fields():
    """Test question with all optional fields populated"""
    question = Question(
        id="complete",
        label="Complete Question",
        descriptiveText="This is a description",
        type="singlechoice",
        element="custom_element",
        options=[QuestionOption(id="opt1", label="Option 1", comment="Help text for option 1")],
        answerOptions="custom",
        powerfeature=True,
        disabled=False,
        settings={"isMandatory": True, "hideInResults": False, "version": 1},
    )

    assert question.descriptive_text == "This is a description"
    assert question.powerfeature is True
    assert question.settings.is_mandatory is True


def test_empty_questionnaire():
    """Test that questionnaire can have empty questions list"""
    # This might be invalid for actual use but should be structurally valid
    questionnaire = Questionnaire(questions=[])
    assert len(questionnaire.questions) == 0
