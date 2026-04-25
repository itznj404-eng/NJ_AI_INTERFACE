 
import streamlit as st
import base64
import webbrowser
import pyttsx3
import os
import tensorflow as tf
import datetime
from groq import Groq  
from youtube_search import YoutubeSearch
import json 

#   MEMORY FUNCTIONS
CHAT_DATA_FILE = "all_chats.json"

def save_all_chats(all_chats):
    with open(CHAT_DATA_FILE, "w") as f:
        json.dump(all_chats, f)

def load_all_chats():
    if os.path.exists(CHAT_DATA_FILE):
        with open(CHAT_DATA_FILE, "r") as f:
            return json.load(f)
    return {"Chat 1": []} # Default starting point

# 1.Background
# --- 2. CUSTOM THEMED BACKGROUND ---
def set_custom_bg(bin_file):
    if os.path.exists(bin_file):
        bin_str = get_base64_of_bin_file(bin_file)
        page_bg_img = f'''
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{bin_str}");
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
        }}

        /* Making text bright and readable against the dark purple/blue */
        h1, h2, h3, p, span, .stMarkdown {{
            color: #ffffff !important;
            text-shadow: 2px 2px 8px #000000;
        }}

        /* Adding a "Glow" effect to the NJ AI title */
        .stTitle {{
            color: #d1b3ff !important;
            text-shadow: 0px 0px 15px #9370db;
        }}

        /* Sidebar and Input Glassmorphism */
        [data-testid="stSidebar"], .stChatFloatingInputContainer {{
            background-color: rgba(10, 10, 20, 0.8) !important;
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        </style>
        '''
        st.markdown(page_bg_img, unsafe_allow_html=True)

# Call the function with your new file name
set_custom_bg('FullLogo.jpg')

# 2. VOICE 
def speak(text):
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 180)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"Voice Error: {e}")

#  3. THE BRAIN & MEMORY SETUP
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if 'booted' not in st.session_state:
    speak("Core initialized. Standing by.")
    st.session_state.booted = True

# 4. THE SIDEBAR 
with st.sidebar:
    st.title(" NJ AI controls")
    
    # 1. Load all history
    if "all_chats" not in st.session_state:
        st.session_state.all_chats = load_all_chats()
    
    # 2. "New Chat" Button
    if st.button("➕ New Chat"):
        new_chat_id = f"Chat {len(st.session_state.all_chats) + 1}"
        st.session_state.all_chats[new_chat_id] = []
        st.session_state.current_chat = new_chat_id
        save_all_chats(st.session_state.all_chats)
        st.rerun()

    st.divider()

    # 3. List of Previous Chats
    chat_list = list(st.session_state.all_chats.keys())
    # This dropdown acts like clicking "Previous Chats"
    st.session_state.current_chat = st.selectbox("Switch Topic:", chat_list, index=len(chat_list)-1)
    
    # 4. Delete current chat
    if st.button(" Delete Current Chat"):
        if len(st.session_state.all_chats) > 1:
            del st.session_state.all_chats[st.session_state.current_chat]
            save_all_chats(st.session_state.all_chats)
            st.rerun()

# 5.  COMMAND CENTER 

st.title("NJ AI.")

current_session = st.session_state.current_chat
messages = st.session_state.all_chats[current_session]

for message in messages:
    with st.chat_message(message["role"]):
        # This checks if there is a YouTube player saved in the history
        if '<iframe' in message["content"]:
            st.markdown(message["content"], unsafe_allow_html=True)
        else:
            st.markdown(message["content"])

query = st.chat_input("what do you want to hear...")

if query:
    st.session_state.all_chats[current_session].append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        response_text = ""
        
        # Check Status
        if "status" in query.lower():
            response_text = f"TensorFlow is active (v{tf.__version__}). System status is green."
            st.write(response_text)
            speak("System status is green.")

        # Check Time
        elif "time" in query.lower():
            now = datetime.datetime.now().strftime("%I:%M %p")
            response_text = f"The current time is {now}."
            st.write(response_text)
            speak(response_text)

        # YouTube / Play Songs
        elif "play" in query.lower():
            song = query.lower().replace("play", "").strip()
            st.info(f"Searching for {song}...")
            try:
                results = YoutubeSearch(song, max_results=1).to_dict()
                if results:
                    video_id = results[0]['id']
                    video_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1"
                    
                    # Create the player code
                    iframe_code = f'<iframe width="100%" height="315" src="{video_url}" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>'
                    
                    # Show it on screen
                    st.markdown(iframe_code, unsafe_allow_html=True)
                    
                    response_text = f"Now playing {results[0]['title']}. \n\n {iframe_code}"
                    speak(f"Playing {song}")
                else:
                    response_text = "I couldn't find that song on YouTube."
                    st.error(response_text)
            except Exception as e:
                response_text = f"Music Search Error: {e}"
                st.error(response_text)

        # Groq Brain 
        if not response_text:
            try:
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "system", "content": "You are a helpful AI assistant."},
                              {"role": "user", "content": query}],
                    model="llama-3.3-70b-versatile",
                )
                response_text = chat_completion.choices[0].message.content
                st.markdown(response_text)
                speak("Response generated.")
            except Exception as e:
                response_text = f"Brain Error: {e}"
                st.error(response_text)
        
        # 3. Assistant History
        st.session_state.all_chats[current_session].append({"role": "assistant", "content": response_text})

    #  Save to Permanent File
    save_all_chats(st.session_state.all_chats)
    st.rerun()
