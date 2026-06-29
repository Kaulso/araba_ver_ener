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

        /* Banner superior */
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

        /* Tarjetas del menú */
        .menu-card {
            background-color: #2F5D9F;
            border-radius: 14px;
            padding: 22px;
            text-align: center;
            min-height: 190px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: all 0.3s ease;
            margin-bottom: 10px;
        }

        .menu-card:hover {
            background-color: #3C73BF;
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.25);
        }

        .menu-title {
            font-size: 20px;
            font-weight: 700;
            color: white;
            margin-top: 12px;
        }

        .menu-description {
            font-size: 13px;
            color: #DCE6F2;
            margin-top: 10px;
            line-height: 1.5;
            min-height: 45px;
        }
    </style>

    <div class="purple-banner">
        <h1>📊 Dashboard Energético de Álava</h1>
    </div>
    """, unsafe_allow_html=True)

    mostrar_kpis()

    st.subheader("🚦 Índice de contenidos")

    tarjetas = [
        (
            "Resumen",
            "📊",
            "resumen",
            "Visualización de la calificación energética de edificios."
        ),
        (
            "Municipios",
            "🌍",
            "municipios",
            "Análisis de la distribución de edificios por municipios."
        ),
        (
            "Consumo",
            "📈",
            "consumo",
            "Estudio del consumo energético y sus indicadores."
        ),
        (
            "Tipología",
            "🏠",
            "tipologia",
            "Clasificación de edificios según su tipología."
        ),
        (
            "Energías",
            "⚡",
            "energias",
            "Fuentes de energía utilizadas y su distribución."
        ),
        (
            "Correlaciones",
            "🔍",
            "correlaciones",
            "Relación entre variables energéticas y constructivas."
        ),
        (
            "Ranking",
            "🏆",
            "ranking",
            "Comparativa y clasificación de municipios."
        ),
        (
            "Datos",
            "📋",
            "datos",
            "Consulta y exploración de la base de datos."
        ),
    ]

    cols = st.columns(4)

    for i, (titulo, icono, key, descripcion) in enumerate(tarjetas):
        with cols[i % 4]:

            st.markdown(f"""
            <div class="menu-card">
                <div style="font-size:40px;">{icono}</div>
                <div class="menu-title">{titulo}</div>
                <div class="menu-description">{descripcion}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(
                "Abrir",
                key=f"btn_{key}",
                use_container_width=True
            ):
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

    st.subheader("❓¿Por que es importante este estudio?")
    st.markdown(
        """
        Este estudio permite comprender el estado actual de la eficiencia energética de Álava. A través de esta herramienta, el usuario podrá ver el análisis de los datos de eficiencia energética de edificios en la provincia y cómo se distribuyen los certificados por municipio, tipo de edificio, año de construcción y superficie habitable. 
        
        El usuario puede interactuar con los filtros en la barra lateral para explorar los datos según sus necesidades. Además, se presentan visualizaciones gráficas y estadísticas que permiten comprender mejor el estado energético de los edificios de esta provincia del Pais Vasco.
        """
    )

    st.subheader("🗺️ Mapa Energético de Álava")

    st.markdown("""
    Este mapa representa el score energético medio de cada municipio.

    - 🟢 Verde = municipios más eficientes
    - 🟡 Amarillo = eficiencia media
    - 🔴 Rojo = municipios menos eficientes
    """)

    ranking_mapa = (
        df.groupby("Municipio")
        .agg(
            Score=("Score energético", "mean"),
            Certificados=("Municipio", "count"),
            Consumo=("Consumo anual", "mean"),
            Emisiones=("Emisiones anuales", "mean")
        )
        .reset_index()
    )

    try:

        geo = gpd.read_file("municipios_alava.geojson")

        # IMPORTANTE:
        # Cambiar MUNICIPIO por el nombre real
        # de la columna que tenga el GeoJSON
        geo["Municipio"] = geo["MUNICIPIO"]

        geo = geo.merge(
            ranking_mapa,
            on="Municipio",
            how="left"
        )

        m = folium.Map(
            location=[42.85, -2.68],
            zoom_start=8,
            tiles="CartoDB Positron"
        )

        folium.Choropleth(
            geo_data=geo,
            data=geo,
            columns=["Municipio", "Score"],
            key_on="feature.properties.Municipio",
            fill_color="RdYlGn",
            fill_opacity=0.8,
            line_opacity=0.4,
            legend_name="Score energético medio"
        ).add_to(m)

        folium.GeoJson(
            geo,
            tooltip=folium.GeoJsonTooltip(
                fields=[
                    "Municipio",
                    "Score",
                    "Certificados",
                    "Consumo",
                    "Emisiones"
                ],
                aliases=[
                    "Municipio:",
                    "Score:",
                    "Certificados:",
                    "Consumo medio:",
                    "Emisiones medias:"
                ]
            )
        ).add_to(m)

        st_folium(
            m,
            width=1200,
            height=700
        )

    except Exception as e:

        st.error(
            f"Error cargando el mapa: {e}"
        )
    

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

