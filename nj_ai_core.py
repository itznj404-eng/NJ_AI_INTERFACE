import streamlit as st
import base64
import os
import tensorflow as tf
import datetime
from groq import Groq  
from youtube_search import YoutubeSearch
import json 

st.set_page_config(
    page_title="NJ AI",
    page_icon="FullLogo.jpg",
    layout="centered"
)

# --- 1. MEMORY FUNCTIONS ---
CHAT_DATA_FILE = "all_chats.json"

def save_all_chats(all_chats):
    with open(CHAT_DATA_FILE, "w") as f:
        json.dump(all_chats, f)

def load_all_chats():
    if os.path.exists(CHAT_DATA_FILE):
        with open(CHAT_DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {"Chat 1": []}
    return {"Chat 1": []}

# --- 2. PLAIN & FUNCTIONAL LAYOUT ---
st.markdown(
    """
    <style>
    /* 1. Centers the chat like ChatGPT */
    .block-container {
        max-width: 800px;
        padding-top: 2rem;
    }

    /* 2. FIX: Make header transparent so sidebar arrow is visible */
    header {
        background-color: rgba(0,0,0,0) !important;
        visibility: visible !important;
    }

    /* 3. Hide only the 'Made with Streamlit' footer and the 3-dot menu */
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}

    /* 4. Round the chat bubbles for a modern look */
    [data-testid="stChatMessage"] {
        border-radius: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# --- 3. BROWSER VOICE ---
# --- 3. AUTO-LANGUAGE BROWSER VOICE ---
def speak_in_browser(text):
    # Detect if Malayalam characters are in the text
    import re
    is_malayalam = bool(re.search(r'[\u0d00-\u0d7f]', text))
    lang_code = "ml-IN" if is_malayalam else "en-US"
    
    clean_text = text.replace("'", "\\'").replace("\n", " ")
    js_code = f"""
        <script>
        window.speechSynthesis.cancel(); // Stop any current speaking
        var msg = new SpeechSynthesisUtterance('{clean_text}');
        msg.lang = '{lang_code}';
        msg.rate = 0.9; // Malayalam sounds better slightly slower
        window.speechSynthesis.speak(msg);
        </script>
    """
    st.components.v1.html(js_code, height=0)

# --- 4. BRAIN SETUP ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "all_chats" not in st.session_state:
    st.session_state.all_chats = load_all_chats()

if "current_chat" not in st.session_state:
    st.session_state.current_chat = list(st.session_state.all_chats.keys())[-1]

if 'booted' not in st.session_state:
    speak_in_browser("System online.")
    st.session_state.booted = True

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown(" NJ AI Controls")
    
    # Button to create a new chat
    if st.button("➕ New Conversation", use_container_width=True):
        new_id = f"Chat {len(st.session_state.all_chats) + 1}"
        st.session_state.all_chats[new_id] = []
        st.session_state.current_chat = new_id
        save_all_chats(st.session_state.all_chats)
        st.rerun()

    st.divider()

    # Dropdown to see and switch between previous chats
    chat_list = list(st.session_state.all_chats.keys())
    if st.session_state.current_chat not in chat_list:
        st.session_state.current_chat = chat_list[-1]
        
    selected_chat = st.selectbox(
        "Your Chat History:", 
        chat_list, 
        index=chat_list.index(st.session_state.current_chat)
    )
    
    # Update current chat if changed in dropdown
    if selected_chat != st.session_state.current_chat:
        st.session_state.current_chat = selected_chat
        st.rerun()

    st.divider()

    # THE DELETE OPTION
    if st.button("🗑️ Delete This Chat", use_container_width=True, type="secondary"):
        if len(st.session_state.all_chats) > 1:
            # Remove the current chat from memory
            del st.session_state.all_chats[st.session_state.current_chat]
            # Set current chat to the one remaining
            st.session_state.current_chat = list(st.session_state.all_chats.keys())[0]
            save_all_chats(st.session_state.all_chats)
            st.rerun()
        else:
            st.warning("You can't delete the only chat left!")

# --- 6. CHAT INTERFACE ---
# --- 6. MODERN COMMAND CENTER ---
st.markdown("<h1 style='text-align: center;'>NJ AI</h1>", unsafe_allow_html=True)

# 1. Get the current chat name from session state
current_session = st.session_state.current_chat

# 2. IMPORTANT: Load the messages for THIS specific chat
# If the chat doesn't exist in memory yet, start it as an empty list
if current_session not in st.session_state.all_chats:
    st.session_state.all_chats[current_session] = []

messages = st.session_state.all_chats[current_session]

# 3. Render the history for the SELECTED chat
for i, message in enumerate(messages):
    with st.chat_message(message["role"]):
        if '<iframe' in message["content"]:
            st.markdown(message["content"], unsafe_allow_html=True)
        else:
            st.markdown(message["content"])
            # The 'Listen' button fix we did earlier
            if message["role"] == "assistant":
                unique_key = f"speak_{current_session}_{i}_{len(message['content'])}"
                if st.button("🔊", key=unique_key):
                    speak_in_browser(message["content"])

# 4. Chat Input
query = st.chat_input("Message NJ AI...")

if query:
    # Add user message to the SPECIFIC current session
    st.session_state.all_chats[current_session].append({"role": "user", "content": query})
    
    # ... (rest of your AI logic) ...
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        response_text = ""
        
        # Built-in Logic
        if "status" in query.lower():
            response_text = f"Systems nominal. Running TensorFlow {tf.__version__}."
            st.write(response_text)
        elif "time" in query.lower():
            response_text = f"The current time is {datetime.datetime.now().strftime('%I:%M %p')}."
            st.write(response_text)
        elif "play" in query.lower():
            song = query.lower().replace("play", "").strip()
            try:
                results = YoutubeSearch(song, max_results=1).to_dict()
                if results:
                    v_id = results[0]['id']
                    iframe = f'<iframe width="100%" height="315" src="https://www.youtube.com/embed/{v_id}?autoplay=1" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>'
                    st.markdown(iframe, unsafe_allow_html=True)
                    response_text = f"Now playing {results[0]['title']}. \n\n {iframe}"
                else:
                    response_text = "Sorry, I couldn't find that video."
            except:
                response_text = "There was an error accessing YouTube."

        # AI Groq Logic
        if not response_text:
            try:
                # Provide context from the last 5 messages
                history_chain = [{"role": "system", "content": "You are NJ AI, a high-performance assistant. Be concise and professional."}]
                for m in messages[-5:]:
                    if '<iframe' not in m["content"]:
                        history_chain.append({"role": m["role"], "content": m["content"]})
                
                history_chain.append({"role": "user", "content": query})

                chat_completion = client.chat.completions.create(
                    messages=history_chain,
                    model="llama-3.3-70b-versatile",
                )
                response_text = chat_completion.choices[0].message.content
                st.markdown(response_text)
            except Exception as e:
                response_text = "I'm having trouble connecting to my brain right now."
                st.error(f"Error: {e}")
        
        st.session_state.all_chats[current_session].append({"role": "assistant", "content": response_text})
        speak_in_browser(response_text)

    save_all_chats(st.session_state.all_chats)
    st.rerun()
