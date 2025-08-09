import streamlit as st
import leafmap.foliumap as leafmap

st.set_page_config(layout="wide")

hillshade = "https://github.com/asivitskis/EarthInquiryLab/raw/refs/heads/main/data/Elevation/hillshade_cog.tif"
smoothed_dem = "https://github.com/asivitskis/EarthInquiryLab/raw/refs/heads/main/data/Elevation/smoothed_dem_cog.tif"
basin = "https://raw.githubusercontent.com/asivitskis/EarthInquiryLab/refs/heads/main/data/Hydro_data/pa_HUC10_basin.geojson"
streams = "https://raw.githubusercontent.com/asivitskis/EarthInquiryLab/main/data/Hydro_data/stream_network.geojson"
hstyle = {"color": "black", "weight": 3, "opacity": 1}

m = leafmap.Map(center=[42.70, -108.883], zoom=10)
m.add_basemap("SATELLITE")
m.add_colormap(cmap="terrain", vmin=1500, vmax=4000, label="Elevation (m)", width=4)
m.add_cog_layer(smoothed_dem, name="Smoothed DEM", palette="terrain")
m.add_cog_layer(hillshade, name="Hillshade COG", opacity=0.2)
m.add_geojson(
    basin,
    layer_name="HUC 10 Basin",
    style={"color": "black", "weight": 2, "fillOpacity": 0},
    info_mode="on_click",
    zoom_to_layer=False,
)
m.add_geojson(
    streams,
    layer_name="Drainage Network",
    style={"color": "#ff2a00", "weight": 2},
    hover_style=hstyle,
    zoom_to_layer=False,
)

m.to_streamlit(height=700, width=900)
