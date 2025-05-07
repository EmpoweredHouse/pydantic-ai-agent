from __future__ import annotations

import asyncio
import uuid
import json
from typing import Any, Awaitable, TypeVar, Callable

import streamlit as st
from pydantic import BaseModel

# Import environment setup first
from src.client._env import *  # noqa: F403

# Import API client
from src.client.utls import (
    get_user_email, 
    get_api_client, 
    set_thread_id_in_url,
    get_thread_id_from_url
)

# Import models
from src.service.models.api.internal import AgentType
from src.service.models.api.message_models import MessageResponse
from src.agents.bank_support import SupportOutput

# Import stream models
from src.service.models.api.stream_models import (
    TextDeltaChunk,
    DoneChunk,
    ErrorChunk,
)

# Agent type descriptions with valid values
AGENT_TYPES = [agent.value for agent in AgentType]

# Simple message model for UI display
class UIMessage(BaseModel):
    """Simple message class for UI display"""
    role: str
    content: str


def convert_to_ui_message(message: MessageResponse) -> UIMessage:
    """Convert an API message model to a UI message."""
    return UIMessage(
        role=message.role,
        content=message.content
    )

# Helper for running async functions in Streamlit
T = TypeVar("T")

def run_async(func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
    """Run an async function from Streamlit."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(func(*args, **kwargs))
    finally:
        loop.close()


def _initialize_session_state() -> None:
    """Initialize session state variables for the chat interface."""
    # Initialize messages list if it doesn't exist
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "current_thread_id" not in st.session_state:
        st.session_state.current_thread_id = None

    if "threads" not in st.session_state:
        st.session_state.threads = []

    if "disabled" not in st.session_state:
        st.session_state.disabled = False


async def create_new_thread() -> None:
    """Create a new thread and update the URL."""
    try:    
        api_client = get_api_client()
        thread = await api_client.create_thread(
            agent_type=AgentType.BANK_SUPPORT,
            user_email=get_user_email()
        )
        
        # Set the thread ID in session state and URL
        st.session_state.current_thread_id = thread.id
        set_thread_id_in_url(thread.id)
        
        # Clear existing messages
        st.session_state.messages = []
        
        # Refresh threads list
        await load_threads()
        
        st.rerun()
    except Exception as e:
        st.error(f"Failed to create thread: {str(e)}")



async def load_thread(thread_id: uuid.UUID) -> None:
    """Load a specific thread with its messages using standard API models."""
    try:
        # Get thread data using the standard API model
        api_client = get_api_client()
        thread = await api_client.get_thread(
            thread_id=thread_id,
            user_email=get_user_email()
        )
        
        # Set the thread ID in session state and URL
        st.session_state.current_thread_id = thread.id
        set_thread_id_in_url(thread.id)
        
        # Convert API message models to UI messages
        st.session_state.messages = [convert_to_ui_message(msg) for msg in thread.messages]
        
        st.rerun()
    except Exception as e:
        st.error(f"Failed to load thread: {str(e)}")
        # Continue without messages
        st.session_state.current_thread_id = thread_id
        set_thread_id_in_url(thread_id)
        st.session_state.messages = []


async def load_threads() -> None:
    """Load all threads for the current user."""
    try:
        api_client = get_api_client()
        threads = await api_client.get_threads(user_email=get_user_email())
        st.session_state.threads = threads
    except Exception as e:
        st.error(f"Failed to load threads: {str(e)}")


def _disable_chat_input() -> None:
    """Disable chat input during processing."""
    st.session_state.disabled = True


def _enable_chat_input() -> None:
    """Enable chat input and trigger rerun."""
    st.session_state.disabled = False
    st.rerun()


async def stream_agent_response(thread_id: uuid.UUID, query: str) -> None:
    """Stream the agent response and update a single message bubble."""
    api_client = get_api_client()
    
    # Create a single message container that we'll update
    with st.chat_message("assistant"):
        # Use a single empty container that we'll keep updating
        message_container = st.empty()
        message_container.markdown("_Thinking..._")
        
        # Track the full response to update the container with
        response_json = None

        # Get the stream generator
        stream_generator = api_client.stream_agent_query(
            thread_id=thread_id,
            query=query,
            user_email=get_user_email()
        )
        
        try:
            async for chunk in stream_generator:
                if isinstance(chunk, TextDeltaChunk) and chunk.token:
                    response_json = json.loads(chunk.token)

                    # Update the same container with the growing response
                    message_container.markdown(response_json)
                
                elif isinstance(chunk, DoneChunk):
                    # Add the assistant's response to our messages array
                    assistant_msg = UIMessage(role="assistant", content=str(response_json))
                    st.session_state.messages.append(assistant_msg)

                elif isinstance(chunk, ErrorChunk):
                    # Handle error
                    message_container.markdown(f"_Error: {chunk.error}_")                    
                    break
                
                    
            # Ensure generator is properly closed
            if hasattr(stream_generator, 'aclose'):
                await stream_generator.aclose()
                
        except Exception as e:
            message_container.markdown(f"_Error: {str(e)}_")


def run_agent_sync(query: str) -> None:
    """Process user query and stream response."""
    # Create and add user message
    user_msg = UIMessage(role="user", content=query)
    
    # Add to session state
    st.session_state.messages.append(user_msg)
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(query)
        
    try:
        # Ensure we have a thread
        if not st.session_state.current_thread_id:
            run_async(create_new_thread)
        
        # Process the query and stream the response
        run_async(stream_agent_response, st.session_state.current_thread_id, query)
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    finally:
        # Re-enable chat input even if errors occur
        _enable_chat_input()



def render_threads_sidebar() -> None:
    """Render a sidebar with thread management options."""
    # Render menu (login, etc.) and sidebar components
    with st.sidebar:
        # Thread management section
        st.subheader("Your Conversations")
    
        # Add the New Thread button directly after the agent type selector
        if st.button("➕ New Thread", key="new_thread"):
            run_async(create_new_thread)

        # List of existing threads
        if not st.session_state.threads:
            st.info("No threads found. Select an agent type above and click 'New Thread' to start a conversation.")
        else:
            st.write("Click on a thread to load it:")
            for thread in st.session_state.threads:
                # Format the created_at date/time
                created_at = thread.created_at
                
                # Create a button for each thread
                agent_type = thread.agent_type
                thread_label = f"{created_at} - {agent_type}"
                
                # Check if this is the active thread
                is_active = thread.id == st.session_state.current_thread_id
                
                # Use different styling for active thread
                if is_active:
                    # Display active thread with highlight
                    st.markdown(f"""
                    <div style="background-color: #0078ff; color: white; padding: 10px; border-radius: 5px; margin-bottom: 5px;">
                        <strong> 👉 {thread_label}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Regular button for inactive threads
                    if st.button(thread_label, key=f"thread_{thread.id}"):
                        run_async(load_thread, thread.id)


def display_messages() -> None:
    """Display all messages in the current thread."""
    for msg in st.session_state.messages:
        with st.chat_message(msg.role):
            st.markdown(str(msg.content))



def main() -> None:
    """Main application entry point."""
    # Set page config
    st.set_page_config(
        page_title="Bank Support Agent",
        page_icon="💬",
    )

    # Initialize session state
    _initialize_session_state()

    # Main interface
    with st.empty():
        st.header("Bank Support Agent")
        st.markdown("Ask questions ...")

    # Check for thread_id in URL
    thread_id_from_url = get_thread_id_from_url()
    if thread_id_from_url and thread_id_from_url != st.session_state.current_thread_id:
        run_async(load_thread, thread_id_from_url)

    # Load threads for sidebar
    if not st.session_state.threads:
        run_async(load_threads)

    # Render the threads sidebar
    render_threads_sidebar()

    # Display messages in the current thread
    display_messages()

    # Chat input at the bottom
    if user_query := st.chat_input(
        "What would you like to know about?",
        disabled=st.session_state.disabled,
        on_submit=_disable_chat_input,
    ):
        run_agent_sync(user_query)


if __name__ == "__main__":
    main()