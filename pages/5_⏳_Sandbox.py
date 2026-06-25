import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import requests
import folium
from folium.plugins import Fullscreen, MeasureControl
from streamlit_folium import st_folium

GEOJSON_URL = (
    "https://raw.githubusercontent.com/"
    "asivitskis/wr-creel-study/refs/heads/main/data/kc_data.geojson"
)

# ── Single shared colour palette ───────────────────────────────────────────────
# Keys match the raw Species values in the GeoJSON
SPECIES_COLORS = {
    "Brook_Trout": "#117733",
    "Lake_Trout":  "#88CCEE",
}

# Human-readable labels for display
SPECIES_LABELS = {
    "Brook_Trout": "Brook Trout",
    "Lake_Trout":  "Lake Trout",
}

st.set_page_config(layout="wide")
st.title("Kirkland Lake Creel Study")

@st.cache_data
def load_data():
    gdf = gpd.read_file(GEOJSON_URL)
    gdf["Entrydate"] = pd.to_datetime(gdf["Entrydate"], errors="coerce")
    # Add a display label column for nicer chart axes/legends
    gdf["Species_Label"] = gdf["Species"].map(SPECIES_LABELS).fillna(gdf["Species"])
    return gdf

gdf = load_data()

# Plotly needs color_discrete_map keyed on whatever column is passed as `color`
PLOTLY_COLOR_MAP = {SPECIES_LABELS[k]: v for k, v in SPECIES_COLORS.items()}

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
    species_counts = (
        gdf["Species_Label"].value_counts().reset_index()
    )
    species_counts.columns = ["Species", "Count"]
    fig_pie = px.pie(
        species_counts,
        names="Species",
        values="Count",
        hole=0.3,
        color="Species",
        color_discrete_map=PLOTLY_COLOR_MAP,
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
        color="Species_Label",
        color_discrete_map=PLOTLY_COLOR_MAP,
        barmode="overlay",
    )
    fig_hist.update_layout(
        margin={"r": 0, "t": 10, "l": 0, "b": 0},
        xaxis_title="Length (in)",
        yaxis_title="Count",
        legend_title="Species",
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
        zoom_start=12,
        tiles=None,
        control_scale=True,
    )

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

    # Markers
    for _, row in gdf.iterrows():
        species = row.get("Species", "Unknown")
        length  = row.get("Length", "N/A")
        weight  = row.get("Weight", "N/A")
        color   = SPECIES_COLORS.get(species, "#888888")
        label   = SPECIES_LABELS.get(species, species)

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
            fill_opacity=0.9,
            popup=folium.Popup(popup_html, max_width=180),
            tooltip=f"{label} — {length} in",
        ).add_to(m)

    # HTML legend matching the shared palette
    legend_items = "".join(
        f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">'
        f'<div style="width:14px;height:14px;border-radius:50%;'
        f'background:{color};border:1.5px solid white;flex-shrink:0"></div>'
        f'<span>{SPECIES_LABELS[key]}</span></div>'
        for key, color in SPECIES_COLORS.items()
    )
    legend_html = f"""
    <div style="
        position: fixed;
        topleft: 36px; left: 10px; z-index: 9999;
        background: rgba(0,0,0,0.6);
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-family: sans-serif;
        font-size: 13px;
        line-height: 1.5;
    ">
      <b style="display:block;margin-bottom:4px">Species</b>
      {legend_items}
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    Fullscreen(position="topright").add_to(m)
    MeasureControl(position="bottomright", primary_length_unit="meters").add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    st_folium(m, use_container_width=True, height=580, returned_objects=[])

# ── Right: summary + length by species ────────────────────────────────────────
with right:
    st.subheader("Survey Summary")
    st.markdown(
        """
This creel study was conducted at Kirkland Lake on June 25, 2026 from 12:00pm to 1:00pm. Catch was predominantly
lake trout, with a smaller number of brook trout observed. The average length of fish caught was {:.1f} inches.
"""
    )

    st.subheader("Length by Species")
    fig_box = px.box(
        gdf, x="Species_Label", y="Length",
        color="Species_Label",
        color_discrete_map=PLOTLY_COLOR_MAP,
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