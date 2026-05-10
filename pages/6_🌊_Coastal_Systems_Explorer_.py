import streamlit as st
import leafmap.foliumap as leafmap
import geopandas as gpd
import requests
import tempfile
import os
from folium.plugins import Draw, MeasureControl

st.set_page_config(layout="wide", page_title="Coastal Systems Explorer")

# -------------------------------------------------------------------
# Title and description
# -------------------------------------------------------------------
st.title("🌊 Coastal Systems Explorer: La Paz & Cabo Pulmo")

st.markdown(
    """
    An interactive geo-inquiry tool for exploring two coastal places along the **Baja California Sur** coast.
    Compare the mangrove and harbor systems of **La Paz Bay** with the community-led marine reserve at **Cabo Pulmo** —
    two places connected by the same sea, shaped by very different histories of protection and use.
    """
)

# -------------------------------------------------------------------
# Custom CSS
# -------------------------------------------------------------------
st.markdown(
    """
    <style>
    input[type="checkbox"] {
        transform: scale(1.3);
        margin-right: 8px;
    }
    .stCheckbox label {
        font-size: 1.05rem;
        font-weight: 500;
    }
    section[data-testid="stSidebar"] .stMarkdown h3 {
        font-size: 1.3rem;
        font-weight: 650;
        margin-bottom: 0.3rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# Sidebar — layer controls and settings ONLY
# -------------------------------------------------------------------
with st.sidebar:

    site_choice = st.radio(
        "Active site:",
        ["La Paz harbor", "Cabo Pulmo", "Compare both"],
        index=0,
    )

    st.markdown("---")

    if site_choice in ["La Paz harbor", "Compare both"]:
        st.markdown("### La Paz layers")
        show_mangroves = st.checkbox("Mangrove habitat", value=True)
        show_harbor    = st.checkbox("Port & marina development", value=True)
        show_lapaz_mpa = st.checkbox("Bay of La Paz biosphere reserve", value=False)
    else:
        show_mangroves = False
        show_harbor    = False
        show_lapaz_mpa = False

    if site_choice in ["Cabo Pulmo", "Compare both"]:
        st.markdown("### Cabo Pulmo layers")
        show_cabo_mpa  = st.checkbox("Marine park boundary", value=True)
    else:
        show_cabo_mpa  = False

    st.markdown("---")
    st.markdown("### Map settings")

    basemap_choice = st.selectbox(
        "Select a basemap:",
        list(leafmap.basemaps.keys()),
        index=list(leafmap.basemaps.keys()).index("SATELLITE"),
    )

    show_draw    = st.checkbox(
        "Drawing tools", value=True,
        help="Sketch polygons, lines, and markers directly on the map. Drawings are not saved when the page reloads."
    )
    show_measure = st.checkbox(
        "Measure distances & areas", value=False,
        help="Click points on the map to measure distances in km or areas in km²."
    )

    st.markdown("---")
    with st.expander("About the data"):
        st.markdown(
            """
            **Mangroves:** The Nature Conservancy (TNC) — clipped to the Port of La Paz area.  
            **Marine park:** CONANP / WDPA (Protected Planet).  
            **Harbor development:** Illustrative — derived from satellite imagery.  
            **Community settlement:** Illustrative — approximate extent.  

            *Layers marked as illustrative use approximate geometries and should not
            be used for legal or decision-making purposes.*
            """
        )

# -------------------------------------------------------------------
# Fallback / illustrative GeoJSON
# -------------------------------------------------------------------
HARBOR_DEV_FALLBACK = {
    "type": "FeatureCollection",
    "features": [
        {"type": "Feature", "properties": {"name": "La Paz waterfront & marina"},
         "geometry": {"type": "Polygon", "coordinates": [[
             [-110.318, 24.175], [-110.310, 24.185], [-110.305, 24.180],
             [-110.312, 24.170], [-110.318, 24.175]]]}},
        {"type": "Feature", "properties": {"name": "Port terminal"},
         "geometry": {"type": "Polygon", "coordinates": [[
             [-110.310, 24.167], [-110.305, 24.172], [-110.300, 24.168],
             [-110.306, 24.163], [-110.310, 24.167]]]}},
    ]
}

LAPAZ_MPA_GEOJSON = {
    "type": "FeatureCollection",
    "features": [{"type": "Feature",
                  "properties": {"name": "Bay of La Paz biosphere reserve (approx.)"},
                  "geometry": {"type": "Polygon", "coordinates": [[
                      [-110.520, 24.280], [-110.350, 24.300], [-110.250, 24.100],
                      [-110.280, 24.040], [-110.450, 24.050], [-110.550, 24.150],
                      [-110.520, 24.280]]]}}]
}

# -------------------------------------------------------------------
# Data loading with fallback
# -------------------------------------------------------------------
MANGROVE_URL = (
    "https://raw.githubusercontent.com/asivitskis/EarthInquiryLab/"
    "main/data/bcs_coastal_ed_data/LP_TNC_mangrove.json"
)
CABO_MPA_URL = (
    "https://raw.githubusercontent.com/asivitskis/EarthInquiryLab/"
    "main/data/bcs_coastal_ed_data/CaboPulmo_Boundary_CONANP.json"
)

@st.cache_data(show_spinner="Loading spatial data…")
def load_geojson_with_fallback(url, fallback_dict):
    try:
        if not url:
            raise ValueError("No URL provided")
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        gdf = gpd.GeoDataFrame.from_features(r.json()["features"], crs="EPSG:4326")
        if gdf.empty:
            raise ValueError("Empty dataset returned")
        return gdf, False
    except Exception:
        gdf = gpd.GeoDataFrame.from_features(fallback_dict["features"], crs="EPSG:4326")
        return gdf, True

# Mangrove color map — keyed on Cmbio81_20 field
MANGROVE_COLOR_DICT = {
    "Pérdida de manglar":   "#ea0c00",   # red   — loss
    "Manglar sin cambios":  "#027433",   # green — no change
    "Ganancia de manglar":  "#00fb15",   # lime  — gain
}

def mangrove_style_callback(feature):
    value = feature["properties"].get("Cmbio81_20", "")
    return {
        "color": "black",
        "weight": 0.5,
        "fillColor": MANGROVE_COLOR_DICT.get(value, "#888888"),
        "fillOpacity": 0.8,
    }

mangrove_hover_style = {"weight": 2, "color": "yellow", "fillOpacity": 0.9}
harbor_gdf,    _ = load_geojson_with_fallback("", HARBOR_DEV_FALLBACK)

# -------------------------------------------------------------------
# Map center & zoom
# -------------------------------------------------------------------
if site_choice == "La Paz harbor":
    center, zoom = [24.14, -110.36], 13
elif site_choice == "Cabo Pulmo":
    center, zoom = [23.438124935783712, -109.42855096911228], 12
else:
    center, zoom = [23.85, -110.10], 9

# -------------------------------------------------------------------
# Styles
# -------------------------------------------------------------------
harbor_style    = {"color": "#993C1D", "fillColor": "#D85A30", "fillOpacity": 0.45, "weight": 1}
harbor_hover    = {"fillOpacity": 0.65, "weight": 2}
lapaz_mpa_style = {"color": "#18A550", "fillColor": "#DDC137", "fillOpacity": 0.08,
                   "weight": 2, "dashArray": "6 4"}
# -------------------------------------------------------------------
# Build map
# -------------------------------------------------------------------
m = leafmap.Map(center=center, zoom=zoom)
m.add_basemap(basemap_choice)

legend_dict = {}

if show_mangroves:
    m.add_vector(
        MANGROVE_URL,
        layer_name="Mangrove habitat",
        style_callback=mangrove_style_callback,
        hover_style=mangrove_hover_style,
        info_mode="on_hover",
        zoom_to_layer=False,
    )
    legend_dict["Mangrove habitat — loss"]      = "#ea0c00"
    legend_dict["Mangrove habitat — no change"] = "#027433"
    legend_dict["Mangrove habitat — gain"]      = "#00fb15"

if show_harbor:
    m.add_gdf(harbor_gdf, style=harbor_style, hover_style=harbor_hover,
              layer_name="Port & marina development", info_mode="on_hover", zoom_to_layer=False)
    legend_dict["Port & marina development"] = "#D85A30"

if show_lapaz_mpa:
    m.add_geojson(LAPAZ_MPA_GEOJSON, layer_name="La Paz biosphere reserve",
                  style=lapaz_mpa_style, info_mode=None, zoom_to_layer=False)
    legend_dict["La Paz biosphere reserve"] = "#378ADD"

if show_cabo_mpa:
    m.add_vector(
        CABO_MPA_URL,
        layer_name="Marine park boundary",
        style={"color": "#000000", "fillColor": "#FF6B35", "fillOpacity": 0.50,
               "weight": 2, "dashArray": "6 4"},
        hover_style={"fillOpacity": 0.25, "weight": 3},
        info_mode="on_hover",
        zoom_to_layer=False,
    )
    legend_dict["Marine park boundary"] = "#FF6B35"

if legend_dict:
    m.add_legend(title="Map key", legend_dict=legend_dict, position="bottomright")

# Drawing tools — added to underlying Folium map object
if show_draw:
    Draw(
        export=False,
        draw_options={
            "polyline":     {"shapeOptions": {"color": "#e63946", "weight": 3}},
            "polygon":      {"shapeOptions": {"color": "#e63946", "weight": 2, "fillOpacity": 0.15}},
            "rectangle":    {"shapeOptions": {"color": "#e63946", "weight": 2, "fillOpacity": 0.15}},
            "circle":       {"shapeOptions": {"color": "#e63946", "weight": 2, "fillOpacity": 0.10}},
            "marker":       True,
            "circlemarker": False,
        },
        edit_options={"edit": True, "remove": True},
    ).add_to(m)

if show_measure:
    MeasureControl(
        primary_length_unit="kilometers",
        secondary_length_unit="miles",
        primary_area_unit="sqkilometers",
        secondary_area_unit="acres",
    ).add_to(m)

# -------------------------------------------------------------------
# Render map via HTML export (preserves Draw plugin correctly)
# -------------------------------------------------------------------
map_html = m.to_html()
st.components.v1.html(map_html, height=680, scrolling=False)

# Download map button
with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
    f.write(map_html)
    tmp_path = f.name

with open(tmp_path, "rb") as f:
    st.download_button(
        label="⬇️ Download map as HTML",
        data=f,
        file_name=f"coastal_explorer_{site_choice.lower().replace(' ', '_')}.html",
        mime="text/html",
        help="Download the current map as a standalone HTML file — open it in any browser, even offline.",
    )
os.unlink(tmp_path)

# -------------------------------------------------------------------
# Inquiry prompts — below the map, two-column layout
# -------------------------------------------------------------------
st.markdown("---")
st.subheader("🔍 Inquiry prompts")

if site_choice == "La Paz harbor":
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            """
            **Observe the map**
            - Where do mangrove patches remain, and where have they been displaced by development?
            - Which mangrove areas appear most isolated or fragmented?
            - What patterns do you notice about the relationship between the port and the mangroves?
            """
        )
    with col_b:
        st.markdown(
            """
            **Go deeper**
            - Mangroves are sometimes called "nurseries of the sea." What does their fragmentation mean for the broader bay system?
            - What questions does this map raise that you'd want to explore during the OPRE mangrove tour?
            - What data is *missing* from this map that would help you understand this system better?
            """
        )

elif site_choice == "Cabo Pulmo":
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            """
            **Observe the map**
            - Where does the marine park boundary fall relative to reef habitat?
            - How does the community settlement relate spatially to the protected area?
            - Where would you place a no-take zone, based on what you can see?
            """
        )
    with col_b:
        st.markdown(
            """
            **Go deeper**
            - In 1995, the Cabo Pulmo community stopped fishing and advocated for marine park status. Reef biomass has increased by over 460% since then. What spatial patterns might reflect that recovery?
            - What would this place look like without the marine park? What systems thinking tools help you reason about that counterfactual?
            - What can't this map tell you about what happened here?
            """
        )

else:  # Compare both
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown(
            """
            **Compare the two places**
            - What is similar about the pressures La Paz and Cabo Pulmo face?
            - What looks different about how each place has responded?
            - Where do you see more fragmentation? More protection?
            """
        )
    with col_b:
        st.markdown(
            """
            **Systems thinking**
            - Where are the leverage points in each system?
            - What feedback loops might be reinforcing the current trajectory of each place?
            - How does community governance show up — or not — in each map?
            """
        )
    with col_c:
        st.markdown(
            """
            **Curriculum design**
            - What is the one tension you'd most want learners to sit with?
            - What local knowledge is entirely absent from these datasets?
            - How would you involve the Cabo Pulmo community in deciding what this map shows?
            """
        )

# -------------------------------------------------------------------
# Observation text area
# -------------------------------------------------------------------
st.markdown("---")
st.subheader("📝 Record your observations")

obs_col, tip_col = st.columns([2, 1])
with obs_col:
    st.text_area(
        f"Your observations — {site_choice}",
        placeholder="What do you notice? What patterns stand out? What questions does the map raise for you?",
        height=140,
        key="observation_box",
    )
with tip_col:
    st.info(
        "💡 Use the **drawing tools** on the map above to sketch patterns you notice — "
        "trace mangrove edges, mark interesting intersections, or drop a pin on something worth discussing.\n\n"
        "*Drawings are visible during your session but are not saved when the page reloads.*"
    )

# -------------------------------------------------------------------
# Data note footer
# -------------------------------------------------------------------
st.markdown("---")
st.caption(
    "**Data sources:** La Paz mangroves — The Nature Conservancy (TNC), clipped to Port of La Paz area · "
    "CONANP / WDPA Protected Planet · "
    "Illustrative layers derived from satellite imagery and published survey data. "
    "All data are for educational purposes only and should not be used for legal or decision-making purposes."
)