elif st.session_state.seccion == "municipios":
    page("🌍 Municipios")

    st.subheader("Municipios con más certificados")
    st.markdown(
    """
    
    Esta visualización muestra los municipios con mayor cantidad de certificados energéticos. Permite identificar qué municipios tienen más edificios certificados y cómo se distribuyen en términos de eficiencia energética.
    
    La barra presenta la cantidad de certificados por municipio, que se puede modificar mediante el deslizador inferior, y el color indica el score energético promedio de cada municipio.
    """
    )

    top_n = st.slider("Número de municipios", 5, 25, 10)

    top = df["Municipio"].value_counts().head(top_n).reset_index()
    top.columns = ["Municipio", "Certificados"]

    fig = px.bar(
        top,
        x="Certificados",
        y="Municipio",
        orientation="h",
        text_auto=True
    )

    st.plotly_chart(fig, width="stretch")

    st.divider()

    st.subheader("Mapa interactivo de municipios")
    st.markdown(
        """

        Este mapa interactivo muestra la ubicación de los municipios de Álava y permite visualizar el score energético promedio de cada municipio.
        Al hacer clic en un municipio, se puede ver información detallada sobre el score energético, la cantidad de certificados, el consumo medio y las emisiones medias.
        """
    )

    # Coordenadas aproximadas de municipios principales de Álava
    coords = {
        "Vitoria-Gasteiz": (42.8467, -2.6716),
        "Amurrio": (43.0540, -3.0016),
        "Laudio/Llodio": (43.1433, -2.9627),
        "Agurain/Salvatierra": (42.8512, -2.3896),
        "Alegría-Dulantzi": (42.8418, -2.5139),
        "Araia": (42.8938, -2.3124),
        "Artziniega": (43.1219, -3.1274),
        "Labastida": (42.5907, -2.7698),
        "Laguardia": (42.5546, -2.5856),
        "Oion": (42.5067, -2.4369),
        "Zuia (Murgia)": (42.9636, -2.8197)
    }

    mapa = (
        df.groupby("Municipio")
        .agg(
            Certificados=("Municipio", "count"),
            Consumo_Medio=("Consumo anual", "mean"),
            Emisiones_Medias=("Emisiones anuales", "mean")
        )
        .reset_index()
    )

    mapa["lat"] = mapa["Municipio"].map(
        lambda x: coords.get(x, (None, None))[0]
    )

    mapa["lon"] = mapa["Municipio"].map(
        lambda x: coords.get(x, (None, None))[1]
    )

    mapa = mapa.dropna(subset=["lat", "lon"])

    if not mapa.empty:

        fig_map = px.scatter_map(
            mapa,
            lat="lat",
            lon="lon",
            size="Certificados",
            color="Consumo_Medio",
            hover_name="Municipio",
            hover_data={
                "Certificados": True,
                "Consumo_Medio": ":.1f",
                "Emisiones_Medias": ":.1f",
                "lat": False,
                "lon": False
            },
            zoom=8,
            center={
                "lat": 42.85,
                "lon": -2.68
            },
            height=650,
            map_style="carto-positron"
        )

        fig_map.update_layout(
            margin=dict(l=0, r=0, t=30, b=0)
        )

        st.plotly_chart(
            fig_map,
            width="stretch",
        )

    else:
        st.info(
            "No hay coordenadas disponibles para los municipios seleccionados."
        )

    st.subheader("Mapa de calor: Municipio vs Calificación")
    st.markdown(
        """             
    Este mapa de calor muestra la relación entre los municipios y la calificación energética de los edificios.
    Permite identificar qué calificaciones son más comunes en cada municipio y cómo se distribuyen los edificios según su eficiencia energética.
        """
        )

    heat = pd.crosstab(
        df["Municipio"],
        df["Calificación energética"]
    )

    fig = px.imshow(
        heat,
        labels=dict(
            x="Calificación",
            y="Municipio",
            color="Nº edificios"
        ),
        color_continuous_scale="YlOrRd",
        aspect="auto"
    )

    st.plotly_chart(fig, width="stretch")

    st.subheader("Mapa de calor: Consumo vs Emisiones")
    st.markdown(
        """
    Este gráfico muestra la densidad de edificios en función de su consumo anual y sus emisiones de CO2.
    Permite observar la correlación entre ambos parámetros y detectar grupos de edificios con comportamientos similares.
        """
    )

    fig = px.density_heatmap(
    df,
    x="Consumo anual",
    y="Emisiones anuales",
    nbinsx=40,
    nbinsy=40,
    color_continuous_scale="Turbo"
    )

    st.plotly_chart(fig, width="stretch")

