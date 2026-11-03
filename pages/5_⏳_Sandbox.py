import os
import requests
import streamlit as st
import leafmap.foliumap as leafmap
import geopandas as gpd
from shapely.ops import unary_union

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

# Two-column layout: left map, right controls
col1, col2 = st.columns([4, 1])

# Control panel in col2
options = list(leafmap.basemaps.keys())
default_basemap = "SATELLITE" if "SATELLITE" in options else "OpenStreetMap"
index = options.index(default_basemap)

with col2:
    basemap_choice = st.selectbox("Select a basemap:", options, index)
    buffer_distance = st.slider(
        "Buffer Distance (meters)", min_value=10, max_value=200, value=50, step=10
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

# Load data
bbox_geometry = {
    "xmin": -80.448555,
    "ymin": 36.375243,
    "xmax": -80.388988,
    "ymax": 36.415039,
}
gdf = gpd.read_file("stokes_parcels_demo.geojson")

NWI_URL = (
    "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/"
    "rest/services/Wetlands/MapServer/0/query"
)
NWI_CACHE_FILE = "nwi_demo.geojson"


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


bbox = (
    bbox_geometry["xmin"],
    bbox_geometry["ymin"],
    bbox_geometry["xmax"],
    bbox_geometry["ymax"],
)

try:
    gdf_nwi = load_nwi(bbox)
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

# Styles
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

# Map rendering
with col1:
    m = leafmap.Map(center=[36.4039, -80.4379], zoom=16)

    # Apply buffer (only if features exist)
    if not gdf_nwi.empty:
        # Reproject to UTM 17N (meters) so the slider value is a true distance
        nwi_utm = gdf_nwi.to_crs(epsg=32617)
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

    # Parcels
    m.add_gdf(
        gdf,
        style=parcel_style,
        hover_style=parcel_hover,
        layer_name="Stokes Parcels",
        info_mode="on_click",
        zoom_to_layer=False,
    )

    # Add basemap from dropdown
    m.add_basemap(basemap_choice)

    m.to_streamlit(height=700)