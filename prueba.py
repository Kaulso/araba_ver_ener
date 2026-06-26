import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
import geopandas as gpd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Dashboard Energético", layout="wide")

# -----------------------------
# ESTADO DE LA SESIÓN
# -----------------------------
if "seccion" not in st.session_state:
    st.session_state.seccion = "menu"

# -----------------------------
# ESTILOS CSS GENERALES
# -----------------------------
st.markdown("""
<style>
.menu-card {
    border: 1px solid #E5E7EB;
    border-radius: 16px;
    padding: 16px;
    background: white;
    min-height: 150px;
    margin-bottom: 10px;
}
.menu-title {
    font-size: 18px;
    font-weight: 600;
}
.menu-desc {
    font-size: 13px;
    color: #6B7280;
}
</style>
""", unsafe_allow_html=True)

# ==================================================
# CARGA DE DATOS
# ==================================================
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv("data_araba_cleaned.csv")
    except FileNotFoundError:
        # Fallback de datos simulados para pruebas en local si falta el archivo
        df = pd.DataFrame({
            "Municipio": ["Vitoria-Gasteiz", "Amurrio", "Llodio"] * 10,
            "Tipo edificio": ["Residencial", "Industrial"] * 15,
            "Año construcción": [1990, 2005, 2015] * 10,
            "Superficie habitable": [85, 120, 200] * 10,
            "Calificación energética": ["A", "C", "E"] * 10,
            "Calificación energ. emisiones": ["B", "C", "F"] * 10,
            "Consumo anual": [150, 230, 410] * 10,
            "Emisiones anuales": [30, 55, 90] * 10
        })

    columnas_constantes = [
        col for col in df.columns
        if df[col].nunique(dropna=False) <= 1
    ]
    df = df.drop(columns=columnas_constantes)
    return df

df_total = cargar_datos()

# -----------------------------
# FUNCIONES MATEMÁTICAS / UTILS
# -----------------------------
def safe_norm(col):
    denom = col.max() - col.min()
    if denom == 0:
        return pd.Series(50, index=col.index)
    return (1 - (col - col.min()) / denom) * 100

def calcular_score_energetico(df):
    mapa_calificacion = {
        "A": 100, "B": 85, "C": 70, "D": 55,
        "E": 40, "F": 25, "G": 10
    }
    score_calificacion = df["Calificación energética"].map(mapa_calificacion).fillna(0)
    score_emisiones_calif = df["Calificación energ. emisiones"].map(mapa_calificacion).fillna(0)

    consumo_norm = safe_norm(df["Consumo anual"])
    emisiones_norm = safe_norm(df["Emisiones anuales"])

    score = (
        score_calificacion * 0.5 +
        score_emisiones_calif * 0.3 +
        consumo_norm * 0.1 +
        emisiones_norm * 0.1
    )
    return score.round(1)

def compute_score(df):
    mapc = {"A":100,"B":85,"C":70,"D":55,"E":40,"F":25,"G":10}
    return (
        df["Calificación energética"].map(mapc).fillna(0) * 0.45 +
        df["Calificación energ. emisiones"].map(mapc).fillna(0) * 0.30 +
        safe_norm(df["Consumo anual"]) * 0.15 +
        safe_norm(df["Emisiones anuales"]) * 0.10
    ).round(1)

# Precalculamos scores sobre el DataFrame maestro global
df_total["Score energético"] = calcular_score_energetico(df_total)
df_total["Score"] = compute_score(df_total)

# -----------------------------
# SIDEBAR INTERACTIVO
# -----------------------------
def render_sidebar():
    try:
        st.sidebar.image("Escudo_alava.png", caption="Fuente: Wikipedia", width=200)
    except:
        pass 
        
    st.sidebar.title("📌 Navegación")

    opciones = {
        "🏠 Menú": "menu",
        "📊 Resumen": "resumen",
        "🌍 Municipios": "municipios",
        "📈 Consumo": "consumo",
        "🏠 Tipología": "tipologia",
        "⚡ Energías": "energias",
        "🔍 Correlaciones": "correlaciones",
        "🏆 Ranking": "ranking",
        "📋 Datos": "datos",
    }

    indice_actual = list(opciones.values()).index(st.session_state.seccion)
    seleccion = st.sidebar.radio("Ir a:", list(opciones.keys()), index=indice_actual)
    
    if opciones[seleccion] != st.session_state.seccion:
        st.session_state.seccion = opciones[seleccion]
        st.rerun()

    st.sidebar.header("Filtros")
    st.sidebar.markdown("Usa estos filtros para actualizar los indicadores en tiempo real.")

    municipios = sorted(df_total["Municipio"].dropna().unique())
    municipio_sel = st.sidebar.multiselect("Municipio", municipios)

    tipos = sorted(df_total["Tipo edificio"].dropna().unique())
    tipo_edificio_sel = st.sidebar.multiselect("Tipo edificio", tipos)

    min_year, max_year = int(df_total["Año construcción"].min()), int(df_total["Año construcción"].max())
    rango_sel = st.sidebar.slider("Año construcción", min_year, max_year, (min_year, max_year))

    sup_min, sup_max = int(df_total["Superficie habitable"].min()), int(df_total["Superficie habitable"].max())
    superficie_sel = st.sidebar.slider("Superficie habitable (m²)", sup_min, sup_max, (sup_min, sup_max))

    return municipio_sel, tipo_edificio_sel, rango_sel, superficie_sel

