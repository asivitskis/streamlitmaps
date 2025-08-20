import streamlit as st
import leafmap.foliumap as leafmap
import leafmap as leafmap_utils  # to call get_nwi
from shapely.ops import unary_union
import geopandas as gpd

st.set_page_config(layout="wide")

st.title("Interactive Parcel & Streams Demo")

st.markdown(
    """
    An interactive web map for **visualizing parcels, streams, and wetlands** in 
    relation to potential restoration opportunities. Designed to support 
    conservation planning, mitigation project design, and stakeholder engagement. 
    (Data from NC OneMap and USFWS National Wetlands Inventory)
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
        distances around streams and wetlands. This can help evalaute potential 
        restoration opporunities for planning, design, and environmental review.
        
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

# Try fetching NWI data safely
try:
    gdf_nwi = leafmap_utils.get_nwi(bbox_geometry)
    if gdf_nwi is None or gdf_nwi.empty:
        st.warning("No NWI features found in this area. Stream layer will be empty.")
        gdf_nwi = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
except Exception as e:
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

    # Apply buffer (only if streams exist)
    if not gdf_nwi.empty:
        buffer_gdf = gdf_nwi.buffer(buffer_distance)
        merged_buffer = unary_union(buffer_gdf)
        buffer_gdf_merged = gpd.GeoDataFrame(geometry=[merged_buffer], crs=gdf_nwi.crs)
        buffer_gdf_merged = buffer_gdf_merged.to_crs(epsg=4326)

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
