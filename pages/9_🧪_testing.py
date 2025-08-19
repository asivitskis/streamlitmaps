import streamlit as st
import leafmap.foliumap as leafmap
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
gdf_nwi = leafmap.get_nwi(bbox_geometry)

# Styles
parcel_style = {"color": "red", "fillColor": "red", "fillOpacity": 0, "weight": 2}
parcel_hover = {"color": "#00FFFF", "weight": 4, "opacity": 1}

stream_style = {"color": "#0084FF", "weight": 2, "opacity": 0.7}
stream_hover = {"color": "#0084FF", "weight": 3, "opacity": 1}

buffer_style = {"color": "yellow", "weight": 1, "fillColor": "yellow", "fillOpacity": 0}
buffer_hover_style = {"color": "#FFA500", "weight": 2, "fillColor": "#FFFF00", "fillOpacity": 0.2}

# Function to generate the map
def create_map(buffer_distance):
    # Compute dynamic buffer
    buffer_gdf = gdf_nwi.buffer(buffer_distance)
    merged_buffer = unary_union(buffer_gdf)
    buffer_gdf_merged = gpd.GeoDataFrame(geometry=[merged_buffer], crs=gdf_nwi.crs)
    buffer_gdf_merged = buffer_gdf_merged.to_crs(epsg=4326)
    
    # Create map
    m = leafmap.Map(center=[36.4039, -80.4379], zoom=16)
    
    # Add layers
    m.add_gdf(buffer_gdf_merged, style=buffer_style, hover_style=buffer_hover_style, layer_name="Stream Buffer", info_mode="off")
    m.add_gdf(gdf, style=parcel_style, hover_style=parcel_hover, layer_name="Stokes Parcels")
    m.add_gdf(gdf_nwi, style=stream_style, hover_style=stream_hover, layer_name="Streams and Wetlands", info_mode="off")
    
    # Add basemap
    m.add_basemap(basemap_choice)
    return m

# Display map
m = create_map(buffer_distance)
m.to_streamlit(height=700)
