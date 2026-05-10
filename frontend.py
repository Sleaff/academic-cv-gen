import streamlit as st
import requests

st.set_page_config(page_title="CV Generator", page_icon="📄")

st.title("Academic CV Generator")
st.write("Generate a DFF 2026 CV from Wikidata and a previous PDF.")

# Finns QUID default value for testing
wikidata_qid = st.text_input("Wikidata QID", value="Q20980928")
output_format = st.selectbox("Output Format", ["docx", "pdf", "markdown", "latex"])
uploaded_file = st.file_uploader("Upload Previous CV (Optional)", type="pdf")

if st.button("Generate CV"):
    with st.spinner("Processing with LLM..."):
        url = f"http://127.0.0.1:8000/api/v1/generate/{wikidata_qid}"
        params = {"format": output_format}
        
        files = None
        if uploaded_file:
            files = {"previous_cv": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}

        try:
            response = requests.post(url, params=params, files=files)
            
            if response.status_code == 200:
                st.success("CV Generated Successfully!")
                st.download_button(
                    label=f"Download {output_format.upper()}",
                    data=response.content,
                    file_name=f"generated_cv.{output_format}",
                    mime=response.headers.get("content-type")
                )
            else:
                st.error(f"Error: {response.json().get('detail')}")
        except Exception as e:
            st.error(f"Could not connect to backend: {e}")