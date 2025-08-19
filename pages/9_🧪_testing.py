import streamlit as st
import leafmap.foliumap as leafmap_folium
import leafmap
from shapely.ops import unary_union
import geopandas as gpd

st.set_page_config(layout="wide")
st.title("Interactive Parcel & Streams Demo")

# Sidebar controls
buffer_distance = st.sidebar.slider("Buffer Distance (meters)", min_value=10, max_value=200, value=50, step=10)
basemap_choice = st.sidebar.selectbox("Select Basemap", ["Satellite", "Esri.WorldTopoMap", "OpenStreetMap"])

# Load static data
bbox_geometry = {"xmin": -80.448555, "ymin": 36.375243, "xmax": -80.388988, "ymax": 36.415039}
gdf = gpd.read_file("stokes_parcels_demo.geojson")

# Try fetching NWI data safely
try:
    gdf_nwi = leafmap.get_nwi(bbox_geometry)
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
buffer_hover_style = {"color": "#FFA500", "weight": 2, "fillColor": "#FFFF00", "fillOpacity": 0.2}

# Function to generate the map
def create_map(buffer_distance):
    m = leafmap_folium.Map(center=[36.40391048635998, -80.43790340423585], zoom=16)

    # Only build buffer if streams exist
    if not gdf_nwi.empty:
        buffer_gdf = gdf_nwi.buffer(buffer_distance)
        merged_buffer = unary_union(buffer_gdf)
        buffer_gdf_merged = gpd.GeoDataFrame(geometry=[merged_buffer], crs=gdf_nwi.crs)
        buffer_gdf_merged = buffer_gdf_merged.to_crs(epsg=4326)

        m.add_gdf(buffer_gdf_merged, style=buffer_style, hover_style=buffer_hover_style, layer_name="Stream Buffer", info_mode="off")
        m.add_gdf(gdf_nwi, style=stream_style, hover_style=stream_hover, layer_name="Streams and Wetlands", info_mode="off")

    # Always add parcels
    m.add_gdf(gdf, style=parcel_style, hover_style=parcel_hover, layer_name="Stokes Parcels")

    m.add_basemap(Satellite)
    return m

# Display map
m = create_map(buffer_distance)
m.to_streamlit(height=700)