# Construir sidebar
municipio, tipo_edificio, rango, superficie = render_sidebar()

# -----------------------------
# PROCESAMIENTO DE FILTRADO
# -----------------------------
def aplicar_filtros(df_origen):
    dff = df_origen.copy()
    if municipio:
        dff = dff[dff["Municipio"].isin(municipio)]
    if tipo_edificio:
        dff = dff[dff["Tipo edificio"].isin(tipo_edificio)]
        
    dff = dff[
        (dff["Año construcción"].between(*rango)) &
        (dff["Superficie habitable"].between(*superficie))
    ]
    return dff

df = aplicar_filtros(df_total)

if not df.empty:
    df["Score energético"] = calcular_score_energetico(df)
    df["Score"] = compute_score(df)

# ==================================================
# MOSTRAR KPIs GLOBALES (En Recuadro Verde Claro HTML)
# ==================================================
def mostrar_kpis():
    st.subheader("Indicadores generales")
    if df.empty:
        st.warning("No hay datos disponibles para los filtros seleccionados.")
        return
        
    porcentaje = round(len(df) / len(df_total) * 100, 1)
    certificados = f"{len(df):,}"
    consumo = f"{df['Consumo anual'].mean():.1f}"
    emisiones = f"{df['Emisiones anuales'].mean():.1f}"
    sup_media = f"{df['Superficie habitable'].mean():.1f} m²"
    score = f"{df['Score energético'].mean():.1f}/100"
    
    st.markdown(f"""
    <style>
        .green-container {{
            background-color: #f0fdf4; 
            border: 1px solid #bbf7d0;  
            border-radius: 12px;
            padding: 20px 15px;
            margin-bottom: 25px;
            box-shadow: 0 4px 10px rgba(22, 163, 74, 0.03);
            display: flex;
            justify-content: space-around;
            align-items: center;
            flex-wrap: wrap;
            font-family: 'Inter', sans-serif;
        }}
        .kpi-block {{
            text-align: center;
            flex: 1;
            min-width: 140px;
            padding: 5px;
        }}
        .kpi-label {{
            font-size: 14px;
            color: #4b5563; 
            margin-bottom: 6px;
            font-weight: 500;
        }}
        .kpi-value {{
            font-size: 26px;
            font-weight: 700;
            color: #166534; 
        }}
        .kpi-delta {{
            font-size: 12px;
            color: #15803d;
            margin-top: 2px;
            font-weight: 500;
        }}
    </style>
    
    <div class="green-container">
        <div class="kpi-block">
            <div class="kpi-label">Certificados</div>
            <div class="kpi-value">{certificados}</div>
            <div class="kpi-delta">▲ {porcentaje}% del total</div>
        </div>
        <div class="kpi-block">
            <div class="kpi-label">Consumo medio</div>
            <div class="kpi-value">{consumo}</div>
        </div>
        <div class="kpi-block">
            <div class="kpi-label">Emisiones medias</div>
            <div class="kpi-value">{emisiones}</div>
        </div>
        <div class="kpi-block">
            <div class="kpi-label">Superficie media</div>
            <div class="kpi-value">{sup_media}</div>
        </div>
        <div class="kpi-block">
            <div class="kpi-label">Score energético</div>
            <div class="kpi-value">{score}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

# ==================================================
# VISTAS DE LAS SECCIONES
# ==================================================
colores_calificacion = {
    "A": "#00A651", "B": "#65B32E", "C": "#A8C545",
    "D": "#FFD700", "E": "#F9A602", "F": "#FF6B35", "G": "#D62828"
}
orden_calif = ["A", "B", "C", "D", "E", "F", "G"]

def menu():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@600;700&display=swap');
        .purple-banner {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%);
            color: #ffffff;
            border-radius: 12px;
            padding: 25px 20px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(124, 58, 237, 0.2);
            margin-bottom: 30px;
        }
        .purple-banner h1 {
            color: white !important;
            margin: 0;
            font-size: 40px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
    </style>
    <div class="purple-banner">
        <h1>📊 Dashboard Energético de Álava</h1>
    </div>
    """, unsafe_allow_html=True)

    mostrar_kpis()

    tarjetas = [
        ("Resumen", "📊", "resumen"),
        ("Municipios", "🌍", "municipios"),
        ("Consumo", "📈", "consumo"),
        ("Tipología", "🏠", "tipologia"),
        ("Energías", "⚡", "energias"),
        ("Correlaciones", "🔍", "correlaciones"),
        ("Ranking", "🏆", "ranking"),
        ("Datos", "📋", "datos"),
    ]

    cols = st.columns(4)
    for i, (titulo, icono, key) in enumerate(tarjetas):
        with cols[i % 4]:
            st.markdown(f"""
            <div class="menu-card">
                <div style="font-size:32px;">{icono}</div>
                <div class="menu-title">{titulo}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Abrir", key=f"btn_{key}"):
                st.session_state.seccion = key
                st.rerun()

def page(title):
    if st.button("⬅ Volver al menú"):
        st.session_state.seccion = "menu"
        st.rerun()

    st.subheader(title)
    mostrar_kpis()

# ==================================================
# ROUTER ENRUTADOR PRINCIPAL DE PÁGINAS
# ==================================================
if st.session_state.seccion == "menu":
    menu()

elif st.session_state.seccion == "resumen":
    page("📊 Resumen")
    
    st.subheader("Calificación energética")
    st.markdown("Esta visualización muestra la distribución de la calificación energética de los edificios en Álava. Permite identificar qué porcentaje de edificios se encuentra en cada categoría de eficiencia energética, desde A (más eficiente) hasta G (menos eficiente).")

    if not df.empty:
        calif = df["Calificación energética"].value_counts().reset_index()
        calif.columns = ["Calificación", "Cantidad"]
        calif["Calificación"] = pd.Categorical(calif["Calificación"], categories=orden_calif, ordered=True)
        calif = calif.sort_values("Calificación")

        fig1 = px.bar(
            calif,
            x="Calificación",
            y="Cantidad",
            color="Calificación",
            color_discrete_map=colores_calificacion,
            text_auto=True
        )
        st.plotly_chart(fig1, width="stretch", key="grafico_calificacion_unico")

        st.write("---")
        st.subheader("Calificación energética vs. Calificación de emisiones")
        st.markdown(
            """
            Esta visualización muestra la relación entre la calificación energética de los edificios y su calificación de emisiones. 
            Permite identificar si existe una correlación entre la eficiencia energética y las emisiones generadas por los edificios.
            """
        )

        # Gráficos paralelos modernos
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown("##### ⚡ Eficiencia Energética")
            st.plotly_chart(fig1, width="stretch", key="fig_resumen_energia")

        with col_g2:
            st.markdown("##### 💨 Emisiones CO₂")
            emisiones = df["Calificación energ. emisiones"].value_counts().reset_index()
            emisiones.columns = ["Calificación", "Cantidad"]
            emisiones["Calificación"] = pd.Categorical(emisiones["Calificación"], categories=orden_calif, ordered=True)
            emisiones = emisiones.sort_values("Calificación")

            fig2 = px.bar(
                emisiones,
                x="Calificación",
                y="Cantidad",
                color="Calificación",
                color_discrete_map=colores_calificacion,
                text_auto=True
            )
            st.plotly_chart(fig2, width="stretch", key="fig_resumen_emisiones")
    else:
        st.info("Por favor, selecciona filtros válidos en el menú lateral para actualizar los gráficos.")

# Resto de subpáginas dinámicas
else:
    titulos_paginas = {
        "municipios": "🌍 Municipios",
        "consumo": "📈 Consumo",
        "tipologia": "🏠 Tipología",
        "energias": "⚡ Energías",
        "correlaciones": "🔍 Correlaciones",
        "ranking": "🏆 Ranking",
        "datos": "📋 Datos"
    }
    seccion_actual = st.session_state.seccion
    if seccion_actual in titulos_paginas:
        page(titulos_paginas[seccion_actual])
        st.write(f"Contenido específico para la sección de {titulos_paginas[seccion_actual]}")
