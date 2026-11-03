import os

import geopandas as gpd
import leafmap.foliumap as leafmap
import requests
import streamlit as st
from shapely.geometry import box
from shapely.ops import unary_union
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

st.title("Restoration Planner: Interactive Demo")

st.markdown(
    """
    An interactive web map for exploring **parcels, streams, and wetlands** in relation
    to potential restoration opportunities. Built to support conservation planning,
    mitigation design, and stakeholder engagement.
    (Data: NC OneMap, USFWS National Wetlands Inventory)
    """
)

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
DEFAULT_CENTER = [36.4039, -80.4379]
DEFAULT_ZOOM = 16
UTM_EPSG = 32617  # UTM 17N, meters, covers Stokes County, NC
SQ_M_PER_ACRE = 4046.8564224

NWI_URL = (
    "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/"
    "rest/services/Wetlands/MapServer/0/query"
)
NWI_CACHE_FILE = "nwi_demo.geojson"

BBOX = (-80.448555, 36.375243, -80.388988, 36.415039)  # xmin, ymin, xmax, ymax

# ----------------------------------------------------------------------------
# Session state (keeps the map view stable across reruns)
# ----------------------------------------------------------------------------
if "map_center" not in st.session_state:
    st.session_state.map_center = DEFAULT_CENTER
if "map_zoom" not in st.session_state:
    st.session_state.map_zoom = DEFAULT_ZOOM
if "area_result" not in st.session_state:
    st.session_state.area_result = None


# ----------------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading parcels...")
def load_parcels(path):
    return gpd.read_file(path)


