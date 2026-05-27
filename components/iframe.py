import streamlit as st

def render_mapa():
    st.subheader("Mapa Interativo - Bacia do Guaíba (SGB)")
    MAPA_URL = "https://sace.sgb.gov.br/guaiba/"
    st.iframe(MAPA_URL, height=650)
    st.markdown(
        f"""
        <style>
            iframe {{ border-radius: 16px; border: 2px solid #4A90E2; }}
            .links-row {{ display: flex; gap: 16px; flex-wrap: wrap; margin-top: 12px; }}
            .links-row a {{
                color: #1f78d1;
                text-decoration: underline;
                font-weight: 600;
            }}
        </style>
        <div class="links-row">
            <a href="{MAPA_URL}" target="_blank" rel="noopener noreferrer">Abrir Mapa em Nova Aba</a>
            <a href="https://nivelguaiba.com.br/" target="_blank" rel="noopener noreferrer">Acessar Site Nivel Guaiba</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
    

    