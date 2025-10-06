import streamlit as st
import leafmap.foliumap as leafmap

st.set_page_config(layout="wide")

# -------------------------------------------------------------------
# Title and description
# -------------------------------------------------------------------
st.title("Pipeline Explorer: Interactive Demo")

st.markdown(
    """
    An interactive web map for exploring **U.S. petroleum product pipelines** and 
    **federally recognized Tribal lands**.  

    This tool is inspired by and seeks to honor the work of 
    [Tribal Nations Maps](https://tribalnationsmaps.com/), who have created detailed 
    maps and educational resources highlighting pipeline projects and their 
    intersections with sovereign Tribal territories.  

    The goal here is not to replace those resources, but to offer a **dynamic, 
    open-source map** that might complement them, enabling educators, students, 
    and communities to:
    - Zoom into regions of interest  
    - Explore pipeline attributes interactively  
    - Compare with publicly available federal datasets on Tribal lands  
    - Engage in critical inquiry around geography, data, and sovereignty 
    """
)

# -------------------------------------------------------------------
# Two-column layout: left = map, right = controls
# -------------------------------------------------------------------
col1, col2 = st.columns([4, 1])

# -------------------------------------------------------------------
# Sidebar / Controls
# -------------------------------------------------------------------
options = list(leafmap.basemaps.keys())
default_basemap = "OpenStreetMap"
index = options.index(default_basemap)

with col2:
    basemap_choice = st.selectbox("Select a basemap:", options, index)

    # Toggle to show or hide the Tribal Census Tracts layer
    show_tribal = st.checkbox("Show Federally Recognized Tribal Lands", value=True)

    st.markdown(
        """
        **About the Tribal Lands layer**

        Data source: **U.S. Bureau of Indian Affairs (BIA)** via the  
        *American Conservation and Stewardship Atlas*  
        ([GeoJSON link](https://services.arcgis.com/U7I2hMhPtOeGx0fs/arcgis/rest/services/Land_Areas_of_Federally_Recognized_Tribes/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson))  

        This dataset represents **federally recognized Tribal land areas**, including 
        reservations, trust lands, and dependent communities.  
        It is suitable for **educational and illustrative purposes only** and does not 
        define legal or jurisdictional boundaries.  

        ---
        Use the dropdown above to switch basemaps.  
        Pipelines can be hovered over to reveal operator and facility attributes.
        """
    )

# -------------------------------------------------------------------
# Map Rendering
# -------------------------------------------------------------------
with col1:
    m = leafmap.Map(center=[40, -100], zoom=4)

    # --- Pipelines Layer ---
    pipeline_data = (
        "https://openenergyhub.ornl.gov/api/explore/v2.1/catalog/datasets/"
        "petroleumproduct_pipelines_us_eia/exports/geojson"
    )
    pipeline_style = {"color": "#a11998", "weight": 1, "opacity": 1}
    pipeline_hover = {"color": "black", "weight": 3, "opacity": 1}

    m.add_vector(
        pipeline_data,
        layer_name="Pipelines",
        info_mode="on_hover",
        style=pipeline_style,
        hover_style=pipeline_hover,
    )

    # --- Tribal Census Tracts Layer (optional toggle) ---
    if show_tribal:
        tribal_layer_url = (
            "https://services.arcgis.com/U7I2hMhPtOeGx0fs/arcgis/rest/services/"
            "Land_Areas_of_Federally_Recognized_Tribes/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"
        )

        tribal_style = {"color": "#2E8B57", "fillColor": "#2E8B57", "weight": 1, "fillOpacity": 0.3}
        tribal_hover = {"color": "black", "weight": 2, "opacity": 1}

        m.add_vector(
            tribal_layer_url,
            layer_name="Tribal Census Tracts",
            info_mode="on_hover",
            style=tribal_style,
            hover_style=tribal_hover,
        )

    # --- Basemap ---
    m.add_basemap(basemap_choice)

    # --- Render Map in Streamlit ---
    m.to_streamlit(height=700)
