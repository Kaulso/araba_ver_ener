import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# ==================================================
# CONFIGURACIÓN GENERAL
# ==================================================

st.set_page_config(
    page_title="Certificados Energéticos de Álava",
    layout="wide"
)

st.title("🏠 Certificados Energéticos de Álava")

st.markdown("Dashboard, cuadro de mandos, donde se ofrece un análisis interactivo de eficiencia energética de edificios en Álava.")

# ==================================================
# CARGA DE DATOS
# ==================================================

@st.cache_data
def cargar_datos():
    df = pd.read_csv("data_araba_cleaned.csv")

    columnas_constantes = [
        col for col in df.columns
        if df[col].nunique(dropna=False) <= 1
    ]

    df = df.drop(columns=columnas_constantes)
    return df


df_total = cargar_datos()

# ==================================================
# FUNCIONES
# ==================================================

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


# ==================================================
# SIDEBAR - FILTROS
# ==================================================

st.sidebar.image("Escudo_alava.png", caption="Fuente: Wikipedia", width=200)

st.sidebar.header("Filtros")
st.sidebar.markdown("Sidebar donde se puede seleccionar los filtros de este dashboard interactivo de Álava.")

df = df_total.copy()

municipios = sorted(df["Municipio"].dropna().unique())
municipio = st.sidebar.multiselect("Municipio", municipios)

tipos = sorted(df["Tipo edificio"].dropna().unique())
tipo_edificio = st.sidebar.multiselect("Tipo edificio", tipos)

min_year, max_year = int(df["Año construcción"].min()), int(df["Año construcción"].max())

rango = st.sidebar.slider(
    "Año construcción",
    min_year,
    max_year,
    (min_year, max_year)
)

sup_min, sup_max = int(df["Superficie habitable"].min()), int(df["Superficie habitable"].max())

superficie = st.sidebar.slider(
    "Superficie habitable (m²)",
    sup_min,
    sup_max,
    (sup_min, sup_max)
)

# ==================================================
# FILTRADO CENTRALIZADO
# ==================================================

def aplicar_filtros(df):
    dff = df.copy()

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

df = df.copy()
df.loc[:, "Score energético"] = calcular_score_energetico(df)

df_total.loc[:, "Score energético"] = calcular_score_energetico(df_total)

def compute_score(df):
    mapc = {"A":100,"B":85,"C":70,"D":55,"E":40,"F":25,"G":10}

    return (
        df["Calificación energética"].map(mapc).fillna(0) * 0.45 +
        df["Calificación energ. emisiones"].map(mapc).fillna(0) * 0.30 +
        safe_norm(df["Consumo anual"]) * 0.15 +
        safe_norm(df["Emisiones anuales"]) * 0.10
    ).round(1)

df["Score"] = compute_score(df)
df_total["Score"] = compute_score(df_total)

# ==================================================
# KPIs
# ==================================================

st.subheader("Indicadores generales")

porcentaje = round(len(df) / len(df_total) * 100, 1)

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Certificados", f"{len(df):,}", f"{porcentaje}% del total")
c2.metric("Consumo medio", round(df["Consumo anual"].mean(), 1))
c3.metric("Emisiones medias", round(df["Emisiones anuales"].mean(), 1))
c4.metric("Superficie media", round(df["Superficie habitable"].mean(), 1))
c5.metric("Score energético", f"{df['Score energético'].mean():.1f}/100")

st.divider()

# ==================================================
# COLORES
# ==================================================

colores_calificacion = {
    "A": "#00A651", "B": "#65B32E", "C": "#A8C545",
    "D": "#FFD700", "E": "#F9A602", "F": "#FF6B35", "G": "#D62828"
}

orden_calif = ["A", "B", "C", "D", "E", "F", "G"]

# ==================================================
# TABS
# ==================================================

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "🏠 Menu Principal",
    "📊 Resumen",
    "🏙️ Municipios",
    "📈 Consumo",
    "🏠 Tipología",
    "⚡ Energías",
    "🔍 Correlaciones",
    "🏆 Ranking",
    "📋 Datos"
])