elif st.session_state.seccion == "consumo":
    page("📈 Consumo")

    st.subheader("🧠 Clustering de municipios")
    st.markdown(
        """
        Esta visualización muestra un clustering de los municipios según su consumo anual, emisiones anuales y score energético. 
        Permite identificar grupos de municipios con características similares en términos de eficiencia energética.
        """
    )   

    cluster_data = df.groupby("Municipio").agg({
    "Consumo anual":"mean",
    "Emisiones anuales":"mean",
    "Score":"mean"
    }).dropna()

    k = min(4, len(cluster_data))

    kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
    cluster_data["Cluster"] = kmeans.fit_predict(cluster_data)

    fig = px.scatter(
        cluster_data,
        x="Consumo anual",
        y="Emisiones anuales",
        size="Score",
        color="Cluster",
        text=cluster_data.index
    )

    st.plotly_chart(fig, width='stretch')

    st.subheader("Consumo vs Emisiones")
    st.markdown(    
    """
    Este gráfico muestra la relación entre el consumo anual y las emisiones de CO2 de los edificios.
    Permite identificar patrones y correlaciones entre ambos parámetros, así como detectar edificios con consumos
    y emisiones atípicas.   
    """
    ) 

    fig = px.scatter(
        df,
        x="Consumo anual",
        y="Emisiones anuales",
        color="Tipo edificio",
        size="Superficie habitable",
        hover_data=["Municipio"]
        # ❌ sin trendline para evitar dependencia statsmodels
    )

    st.plotly_chart(fig, width="stretch")

    st.subheader("Distribución consumo")
    st.markdown(    
    """
    Este histograma muestra la distribución del consumo anual de los edificios.
    Permite observar la frecuencia de los diferentes niveles de consumo y detectar posibles valores atípicos.    
    """
    )   

    st.plotly_chart(
        px.histogram(df, x="Consumo anual", nbins=40),
        width="stretch"
    )

    st.subheader("Distribución emisiones")
    st.markdown(    
    """ 
    Este histograma muestra la distribución de las emisiones de CO2 de los edificios.
    Aquí también se puede observar la frecuencia y detectar posibles valores atípicos.   
    """
    )

    st.plotly_chart(
        px.histogram(df, x="Emisiones anuales", nbins=40),
        width="stretch"
    )

elif st.session_state.seccion == "tipologia":
    page("🏠 Tipología")

    st.subheader("Tipos de vivienda")
    st.markdown(    
    """ 
    Esta visualización muestra la distribución de los diferentes tipos de edificios en Álava.
    Permite identificar qué tipos de edificios son más comunes y cómo se distribuyen en términos de eficiencia energética.
    """
    )

    tipos = df["Tipo edificio"].value_counts().reset_index()
    tipos.columns = ["Tipo edificio", "Cantidad"]

    st.plotly_chart(
        px.bar(tipos, x="Tipo edificio", y="Cantidad", text_auto=True),
        width="stretch"
    )

    st.subheader("Consumo y emisiones por tipo de edificio")
    st.markdown(    
    """ 
    Esta visualización muestra la relación entre el tipo de edificio y su consumo anual y emisiones de CO2.
    Aquí se puede observar elimpacto ambiental, permitiendo comparar el desempeño energético de los diferentes tipos de edificios y detectar cuáles son más eficientes
    """
    )


    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(
            px.box(df, x="Tipo edificio", y="Consumo anual"),
            width="stretch"
        )

    with col2:
        st.plotly_chart(
            px.box(df, x="Tipo edificio", y="Emisiones anuales"),
            width="stretch"
        )


