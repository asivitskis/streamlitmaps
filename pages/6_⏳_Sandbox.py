import streamlit as st
import leafmap.foliumap as leafmap

st.title("Popo Agie River Watershed Viewer")
st.markdown(
    """
This app is a demonstration of visualizing delineated stream network data generated with [WhiteboxTools](https://www.whiteboxgeo.com) and [leafmap](https://leafmap.org/). 
Both open source python packages can support highly customizable geospatial applications.
"""
)
st.set_page_config(layout="wide")

# -------------------------------------------------------------------
# Data URLs
# -------------------------------------------------------------------
# hillshade = "https://github.com/asivitskis/EarthInquiryLab/raw/refs/heads/main/data/Elevation/hillshade_cog.tif"
# smoothed_dem = "https://github.com/asivitskis/EarthInquiryLab/raw/refs/heads/main/data/Elevation/smoothed_dem_cog.tif"
basin = "https://raw.githubusercontent.com/asivitskis/EarthInquiryLab/refs/heads/main/data/Hydro_data/pa_HUC10_basin.geojson"
BRAT = "https://raw.githubusercontent.com/asivitskis/EarthInquiryLab/main/data/PA_BRAT_2.geojson"
VBET = "https://raw.githubusercontent.com/asivitskis/EarthInquiryLab/main/data/PA_VBET_Simplified.geojson"

# -------------------------------------------------------------------
# Layout
# -------------------------------------------------------------------
col1, col2 = st.columns([4, 1])

# -------------------------------------------------------------------
# Sidebar
# -------------------------------------------------------------------
with col2:
    st.markdown("### Layer Controls")
    # show_dem     = st.checkbox("Smoothed DEM",        value=True)
    # show_hillshade = st.checkbox("Hillshade",         value=True)
    show_basin   = st.checkbox("HUC 10 Basin",        value=True)
    show_brat    = st.checkbox("BRAT Dam Capacity",   value=True)
    show_vbet    = st.checkbox("VBET Stream Network", value=True)
    st.markdown("---")
    st.markdown("### Basemap")
    basemap_choice = st.selectbox(
        "Select a basemap:",
        list(leafmap.basemaps.keys()),
        index=list(leafmap.basemaps.keys()).index("SATELLITE")
    )

    st.markdown("---")
    with st.expander("About BRAT"):
        st.markdown(
            """
            The **Beaver Restoration Assessment Tool (BRAT)** models the 
            capacity of stream reaches to support beaver dam activity.  
            
            `oCC_EX` = existing capacity in dams/km.
            """
        )

    with st.expander("About VBET"):
        st.markdown(
            """
            The **Valley Bottom Extraction Tool (VBET)** uses a DEM 
            and a channel area network to estimate valley bottom extents.  
            
            This can be used to define a Riverscape Network.
            """
        )

# -------------------------------------------------------------------
# Style helpers
# -------------------------------------------------------------------
hstyle = {"color": "black", "weight": 3, "opacity": 1}

def brat_style(feature):
    val = feature.get("properties", {}).get("oCC_EX", 0) or 0
    if val <= 0:
        color = "#d7191c"   # None
    elif val < 1:
        color = "#fdae61"   # Rare
    elif val < 5:
        color = "#ffffbf"   # Occasional
    elif val < 15:
        color = "#a6d96a"   # Frequent
    else:
        color = "#2b83ba"   # Pervasive
    return {"color": color, "weight": 2, "opacity": 0.9}

# -------------------------------------------------------------------
# Map
# -------------------------------------------------------------------
with col1:
    m = leafmap.Map(center=[42.70, -108.883], zoom=10)
    m.add_basemap(basemap_choice)

    # if show_dem:
    #     m.add_colormap(cmap="terrain", vmin=1500, vmax=4000, label="Elevation (m)", width=2)
    #     m.add_cog_layer(smoothed_dem, name="Smoothed DEM", palette="terrain")

    # if show_hillshade:
    #     m.add_cog_layer(hillshade, name="Hillshade COG", opacity=0.2)

    if show_basin:
        m.add_geojson(
            basin,
            layer_name="HUC 10 Basin",
            style={"color": "black", "weight": 2, "fillOpacity": 0},
            info_mode=None,
            zoom_to_layer=False,
        )

    if show_brat:
        m.add_geojson(
            BRAT,
            layer_name="BRAT Dam Capacity",
            style_function=brat_style,
            info_mode="on_click",
            zoom_to_layer=False,
        )
    if show_vbet:
        m.add_geojson(
            VBET,
            layer_name="Valley Bottom (VBET)",
            style={
                "color": "#000000",       # border
                "weight": 0.1,
                "fillColor": "#4a90d9",
                "fillOpacity": 0.25,
            },
            hover_style={"fillOpacity": 0.5, "weight": 2},
            info_mode=None,
            zoom_to_layer=False,
        )
    # --- Dynamic legend ---
    legend_dict = {}
    # if show_dem:
    #     legend_dict["Smoothed DEM"] = "#6a994e"
    # if show_basin:
    #     legend_dict["HUC 10 Basin"] = "#000000"
    if show_brat:
        legend_dict["None (0 dams/km)"]         = "#d7191c"
        legend_dict["Rare (< 1 dam/km)"]        = "#fdae61"
        legend_dict["Occasional (1–5 dams/km)"] = "#ffffbf"
        legend_dict["Frequent (5–15 dams/km)"]  = "#a6d96a"
        legend_dict["Pervasive (> 15 dams/km)"] = "#2b83ba"

    if show_vbet:
        legend_dict["Valley Bottom (VBET)"] = "#4a90d9"

    if legend_dict:
        m.add_legend(title="Map Key", legend_dict=legend_dict, position="bottomright")

    m.to_streamlit(height=700)