import streamlit as st 
import requests
import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin import firestore
import datetime

st.set_page_config(page_title="MovieRag Agentic System")

st.title("MovieRag Agentic System")

if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("firebase.json")
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase başlatma hatası: {e}")
        st.stop()

db = firestore.client()

def save_chat_to_firestore(username, chat_id, messages):
    try:
        
        storable_messages = []
        for msg in messages:
            storable_msg = msg.copy()
            storable_messages.append(storable_msg)
        
        doc_ref = db.collection("users").document(username).collection("chats").document(chat_id)
        doc_ref.set({"messages": storable_messages, "created_at": chat_id})
    except Exception as e:
        st.error(f"Sohbet kaydedilirken hata: {e}")

def load_user_chats(username):
    try:
        chat_histories = {}
        chats_ref = db.collection("users").document(username).collection("chats")
        for chat_doc in chats_ref.stream():
            chat_histories[chat_doc.id] = chat_doc.to_dict().get("messages", [])
        return chat_histories
    except Exception as e:
        st.error(f"Sohbetler yüklenirken hata: {e}")
        return {}
    
def delete_chat_from_firestore(username, chat_id):
    try:
        doc_ref = db.collection("users").document(username).collection("chats").document(chat_id)
        doc_ref.delete()
        return True
    except Exception as e:
        st.error(f"Sohbet silinirken hata: {e}")
        return False



if "username" in st.session_state:
    username = st.session_state["username"]
    st.session_state["chat_histories"] = load_user_chats(username)
    st.subheader(f"Hello {username}! Which movie do you want to watch today?")
else:
    st.warning("Lütfen giriş yapın.")
    st.switch_page("pages/login.py")

if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "chat_histories" not in st.session_state:
    st.session_state["chat_histories"] = {}
if "current_chat" not in st.session_state:
    st.session_state["current_chat"] = None
if "confirm_delete" not in st.session_state:
    st.session_state["confirm_delete"] = None
    
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        
def save_session_state(mode,recommendations=None, emotion_response=None):
    if mode=="emotion":
        st.session_state.messages.append({"role": "assistant", "content": emotion_response})
    elif mode=="category":
        for rec in recommendations:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"**Title:** {rec.get('Title', 'N/A')}\n"
                           f"**Director:** {rec.get('Director', 'N/A')}\n"
                           f"**Star Cast:** {', '.join(rec.get('Star Cast', []))}\n"
                           f"**Genre:** {rec.get('Genre', 'N/A')}\n"
                           f"**Overview:** {rec.get('Overview', 'N/A')}\n"
                           f"**Reason:** {rec.get('Reason', 'N/A')}\n"
            })
            if rec.get("Image URL"):
                st.session_state.messages[-1]["content"] += f"\n![Image]({rec['Image URL']})"
                
st.sidebar.title("Sohbet Geçmişi")

button_container = st.sidebar.container()
col1, col2 = button_container.columns([1, 1])

with col1:
    new_chat_button = st.button("Yeni Sohbet", use_container_width=True)
with col2:
    logout_button = st.button("Çıkış Yap", use_container_width=True)


if new_chat_button:
    new_chat_id = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state["chat_histories"][new_chat_id] = []
    st.session_state["current_chat"] = new_chat_id
    st.session_state["messages"] = []
    
    save_chat_to_firestore(username, new_chat_id, [])
    st.rerun()


if logout_button:
    st.session_state.clear()
    st.switch_page("pages/login.py")


sorted_chat_histories = sorted(
    st.session_state["chat_histories"].items(),
    key=lambda x: x[0],
    reverse=True
)


for chat_id, chat_history in sorted_chat_histories:
    with st.sidebar.container():
        try:
            chat_date = datetime.datetime.strptime(chat_id, "%Y-%m-%d %H:%M:%S")
            display_date = chat_date.strftime("%d %b %Y, %H:%M")
        except ValueError:
            display_date = chat_id

        user_query_preview = (
            chat_history[0]["content"]
            if chat_history and isinstance(chat_history[0]["content"], str)
            else f"Sohbet ({display_date})"
        )
        if len(user_query_preview) > 30:
            user_query_preview = user_query_preview[:27] + "..."

        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(f"{user_query_preview} ({display_date})", key=chat_id):
                st.session_state["current_chat"] = chat_id
                st.session_state["messages"] = chat_history
                st.session_state["confirm_delete"] = None  
                st.rerun()

        with col2:
            if st.button("🗑️", key=f"delete_{chat_id}"):
                st.session_state["confirm_delete"] = chat_id
                st.rerun()

    if st.session_state["confirm_delete"] == chat_id:
        with st.sidebar.container():
            st.warning(f"'{user_query_preview}' sohbetini silmek istediğinize emin misiniz?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Evet, Sil", key=f"confirm_delete_{chat_id}"):
                    if delete_chat_from_firestore(username, chat_id):
                        st.session_state["chat_histories"].pop(chat_id, None)
                        
                        if st.session_state["current_chat"] == chat_id:
                            st.session_state["current_chat"] = None
                            st.session_state["messages"] = []
                        
                        st.session_state["chat_histories"] = load_user_chats(username)
                        
                        st.session_state["confirm_delete"] = None
                        
                        st.success("Sohbet silindi.")
                        st.rerun()
            
            with col2:
                if st.button("İptal", key=f"cancel_delete_{chat_id}"):
                    st.session_state["confirm_delete"] = None
                    st.rerun()
    

user_query= st.chat_input("Enter your query here:")
if user_query:
    with st.chat_message("user"):
        st.write(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    response = requests.get(
            f"http://localhost:8000/process_query/{user_query}"
           
        )
        
    if response.status_code == 200:
        data = response.json()
        mode = data.get("mode")
        

            
            
        if mode == "category":
                recommendations = data.get("recommendations", [])
                for rec in recommendations:  
                        st.write(f"**Title:** {rec.get('Title', 'N/A')}")
                        st.write(f"**Director:** {rec.get('Director', 'N/A')}")
                        st.write(f"**Star Cast:** {', '.join(rec.get('Star Cast', []))}")
                        st.write(f"**Genre:** {rec.get('Genre', 'N/A')}")
                        st.write(f"**Overview:** {rec.get('Overview', 'N/A')}")
                        st.write(f"**Reason:** {rec.get('Reason', 'N/A')}")
                        if rec.get("Image URL"):
                            st.image(rec["Image URL"],caption=rec.get("Title", "N/A"), use_column_width=True)
        elif mode == "emotion":
            emotion_response = data.get("emotion_response", "")
            with st.chat_message("assistant"):
                st.write(emotion_response)
                            
    else:
        st.error(f"Error: {response.status_code} - {response.text}")

    
    save_session_state(
        mode,
        recommendations=data.get("recommendations", []), 
        emotion_response=data.get("emotion_response", "")
    )
    
    if st.session_state["current_chat"]:
            st.session_state["chat_histories"][st.session_state["current_chat"]] = st.session_state["messages"]
            save_chat_to_firestore(username, st.session_state["current_chat"], st.session_state["messages"])
    else:
            
            new_chat_id = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state["current_chat"] = new_chat_id
            st.session_state["chat_histories"][new_chat_id] = st.session_state["messages"]
            save_chat_to_firestore(username, new_chat_id, st.session_state["messages"])
    
    