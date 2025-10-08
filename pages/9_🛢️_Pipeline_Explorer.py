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
    maps and educational resources highlighting pipeline projects and their 
    intersections with sovereign Tribal territories.   

    The goal here is to offer an **open-source, dynamic mapping platform** to help 
    educators, students, and communities:
    - Visualize where pipelines and Tribal lands intersect  
    - Explore public geospatial data with transparency  
    - Foster inquiry and discussion around environmental justice and sovereignty  

    *Note: All data are for illustrative purposes only and should not be used for 
    legal or jurisdictional decisions.*
    """
)

# -------------------------------------------------------------------
# Layout
# -------------------------------------------------------------------
col1, col2 = st.columns([4, 1])

# Basemap selection
options = list(leafmap.basemaps.keys())
default_basemap = "OpenStreetMap"
index = options.index(default_basemap)

with col2:
    basemap_choice = st.selectbox("Select a basemap:", options, index)

    # Toggle to show or hide Tribal layers
    show_tribal = st.checkbox("Show Federally Recognized Tribal Lands", value=True)

    # Description
    st.markdown(
        """
        Data source: **U.S. Bureau of Indian Affairs (BIA)** via the  
        *American Conservation and Stewardship Atlas*  
        ([GeoJSON link](https://services.arcgis.com/U7I2hMhPtOeGx0fs/arcgis/rest/services/Land_Areas_of_Federally_Recognized_Tribes/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson))  

        This dataset represents **federally recognized Tribal land areas**, including 
        reservations, trust lands, and dependent communities.It is suitable for **educational and illustrative purposes only** and does not 
        define legal or jurisdictional boundaries. 
        """
    )

    # Toggle to show or hide Pipeline layers
    show_pipeline = st.checkbox("Show U.S. Major Petroleum Pipelines", value=True)

    # Description
    st.markdown(
        """
        Data source: **U.S. Bureau of Indian Affairs (BIA)** via the  
        *American Conservation and Stewardship Atlas*  
        ([GeoJSON link](https://services.arcgis.com/U7I2hMhPtOeGx0fs/arcgis/rest/services/Land_Areas_of_Federally_Recognized_Tribes/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson))  

        This dataset represents **federally recognized Tribal land areas**, including 
        reservations, trust lands, and dependent communities.It is suitable for **educational and illustrative purposes only** and does not 
        define legal or jurisdictional boundaries. 
        """
    )

# -------------------------------------------------------------------
# Load datasets
# -------------------------------------------------------------------
pipeline_url = (
    "https://openenergyhub.ornl.gov/api/explore/v2.1/catalog/datasets/"
    "petroleumproduct_pipelines_us_eia/exports/geojson"
)
tribal_url = (
    "https://services.arcgis.com/U7I2hMhPtOeGx0fs/arcgis/rest/services/"
    "Land_Areas_of_Federally_Recognized_Tribes/FeatureServer/0/"
    "query?outFields=*&where=1%3D1&f=geojson"
)

@st.cache_data(show_spinner=True)
def load_data():
    pipe_gdf = gpd.read_file(pipeline_url)
    tribal_gdf = gpd.read_file(tribal_url)
    pipe_gdf = pipe_gdf.to_crs(epsg=4326)
    tribal_gdf = tribal_gdf.to_crs(epsg=4326)
    return pipe_gdf, tribal_gdf

pipeline_gdf, tribal_gdf = load_data()

# -------------------------------------------------------------------
# Compute intersections (fixed Streamlit-safe function)
# -------------------------------------------------------------------
@st.cache_data(show_spinner=True)
def compute_intersections(_pipe_gdf, _tribal_gdf):
    """Compute where pipelines intersect tribal land polygons."""
    try:
        intersections = gpd.overlay(_pipe_gdf, _tribal_gdf, how="intersection")
    except Exception as e:
        st.error(f"Error computing intersections: {e}")
        intersections = gpd.GeoDataFrame(geometry=[], crs=_pipe_gdf.crs)
    return intersections

intersection_gdf = compute_intersections(pipeline_gdf, tribal_gdf)

# -------------------------------------------------------------------
# Map rendering
# -------------------------------------------------------------------
with col1:
    m = leafmap.Map(center=[40, -100], zoom=4)

    pipeline_style = {"color": "#a11998", "weight": 1, "opacity": 1}
    pipeline_hover = {"color": "black", "weight": 3, "opacity": 1}

    tribal_style = {"color": "#00704A", "fillColor": "#00704A", "fillOpacity": 0.2, "weight": 1}
    tribal_hover = {"color": "black", "weight": 2, "fillOpacity": 0.3}

    intersection_style = {"color": "orange", "weight": 2, "opacity": 1}
    intersection_hover = {"color": "red", "weight": 3, "opacity": 1}

    # Add layers
    if show_pipeline:
        m.add_gdf(
            pipeline_gdf, 
            style=pipeline_style, 
            hover_style=pipeline_hover, 
            layer_name="Pipelines"
        )

    if show_tribal:
        m.add_gdf(
            tribal_gdf, 
            style=tribal_style, 
            hover_style=tribal_hover, 
            layer_name="Tribal Lands",
        )

    if not intersection_gdf.empty:
        m.add_gdf(
            intersection_gdf,
            style=intersection_style,
            hover_style=intersection_hover,
            layer_name="Pipeline-Tribal Intersections",
        )

    m.add_basemap(basemap_choice)
    m.to_streamlit(height=700)
