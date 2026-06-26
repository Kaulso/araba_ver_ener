import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# ==================================================
# CONFIG
# ==================================================

st.set_page_config(
    page_title="Certificados Energéticos de Álava",
    layout="wide"
)

st.title("🏠 Certificados Energéticos de Álava")

st.markdown(
    "Dashboard interactivo para analizar la eficiencia energética de edificios en Álava."
)

# ==================================================
# DATA
# ==================================================

@st.cache_data
def cargar_datos():
    df = pd.read_csv("data_araba_cleaned.csv")

    constantes = [
        c for c in df.columns
        if df[c].nunique(dropna=False) <= 1
    ]
    return df.drop(columns=constantes)


df_total = cargar_datos()

# ==================================================
# SCORE (ÚNICO Y LIMPIO)
# ==================================================

def safe_norm(col):
    denom = col.max() - col.min()
    if denom == 0:
        return pd.Series(50, index=col.index)
    return (1 - (col - col.min()) / denom) * 100


def calcular_score(df):
    mapc = {"A":100,"B":85,"C":70,"D":55,"E":40,"F":25,"G":10}

    return (
        df["Calificación energética"].map(mapc).fillna(0) * 0.4 +
        df["Calificación energ. emisiones"].map(mapc).fillna(0) * 0.3 +
        safe_norm(df["Consumo anual"]) * 0.15 +
        safe_norm(df["Emisiones anuales"]) * 0.15
    ).round(1)


# ==================================================
# FILTROS
# ==================================================

df = df_total.copy()

st.sidebar.image("Escudo_alava.png", width=200)

municipios = sorted(df["Municipio"].dropna().unique())
tipos = sorted(df["Tipo edificio"].dropna().unique())

municipio = st.sidebar.multiselect("Municipio", municipios)
tipo = st.sidebar.multiselect("Tipo edificio", tipos)

rango = st.sidebar.slider(
    "Año construcción",
    int(df["Año construcción"].min()),
    int(df["Año construcción"].max()),
    (int(df["Año construcción"].min()), int(df["Año construcción"].max()))
)

superficie = st.sidebar.slider(
    "Superficie (m²)",
    int(df["Superficie habitable"].min()),
    int(df["Superficie habitable"].max()),
    (int(df["Superficie habitable"].min()), int(df["Superficie habitable"].max()))
)

def aplicar_filtros(df):
    if municipio:
        df = df[df["Municipio"].isin(municipio)]
    if tipo:
        df = df[df["Tipo edificio"].isin(tipo)]

    return df[
        df["Año construcción"].between(*rango) &
        df["Superficie habitable"].between(*superficie)
    ]


df = aplicar_filtros(df_total)

df["Score energético"] = calcular_score(df)
df_total["Score energético"] = calcular_score(df_total)

# ==================================================
# KPIs
# ==================================================

st.subheader("📊 Indicadores generales")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Certificados", len(df))
c2.metric("Consumo medio", round(df["Consumo anual"].mean(), 1))
c3.metric("Emisiones medias", round(df["Emisiones anuales"].mean(), 1))
c4.metric("Superficie media", round(df["Superficie habitable"].mean(), 1))
c5.metric("Score energético", f"{df['Score energético'].mean():.1f}/100")

st.divider()

# ==================================================
# TABS
# ==================================================

