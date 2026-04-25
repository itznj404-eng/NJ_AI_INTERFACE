import streamlit as st
import base64
import os
import tensorflow as tf
import datetime
from groq import Groq  
from youtube_search import YoutubeSearch
import json 

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

# --- 2. BACKGROUND SETUP ---
# --- 2. PRO LAYOUT & BACKGROUND SETUP ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_pro_layout(bin_file):
    if os.path.exists(bin_file):
        bin_str = get_base64_of_bin_file(bin_file)
        page_bg_img = f'''
        <style>
        /* 1. Background */
        .stApp {{
            background-image: url("data:image/jpg;base64,{bin_str}");
            background-size: cover;
            background-attachment: fixed;
        }}

        /* 2. Main Chat Container (Centers the chat like ChatGPT) */
        .block-container {{
            max-width: 800px;
            padding-top: 2rem;
        }}

        /* 3. Chat Message Bubbles */
        [data-testid="stChatMessage"] {{
            background-color: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            margin-bottom: 10px;
            backdrop-filter: blur(5px);
        }}

        /* 4. Chat Input Bar */
        .stChatFloatingInputContainer {{
            background-color: rgba(0, 0, 0, 0.6) !important;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(15px);
            padding-bottom: 20px;
        }}

        /* 5. Clean Text styling */
        h1, h2, h3, p, span {{
            color: #ffffff !important;
            font-family: 'Inter', sans-serif;
        }}
        
        /* Hide Streamlit branding for a cleaner look */
        #MainMenu, footer, header {{visibility: hidden;}}
        </style>
        '''
        st.markdown(page_bg_img, unsafe_allow_html=True)

set_pro_layout('FullLogo.jpg')

# ... (Keep Sections 3, 4, and 5 the same) ...

# --- 6. MODERN COMMAND CENTER ---
st.markdown("<h1 style='text-align: center;'>NJ AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; opacity: 0.7;'>Advanced Intelligence Interface</p>", unsafe_allow_html=True)

current_session = st.session_state.current_chat
messages = st.session_state.all_chats[current_session]

# Wrapper for the chat history to keep it tidy
for i, message in enumerate(messages):
    with st.chat_message(message["role"]):
        if '<iframe' in message["content"]:
            st.markdown(message["content"], unsafe_allow_html=True)
        else:
            st.markdown(message["content"])
            if message["role"] == "assistant" and not '<iframe' in message["content"]:
                # Small, subtle listen button
                if st.button(f"🔊", key=f"lis_{current_session}_{i}"):
                    speak_in_browser(message["content"])

# Bottom Input (Standard Streamlit Chat Input looks like ChatGPT)
query = st.chat_input("Message NJ AI...")

# ... (Keep the rest of your 'if query:' logic the same) ...
# --- 3. BROWSER VOICE ---
def speak_in_browser(text):
    clean_text = text.replace("'", "\\'").replace("\n", " ")
    js_code = f"""
        <script>
        var msg = new SpeechSynthesisUtterance('{clean_text}');
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
    speak_in_browser("Core initialized. Standing by.")
    st.session_state.booted = True

# --- 5. SIDEBAR CONTROLS ---
with st.sidebar:
    st.title("NJ AI Controls")
    
    if st.button("➕ New Chat"):
        new_id = f"Chat {len(st.session_state.all_chats) + 1}"
        st.session_state.all_chats[new_id] = []
        st.session_state.current_chat = new_id
        save_all_chats(st.session_state.all_chats)
        st.rerun()

    st.divider()
    chat_list = list(st.session_state.all_chats.keys())
    st.session_state.current_chat = st.selectbox("Switch Topic:", chat_list, index=chat_list.index(st.session_state.current_chat))
    
    if st.button("🗑️ Delete Current Chat"):
        if len(st.session_state.all_chats) > 1:
            del st.session_state.all_chats[st.session_state.current_chat]
            st.session_state.current_chat = list(st.session_state.all_chats.keys())[-1]
            save_all_chats(st.session_state.all_chats)
            st.rerun()

# --- 6. COMMAND CENTER ---
st.title("NJ AI.")

current_session = st.session_state.current_chat
messages = st.session_state.all_chats[current_session]

# Display History
for i, message in enumerate(messages):
    with st.chat_message(message["role"]):
        if '<iframe' in message["content"]:
            st.markdown(message["content"], unsafe_allow_html=True)
        else:
            st.markdown(message["content"])
            if message["role"] == "assistant" and not '<iframe' in message["content"]:
                if st.button(f"🔊 Listen", key=f"lis_{current_session}_{i}"):
                    speak_in_browser(message["content"])

query = st.chat_input("What do you want to hear...")

if query:
    st.session_state.all_chats[current_session].append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        response_text = ""
        
        # Commands
        if "status" in query.lower():
            response_text = f"TensorFlow active (v{tf.__version__}). System green."
            st.write(response_text)
        elif "time" in query.lower():
            response_text = f"It is {datetime.datetime.now().strftime('%I:%M %p')}."
            st.write(response_text)
        elif "play" in query.lower():
            song = query.lower().replace("play", "").strip()
            try:
                results = YoutubeSearch(song, max_results=1).to_dict()
                if results:
                    v_id = results[0]['id']
                    iframe = f'<iframe width="100%" height="315" src="https://www.youtube.com/embed/{v_id}?autoplay=1" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>'
                    st.markdown(iframe, unsafe_allow_html=True)
                    response_text = f"Playing {results[0]['title']}. \n\n {iframe}"
                else:
                    response_text = "Not found."
            except:
                response_text = "Search error."

        # --- THE CONNECTED BRAIN ---
        if not response_text:
            try:
                # Building context history
                history_chain = [{"role": "system", "content": "You are a helpful AI. Remember the context of this conversation."}]
                for m in messages[-6:]:
                    content = m["content"] if '<iframe' not in m["content"] else "User played music."
                    history_chain.append({"role": m["role"], "content": content})
                
                history_chain.append({"role": "user", "content": query})

                chat_completion = client.chat.completions.create(
                    messages=history_chain,
                    model="llama-3.3-70b-versatile",
                )
                response_text = chat_completion.choices[0].message.content
                st.markdown(response_text)
            except Exception as e:
                response_text = f"Brain Error: {e}"
                st.error(response_text)
        
        st.session_state.all_chats[current_session].append({"role": "assistant", "content": response_text})
        speak_in_browser(response_text)

    save_all_chats(st.session_state.all_chats)
    st.rerun()

    #  Save to Permanent File
    save_all_chats(st.session_state.all_chats)
    st.rerun()
