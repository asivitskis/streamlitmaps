import streamlit as st
import leafmap.foliumap as leafmap
import geopandas as gpd
import requests

st.set_page_config(layout="wide", page_title="Coastal Systems Explorer")

# -------------------------------------------------------------------
# Title and description
# -------------------------------------------------------------------
st.title("Coastal Systems Explorer: La Paz & Cabo Pulmo")

st.markdown(
    """
    An interactive geo-inquiry tool for exploring two coastal places along the **Baja California Sur** coast.
    Compare the mangrove and harbor systems of **La Paz Bay** with the community-led marine reserve at **Cabo Pulmo** —
    two places connected by the same sea, shaped by very different histories of protection and use.

    This tool is designed to support **place-based inquiry** and **systems thinking** in environmental education.
    Use the map layers to observe spatial patterns, then reflect using the inquiry prompts below.
    """
)

# -------------------------------------------------------------------
# Custom CSS — matching the Pipeline Explorer style
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
    .sidebar-instructions {
        font-size: 0.92rem;
        line-height: 1.4;
        color: #cccccc;
        margin-bottom: 0.75rem;
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
# Layout
# -------------------------------------------------------------------
col1, col2 = st.columns([4, 1])

# -------------------------------------------------------------------
# Data URLs
# -------------------------------------------------------------------

# Global Mangrove Watch 2020 — clipped to Baja California Sur
# Source: JAXA / Global Mangrove Watch via OpenDevelopment Mekong mirror / WCMC
MANGROVE_URL = (
    "https://raw.githubusercontent.com/opengeos/datasets/main/places/"
    "Baja_California_Sur_mangroves.geojson"
)

# Cabo Pulmo National Marine Park boundary — CONANP via OpenStreetMap/WDPA
# WDPA ID: 4208 — publicly accessible GeoJSON from Protected Planet
CABO_MPA_URL = (
    "https://raw.githubusercontent.com/opengeos/datasets/main/places/"
    "Cabo_Pulmo_NMP.geojson"
)

# Federally recognized Indigenous territories — BCS region
# Source: Native Land Digital public API (non-authoritative, illustrative only)
NATIVE_LANDS_URL = (
    "https://native-land.ca/api/index.php?maps=territories&position=24.1426,-110.3128"
)

# La Paz Bay boundary — derived from INEGI coastal polygon data
LAPAZ_BAY_URL = (
    "https://raw.githubusercontent.com/opengeos/datasets/main/places/"
    "La_Paz_Bay.geojson"
)

# -------------------------------------------------------------------
# Fallback GeoJSON — used if remote sources are unavailable
# (Approximate representative geometry for educational use)
# -------------------------------------------------------------------

MANGROVE_FALLBACK = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"name": "Ensenada de La Paz mangroves"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-110.380, 24.180], [-110.360, 24.200], [-110.340, 24.192],
                    [-110.345, 24.172], [-110.370, 24.162], [-110.380, 24.180]
                ]]
            }
        },
        {
            "type": "Feature",
            "properties": {"name": "Canal de San Lorenzo mangroves"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-110.400, 24.220], [-110.382, 24.232], [-110.372, 24.222],
                    [-110.388, 24.210], [-110.400, 24.220]
                ]]
            }
        },
        {
            "type": "Feature",
            "properties": {"name": "El Mogote mangroves"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-110.345, 24.140], [-110.328, 24.152], [-110.315, 24.142],
                    [-110.330, 24.130], [-110.345, 24.140]
                ]]
            }
        },
    ]
}

CABO_MPA_FALLBACK = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"name": "Cabo Pulmo National Marine Park", "WDPA_ID": "4208", "status": "Designated 1995"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-109.880, 23.470], [-109.820, 23.500], [-109.770, 23.445],
                    [-109.800, 23.400], [-109.870, 23.410], [-109.880, 23.470]
                ]]
            }
        }
    ]
}

CABO_REEF_FALLBACK = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"name": "El Bajo reef"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-109.865, 23.445], [-109.845, 23.455], [-109.835, 23.448],
                    [-109.850, 23.438], [-109.865, 23.445]
                ]]
            }
        },
        {
            "type": "Feature",
            "properties": {"name": "Los Frailes reef"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-109.855, 23.462], [-109.840, 23.470], [-109.830, 23.465],
                    [-109.845, 23.456], [-109.855, 23.462]
                ]]
            }
        },
    ]
}

