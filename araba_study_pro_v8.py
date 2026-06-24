import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans

# =========================
# CONFIG
# =========================

st.set_page_config("Energy Dashboard ULTRA PRO", layout="wide")

st.title("🏠 Energy Certificates Dashboard - ULTRA PRO")

# =========================
# DATA CACHE
# =========================

@st.cache_data
def load_data():
    df = pd.read_csv("data_araba_cleaned.csv")
    df = df.loc[:, df.nunique(dropna=False) > 1]
    return df

df_total = load_data()

# =========================
# SCORE ENGINE PRO
# =========================

def safe_norm(col):
    denom = col.max() - col.min()
    return pd.Series(50, index=col.index) if denom == 0 else (col.max() - col) / denom * 100


def compute_score(df):
    mapc = {"A":100,"B":85,"C":70,"D":55,"E":40,"F":25,"G":10}

    return (
        df["Calificación energética"].map(mapc).fillna(0) * 0.45 +
        df["Calificación energ. emisiones"].map(mapc).fillna(0) * 0.30 +
        safe_norm(df["Consumo anual"]) * 0.15 +
        safe_norm(df["Emisiones anuales"]) * 0.10
    ).round(1)

# =========================
# FILTER ENGINE (CACHE KEY)
# =========================

@st.cache_data
def filter_data(df, muni, tipo, year, sup):

    dff = df.copy()

    if muni:
        dff = dff[dff["Municipio"].isin(muni)]

    if tipo:
        dff = dff[dff["Tipo edificio"].isin(tipo)]

    dff = dff[
        dff["Año construcción"].between(*year) &
        dff["Superficie habitable"].between(*sup)
    ]

    return dff

# =========================
# SIDEBAR
# =========================

st.sidebar.header("🎛 Filtros")

df = df_total.copy()

municipios = st.sidebar.multiselect(
    "Municipio",
    sorted(df["Municipio"].dropna().unique()),
    default=None
)

tipos = st.sidebar.multiselect(
    "Tipo edificio",
    sorted(df["Tipo edificio"].dropna().unique()),
    default=None
)

year_range = st.sidebar.slider(
    "Año construcción",
    int(df["Año construcción"].min()),
    int(df["Año construcción"].max()),
    (int(df["Año construcción"].min()), int(df["Año construcción"].max()))
)

sup_range = st.sidebar.slider(
    "Superficie",
    int(df["Superficie habitable"].min()),
    int(df["Superficie habitable"].max()),
    (int(df["Superficie habitable"].min()), int(df["Superficie habitable"].max()))
)

df = filter_data(df_total, municipios, tipos, year_range, sup_range)

df["Score"] = compute_score(df)
df_total["Score"] = compute_score(df_total)

# =========================
# KPI ENGINE PRO
# =========================

st.subheader("📊 KPIs Inteligentes")

def kpi(col, name):
    return col.mean(), col.mean() - df_total[col.name].mean()

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Certificados", len(df), f"{len(df)/len(df_total):.1%}")

c2.metric("Consumo", f"{df['Consumo anual'].mean():.1f}",
          f"{df['Consumo anual'].mean()-df_total['Consumo anual'].mean():.1f}")

c3.metric("Emisiones", f"{df['Emisiones anuales'].mean():.1f}",
          f"{df['Emisiones anuales'].mean()-df_total['Emisiones anuales'].mean():.1f}")

c4.metric("Score", f"{df['Score'].mean():.1f}",
          f"{df['Score'].mean()-df_total['Score'].mean():.1f}")

c5.metric("Eficiencia", f"{(df['Score'].mean()/100):.2f}")

st.divider()

# =========================
# CLUSTERING (ULTRA FEATURE)
# =========================

st.subheader("🧠 Clustering de municipios")

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

st.plotly_chart(fig, use_container_width=True)

# =========================
# MAPA INTELIGENTE
# =========================

st.subheader("🗺️ Mapa energético")

coords = {
    "Vitoria-Gasteiz": (42.8467, -2.6726),
    "Amurrio": (43.0526, -3.0007),
    "Laudio/Llodio": (43.1430, -2.9630),
    "Agurain/Salvatierra": (42.85, -2.39),
}

map_df = df.groupby("Municipio").agg(
    Certificados=("Municipio","count"),
    Score=("Score","mean")
).reset_index()

map_df["lat"] = map_df["Municipio"].map(lambda x: coords.get(x,(None,None))[0])
map_df["lon"] = map_df["Municipio"].map(lambda x: coords.get(x,(None,None))[1])

map_df = map_df.dropna()

fig = px.scatter_mapbox(
    map_df,
    lat="lat",
    lon="lon",
    size="Certificados",
    color="Score",
    zoom=7,
    mapbox_style="carto-positron",
    hover_name="Municipio"
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# RANKING ULTRA PRO
# =========================

st.subheader("🏆 Ranking inteligente")

ranking = cluster_data.sort_values("Score", ascending=False)

st.dataframe(ranking)

st.plotly_chart(
    px.bar(
        ranking.head(15),
        y=ranking.head(15).index,
        x="Score",
        orientation="h",
        color="Score",
        color_continuous_scale="RdYlGn"
    ),
    use_container_width=True
)

# =========================
# INSIGHTS AUTOMÁTICOS
# =========================

st.subheader("🧠 Insights automáticos")

best = ranking.index[0]
worst = ranking.index[-1]

st.success(f"🏆 Mejor municipio: {best}")
st.error(f"⚠️ Peor municipio: {worst}")

st.info(
    f"📊 Diferencia de score: "
    f"{ranking['Score'].max() - ranking['Score'].min():.1f} puntos"
)

# =========================
# EXPORT
# =========================

st.download_button(
    "⬇️ Descargar dataset",
    df.to_csv(index=False).encode("utf-8"),
    "energy_ultra_pro.csv"
)