import streamlit as st
import leafmap.foliumap as leafmap
import geopandas as gpd

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
    static maps and educational resources highlighting pipeline projects and their 
    intersections with sovereign Tribal territories.  

    The goal here is not to replace those resources, but to offer a **dynamic, 
    open-source map** that might complement them — enabling educators, students, 
    and communities to:
    - Zoom into regions of interest  
    - Explore pipeline attributes interactively  
    - Compare with publicly available federal datasets on Tribal lands  
    - Engage in critical inquiry around geography, data, and sovereignty  
    """
)

# -------------------------------------------------------------------
# URLs for data sources
# -------------------------------------------------------------------
PIPELINE_URL = (
    "https://openenergyhub.ornl.gov/api/explore/v2.1/catalog/datasets/"
    "petroleumproduct_pipelines_us_eia/exports/geojson"
)

TRIBAL_URL = (
    "https://services.arcgis.com/U7I2hMhPtOeGx0fs/arcgis/rest/services/"
    "Land_Areas_of_Federally_Recognized_Tribes/FeatureServer/0/query?"
    "outFields=*&where=1%3D1&f=geojson"
)

# -------------------------------------------------------------------
# Data loading + intersection computation
# -------------------------------------------------------------------
@st.cache_data(show_spinner=True)
def load_data():
    """Fetch and prepare the two GeoJSON datasets."""
    pipe_gdf = gpd.read_file(PIPELINE_URL)
    tribal_gdf = gpd.read_file(TRIBAL_URL)

    # Ensure both are in the same coordinate reference system
    tribal_gdf = tribal_gdf.to_crs(pipe_gdf.crs)
    return pipe_gdf, tribal_gdf


@st.cache_data(show_spinner=True)
def compute_intersections(pipe_gdf, tribal_gdf):
    """Compute where pipelines intersect tribal land polygons."""
    try:
        intersections = gpd.overlay(pipe_gdf, tribal_gdf, how="intersection")
    except Exception as e:
        st.error(f"Error computing intersections: {e}")
        intersections = gpd.GeoDataFrame(geometry=[], crs=pipe_gdf.crs)
    return intersections


# Load data
with st.spinner("Loading geospatial data..."):
    pipeline_gdf, tribal_gdf = load_data()

# Compute intersections
with st.spinner("Computing intersections between pipelines and tribal lands..."):
    intersection_gdf = compute_intersections(pipeline_gdf, tribal_gdf)

# -------------------------------------------------------------------
# Sidebar / Controls
# -------------------------------------------------------------------
col1, col2 = st.columns([4, 1])

options = list(leafmap.basemaps.keys())
default_basemap = "OpenStreetMap"
index = options.index(default_basemap)

with col2:
    basemap_choice = st.selectbox("Select a basemap:", options, index)
    show_tribal = st.checkbox("Show Federally Recognized Tribal Lands", True)
    show_intersections = st.checkbox("Show Pipeline–Tribal Land Intersections", True)

    st.markdown(
        """
        ---
        **About the Tribal Lands layer**

        Data source: **U.S. Bureau of Indian Affairs (BIA)** via the  
        *American Conservation and Stewardship Atlas*  
        ([GeoJSON link](https://services.arcgis.com/U7I2hMhPtOeGx0fs/arcgis/rest/services/Land_Areas_of_Federally_Recognized_Tribes/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson))  

        This dataset represents **federally recognized Tribal land areas**, including 
        reservations, trust lands, and dependent communities.  
        It is suitable for **educational and illustrative purposes only** and does not 
        define legal or jurisdictional boundaries.  

        ---
        The **intersection layer** highlights where pipeline routes overlap these Tribal 
        lands based on publicly available datasets.  
        These results are for **exploratory learning only** and should not be used for 
        legal, environmental, or policy analysis.
        """
    )

# -------------------------------------------------------------------
# Map Rendering
# -------------------------------------------------------------------
with col1:
    m = leafmap.Map(center=[40, -100], zoom=4)

    # --- Pipelines ---
    pipeline_style = {"color": "#a11998", "weight": 1, "opacity": 1}
    pipeline_hover = {"color": "black", "weight": 3, "opacity": 1}
    m.add_gdf(
        pipeline_gdf,
        layer_name="Pipelines",
        info_mode="on_hover",
        style=pipeline_style,
        hover_style=pipeline_hover,
    )

    # --- Tribal Lands ---
    if show_tribal:
        tribal_style = {"color": "#2E8B57", "fillColor": "#2E8B57", "weight": 1, "fillOpacity": 0.3}
        tribal_hover = {"color": "black", "weight": 2, "opacity": 1}
        m.add_gdf(
            tribal_gdf,
            layer_name="Federally Recognized Tribal Lands (BIA)",
            info_mode="on_hover",
            style=tribal_style,
            hover_style=tribal_hover,
        )

    # --- Intersections ---
    if show_intersections and not intersection_gdf.empty:
        intersection_style = {"color": "#FFA500", "weight": 3, "opacity": 0.9}
        m.add_gdf(
            intersection_gdf,
            layer_name="Pipeline–Tribal Land Intersections",
            info_mode="on_hover",
            style=intersection_style,
        )
        st.success(f"Found {len(intersection_gdf)} intersection features.")
    elif show_intersections:
        st.warning("No intersections found or data unavailable.")

    # --- Basemap ---
    m.add_basemap(basemap_choice)

    # --- Render Map in Streamlit ---
    m.to_streamlit(height=700)
