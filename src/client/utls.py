from typing import Optional, cast
from uuid import UUID
import streamlit as st

from src.client.api_client import ApiClient

def get_api_client() -> ApiClient:
    """Get or create an API client instance."""
    if "api_client" not in st.session_state:
        st.session_state.api_client = ApiClient()
    return cast(ApiClient, st.session_state.api_client)


def get_thread_id_from_url() -> Optional[UUID]:
    """Extract thread ID from URL query parameters."""
    # Access st.query_params directly as an object, not as a function
    thread_id = st.query_params.get("thread_id", None)
    if thread_id:
        try:
            return UUID(thread_id)
        except ValueError:
            return None
    return None


def set_thread_id_in_url(thread_id: UUID) -> None:
    """Set thread ID in URL query parameters."""
    # Update st.query_params directly
    st.query_params["thread_id"] = str(thread_id)


def clear_thread_id_from_url() -> None:
    """Remove thread ID from URL query parameters."""
    # Delete from st.query_params if exists
    if "thread_id" in st.query_params:
        del st.query_params["thread_id"] 


def get_user_email() -> str:
    """Get the user email from the session state."""
    if hasattr(st, "experimental_user") and hasattr(st.experimental_user, "email"):
        user_id = st.experimental_user.email
        if user_id is not None and isinstance(user_id, str):
            return user_id

    # Fallback to a test user ID if running locally without authentication
    return "00000000-0000-0000-0000-000000000000"
