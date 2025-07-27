import streamlit as st
import leafmap.foliumap as leafmap

markdown = """
A Streamlit map template
<https://github.com/opengeos/streamlit-map-template>
"""

st.sidebar.title("About")
st.sidebar.info(markdown)
logo = "https://i.imgur.com/UbOXYAU.png"
st.sidebar.image(logo)


st.title("Interactive Map")

col1, col2 = st.columns([4, 1])
options = list(leafmap.basemaps.keys())
index = options.index("Satellite")

with col2:

    basemap = st.selectbox("Select a basemap:", options, index)


with col1:
    hillshade = "https://github.com/asivitskis/EarthInquiryLab/raw/refs/heads/main/data/Elevation/hillshade_cog.tif"
    smoothed_dem = "https://github.com/asivitskis/EarthInquiryLab/raw/refs/heads/main/data/Elevation/smoothed_dem_cog.tif"
    basin = "https://raw.githubusercontent.com/asivitskis/EarthInquiryLab/refs/heads/main/data/Hydro_data/pa_HUC10_basin.geojson"
    streams = "https://raw.githubusercontent.com/asivitskis/EarthInquiryLab/main/data/Hydro_data/stream_network.geojson"
    hstyle = {"color": "black", "weight": 3, "opacity": 1}
    
    m = leafmap.Map(
        locate_control=True, latlon_control=True, draw_export=True, minimap_control=True
    )
    m.add_basemap(basemap)
    m.add_cog_layer(smoothed_dem, name="Smoothed DEM", palette="terrain")
        m.add_cog_layer(hillshade, name="Hillshade COG", opacity=0.2)
        m.add_geojson(
            basin,
            layer_name="HUC 10 Basin",
            style={"color": "black", "weight": 2, "fillOpacity": 0},
            info_mode="on_click",
        )
        m.add_geojson(
            streams,
            layer_name="Drainage Network",
            style={"color": "#ff2a00", "weight": 2},
            hover_style=hstyle,
        )
    m.to_streamlit(height=700)
