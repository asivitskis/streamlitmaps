import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import requests

GEOJSON_URL = (
    "https://raw.githubusercontent.com/"
    "asivitskis/wr-creel-study/refs/heads/main/data/kc_data.geojson"
)

st.set_page_config(layout="wide")

st.title("KR Fish Creel Study")

@st.cache_data
def load_data():
    gdf = gpd.read_file(GEOJSON_URL)
    gdf["Entrydate"] = pd.to_datetime(gdf["Entrydate"], errors="coerce")
    return gdf

gdf = load_data()

# ── Metrics ────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Fish", len(gdf))
col2.metric("Lake Trout",  (gdf["Species"] == "Lake_Trout").sum())
col3.metric("Brook Trout", (gdf["Species"] == "Brook_Trout").sum())
col4.metric("Average Length", f"{gdf['Length'].mean():.1f} in")

# ── Charts ─────────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    species_counts = gdf["Species"].value_counts().reset_index()
    species_counts.columns = ["Species", "Count"]
    fig = px.pie(species_counts, names="Species", values="Count",
                 title="Species Composition")
    st.plotly_chart(fig, use_container_width=True)

with col2:  # only defined once now
    fig = px.histogram(gdf, x="Length", nbins=10,
                       title="Fish Length Distribution")
    st.plotly_chart(fig, use_container_width=True)

# ── Photos ─────────────────────────────────────────────────────────────────────
st.header("Fish Photos")

photos = gdf["git_photo"].dropna().unique().tolist()
valid_photos = []
for url in photos:
    try:
        r = requests.head(url, timeout=5)
        if r.status_code == 200:
            valid_photos.append(url)
    except Exception:
        pass

if valid_photos:
    cols = st.columns(3)
    for i, photo in enumerate(valid_photos):
        with cols[i % 3]:
            st.image(photo, use_container_width=True)
else:
    st.info("No photos could be loaded. Check that `git_photo` URLs are publicly accessible.")

# ── Observations table ─────────────────────────────────────────────────────────
st.header("Observations")

display_cols = ["Species", "Length", "Weight", "Entrydate", "git_photo"]
st.dataframe(gdf[display_cols], use_container_width=True)

# ── Map ────────────────────────────────────────────────────────────────────────
st.header("Observation Map")

# px.scatter_map was added in Plotly 5.19; scatter_mapbox is more widely
# supported in typical Streamlit deployments.
fig = px.scatter_mapbox(
    gdf,
    lat=gdf.geometry.y,
    lon=gdf.geometry.x,
    color="Species",
    hover_data=["Length", "Weight"],
    zoom=13,
)
fig.update_layout(
    mapbox_style="open-street-map",
    height=600,
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
)
st.plotly_chart(fig, use_container_width=True)