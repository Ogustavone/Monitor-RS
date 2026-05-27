import streamlit as st
from components.iframe import render_mapa
from components.noticias import render_noticias
from components.clima import render_clima

st.set_page_config(layout="wide", page_title="Monitoramento Bacia do Guaíba")

st.title("Sistema de Monitoramento Hidrológico")

col_mapa, col_noticias = st.columns([2.3, 1.0], gap="large")

with col_mapa:
    render_clima()
    st.markdown("<br>", unsafe_allow_html=True)
    render_mapa()
    

with col_noticias:
    render_noticias()