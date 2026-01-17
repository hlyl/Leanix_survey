"""
Streamlit application for creating LeanIX surveys.

This UI allows users to:
1. Upload/paste survey JSON
2. Validate the JSON against the schema via backend API
3. Configure survey settings (language, fact sheet type, due date, workspace)
4. Create the survey in LeanIX via backend API
5. Submit batch survey creation requests
"""

from __future__ import annotations

import logging
import os
from datetime import date, timedelta
from pathlib import Path
from uuid import UUID

import httpx
import streamlit as st

from src.leanix_survey_models import SurveyInput
from src.validate_survey import validate_json_string

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


# ============================================================================
# Backend API Client Functions
# ============================================================================


def validate_survey_via_api(json_text: str) -> tuple[bool, SurveyInput | None, str]:
    """Validate survey JSON via the backend API endpoint."""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{BACKEND_URL}/api/validate",
                json={"json_input": json_text},
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("valid"):
                    return True, SurveyInput(**result.get("survey_input", {})), ""
                else:
                    return False, None, result.get("error", "Validation failed")
            else:
                error_msg = response.json().get("detail", f"HTTP {response.status_code}")
                return False, None, error_msg
    except Exception as exc:
        return False, None, f"Backend error: {exc}"


def create_survey_via_api(
    survey_input: SurveyInput,
    leanix_url: str,
    api_token: str,
    workspace_id: str,
    language: str,
    fact_sheet_type: str,
    due_date: date | None,
) -> tuple[bool, str | None, str]:
    """Create survey via backend API endpoint."""
    try:
        payload = {
            "survey_input": survey_input.model_dump(by_alias=True, exclude_none=True),
            "language": language,
            "fact_sheet_type": fact_sheet_type,
            "due_date": due_date.isoformat() if due_date else None,
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{BACKEND_URL}/api/surveys/create",
                params={
                    "leanix_url": leanix_url,
                    "api_token": api_token,
                    "workspace_id": workspace_id,
                },
                json=payload,
            )
            if response.status_code == 200:
                result = response.json()
                return result["success"], result.get("poll_id"), result.get("message", "")
            else:
                error_msg = response.json().get("detail", f"HTTP {response.status_code}")
                return False, None, error_msg
    except Exception as exc:
        return False, None, f"Backend error: {exc}"


def simple_url_validation(url: str) -> tuple[bool, str]:
    """Simple client-side URL validation for LeanIX."""
    if not url or url == "https://your-instance.leanix.net":
        return False, "LeanIX URL not configured"
    if not url.startswith(("http://", "https://")):
        return False, "URL must start with http:// or https://"
    return True, ""


def simple_token_validation(token: str) -> tuple[bool, str]:
    """Simple client-side token validation."""
    if not token or len(token.strip()) == 0:
        return False, "API token cannot be empty"
    return True, ""


def validate_workspace_id_format(workspace_id: str) -> tuple[bool, str]:
    """Validate workspace UUID format locally (no backend call needed)."""
    if not workspace_id or len(workspace_id.strip()) == 0:
        return False, "Workspace ID cannot be empty"
    try:
        UUID(workspace_id)
        return True, ""
    except ValueError:
        return False, "Workspace ID must be a valid UUID"


# ============================================================================
# Configuration
# ============================================================================

st.set_page_config(
    page_title="LeanIX Survey Creator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",)

# ============================================================================
# Novo Nordisk CVI Branding & Styling
# ============================================================================

