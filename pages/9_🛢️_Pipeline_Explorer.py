import streamlit as st
import leafmap.foliumap as leafmap

st.set_page_config(layout="wide")

# Title and description
st.title("Pipeline Explorer: Interactive Demo")

st.markdown(
    """
    An interactive web map for exploring **U.S. petroleum product pipelines**.  
    This tool is inspired by and seeks to honor the work of 
    [Tribal Nations Maps](https://tribalnationsmaps.com/), who have created detailed 
    static maps and educational resources highlighting pipeline projects and their 
    intersections with sovereign Tribal territories.  

    The goal here is not to replace those resources, but to offer a **dynamic, 
    open-source map** that might complement them — allowing educators, students, 
    and communities to:
    
    - Zoom into regions of interest  
    - Explore pipeline attributes interactively  
    - Compare with other open-source geographic datasets  

    """
)

# Two-column layout: left = map, right = controls
col1, col2 = st.columns([4, 1])

# Basemap control
options = list(leafmap.basemaps.keys())
default_basemap = "OpenStreetMap"
index = options.index(default_basemap)

with col2:
    basemap_choice = st.selectbox("Select a basemap:", options, index)
    st.markdown(
        """
        Use the dropdown above to switch basemaps. Pipelines can be hovered over 
        to reveal their attributes, such as operator information.
        """
    )
    # (Optional future control)
    # buffer_distance = st.slider("Pipeline Buffer (miles)", min_value=1, max_value=20, value=5, step=1)

# Map rendering
with col1:
    m = leafmap.Map(center=[40, -100], zoom=4)

    data = "https://openenergyhub.ornl.gov/api/explore/v2.1/catalog/datasets/petroleumproduct_pipelines_us_eia/exports/geojson"
    style = {"color": "#a11998", "weight": 1, "opacity": 1}
    hover_style = {"color": "black", "weight": 3, "opacity": 1}

    m.add_vector(
        data,
        layer_name="Pipelines",
        info_mode="on_hover",
        style=style,
        hover_style=hover_style,
    )

    # Add basemap
    m.add_basemap(basemap_choice)

    # Render in Streamlit
    m.to_streamlit(height=700)
