import streamlit as st
import leafmap.foliumap as leafmap

st.set_page_config(layout="wide")

markdown = """
A Streamlit map template
<https://github.com/opengeos/streamlit-map-template>
"""

st.sidebar.title("About")
st.sidebar.info(markdown)
logo = "https://i.imgur.com/UbOXYAU.png"
st.sidebar.image(logo)

st.title("Popo Agie Watershed Viewer")

with st.expander("Popo Agie Watershed Explorer"):
    with st.echo():

        hillshade = "https://github.com/asivitskis/EarthInquiryLab/raw/refs/heads/main/data/Elevation/hillshade_cog.tif"
        smoothed_dem = "https://github.com/asivitskis/EarthInquiryLab/raw/refs/heads/main/data/Elevation/smoothed_dem_cog.tif"
        streams = "https://raw.githubusercontent.com/asivitskis/EarthInquiryLab/main/data/Hydro_data/stream_network.geojson"
        style = {"color": "black", "weight": 3, "opacity": 1}
        
        m = leafmap.Map(center=[40, -100], zoom=4)
        m.add_cog_layer(smoothed_dem, name="Smoothed DEM", palette="terrain")
        m.add_cog_layer(hillshade, name="Hillshade COG", layer_opacity=0.3)
        m.add_geojson(
            streams,
            layer_name="streams",
            hover_style=style,
        )

m.to_streamlit(height=700)
