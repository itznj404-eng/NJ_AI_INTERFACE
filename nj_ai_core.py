import base64
import datetime
import json
import os
import re
import streamlit as st
import tensorflow as tf
from groq import Groq
from youtube_search import YoutubeSearch

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="NJ AI",
    page_icon="FullLogo.ico",
    layout="centered"
)

# --- PWA MANIFEST INJECTION ---
st.markdown(
    """
    <script>
    document.title = "NJ AI";
    const manifest = {
        "name": "NJ AI",
        "short_name": "NJ AI",
        "icons": [{ "src": "FullLogo.ico", "sizes": "192x192 256x256 512x512", "type": "image/x-icon" }],
        "start_url": ".",
        "display": "standalone",
        "theme_color": "#000000",
        "background_color": "#000000"
    };
    const stringManifest = JSON.stringify(manifest);
    const blob = new Blob([stringManifest], {type: 'application/json'});
    const manifestURL = URL.createObjectURL(blob);
    
    var oldManifest = document.querySelector('link[rel="manifest"]');
    if (oldManifest) {
        oldManifest.setAttribute('href', manifestURL);
    } else {
        var link = document.createElement('link');
        link.rel = 'manifest';
        link.href = manifestURL;
        document.head.appendChild(link);
    }
    </script>
    """,
    unsafe_allow_html=True
)

# --- CSS STYLING ---
st.markdown(
    """
    <style>
    .block-container {
        max-width: 800px;
        padding-top: 2rem;
    }
    header {
        background-color: rgba(0,0,0,0) !important;
        visibility: visible !important;
    }
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    [data-testid="stChatMessage"] {
        border-radius: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 1. PERSISTENCE MEMORY FUNCTIONS ---
CHAT_DATA_FILE = "all_chats.json"

def save_all_chats(all_chats):
    with open(CHAT_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chats, f, indent=2)

def load_all_chats():
    if os.path.exists(CHAT_DATA_FILE):
        try:
            with open(CHAT_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"Chat 1": []}
    return {"Chat 1": []}

# --- 2. BROWSER VOICE FUNCTION ---
def speak_in_browser(text):
    # Remove HTML tags if present before sending to TTS
    clean_text_no_html = re.sub(r'<[^<]+?>', '', text)
    
    is_malayalam = bool(re.search(r'[\u0d00-\u0d7f]', clean_text_no_html))
    lang_code = "ml-IN" if is_malayalam else "en-US"
    
    # Safe JSON string encoding for JS execution
    safe_js_text = json.dumps(clean_text_no_html)
    
    js_code = f"""
        <script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance({safe_js_text});
        msg.lang = '{lang_code}';
        msg.rate = 0.9;
        window.speechSynthesis.speak(msg);
        </script>
    """
    st.components.v1.html(js_code, height=0)

# --- 3. SESSION INITIALIZATION ---
if "all_chats" not in st.session_state:
    st.session_state.all_chats = load_all_chats()

if "current_chat" not in st.session_state:
    st.session_state.current_chat = list(st.session_state.all_chats.keys())[-1]

# >>> THIS IS THE API KEY LINE <<<
# --- 4. BRAIN SETUP ---
client = Groq(api_key=st.secrets.get("GROQ_API_KEY", ""))
if 'booted' not in st.session_state:
    speak_in_browser("System online.")
    st.session_state.booted = True

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ NJ AI Controls")
    
    if st.button("➕ New Conversation", use_container_width=True):
        new_id = f"Chat {len(st.session_state.all_chats) + 1}"
        st.session_state.all_chats[new_id] = []
        st.session_state.current_chat = new_id
        save_all_chats(st.session_state.all_chats)
        st.rerun()

    st.divider()

    chat_list = list(st.session_state.all_chats.keys())
    if st.session_state.current_chat not in chat_list:
        st.session_state.current_chat = chat_list[-1]
        
    selected_chat = st.selectbox(
        "Your Chat History:", 
        chat_list, 
        index=chat_list.index(st.session_state.current_chat)
    )
    
    if selected_chat != st.session_state.current_chat:
        st.session_state.current_chat = selected_chat
        st.rerun()

    st.divider()

    if st.button("🗑️ Delete This Chat", use_container_width=True, type="secondary"):
        if len(st.session_state.all_chats) > 1:
            del st.session_state.all_chats[st.session_state.current_chat]
            st.session_state.current_chat = list(st.session_state.all_chats.keys())[0]
            save_all_chats(st.session_state.all_chats)
            st.rerun()
        else:
            st.warning("You can't delete the only remaining chat!")

# --- 5. MAIN CHAT INTERFACE ---
st.markdown("<h1 style='text-align: center;'>NJ AI</h1>", unsafe_allow_html=True)

current_session = st.session_state.current_chat
if current_session not in st.session_state.all_chats:
    st.session_state.all_chats[current_session] = []

messages = st.session_state.all_chats[current_session]

# Render history
for i, message in enumerate(messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)
        
        if message["role"] == "assistant":
            unique_key = f"speak_{current_session}_{i}"
            if st.button("🔊", key=unique_key):
                speak_in_browser(message["content"])

# --- 6. USER INPUT & RESPONSE LOGIC ---
query = st.chat_input("Message NJ AI...")

if query:
    # 1. Store and display user input
    st.session_state.all_chats[current_session].append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # 2. Process Assistant Response
    with st.chat_message("assistant"):
        response_text = ""
        q_lower = query.lower().strip()

        # Command: Status
        if "status" in q_lower:
            response_text = f"Systems nominal. Running TensorFlow version `{tf.__version__}`."
            st.markdown(response_text)

        # Command: Time
        elif "time" in q_lower:
            now_str = datetime.datetime.now().strftime('%I:%M %p')
            response_text = f"The current time is **{now_str}**."
            st.markdown(response_text)

        # Command: YouTube Play
        elif q_lower.startswith("play "):
            song = q_lower.replace("play", "", 1).strip()
            try:
                results = YoutubeSearch(song, max_results=1).to_dict()
                if results:
                    v_id = results[0]['id']
                    v_title = results[0]['title']
                    iframe = f'<iframe width="100%" height="315" src="https://www.youtube.com/embed/{v_id}?autoplay=1" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>'
                    response_text = f"Now playing **{v_title}**:\n\n{iframe}"
                    st.markdown(response_text, unsafe_allow_html=True)
                else:
                    response_text = "Sorry, I couldn't find any video for that search."
                    st.markdown(response_text)
            except Exception as e:
                response_text = f"There was an error querying YouTube: `{e}`"
                st.markdown(response_text)

        # Default: Fallback to Groq Llama 3
        else:
            try:
                history_chain = [{"role": "system", "content": "You are NJ AI, a high-performance assistant. Be concise and professional."}]
                
                # Context limit (last 5 messages)
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
                response_text = f"I couldn't reach the backend LLM service."
                st.error(f"Error: {e}")

        # 3. Store assistant response
        st.session_state.all_chats[current_session].append({"role": "assistant", "content": response_text})
        save_all_chats(st.session_state.all_chats)
        
        # Trigger TTS for immediate feedback
        speak_in_browser(response_text)