st.markdown(
    """
    <style>
    /* CVI Color Palette - Novo Nordisk */
    h1, h2, h3 { color: #001965 !important; }
    p, body { color: #001965; }
    
    /* Buttons - Sea Blue (Primary) */
    div.stButton > button {
        background-color: #0055B8;
        color: #FFFFFF;
        border: none;
        border-radius: 24px;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(0, 25, 101, 0.1);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #001965;
        box-shadow: 0 4px 8px rgba(0, 25, 101, 0.2);
        transform: translateY(-1px);
    }
    
    /* Text Areas - True Blue Border */
    .stTextArea textarea {
        border-radius: 6px !important;
        border: 1px solid #0055B8 !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab"] { color: #001965; font-weight: 500; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #0055B8;
        border-bottom-color: #0055B8 !important;
    }
    
    /* Status Messages */
    .stSuccess { background-color: #E8F5E9 !important; }
    .stError { background-color: #FFEBEE !important; }
    .stWarning { background-color: #FFF3E0 !important; }
    .stInfo { background-color: #E3F2FD !important; }
    
    /* Dividers */
    hr { border-color: #0055B8 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================================
# Session State Initialization
# ============================================================================

if "survey_input" not in st.session_state:
    st.session_state.survey_input = None

if "validation_result" not in st.session_state:
    st.session_state.validation_result = None

if "created_poll_id" not in st.session_state:
    st.session_state.created_poll_id = None

if "json_input" not in st.session_state:
    st.session_state.json_input = ""


# ============================================================================
# Helper Functions
# ============================================================================


def load_example(example_name: str) -> str:
    """Load example JSON file"""
    example_files = {
        "Simple": "example_survey_simple.json",
        "Comprehensive": "example_survey_comprehensive.json",
        "Fact Sheet Mapping": "example_survey_factsheet_mapping.json",
    }

    if example_name in example_files:
        # Examples are in /examples directory (parent of /src)
        file_path = Path(__file__).parent.parent / "examples" / example_files[example_name]
        if file_path.exists():
            with open(file_path, encoding="utf-8") as f:
                return f.read()

    return ""


def validate_survey_json(json_text: str) -> tuple[bool, SurveyInput | None, str]:
    """Validate survey JSON via the local validate_json_string function."""
    return validate_json_string(json_text)


def create_survey_in_leanix(
    survey_input: SurveyInput,
    leanix_url: str,
    api_token: str,
    workspace_id: str,
    language: str,
    fact_sheet_type: str,
    due_date: date | None,
) -> tuple[bool, str | None, str]:
    """Create survey in LeanIX via the FastAPI backend."""
    return create_survey_via_api(
        survey_input, leanix_url, api_token, workspace_id, language, fact_sheet_type, due_date
    )


# ============================================================================
# UI Layout
# ============================================================================

st.title("📊 LeanIX Survey Creator")
st.markdown(
    """
Create and manage LeanIX surveys programmatically. Upload your survey definition JSON,
validate it, and create the survey in your LeanIX workspace.
"""
)

# ============================================================================
# Sidebar - LeanIX Configuration
# ============================================================================

with st.sidebar:
    st.header("⚙️ LeanIX Configuration")

    leanix_url = st.text_input(
        "LeanIX Instance URL",
        value="https://your-instance.leanix.net",
        help="Your LeanIX instance URL",
    )

    api_token = st.text_input(
        "API Token", type="password", help="LeanIX API token with poll creation permissions"
    )

    workspace_id = st.text_input(
        "Workspace ID", help="UUID of the workspace where the survey will be created"
    )

    st.divider()

    st.header("📋 Survey Settings")

    # Language selection
    language_options = {
        "English": "en",
        "German": "de",
        "French": "fr",
        "Spanish": "es",
        "Italian": "it",
        "Dutch": "nl",
        "Portuguese": "pt",
    }

    selected_language = st.selectbox("Language", options=list(language_options.keys()), index=0)
    language_code = language_options[selected_language]

    # Fact sheet type
    fact_sheet_type = st.text_input(
        "Fact Sheet Type",
        value="Application",
        help="Type of fact sheet to survey (e.g., Application, ITComponent, etc.)",
    )

    # Due date
    use_due_date = st.checkbox("Set Due Date")
    due_date_value = None
    if use_due_date:
        due_date_value = st.date_input(
            "Due Date", value=date.today() + timedelta(days=14), min_value=date.today()
        )

    st.divider()

    # Example loader
    st.header("📝 Load Example")
    example_choice = st.selectbox(
        "Choose an example", options=["None", "Simple", "Comprehensive", "Fact Sheet Mapping"]
    )

    if st.button("Load Example") and example_choice != "None":
        example_json = load_example(example_choice)
        if example_json:
            st.session_state.json_input = example_json
            st.success(f"Loaded {example_choice} example!")
            st.rerun()


# ============================================================================
# Main Content
# ============================================================================

# Tab layout
tab1, tab2, tab3 = st.tabs(["📝 JSON Input", "✅ Validation", "🚀 Create Survey"])

# --------------------------------------------------------------------------
# Tab 1: JSON Input
# --------------------------------------------------------------------------

with tab1:
    st.header("Survey Definition (JSON)")

    json_input = st.text_area(
        "Paste your survey JSON here",
        value=st.session_state.json_input,
        key="json_input",
        height=400,
        help="Enter or paste the survey definition JSON",
    )

    col_buttons, col_uploader = st.columns([2, 1], vertical_alignment="center")
    
    with col_buttons:
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("Validate JSON", type="primary", use_container_width=True):
                if not json_input.strip():
                    st.error("Please enter survey JSON")
                else:
                    with st.spinner("Validating..."):
                        is_valid, survey_input, error_msg = validate_survey_json(json_input)

                        st.session_state.validation_result = {
                            "valid": is_valid,
                            "survey_input": survey_input,
                            "error": error_msg,
                        }

                        if is_valid:
                            st.session_state.survey_input = survey_input
                            st.success("✓ JSON is valid!")
                        else:
                            st.error("✗ Validation failed")
                            st.code(error_msg)
        
        with btn_col2:
            if st.button("Clear", use_container_width=True):
                st.session_state.survey_input = None
                st.session_state.validation_result = None
                st.session_state.json_input = ""
                st.rerun()
    
    with col_uploader:
        uploaded_file = st.file_uploader(
            "Upload JSON",
            type="json",
            label_visibility="collapsed",
            help="Upload a JSON file"
        )
        if uploaded_file is not None:
            try:
                file_content = uploaded_file.read().decode("utf-8")
                st.session_state.json_input = file_content
                st.success(f"Loaded: {uploaded_file.name}")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")


# --------------------------------------------------------------------------
# Tab 2: Validation Results
# --------------------------------------------------------------------------

with tab2:
    st.header("Validation Results")

    if st.session_state.validation_result is None:
        st.info("👈 Enter and validate JSON in the 'JSON Input' tab first")

    elif not st.session_state.validation_result["valid"]:
        st.error("❌ Validation Failed")
        st.code(st.session_state.validation_result["error"])

    else:
        survey = st.session_state.validation_result["survey_input"]

        st.success("✅ Validation Successful")

        # Survey overview
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Title", survey.title)

        with col2:
            st.metric("Questions", len(survey.questionnaire.questions))

        with col3:
            query_type = (
                "User Query"
                if survey.user_query
                else "Fact Sheet Query" if survey.fact_sheet_query else "None"
            )
            st.metric("Query Type", query_type)

        # Question details
        st.subheader("Questions Overview")

        for idx, question in enumerate(survey.questionnaire.questions, 1):
            with st.expander(f"Question {idx}: {question.label}"):
                st.write(f"**Type:** {question.type}")
                st.write(f"**ID:** {question.id}")

                if question.descriptive_text:
                    st.write(f"**Description:** {question.descriptive_text}")

                if question.options:
                    st.write("**Options:**")
                    for opt in question.options:
                        st.write(f"  - {opt.label}")

                if question.settings:
                    settings_info = []
                    if question.settings.is_mandatory:
                        settings_info.append("Mandatory")
                    if question.settings.is_conditional:
                        settings_info.append("Conditional")
                    if question.settings.hide_in_results:
                        settings_info.append("Hidden in results")

                    if settings_info:
                        st.write(f"**Settings:** {', '.join(settings_info)}")

                if question.children:
                    st.write(f"**Child Questions:** {len(question.children)}")

        # User Query details
        if survey.user_query:
            st.subheader("User Query Configuration")
            st.write(f"**Roles:** {len(survey.user_query.roles)}")
            for role in survey.user_query.roles:
                st.write(f"  - Subscription Type: {role.subscription_type}")


# --------------------------------------------------------------------------
# Tab 3: Create Survey
# --------------------------------------------------------------------------

with tab3:
    st.header("Create Survey in LeanIX")

    if st.session_state.survey_input is None:
        st.warning("⚠️ Please validate your survey JSON first")
    else:
        survey = st.session_state.survey_input

        st.success(f"✓ Ready to create: **{survey.title}**")

        # Configuration summary
        st.subheader("Configuration Summary")

        config_col1, config_col2 = st.columns(2)

        with config_col1:
            st.write(f"**Language:** {selected_language} ({language_code})")
            st.write(f"**Fact Sheet Type:** {fact_sheet_type}")
            st.write(f"**Due Date:** {due_date_value if due_date_value else 'Not set'}")

        with config_col2:
            st.write(f"**Workspace ID:** {workspace_id if workspace_id else 'Not set'}")
            st.write(f"**Questions:** {len(survey.questionnaire.questions)}")

        st.divider()

        # Validation checks
        ready_to_create = True
        issues = []

        # Validate URL
        url_valid, url_error = simple_url_validation(leanix_url)
        if not url_valid:
            issues.append(f"LeanIX URL: {url_error}")
            ready_to_create = False

        # Validate API token
        token_valid, token_error = simple_token_validation(api_token)
        if not token_valid:
            issues.append(f"API Token: {token_error}")
            ready_to_create = False

        # Validate workspace ID
        ws_valid, ws_error = validate_workspace_id_format(workspace_id)
        if not ws_valid:
            issues.append(f"Workspace ID: {ws_error}")
            ready_to_create = False

        if not fact_sheet_type:
            issues.append("Fact Sheet Type not specified")
            ready_to_create = False

        if issues:
            st.warning("⚠️ Configuration Issues:")
            for issue in issues:
                st.write(f"  • {issue}")

        # Create button
        if st.button(
            "🚀 Create Survey in LeanIX",
            type="primary",
            disabled=not ready_to_create,
            use_container_width=True,
        ):
            with st.spinner("Creating survey in LeanIX..."):
                success, poll_id, message = create_survey_in_leanix(
                    survey_input=survey,
                    leanix_url=leanix_url,
                    api_token=api_token,
                    workspace_id=workspace_id,
                    language=language_code,
                    fact_sheet_type=fact_sheet_type,
                    due_date=due_date_value,
                )

                if success:
                    st.success(f"✅ {message}")
                    if poll_id:
                        st.session_state.created_poll_id = poll_id
                        st.info(f"**Poll ID:** {poll_id}")

                        # Show link to LeanIX
                        poll_url = f"{leanix_url}/surveys/{poll_id}"
                        st.markdown(f"[Open in LeanIX]({poll_url})")
                else:
                    st.error(f"❌ {message}")

        # Show previously created poll
        if st.session_state.created_poll_id:
            st.divider()
            st.info(f"**Last Created Poll ID:** {st.session_state.created_poll_id}")


# ============================================================================
# Footer
# ============================================================================

st.divider()
st.caption("LeanIX Survey Creator v1.0.0 | Built with Streamlit")