HARBOR_DEV_FALLBACK = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"name": "La Paz waterfront & marina"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-110.318, 24.175], [-110.310, 24.185], [-110.305, 24.180],
                    [-110.312, 24.170], [-110.318, 24.175]
                ]]
            }
        },
        {
            "type": "Feature",
            "properties": {"name": "Port terminal"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-110.310, 24.167], [-110.305, 24.172], [-110.300, 24.168],
                    [-110.306, 24.163], [-110.310, 24.167]
                ]]
            }
        },
    ]
}

CABO_COMMUNITY_FALLBACK = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"name": "Cabo Pulmo village", "population": "~100 residents"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-109.875, 23.450], [-109.868, 23.455], [-109.862, 23.452],
                    [-109.868, 23.447], [-109.875, 23.450]
                ]]
            }
        }
    ]
}

# -------------------------------------------------------------------
# Data loading with fallback
# -------------------------------------------------------------------
@st.cache_data(show_spinner=True)
def load_geojson_with_fallback(url, fallback_dict, layer_name):
    """Attempt to load GeoJSON from URL; fall back to local dict if unavailable."""
    try:
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        gdf = gpd.GeoDataFrame.from_features(r.json()["features"], crs="EPSG:4326")
        if gdf.empty:
            raise ValueError("Empty dataset returned")
        return gdf, False
    except Exception:
        gdf = gpd.GeoDataFrame.from_features(fallback_dict["features"], crs="EPSG:4326")
        return gdf, True  # True = using fallback


# -------------------------------------------------------------------
# Sidebar controls
# -------------------------------------------------------------------
with col2:

    site_choice = st.radio(
        "Active site:",
        ["La Paz harbor", "Cabo Pulmo", "Compare both"],
        index=0,
    )

    st.markdown("---")

    # ===== La Paz layers =====
    if site_choice in ["La Paz harbor", "Compare both"]:
        st.markdown("### La Paz layers")
        show_mangroves = st.checkbox("Mangrove habitat", value=True)
        show_harbor    = st.checkbox("Port & marina development", value=True)
        show_lapaz_mpa = st.checkbox("Bay of La Paz biosphere reserve", value=False)
    else:
        show_mangroves = False
        show_harbor    = False
        show_lapaz_mpa = False

    # ===== Cabo Pulmo layers =====
    if site_choice in ["Cabo Pulmo", "Compare both"]:
        st.markdown("### Cabo Pulmo layers")
        show_cabo_mpa   = st.checkbox("Marine park boundary", value=True)
        show_reef       = st.checkbox("Reef habitat", value=True)
        show_community  = st.checkbox("Community settlement", value=True)
        show_notake     = st.checkbox("No-take buffer zone", value=False)
    else:
        show_cabo_mpa  = False
        show_reef      = False
        show_community = False
        show_notake    = False

    st.markdown("---")

    # ===== Basemap =====
    st.markdown("### Map settings")
    basemap_choice = st.selectbox(
        "Select a basemap:",
        list(leafmap.basemaps.keys()),
        index=list(leafmap.basemaps.keys()).index("SATELLITE"),
    )

    st.markdown("---")

    # ===== Inquiry Prompts =====
    with st.expander("Inquiry prompts — La Paz"):
        st.markdown(
            """
            - Where are the mangroves in relation to port and marina development?
            - Which mangrove patches appear most isolated or fragmented?
            - What pressures are visible from the map alone?
            - What data is *missing* that would help you understand this system better?
            """
        )

    with st.expander("Inquiry prompts — Cabo Pulmo"):
        st.markdown(
            """
            - Where does the marine park boundary fall relative to reef habitat?
            - How does the community settlement relate to the protected area?
            - What spatial patterns suggest the reserve is — or isn't — working?
            - What would you want to know that this map can't tell you?
            """
        )

    with st.expander("Comparison prompts"):
        st.markdown(
            """
            - What is similar about the pressures these two places face?
            - What role does community governance play in each? What might explain different outcomes?
            - Where do you see feedback loops — reinforcing or balancing — in each system?
            - If you were designing curriculum here, what tensions would you want learners to sit with?
            """
        )

    st.markdown("---")

    with st.expander("About the data"):
        st.markdown(
            """
            **Mangroves:** Global Mangrove Watch 2020 (JAXA).  
            **Marine park:** CONANP / WDPA (Protected Planet).  
            **Reef habitat:** Illustrative — based on published reef survey locations.  
            **Harbor development:** Illustrative — derived from satellite imagery.  
            **Community settlement:** Illustrative — approximate extent.  

            *All data are for educational purposes only. Layers marked as illustrative 
            use approximate geometries and should not be used for legal or 
            decision-making purposes.*
            """
        )

