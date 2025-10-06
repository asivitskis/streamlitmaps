import streamlit as st
import leafmap.foliumap as leafmap

st.set_page_config(layout="wide")

# -------------------------------------------------------------------
# Title and description
# -------------------------------------------------------------------
st.title("Pipeline Explorer: Interactive Demo")

st.markdown(
    """
    An interactive web map for exploring **U.S. petroleum product pipelines**.  
    This tool is inspired by and seeks to honor the work of 
    [Tribal Nations Maps](https://tribalnationsmaps.com/), who have created detailed 
    static maps and educational resources highlighting pipeline projects and their 
    intersections with sovereign Tribal territories.  

    The goal here is not to replace those resources, but to offer a **dynamic, 
    open-source map** that might complement them, allowing educators, students, 
    and communities to:
    - Zoom into regions of interest  
    - Explore pipeline attributes interactively  
    - Compare with other open-source geographic datasets  

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
    show_tribal = st.checkbox("Show Tribal Census Tracts", value=True)

    st.markdown(
        """
        **About the Tribal Census Tracts layer**

        This layer displays *Tribal Census Tracts* from the **U.S. Census Bureau**,  
        accessed via **Esri Federal Data** under a [CC BY 4.0 license](https://creativecommons.org/licenses/by/4.0/).  

        Tribal census tracts are **statistical areas** created for Census purposes —  
        they may not reflect the full extent of sovereign or culturally significant 
        territories. They are included here to support exploration of how federal 
        datasets represent Indigenous lands and to encourage critical discussion 
        about **sovereignty, representation, and data ethics**.

        ---
        Use the dropdown above to switch basemaps. Pipelines can be hovered over 
        to reveal their attributes, such as operator information.
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

        m.add_vector(
            tribal_layer_url,
            layer_name="Tribal Census Tracts",
            info_mode="on_hover",
            style={"color": "#2E8B57", "weight": 1, "fillOpacity": 0.2},
        )

    # --- Basemap ---
    m.add_basemap(basemap_choice)

    # --- Render Map in Streamlit ---
    m.to_streamlit(height=700)