tabs = st.tabs([
    "🏠 Inicio",
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
# TAB 1 - INTRO
# ==================================================

with tabs[0]:
    st.subheader("📌 Introducción")

    st.markdown("""
    Dashboard interactivo para analizar eficiencia energética en Álava.
    """)

# ==================================================
# TAB 2 - RESUMEN
# ==================================================

with tabs[1]:

    calif = df["Calificación energética"].value_counts().reset_index()
    calif.columns = ["Calificación", "Cantidad"]

    fig = px.bar(
        calif,
        x="Calificación",
        y="Cantidad",
        text_auto=True
    )

    st.plotly_chart(fig, use_container_width=True)

# ==================================================
# TAB 3 - MUNICIPIOS
# ==================================================

with tabs[2]:

    st.subheader("Municipios")

    top = df["Municipio"].value_counts().head(10).reset_index()
    top.columns = ["Municipio", "Certificados"]

    st.plotly_chart(
        px.bar(top, x="Certificados", y="Municipio", orientation="h"),
        use_container_width=True
    )

    # MAPA SIMPLE (optimizado)
    geo = gpd.read_file("municipios_alava.geojson")
    geo["Municipio"] = geo["MUNICIPIO"]

    ranking = df.groupby("Municipio").agg(
        Score=("Score energético", "mean"),
        Consumo=("Consumo anual", "mean"),
        Emisiones=("Emisiones anuales", "mean")
    ).reset_index()

    geo = geo.merge(ranking, on="Municipio", how="left")

    m = folium.Map(location=[42.85, -2.68], zoom_start=8)

    folium.Choropleth(
        geo_data=geo,
        data=geo,
        columns=["Municipio", "Score"],
        key_on="feature.properties.Municipio",
        fill_color="RdYlGn",
        fill_opacity=0.8
    ).add_to(m)

    st_folium(m, width=1000, height=600)

# ==================================================
# TAB 4 - CONSUMO + CLUSTERING (MEJORADO)
# ==================================================

with tabs[3]:

    st.subheader("Clustering de municipios")

    cluster = df.groupby("Municipio")[[
        "Consumo anual",
        "Emisiones anuales",
        "Score energético"
    ]].mean().dropna()

    scaler = StandardScaler()
    X = scaler.fit_transform(cluster)

    k = min(4, len(cluster))
    kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)

    cluster["Cluster"] = kmeans.fit_predict(X)

    fig = px.scatter(
        cluster,
        x="Consumo anual",
        y="Emisiones anuales",
        size="Score energético",
        color="Cluster",
        text=cluster.index
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Consumo vs Emisiones")

    st.plotly_chart(
        px.scatter(
            df,
            x="Consumo anual",
            y="Emisiones anuales",
            color="Tipo edificio",
            size="Superficie habitable"
        ),
        use_container_width=True
    )

# ==================================================
# TAB 5 - TIPOLOGÍA
# ==================================================

with tabs[4]:

    tipos = df["Tipo edificio"].value_counts().reset_index()
    tipos.columns = ["Tipo", "Cantidad"]

    st.plotly_chart(
        px.bar(tipos, x="Tipo", y="Cantidad", text_auto=True),
        use_container_width=True
    )

# ==================================================
# TAB 6 - ENERGÍAS
# ==================================================

with tabs[5]:

    calef = df["Cal. Tipo Energia"].value_counts().reset_index()
    calef.columns = ["Energía", "Cantidad"]

    acs = df["ACS Tipo Energia"].value_counts().reset_index()
    acs.columns = ["Energía", "Cantidad"]

    c1, c2 = st.columns(2)

    with c1:
        st.plotly_chart(px.pie(calef, names="Energía", values="Cantidad"))

    with c2:
        st.plotly_chart(px.pie(acs, names="Energía", values="Cantidad"))

# ==================================================
# TAB 7 - CORRELACIÓN
# ==================================================

with tabs[6]:

    num = df.select_dtypes(include="number")

    st.plotly_chart(
        px.imshow(num.corr(), text_auto=True, color_continuous_scale="Blues"),
        use_container_width=True
    )

    st.dataframe(num.describe())

# ==================================================
# TAB 8 - RANKING
# ==================================================

with tabs[7]:

    ranking = df.groupby("Municipio")["Score energético"].mean().sort_values(ascending=False)

    st.bar_chart(ranking)

    st.dataframe(ranking)

# ==================================================
# TAB 9 - DATOS
# ==================================================

with tabs[8]:

    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Descargar datos",
        csv,
        "datos.csv",
        "text/csv"
    )