import streamlit as st
<<<<<<< HEAD
from main import findAnomalies
from pathlib import Path

st.set_page_config(page_title="Sentinel")
st.title("Sentinel", text_alignment="center")
uploaded = st.file_uploader("Choose a file", type=["json"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

if uploaded is not None:
    save_path = UPLOAD_DIR / Path(uploaded.name).name
    save_path.write_bytes(uploaded.getbuffer())

    st.session_state["uploaded_file_path"] = str(save_path)
    st.success(f"File uploaded successfully: {save_path}")

    returned = findAnomalies(str(save_path))
    flagged = returned[returned["flagged"] == 1]
    st.write("Flagged:", len(flagged), "of", len(returned))
    st.dataframe(flagged[["user_id", "timestamp", "location", "device_type", "speed_mph", "category"]])

# path = st.session_state.get("uploaded_file_path")
# if path:
    
=======
>>>>>>> a30e33d016156caa90c7ffd8cbd91c22c12b8d63
