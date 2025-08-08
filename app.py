from io import BytesIO
import streamlit as st
from audiorecorder import audiorecorder  # type: ignore
from dotenv import dotenv_values
from hashlib import md5
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from datetime import datetime
import time

# Main app configuration - MUST BE FIRST!
st.set_page_config(
    page_title="Audio Notatki",
    page_icon="🎤",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main container styling */
    .main > div {
        padding-top: 2rem;
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    
    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .header-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
        font-weight: 300;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: #f8fafc;
        padding: 8px;
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        padding: 0px 24px;
        background-color: transparent;
        border-radius: 8px;
        color: #64748b;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    /* Note container styling */
    .note-container {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    
    .note-container:hover {
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        border-color: #667eea;
    }
    
    .note-text {
        font-size: 1rem;
        line-height: 1.6;
        color: #334155;
        margin-bottom: 1rem;
    }
    
    .note-score {
        display: inline-block;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .note-timestamp {
        color: #64748b;
        font-size: 0.875rem;
        font-style: italic;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(102, 126, 234, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Audio player styling */
    .stAudio {
        border-radius: 12px;
        overflow: hidden;
        margin: 1rem 0;
    }
    
    /* Success message styling */
    .success-message {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        font-weight: 600;
        margin: 1rem 0;
    }
    
    /* Empty state styling */
    .empty-state {
        text-align: center;
        padding: 3rem 1rem;
        color: #64748b;
    }
    
    .empty-state-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    /* Loading animation */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Stats cards */
    .stats-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .stats-card {
        flex: 1;
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .stats-number {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 0.5rem;
    }
    
    .stats-label {
        color: #64748b;
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

env = dotenv_values(".env")

if "QDRANT_URL" in st.secrets:
    env['QDRANT_URL'] = st.secrets['QDRANT_URL']
if "QDRANT_API_KEY" in st.secrets:
    env['QDRANT_API_KEY'] = st.secrets['QDRANT_API_KEY']

EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIM = 3072
AUDIO_TRANSCRIBE_MODEL = "whisper-1"
QDRANT_COLLECTION_NAME = "notes"

def get_openai_client():
    return OpenAI(api_key=st.session_state["openai_api_key"])

def transcribe_audio(audio_bytes):
    openai_client = get_openai_client()
    audio_file = BytesIO(audio_bytes)
    audio_file.name = "audio.mp3"
    transcript = openai_client.audio.transcriptions.create(
        file=audio_file,
        model=AUDIO_TRANSCRIBE_MODEL,
        response_format="verbose_json",
    )
    return transcript.text

@st.cache_resource
def get_qdrant_client():
    return QdrantClient(
        url=env["QDRANT_URL"],
        api_key=env["QDRANT_API_KEY"],
    )

def assure_db_collection_exists():
    qdrant_client = get_qdrant_client()
    if not qdrant_client.collection_exists(QDRANT_COLLECTION_NAME):
        print("Tworzę kolekcję")
        qdrant_client.create_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_DIM,
                distance=Distance.COSINE,
            ),
        )
    else:
        print("Kolekcja już istnieje")

def get_embeddings(text):
    openai_client = get_openai_client()
    result = openai_client.embeddings.create(
        input=[text],
        model=EMBEDDING_MODEL,
        dimensions=EMBEDDING_DIM,
    )
    return result.data[0].embedding

def add_note_to_db(note_text):
    qdrant_client = get_qdrant_client()
    points_count = qdrant_client.count(
        collection_name=QDRANT_COLLECTION_NAME,
        exact=True,
    )
    qdrant_client.upsert(
        collection_name=QDRANT_COLLECTION_NAME,
        points=[
            PointStruct(
                id=points_count.count + 1,
                vector=get_embeddings(text=note_text),
                payload={
                    "text": note_text,
                    "timestamp": datetime.now().isoformat(),
                },
            )
        ]
    )

def list_notes_from_db(query=None):
    qdrant_client = get_qdrant_client()
    if not query:
        notes = qdrant_client.scroll(collection_name=QDRANT_COLLECTION_NAME, limit=10)[0]
        result = []
        for note in notes:
            result.append({
                "text": note.payload["text"],
                "score": None,
                "timestamp": note.payload.get("timestamp", ""),
            })
        return result
    else:
        notes = qdrant_client.search(
            collection_name=QDRANT_COLLECTION_NAME,
            query_vector=get_embeddings(text=query),
            limit=10,
        )
        result = []
        for note in notes:
            result.append({
                "text": note.payload["text"],
                "score": note.score,
                "timestamp": note.payload.get("timestamp", ""),
            })
        return result

def get_notes_count():
    try:
        qdrant_client = get_qdrant_client()
        points_count = qdrant_client.count(
            collection_name=QDRANT_COLLECTION_NAME,
            exact=True,
        )
        return points_count.count
    except:
        return 0

# Header
st.markdown("""
<div class="header-container">
    <div class="header-title">🎤 Audio Notatki</div>
    <div class="header-subtitle">Nagrywaj, transkrybuj i wyszukuj swoje notatki głosowe</div>
</div>
""", unsafe_allow_html=True)

# API Key handling
if not st.session_state.get("openai_api_key"):
    if "OPENAI_API_KEY" in env:
        st.session_state["openai_api_key"] = env["OPENAI_API_KEY"]
    else:
        st.markdown("""
        <div style="background: #fee2e2; border: 1px solid #fecaca; color: #dc2626; padding: 1rem; border-radius: 8px; text-align: center;">
            🔑 Dodaj swój klucz API OpenAI aby móc korzystać z tej aplikacji
        </div>
        """, unsafe_allow_html=True)
        st.session_state["openai_api_key"] = st.text_input("Klucz API", type="password", placeholder="sk-...")
        if st.session_state["openai_api_key"]:
            st.rerun()

if not st.session_state.get("openai_api_key"):
    st.stop()

# Initialize session state
if "note_audio_bytes_md5" not in st.session_state:
    st.session_state["note_audio_bytes_md5"] = None
if "note_audio_bytes" not in st.session_state:
    st.session_state["note_audio_bytes"] = None
if "note_text" not in st.session_state:
    st.session_state["note_text"] = ""
if "note_audio_text" not in st.session_state:
    st.session_state["note_audio_text"] = ""

# Ensure database exists
assure_db_collection_exists()

# Stats section
notes_count = get_notes_count()
st.markdown(f"""
<div class="stats-container">
    <div class="stats-card">
        <div class="stats-number">{notes_count}</div>
        <div class="stats-label">Zapisanych notatek</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Main tabs
add_tab, search_tab = st.tabs(["📝 Dodaj notatkę", "🔍 Wyszukaj notatkę"])

with add_tab:
    st.markdown("### Nagraj swoją notatkę")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        note_audio = audiorecorder(
            start_prompt="🎙️ Rozpocznij nagrywanie",
            stop_prompt="⏹️ Zatrzymaj nagrywanie",
            show_visualizer=True,
        )
    
    if note_audio:
        audio = BytesIO()
        note_audio.export(audio, format="mp3")
        st.session_state["note_audio_bytes"] = audio.getvalue()
        current_md5 = md5(st.session_state["note_audio_bytes"]).hexdigest()
        
        if st.session_state["note_audio_bytes_md5"] != current_md5:
            st.session_state["note_audio_text"] = ""
            st.session_state["note_text"] = ""
            st.session_state["note_audio_bytes_md5"] = current_md5

        st.markdown("### 🎧 Podgląd nagrania")
        st.audio(st.session_state["note_audio_bytes"], format="audio/mp3")

        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🤖 Transkrybuj audio", use_container_width=True):
                with st.spinner("Transkrybuję nagranie..."):
                    st.session_state["note_audio_text"] = transcribe_audio(st.session_state["note_audio_bytes"])

        if st.session_state["note_audio_text"]:
            st.markdown("### ✏️ Edytuj transkrypcję")
            st.session_state["note_text"] = st.text_area(
                "Treść notatki", 
                value=st.session_state["note_audio_text"],
                height=150,
                placeholder="Tutaj możesz edytować transkrypcję swojej notatki..."
            )

        with col2:
            if st.session_state["note_text"] and st.button("💾 Zapisz notatkę", use_container_width=True):
                with st.spinner("Zapisuję notatkę..."):
                    add_note_to_db(note_text=st.session_state["note_text"])
                    st.markdown("""
                    <div class="success-message">
                        🎉 Notatka została pomyślnie zapisana!
                    </div>
                    """, unsafe_allow_html=True)
                    time.sleep(1)
                    st.rerun()

with search_tab:
    st.markdown("### Wyszukaj w swoich notatkach")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Wpisz czego szukasz...", 
            placeholder="np. spotkanie z klientem, lista zakupów, pomysł na projekt...",
            label_visibility="collapsed"
        )
    
    with col2:
        search_button = st.button("🔍 Szukaj", use_container_width=True)
    
    if search_button or query:
        with st.spinner("Szukam w Twoich notatkach..."):
            notes = list_notes_from_db(query if query else None)
        
        if notes:
            st.markdown(f"### Znaleziono {len(notes)} notatek")
            
            for i, note in enumerate(notes):
                timestamp_display = ""
                if note["timestamp"]:
                    try:
                        dt = datetime.fromisoformat(note["timestamp"])
                        timestamp_display = dt.strftime("%d.%m.%Y %H:%M")
                    except:
                        timestamp_display = ""
                
                score_display = ""
                if note["score"]:
                    score_display = f"""
                    <div style="margin-top: 1rem;">
                        <span class="note-score">Dopasowanie: {note["score"]:.3f}</span>
                    </div>
                    """
                
                st.markdown(f"""
                <div class="note-container">
                    <div class="note-text">{note["text"]}</div>
                    <div class="note-timestamp">{timestamp_display}</div>
                    {score_display}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <h3>Nie znaleziono notatek</h3>
                <p>Spróbuj użyć innych słów kluczowych lub dodaj nowe notatki.</p>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        # Show recent notes when no search query
        with st.spinner("Ładuję ostatnie notatki..."):
            recent_notes = list_notes_from_db()
        
        if recent_notes:
            st.markdown("### 📚 Twoje ostatnie notatki")
            
            for note in recent_notes[:5]:  # Show only 5 most recent
                timestamp_display = ""
                if note["timestamp"]:
                    try:
                        dt = datetime.fromisoformat(note["timestamp"])
                        timestamp_display = dt.strftime("%d.%m.%Y %H:%M")
                    except:
                        timestamp_display = ""
                
                st.markdown(f"""
                <div class="note-container">
                    <div class="note-text">{note["text"]}</div>
                    <div class="note-timestamp">{timestamp_display}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📝</div>
                <h3>Brak notatek</h3>
                <p>Rozpocznij od nagrania swojej pierwszej notatki!</p>
            </div>
            """, unsafe_allow_html=True)