# -------------------------------------------------------------------
# Load data
# -------------------------------------------------------------------
mangrove_gdf, mangrove_fallback     = load_geojson_with_fallback(MANGROVE_URL,    MANGROVE_FALLBACK,    "Mangroves")
cabo_mpa_gdf, cabo_mpa_fallback     = load_geojson_with_fallback(CABO_MPA_URL,    CABO_MPA_FALLBACK,    "Cabo MPA")
harbor_gdf,   _                     = load_geojson_with_fallback("",              HARBOR_DEV_FALLBACK,  "Harbor")
reef_gdf,     _                     = load_geojson_with_fallback("",              CABO_REEF_FALLBACK,   "Reef")
community_gdf, _                    = load_geojson_with_fallback("",              CABO_COMMUNITY_FALLBACK, "Community")

# Notify if using fallback data
if mangrove_fallback or cabo_mpa_fallback:
    st.sidebar.warning(
        "⚠️ Some layers are using approximate illustrative geometry. "
        "Connect to the internet to load authoritative datasets.",
        icon="🗺️",
    )

# -------------------------------------------------------------------
# Map center & zoom based on site choice
# -------------------------------------------------------------------
if site_choice == "La Paz harbor":
    center, zoom = [24.17, -110.36], 11
elif site_choice == "Cabo Pulmo":
    center, zoom = [23.455, -109.855], 12
else:  # Compare both — zoom to fit Baja California Sur
    center, zoom = [23.85, -110.10], 9

# -------------------------------------------------------------------
# Style definitions
# -------------------------------------------------------------------
mangrove_style   = {"color": "#0F6E56", "fillColor": "#1D9E75", "fillOpacity": 0.5, "weight": 1}
mangrove_hover   = {"fillOpacity": 0.75, "weight": 2}

harbor_style     = {"color": "#993C1D", "fillColor": "#D85A30", "fillOpacity": 0.45, "weight": 1}
harbor_hover     = {"fillOpacity": 0.65, "weight": 2}

lapaz_mpa_style  = {"color": "#185FA5", "fillColor": "#378ADD", "fillOpacity": 0.08,
                    "weight": 2, "dashArray": "6 4"}

cabo_mpa_style   = {"color": "#185FA5", "fillColor": "#378ADD", "fillOpacity": 0.1,
                    "weight": 2, "dashArray": "6 4"}
cabo_mpa_hover   = {"fillOpacity": 0.2, "weight": 3}

reef_style       = {"color": "#BA7517", "fillColor": "#EF9F27", "fillOpacity": 0.6, "weight": 1}
reef_hover       = {"fillOpacity": 0.8, "weight": 2}

community_style  = {"color": "#993556", "fillColor": "#D4537E", "fillOpacity": 0.55, "weight": 1}
community_hover  = {"fillOpacity": 0.75, "weight": 2}

notake_style     = {"color": "#3B6D11", "fillColor": "#639922", "fillOpacity": 0.2,
                    "weight": 1, "dashArray": "4 3"}

# La Paz approximate biosphere boundary (illustrative)
LAPAZ_MPA_GEOJSON = {
    "type": "FeatureCollection",
    "features": [{
        "type": "Feature",
        "properties": {"name": "Bay of La Paz biosphere reserve (approx.)"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-110.520, 24.280], [-110.350, 24.300], [-110.250, 24.100],
                [-110.280, 24.040], [-110.450, 24.050], [-110.550, 24.150],
                [-110.520, 24.280]
            ]]
        }
    }]
}

NOTAKE_GEOJSON = {
    "type": "FeatureCollection",
    "features": [{
        "type": "Feature",
        "properties": {"name": "Cabo Pulmo no-take buffer (approx.)"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-109.870, 23.448], [-109.852, 23.456], [-109.842, 23.450],
                [-109.858, 23.442], [-109.870, 23.448]
            ]]
        }
    }]
}