elif st.session_state.seccion == "energias":
    page("⚡ Energías")

    st.subheader("Gráfico de energías")
    st.markdown(    
    """ 
    Esta visualización muestra la distribución de los tipos de energía utilizados para calefacción y agua caliente sanitaria (ACS) en los edificios de Álava.
    
    De una manera sencilla permite identificar cuáles son las fuentes de energía más comunes y cómo se distribuyen entre los edificios, lo que puede ayudar a entender el impacto ambiental y la eficiencia energética de cada tipo de energía.
    """
    )


    calefaccion = df["Cal. Tipo Energia"].value_counts().head(10).reset_index()
    calefaccion.columns = ["Energía", "Cantidad"]

    acs = df["ACS Tipo Energia"].value_counts().head(10).reset_index()
    acs.columns = ["Energía", "Cantidad"]

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(
            px.pie(calefaccion, names="Energía", values="Cantidad"),
            width="stretch"
        )

    with col2:
        st.plotly_chart(
            px.pie(acs, names="Energía", values="Cantidad"),
            width="stretch"
        )

elif st.session_state.seccion == "correlaciones":
    page("🔍 Correlaciones")

    st.subheader("Correlación entre variables")
    st.markdown(    
    """
    En este apartado se muestra la matriz de correlación entre las variables numéricas del dataset.
    Se puede observar relaciones lineales entre las variables y detectar posibles patrones o dependencias.
    """
    )    

    numericas = df.select_dtypes(include="number")
    numericas = numericas.loc[:, numericas.nunique() > 1]

    corr = numericas.corr()

    fig = px.imshow(
        corr,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="Blues"
    )

    st.plotly_chart(fig, width="stretch")

    st.subheader("Resumen estadístico")
    st.markdown(
    """
    A continuación se muestra un resumen estadístico de las variables numéricas del dataset filtrado.

    Se incluyen medidas como la media, desviación estándar, valores mínimos y máximos, así como los percentiles 25, 50 y 75.    
    """
    )

    st.dataframe(numericas.describe(), width="stretch")

elif st.session_state.seccion == "ranking":
    page("🏆 Ranking")

    st.subheader("Ranking energético")
    st.markdown(
    """ 
    A continuación se muestra un ranking de los municipios de Álava según su score energético promedio.

    Permite identificar qué municipios tienen un mejor desempeño en términos de eficiencia energética y cuáles necesitan mejorar.
    """
    )   

    ranking = (
        df.groupby("Municipio")
        .agg(
            Score=("Score energético", "mean"),
            Certificados=("Municipio", "count"),
            Consumo=("Consumo anual", "mean"),
            Emisiones=("Emisiones anuales", "mean")
        )
        .reset_index()
        .sort_values("Score", ascending=False)
    )

    # ================================
    # 🧠 INSIGHTS AUTOMÁTICOS
    # ================================

    best = ranking.iloc[0]["Municipio"]
    worst = ranking.iloc[-1]["Municipio"]
    diff = ranking["Score"].max() - ranking["Score"].min()

    col1, col2, col3 = st.columns(3)

    col1.success(f"🏆 Mejor municipio: {best}")
    col2.error(f"⚠️ Peor municipio: {worst}")
    col3.info(f"📊 Diferencia de score: {diff:.1f} puntos")

    st.plotly_chart(
        px.bar(
            ranking.head(20),
            x="Score",
            y="Municipio",
            orientation="h",
            color="Score",
            text_auto=".1f",
            color_continuous_scale="RdYlGn"
        ),
        width="stretch"
    )

    st.dataframe(
        ranking.round(2),
        width="stretch"
    )

elif st.session_state.seccion == "datos":
    page("📋 Datos")

    st.subheader("Datos filtrados")
    st.markdown(
    """
    En esta sección se muestran los datos filtrados según los criterios seleccionados en la barra lateral.
    Se puede visualizar la información de los certificados energéticos de los edificios en Álava y descargar el dataset filtrado para su análisis posterior.
    """
    )   
    
    st.dataframe(df, width="stretch")

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Descargar datos filtrados",
        csv,
        "certificados_filtrados.csv",
        "text/csv"
    )


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
