import streamlit as st
import leafmap.foliumap as leafmap

st.title("Geospatial Sandbox")
st.markdown(
    """
Testing Sandbox.
"""
)

st.set_page_config(layout="wide")

layer = "https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/Crude_Oil_Trunk_Pipelines_1/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"

m = leafmap.Map(center=[42.70, -108.883], zoom=10)
m.add_basemap("SATELLITE")
m.add_geojson(
    layer,
    layer_name="Test Layer",
    style={"color": "black", "weight": 2, "fillOpacity": 0},
    info_mode="on_click",
    zoom_to_layer=True,
)

m.to_streamlit(height=700, width=900)
