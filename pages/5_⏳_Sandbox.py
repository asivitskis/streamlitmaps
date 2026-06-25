import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import requests
import folium
from streamlit_folium import st_folium

GEOJSON_URL = (
    "https://raw.githubusercontent.com/"
    "asivitskis/wr-creel-study/refs/heads/main/data/kc_data.geojson"
)

st.set_page_config(layout="wide")

st.title("🎣 Koenig Creek Fish Creel Study")

@st.cache_data
def load_data():
    gdf = gpd.read_file(GEOJSON_URL)
    gdf["Entrydate"] = pd.to_datetime(gdf["Entrydate"], errors="coerce")
    return gdf

gdf = load_data()

# ── Pre-compute summary values ─────────────────────────────────────────────────
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

# ── Metrics ────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Fish", total_n)
col2.metric("Lake Trout",  lake_n)
col3.metric("Brook Trout", brook_n)
col4.metric("Average Length", f"{avg_len:.1f} in")

st.markdown("---")

# ── Three-column layout ────────────────────────────────────────────────────────
left, center, right = st.columns([1, 2, 1])

# ── Left: charts ───────────────────────────────────────────────────────────────
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

# ── Center: Folium map ─────────────────────────────────────────────────────────
with center:
    st.subheader("Observation Map")

    center_lat = gdf.geometry.y.mean()
    center_lon = gdf.geometry.x.mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=14,
        tiles=None,          # suppress default tiles; add ESRI manually
        control_scale=True,  # scale bar bottom-left
    )

    # ESRI World Imagery satellite basemap
    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri World Imagery",
        name="Satellite",
        overlay=False,
        control=True,
    ).add_to(m)

    # Optional: ESRI labels overlay so creek names are visible
    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri",
        name="Labels",
        overlay=True,
        control=True,
        opacity=0.7,
    ).add_to(m)

    # Species colour mapping
    SPECIES_COLORS = {
        "Lake_Trout":  "#e07b39",
        "Brook_Trout": "#3b82c4",
    }

    for _, row in gdf.iterrows():
        species  = row.get("Species", "Unknown")
        length   = row.get("Length", "N/A")
        weight   = row.get("Weight", "N/A")
        color    = SPECIES_COLORS.get(species, "#888888")
        label    = species.replace("_", " ")

        popup_html = f"""
        <div style="font-family:sans-serif;font-size:13px;min-width:120px">
          <b>{label}</b><br>
          Length: {length} in<br>
          Weight: {weight} lbs
        </div>
        """

        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=7,
            color="white",
            weight=1.2,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=180),
            tooltip=f"{label} — {length} in",
        ).add_to(m)

    # Layer control (toggles Satellite / Labels)
    folium.LayerControl(collapsed=False).add_to(m)

    # Fullscreen plugin
    from folium.plugins import Fullscreen, MeasureControl
    Fullscreen(position="topright").add_to(m)
    MeasureControl(position="bottomright", primary_length_unit="meters").add_to(m)

    st_folium(m, use_container_width=True, height=580, returned_objects=[])

# ── Right: summary + length-by-species ────────────────────────────────────────
with right:
    st.subheader("📊 Study Summary")
    st.markdown(
        f"""
        **{total_n} fish** recorded  
        {date_min.strftime('%b %d') if pd.notna(date_min) else '?'} –
        {date_max.strftime('%b %d, %Y') if pd.notna(date_max) else '?'}

        Catch dominated by **{dominant}**  
        ({dom_pct:.0f}% of observations)

        | Stat | Value |
        |------|-------|
        | Mean length | {avg_len:.1f} in |
        | Max length | {max_len:.1f} in |
        | Mean weight | {avg_wt:.2f} lbs |
        | Lake Trout | {lake_n} |
        | Brook Trout | {brook_n} |

        All observations georeferenced  
        along Koenig Creek.
        """
    )

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
    n_cols = 5
    cols = st.columns(n_cols)
    for i, photo in enumerate(valid_photos):
        with cols[i % n_cols]:
            st.image(photo, width=160)
else:
    st.info("No photos could be loaded — check that `git_photo` URLs are publicly accessible.")