# ==================================================
# TAB 1 - MENU PRINCIPAL
# ==================================================

with tab1:

    st.subheader("¿Por que es importante este estudio?")
    st.markdown(
        """
        Bienvenido al dashboard de certificados energéticos de Álava. 
        A lo largo de este estudio podrá ver el análisis de los datos de eficiencia energética de edificios en la provincia y cómo se distribuyen los certificados por municipio, tipo de edificio, año de construcción y superficie habitable. 
        
        El usuario puede interactuar con los filtros en la barra lateral para explorar los datos según sus necesidades. Además, se presentan visualizaciones gráficas y estadísticas que permiten comprender mejor el estado energético de los edificios en Álava.
        """
    )

    st.image(
        "ALAVA-ARABA_Mapa_Político_2019.png",
        caption="Fuente: Wikipedia",
        width=700
    )
    
    st.subheader("Índice de contenidos")
    st.markdown(
        """
        1. **Resumen**: Visualización de la calificación energética de los edificios.
        2. **Municipios**: Análisis de los municipios con más certificados y un mapa interactivo.
        3. **Consumo**: Relación entre consumo y emisiones, y distribución de consumo y emisiones.
        4. **Tipología**: Análisis de los tipos de edificios y su consumo y emisiones.
        5. **Energías**: Distribución de los tipos de energía utilizados para calefacción y ACS.
        6. **Correlaciones**: Matriz de correlación entre variables numéricas y resumen estadístico.
        7. **Ranking**: Ranking energético de los municipios según el score energético.
        8. **Datos**: Visualización y descarga de los datos filtrados.
        """
    )


# ==================================================
# TAB 2 - RESUMEN
# ==================================================

with tab2:

    st.subheader("Calificación energética")
    st.markdown("Esta visualización muestra la distribución de la calificación energética de los edificios en Álava. Permite identificar qué porcentaje de edificios se encuentra en cada categoría de eficiencia energética, desde A (más eficiente) hasta G (menos eficiente).")

    calif = df["Calificación energética"].value_counts().reset_index()
    calif.columns = ["Calificación", "Cantidad"]

    calif["Calificación"] = pd.Categorical(
        calif["Calificación"],
        categories=orden_calif,
        ordered=True
    )

    calif = calif.sort_values("Calificación")

    fig = px.bar(
        calif,
        x="Calificación",
        y="Cantidad",
        color="Calificación",
        color_discrete_map=colores_calificacion,
        text_auto=True
    )

    st.plotly_chart(fig, use_container_width=True)

with tab2:

    st.subheader("Calificación energética vs. Calificación de emisiones")
    st.markdown(
        """
        Esta visualización muestra la relación entre la calificación energética de los edificios y su calificación de emisiones. 
        Permite identificar si existe una correlación entre la eficiencia energética y las emisiones generadas por los edificios.
        """
    )

    calif = df["Calificación energética"].value_counts().reset_index()
    calif.columns = ["Calificación", "Cantidad"]

    fig = px.bar(
        calif,
        x="Calificación",
        y="Cantidad",
        color="Calificación",
        color_discrete_map=colores_calificacion,
        text_auto=True
    )

    st.plotly_chart(fig, use_container_width=True)

    emisiones = df["Calificación energ. emisiones"].value_counts().reset_index()
    emisiones.columns = ["Calificación", "Cantidad"]

    fig = px.bar(
        emisiones,
        x="Calificación",
        y="Cantidad",
        color="Calificación",
        color_discrete_map=colores_calificacion,
        text_auto=True
    )

    st.plotly_chart(fig, use_container_width=True)

# ==================================================
# TAB 3 - MUNICIPIOS
# ==================================================