@st.cache_data(show_spinner="Loading NWI data...")
def load_nwi(bbox):
    """Query the NWI MapServer for a bbox (xmin, ymin, xmax, ymax in EPSG:4326)."""
    params = {
        "geometry": ",".join(str(v) for v in bbox),
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "outSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "returnGeometry": "true",
        "f": "geojson",
    }
    r = requests.get(NWI_URL, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    if "features" not in data:
        raise RuntimeError(f"NWI service error: {data.get('error', data)}")
    return gpd.GeoDataFrame.from_features(data["features"], crs=4326)


gdf = load_parcels("stokes_parcels_demo.geojson")

try:
    gdf_nwi = load_nwi(BBOX)
    if gdf_nwi.empty:
        st.warning("No NWI features found in this area. Stream layer will be empty.")
    elif not os.path.exists(NWI_CACHE_FILE):
        # Save a local copy once so the demo survives a service outage
        gdf_nwi.to_file(NWI_CACHE_FILE, driver="GeoJSON")
except Exception as e:
    if os.path.exists(NWI_CACHE_FILE):
        st.info(f"Live NWI service unavailable ({e}). Using saved local copy.")
        gdf_nwi = gpd.read_file(NWI_CACHE_FILE)
    else:
        st.error(f"Failed to load NWI data: {e}")
        gdf_nwi = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

# ----------------------------------------------------------------------------
# Layout and controls
# ----------------------------------------------------------------------------
col1, col2 = st.columns([4, 1])

options = list(leafmap.basemaps.keys())
default_basemap = "SATELLITE" if "SATELLITE" in options else "OpenStreetMap"
index = options.index(default_basemap)

with col2:
    basemap_choice = st.selectbox("Select a basemap:", options, index)
    buffer_distance = st.slider(
        "Buffer Distance (meters)", min_value=10, max_value=200, value=50, step=10
    )
    ring_only = st.checkbox(
        "Exclude wetland footprints from area",
        value=False,
        help="When checked, the area counts only the buffer ring around "
        "streams and wetlands.",
    )
    st.markdown(
        """
        Use the **buffer size slider** above to experiment with different buffer
        distances around streams and wetlands. This can help evaluate potential
        restoration opportunities for planning, design, and environmental review.

        **Parcels** can be clicked for ownership details, giving quick insight into
        landholder context. Buffer zones update dynamically to support scenario testing
        and conservation planning discussions.
        """
    )
    calc_clicked = st.button("Calculate buffer area in view")

# ----------------------------------------------------------------------------
# Styles
# ----------------------------------------------------------------------------
parcel_style = {"color": "red", "fillColor": "red", "fillOpacity": 0, "weight": 2}
parcel_hover = {"color": "#00FFFF", "weight": 4, "opacity": 1}

stream_style = {"color": "#0084FF", "weight": 2, "opacity": 0.7}
stream_hover = {"color": "#0084FF", "weight": 3, "opacity": 1}

buffer_style = {"color": "yellow", "weight": 1, "fillColor": "yellow", "fillOpacity": 0}
buffer_hover_style = {
    "color": "#FFA500",
    "weight": 2,
    "fillColor": "#FFFF00",
    "fillOpacity": 0.2,
}

# ----------------------------------------------------------------------------
# Map rendering
# ----------------------------------------------------------------------------
with col1:
    m = leafmap.Map(
        center=st.session_state.map_center,
        zoom=st.session_state.map_zoom,
    )

    merged_buffer = None  # shapely geometry in UTM 17N (meters)
    wetland_union = None  # shapely geometry in UTM 17N (meters)

    if not gdf_nwi.empty:
        nwi_utm = gdf_nwi.to_crs(epsg=UTM_EPSG)
        wetland_union = unary_union(nwi_utm.geometry)
        merged_buffer = unary_union(nwi_utm.buffer(buffer_distance))

        buffer_gdf_merged = gpd.GeoDataFrame(
            geometry=[merged_buffer], crs=nwi_utm.crs
        ).to_crs(epsg=4326)

        m.add_gdf(
            buffer_gdf_merged,
            style=buffer_style,
            hover_style=buffer_hover_style,
            layer_name="Stream Buffer",
            info_mode="off",
            zoom_to_layer=False,
        )
        m.add_gdf(
            gdf_nwi,
            style=stream_style,
            hover_style=stream_hover,
            layer_name="Streams and Wetlands",
            info_mode="off",
            zoom_to_layer=False,
        )

    m.add_gdf(
        gdf,
        style=parcel_style,
        hover_style=parcel_hover,
        layer_name="Stokes Parcels",
        info_mode="on_click",
        zoom_to_layer=False,
    )

    m.add_basemap(basemap_choice)

    map_data = st_folium(
        m,
        height=700,
        use_container_width=True,
        returned_objects=["bounds", "center", "zoom"],
        key="restoration_map",
    )

# Remember the current view so the next rerun rebuilds the map in the same place
if map_data:
    center = map_data.get("center")
    zoom = map_data.get("zoom")
    if center and zoom:
        st.session_state.map_center = [center["lat"], center["lng"]]
        st.session_state.map_zoom = zoom

# ----------------------------------------------------------------------------
# Area calculation (runs after the map so the current bounds are available)
# ----------------------------------------------------------------------------
with col2:
    if calc_clicked:
        bounds = (map_data or {}).get("bounds")
        if merged_buffer is None:
            st.session_state.area_result = None
            st.warning("No buffer to measure.")
        elif not bounds:
            st.warning("Map extent not available yet. Pan or zoom once and try again.")
        else:
            sw, ne = bounds["_southWest"], bounds["_northEast"]
            view_box = box(sw["lng"], sw["lat"], ne["lng"], ne["lat"])
            view_utm = gpd.GeoSeries([view_box], crs=4326).to_crs(UTM_EPSG).iloc[0]

            target = merged_buffer
            if ring_only:
                target = merged_buffer.difference(wetland_union)

            acres = target.intersection(view_utm).area / SQ_M_PER_ACRE
            st.session_state.area_result = {
                "acres": acres,
                "buffer_m": buffer_distance,
                "ring_only": ring_only,
            }

    result = st.session_state.area_result
    if result:
        label = "Buffer ring area in view" if result["ring_only"] else "Buffer area in view"
        st.metric(label, f"{result['acres']:,.1f} acres")
        st.caption(
            f"Calculated at a {result['buffer_m']} m buffer. "
            "Click the button again after changing the view or slider."
        )