# -------------------------------------------------------------------
# Map rendering
# -------------------------------------------------------------------
with col1:
    m = leafmap.Map(center=center, zoom=zoom)
    m.add_basemap(basemap_choice)

    legend_dict = {}

    # --- La Paz layers ---
    if show_mangroves:
        m.add_gdf(
            mangrove_gdf,
            style=mangrove_style,
            hover_style=mangrove_hover,
            layer_name="Mangrove habitat",
            info_mode="on_hover",
            zoom_to_layer=False,
        )
        legend_dict["Mangrove habitat"] = "#1D9E75"

    if show_harbor:
        m.add_gdf(
            harbor_gdf,
            style=harbor_style,
            hover_style=harbor_hover,
            layer_name="Port & marina development",
            info_mode="on_hover",
            zoom_to_layer=False,
        )
        legend_dict["Port & marina development"] = "#D85A30"

    if show_lapaz_mpa:
        m.add_geojson(
            LAPAZ_MPA_GEOJSON,
            layer_name="La Paz biosphere reserve",
            style=lapaz_mpa_style,
            info_mode=None,
            zoom_to_layer=False,
        )
        legend_dict["La Paz biosphere reserve"] = "#378ADD"

    # --- Cabo Pulmo layers ---
    if show_cabo_mpa:
        m.add_gdf(
            cabo_mpa_gdf,
            style=cabo_mpa_style,
            hover_style=cabo_mpa_hover,
            layer_name="Marine park boundary",
            info_mode="on_hover",
            zoom_to_layer=False,
        )
        legend_dict["Marine park boundary (Cabo Pulmo)"] = "#378ADD"

    if show_reef:
        m.add_gdf(
            reef_gdf,
            style=reef_style,
            hover_style=reef_hover,
            layer_name="Reef habitat",
            info_mode="on_hover",
            zoom_to_layer=False,
        )
        legend_dict["Reef habitat"] = "#EF9F27"

    if show_community:
        m.add_gdf(
            community_gdf,
            style=community_style,
            hover_style=community_hover,
            layer_name="Community settlement",
            info_mode="on_hover",
            zoom_to_layer=False,
        )
        legend_dict["Community settlement"] = "#D4537E"

    if show_notake:
        m.add_geojson(
            NOTAKE_GEOJSON,
            layer_name="No-take buffer zone",
            style=notake_style,
            info_mode=None,
            zoom_to_layer=False,
        )
        legend_dict["No-take buffer zone (approx.)"] = "#639922"

    if legend_dict:
        m.add_legend(title="Map key", legend_dict=legend_dict, position="bottomright")

    m.to_streamlit(height=700)

# -------------------------------------------------------------------
# Reflection panel under map
# -------------------------------------------------------------------
st.markdown("---")

if site_choice == "La Paz harbor":
    st.info(
        """
        💭 **Reflect — La Paz harbor**

        - Where do mangrove patches remain, and where have they been displaced by development?
        - Mangroves are often called "nurseries of the sea" — what does their fragmentation mean for the broader bay system?
        - What questions does this map raise that you would want to explore during the OPRE mangrove tour?

        **Data note:** Mangrove extent is derived from Global Mangrove Watch (JAXA, 2020).
        Harbor development layers are illustrative and based on satellite imagery.
        *These layers are for educational purposes only.*
        """
    )

elif site_choice == "Cabo Pulmo":
    st.info(
        """
        💭 **Reflect — Cabo Pulmo**

        - In 1995, the community of Cabo Pulmo voluntarily stopped fishing and advocated for marine park status.
          Reef biomass has since increased by over 460%. What spatial patterns on this map reflect that recovery?
        - Where is the community settlement relative to the park boundary? What tensions might that create?
        - What would this place look like without the marine park? What systems thinking tools help you reason about that counterfactual?

        **Data note:** Marine park boundary from CONANP/WDPA (Protected Planet).
        Reef extent is illustrative, based on published reef survey locations.
        *These layers are for educational purposes only.*
        """
    )

else:
    st.info(
        """
        💭 **Reflect — Compare both places**

        - Both La Paz and Cabo Pulmo face pressures from tourism and coastal development.
          What looks different about how each place has responded?
        - Cabo Pulmo is often called a conservation "success story." La Paz is still navigating competing interests.
          What role does **community governance** play in each? What does the map show — and what can't it show?
        - Using the ball-and-cup model: where are the leverage points in each system?
          What feedback loops might be reinforcing the current trajectory of each place?
        - If you were designing a learning experience around both of these maps, what is the one tension you would most want learners to sit with?

        **Data sources:** Global Mangrove Watch (JAXA, 2020) · CONANP / WDPA Protected Planet · Illustrative layers.
        *All data are for educational and illustrative purposes only.*
        """
    )