with tab3:

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

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("Mapa interactivo de municipios")

    # Coordenadas aproximadas de municipios principales de Álava
    coords = {
        "Vitoria-Gasteiz": (42.8467, -2.6726),
        "Amurrio": (43.0526, -3.0007),
        "Laudio/Llodio": (43.1430, -2.9630),
        "Agurain/Salvatierra": (42.8500, -2.3900),
        "Alegría-Dulantzi": (42.9390, -2.5140),
        "Araia": (42.8950, -2.3130),
        "Artziniega": (43.1220, -3.1280),
        "Labastida": (42.5900, -2.7930),
        "Laguardia": (42.5540, -2.5850),
        "Oion": (42.5060, -2.4360),
        "Zuia": (42.9550, -2.8190)
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

        fig_map = px.scatter_mapbox(
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
            mapbox_style="carto-positron"
        )

        fig_map.update_layout(
            margin=dict(l=0, r=0, t=30, b=0)
        )

        st.plotly_chart(
            fig_map,
            use_container_width=True
        )

    else:
        st.info(
            "No hay coordenadas disponibles para los municipios seleccionados."
        )

    st.subheader("Mapa de calor: Municipio vs Calificación")

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

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Mapa de calor: Consumo vs Emisiones")

    fig = px.density_heatmap(
    df,
    x="Consumo anual",
    y="Emisiones anuales",
    nbinsx=40,
    nbinsy=40,
    color_continuous_scale="Turbo"
    )

    st.plotly_chart(fig, use_container_width=True)


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

# ==================================================
# TAB 4 - CONSUMO
# ==================================================

with tab4:

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

    fig = px.scatter(
        df,
        x="Consumo anual",
        y="Emisiones anuales",
        color="Tipo edificio",
        size="Superficie habitable",
        hover_data=["Municipio"]
        # ❌ sin trendline para evitar dependencia statsmodels
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Distribución consumo")

    st.plotly_chart(
        px.histogram(df, x="Consumo anual", nbins=40),
        use_container_width=True
    )

    st.subheader("Distribución emisiones")

    st.plotly_chart(
        px.histogram(df, x="Emisiones anuales", nbins=40),
        use_container_width=True
    )


# ==================================================
# TAB 5 - TIPOLOGÍA
# ==================================================

with tab5:

    tipos = df["Tipo edificio"].value_counts().reset_index()
    tipos.columns = ["Tipo edificio", "Cantidad"]

    st.plotly_chart(
        px.bar(tipos, x="Tipo edificio", y="Cantidad", text_auto=True),
        use_container_width=True
    )

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(
            px.box(df, x="Tipo edificio", y="Consumo anual"),
            use_container_width=True
        )

    with col2:
        st.plotly_chart(
            px.box(df, x="Tipo edificio", y="Emisiones anuales"),
            use_container_width=True
        )

# ==================================================
# TAB 6 - ENERGÍAS
# ==================================================

with tab6:

    calefaccion = df["Cal. Tipo Energia"].value_counts().head(10).reset_index()
    calefaccion.columns = ["Energía", "Cantidad"]

    acs = df["ACS Tipo Energia"].value_counts().head(10).reset_index()
    acs.columns = ["Energía", "Cantidad"]

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(
            px.pie(calefaccion, names="Energía", values="Cantidad"),
            use_container_width=True
        )

    with col2:
        st.plotly_chart(
            px.pie(acs, names="Energía", values="Cantidad"),
            use_container_width=True
        )

# ==================================================
# TAB 7 - CORRELACIONES (mejor orden)
# ==================================================

with tab7:

    st.subheader("Correlación entre variables")

    numericas = df.select_dtypes(include="number")
    numericas = numericas.loc[:, numericas.nunique() > 1]

    corr = numericas.corr()

    fig = px.imshow(
        corr,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="Blues"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Resumen estadístico")
    st.dataframe(numericas.describe(), use_container_width=True)


# ==================================================
# TAB 8 - RANKING ENERGÉTICO
# ==================================================

with tab8:

    st.subheader("Ranking energético")

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
        use_container_width=True
    )

    st.dataframe(
        ranking.round(2),
        use_container_width=True
    )

# ==================================================
# TAB 9 - DATOS
# ==================================================

with tab9:

    st.subheader("Datos filtrados")

    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Descargar datos filtrados",
        csv,
        "certificados_filtrados.csv",
        "text/csv"
    )

