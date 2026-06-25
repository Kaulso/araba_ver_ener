import streamlit as st
st.set_page_config(page_title="Dashboard", layout="wide")
if "seccion" not in st.session_state:
    st.session_state.seccion = "menu"
st.markdown("""
<style>
.menu-subtitle {
    font-size: 13px;
    letter-spacing: 4px;
    color: #6B7280;
    text-transform: uppercase;
    margin-top: 10px;
}
.menu-card {
    border: 1px solid #E5E7EB;
    border-radius: 18px;
    padding: 18px;
    background: #FFFFFF;
    min-height: 170px;
    margin-bottom: 10px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.menu-card-title {
    font-size: 22px;
    font-weight: 600;
    margin-bottom: 8px;
}
.menu-card-text {
    font-size: 14px;
    color: #4B5563;
}
div.stButton > button {
    border-radius: 12px;
    border: 1px solid #D1D5DB;
    background-color: white;
    height: 42px;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)
def volver_menu():
    if st.button("⬅ Volver al menu"):
        st.session_state.seccion = "menu"
        st.rerun()
def mostrar_menu():
    st.markdown('<div class="menu-subtitle">Where to next</div>', unsafe_allow_html=True)
    st.markdown("## Explore the platform")
    tarjetas = [
        {"titulo": "Resumen", "desc": "Calificación energética y métricas generales.", "key": "resumen", "icono": "📊"},
        {"titulo": "Municipios", "desc": "Mapa interactivo y análisis territorial.", "key": "municipios", "icono": "🌍"},
        {"titulo": "Consumo", "desc": "Relación entre consumo y emisiones.", "key": "consumo", "icono": "📈"},
        {"titulo": "Tipología", "desc": "Comparativa por tipo de edificio.", "key": "tipologia", "icono": "🏠"},
        {"titulo": "Energías", "desc": "Fuentes energéticas para calefacción y ACS.", "key": "energias", "icono": "⚡"},
        {"titulo": "Correlaciones", "desc": "Análisis estadístico entre variables.", "key": "correlaciones", "icono": "🔍"},
        {"titulo": "Ranking", "desc": "Municipios ordenados por score energético.", "key": "ranking", "icono": "🏆"},
        {"titulo": "Datos", "desc": "Consulta y descarga del dataset filtrado.", "key": "datos", "icono": "📋"},
    ]
    cols = st.columns(4)
    for i, t in enumerate(tarjetas):
        with cols[i % 4]:
            st.markdown(f"""
            <div class="menu-card">
                <div style="font-size:34px;">{t['icono']}</div>
                <div class="menu-card-title">{t['titulo']}</div>
                <div class="menu-card-text">{t['desc']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Open ->", key=t["key"], use_container_width=True):
                st.session_state.seccion = t["key"]
                st.rerun()
def render_resumen():
    volver_menu()
    st.subheader("Resumen")
    st.write("Contenido de resumen")
def render_municipios():
    volver_menu()
    st.subheader("Municipios")
    st.write("Contenido de municipios")
def render_consumo():
    volver_menu()
    st.subheader("Consumo")
    st.write("Contenido de consumo")
def render_tipologia():
    volver_menu()
    st.subheader("Tipología")
    st.write("Contenido de tipología")
def render_energias():
    volver_menu()
    st.subheader("Energías")
    st.write("Contenido de energías")
def render_correlaciones():
    volver_menu()
    st.subheader("Correlaciones")
    st.write("Contenido de correlaciones")
def render_ranking():
    volver_menu()
    st.subheader("Ranking")
    st.write("Contenido de ranking")
def render_datos():
    volver_menu()
    st.subheader("Datos")
    st.write("Contenido de datos")
if st.session_state.seccion == "menu":
    mostrar_menu()
elif st.session_state.seccion == "resumen":
    render_resumen()
elif st.session_state.seccion == "municipios":
    render_municipios()
elif st.session_state.seccion == "consumo":
    render_consumo()
elif st.session_state.seccion == "tipologia":
    render_tipologia()
elif st.session_state.seccion == "energias":
    render_energias()
elif st.session_state.seccion == "correlaciones":
    render_correlaciones()
elif st.session_state.seccion == "ranking":
    render_ranking()
elif st.session_state.seccion == "datos":
    render_datos()