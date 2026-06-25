import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import requests

GEOJSON_URL = (
    "https://raw.githubusercontent.com/"
    "asivitskis/wr-creel-study/refs/heads/main/data/kc_data.geojson"
)

ESRI_SATELLITE = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/"
    "World_Imagery/MapServer/tile/{z}/{y}/{x}"
)

st.set_page_config(layout="wide")

st.title("🎣 Koenig Creek Fish Creel Study")

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

# ── Summary ────────────────────────────────────────────────────────────────────
st.markdown("---")

lake_n   = int((gdf["Species"] == "Lake_Trout").sum())
brook_n  = int((gdf["Species"] == "Brook_Trout").sum())
total_n  = len(gdf)
avg_len  = gdf["Length"].mean()
avg_wt   = gdf["Weight"].mean()
max_len  = gdf["Length"].max()
date_min = gdf["Entrydate"].min()
date_max = gdf["Entrydate"].max()

dominant = "Lake Trout" if lake_n >= brook_n else "Brook Trout"
dom_pct  = max(lake_n, brook_n) / total_n * 100

st.markdown(
    f"""
    **Study Summary** &nbsp;|&nbsp;
    {total_n} fish recorded between
    {date_min.strftime('%b %d') if pd.notna(date_min) else '?'} –
    {date_max.strftime('%b %d, %Y') if pd.notna(date_max) else '?'}.
    The catch is dominated by **{dominant}** ({dom_pct:.0f}% of observations).
    Mean length was **{avg_len:.1f} in** (max {max_len:.1f} in)
    and mean weight was **{avg_wt:.2f} lbs**.
    All observations were georeferenced along Koenig Creek.
    """
)

st.markdown("---")

# ── Map (center) flanked by charts ────────────────────────────────────────────
left, center, right = st.columns([1, 2, 1])

with left:
    st.subheader("Species Composition")
    species_counts = gdf["Species"].value_counts().reset_index()
    species_counts.columns = ["Species", "Count"]
    fig_pie = px.pie(
        species_counts,
        names="Species",
        values="Count",
        hole=0.3,
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig_pie.update_layout(
        margin={"r": 0, "t": 10, "l": 0, "b": 0},
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
        height=260,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("Length Distribution")
    fig_hist = px.histogram(
        gdf, x="Length", nbins=10,
        color_discrete_sequence=["#4C8CBF"],
    )
    fig_hist.update_layout(
        margin={"r": 0, "t": 10, "l": 0, "b": 0},
        xaxis_title="Length (in)",
        yaxis_title="Count",
        height=240,
    )
    st.plotly_chart(fig_hist, use_container_width=True)

with center:
    st.subheader("Observation Map")
    center_lat = gdf.geometry.y.mean()
    center_lon = gdf.geometry.x.mean()

    fig_map = px.scatter_mapbox(
        gdf,
        lat=gdf.geometry.y,
        lon=gdf.geometry.x,
        color="Species",
        hover_data=["Length", "Weight"],
        zoom=13,
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig_map.update_layout(
        mapbox=dict(
            style="white-bg",
            zoom=13,
            center={"lat": center_lat, "lon": center_lon},
            layers=[{
                "below": "traces",
                "sourcetype": "raster",
                "source": [ESRI_SATELLITE],
                "sourceattribution": "Esri World Imagery",
            }],
        ),
        height=580,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.01,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(0,0,0,0.5)",
            font=dict(color="white"),
        ),
    )
    st.plotly_chart(fig_map, use_container_width=True)

with right:
    st.subheader("Length by Species")
    fig_box = px.box(
        gdf, x="Species", y="Length",
        color="Species",
        color_discrete_sequence=px.colors.qualitative.Safe,
        points="all",
    )
    fig_box.update_layout(
        margin={"r": 0, "t": 10, "l": 0, "b": 0},
        showlegend=False,
        xaxis_title="",
        yaxis_title="Length (in)",
        height=260,
    )
    st.plotly_chart(fig_box, use_container_width=True)

    st.subheader("Weight by Species")
    fig_box2 = px.box(
        gdf, x="Species", y="Weight",
        color="Species",
        color_discrete_sequence=px.colors.qualitative.Safe,
        points="all",
    )
    fig_box2.update_layout(
        margin={"r": 0, "t": 10, "l": 0, "b": 0},
        showlegend=False,
        xaxis_title="",
        yaxis_title="Weight (lbs)",
        height=240,
    )
    st.plotly_chart(fig_box2, use_container_width=True)

st.markdown("---")

# ── Photos ─────────────────────────────────────────────────────────────────────
st.subheader("📷 Fish Photos")

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
    # 5-column grid, smaller images via fixed width
    n_cols = 5
    cols = st.columns(n_cols)
    for i, photo in enumerate(valid_photos):
        with cols[i % n_cols]:
            st.image(photo, width=160)
else:
    st.info("No photos could be loaded — check that `git_photo` URLs are publicly accessible.")

st.markdown("---")

# ── Observations table ─────────────────────────────────────────────────────────
st.subheader("📋 Observations")

display_cols = ["Species", "Length", "Weight", "Entrydate", "git_photo"]
st.dataframe(gdf[display_cols], use_container_width=True)