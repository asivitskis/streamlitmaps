import streamlit as st
import leafmap.foliumap as leafmap
import geopandas as gpd

# -------------------------------------------------------------------
# Title and description
# -------------------------------------------------------------------
st.title("Pipeline Explorer: Interactive Demo")

st.markdown(
    """
    An interactive web map for exploring **U.S. petroleum pipelines** and 
    **federally recognized Tribal lands**. This tool seeks to honor the work of [Tribal Nations Maps](https://tribalnationsmaps.com/) 
    and [Native Lands Advocacy Project](https://nativeland.info/dashboard/us-pipelines-and-hazardous-liquid-spills-2012-2020/)
    whose cartographic efforts highlight how proposed pipelines and hazardous spills relate to important Tribal Lands.
    The goal here is to offer an **open-source, dynamic platform** to help educators, students, and communities 
    visualize and explore data for critical reflection around environmental justice and sovereignty.  
    """
)
st.set_page_config(layout="wide")

# -------------------------------------------------------------------
# Layout
# -------------------------------------------------------------------
col1, col2 = st.columns([4, 1])

# -------------------------------------------------------------------
# Controls (sidebar)
# -------------------------------------------------------------------
with col2:
    st.subheader("Map Settings")

    st.markdown(
        """
        - Use the checkboxes below to calculate where pipelines currently intersect with Tribal Lands.
        - Hover over pipelines or Land boundaries to view attributes.   
        """
    )

    # Basemap control
    options = list(leafmap.basemaps.keys())
    default_basemap = "CartoDB.VoyagerLabelsUnder"
    index = options.index(default_basemap) if default_basemap in options else 0
    basemap_choice = st.selectbox("Select a basemap:", options, index)

    # Layer toggles
    show_intersection = st.checkbox("Show Pipeline-Tribal Land Intersections", value=False)

    st.markdown(
        """
        **Inquiry Prompts:**  
        * Where do you notice pipelines overlapping with Tribal lands?  
        * What might be some historical, environmental, or legal contexts for 
            these regions of intersection?  
        * What data is missing from this map, and why might that matter?
        """
    )

    st.markdown("---")

# -------------------------------------------------------------------
# Load data
# -------------------------------------------------------------------
pipeline_url = (
    "https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/Crude_Oil_Trunk_Pipelines_1/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"
)
tribal_url = (
    "https://services.arcgis.com/U7I2hMhPtOeGx0fs/arcgis/rest/services/"
    "Land_Areas_of_Federally_Recognized_Tribes/FeatureServer/0/"
    "query?outFields=*&where=1%3D1&f=geojson"
)

@st.cache_data(show_spinner=True)
def load_data(pipeline_url, tribal_url):
    pipe_gdf = gpd.read_file(pipeline_url)
    tribal_gdf = gpd.read_file(tribal_url)
    pipe_gdf = pipe_gdf.to_crs(epsg=4326)
    tribal_gdf = tribal_gdf.to_crs(epsg=4326)
    return pipe_gdf, tribal_gdf

pipeline_gdf, tribal_gdf = load_data(pipeline_url, tribal_url)

# -------------------------------------------------------------------
# Compute intersections
# -------------------------------------------------------------------
@st.cache_data(show_spinner=True)
def compute_intersections(_pipe_gdf, _tribal_gdf, pipeline_url):
    """Compute where pipelines intersect tribal land polygons."""
    try:
        intersections = gpd.overlay(_pipe_gdf, _tribal_gdf, how="intersection")
    except Exception as e:
        st.error(f"Error computing intersections: {e}")
        intersections = gpd.GeoDataFrame(geometry=[], crs=_pipe_gdf.crs)
    return intersections

intersection_gdf = compute_intersections(pipeline_gdf, tribal_gdf, pipeline_url)

# -------------------------------------------------------------------
# Map rendering
# -------------------------------------------------------------------
with col1:
    
    m = leafmap.Map(center=[40, -100], zoom=8)

    pipeline_style = {"color": "#b95eff", "weight": 1, "opacity": 0.8}
    pipeline_hover = {"color": "#000000", "weight": 3, "opacity": 1}

    tribal_style = {
        "color": "#00704A",
        "fillColor": "#00704A",
        "fillOpacity": 0.2,
        "weight": 1,
    }
    tribal_hover = {"color": "#004d33", "weight": 2, "fillOpacity": 0.3}

    intersection_style = { "color": "#ff8c00", # orange border 
                          "weight": 4, 
                          "opacity": 1, 
                          "fillColor": "#ffa500", 
                          }
    intersection_hover = {"color": "red", "weight": 5, "opacity": 1}

    # Add layers
    m.add_gdf(
            pipeline_gdf,
            style=pipeline_style,
            hover_style=pipeline_hover,
            layer_name="Pipelines",
        )

    m.add_gdf(
            tribal_gdf,
            style=tribal_style,
            hover_style=tribal_hover,
            layer_name="Tribal Lands",
        )

    if show_intersection and not intersection_gdf.empty:
        m.add_gdf(
            intersection_gdf,
            style=intersection_style,
            hover_style=intersection_hover,
            layer_name="Pipeline-Tribal Intersections",
        )

    # update legend based on layers
    if show_intersection and not intersection_gdf.empty:
        legend_dict = {
            "Pipelines": "#b95eff",
            "Tribal Lands": "#00704A",
            "Intersections": "#ff8c00",
        }
    else:
        legend_dict = {
            "Pipelines": "#b95eff",
            "Tribal Lands": "#00704A",
        }

    m.add_legend(title="Map Key", legend_dict=legend_dict, position="bottomright")

    m.add_basemap(basemap_choice)
    m.to_streamlit(height=700)

# -------------------------------------------------------------------
# Reflection prompt under map
# -------------------------------------------------------------------
st.info(
    """
    💭 **Think About:**  
    - What regions show the most overlap between pipelines and Tribal lands?  
    - What might these intersections mean for sovereignty and environmental safety?  
    - What additional data could make this map more complete or just?  

     **Data Sources**  
        - **Pipelines:** U.S. Energy Information Administration  
          ([ESRI U.S. Federal Datasets](https://hub.arcgis.com/datasets/fedmaps::crude-oil-trunk-pipelines-2/about))  
        - **Federally Recognized Tribal Lands:** Bureau of Indian Affairs  
          ([American Conservation and Stewardship Atlas](https://services.arcgis.com/U7I2hMhPtOeGx0fs/arcgis/rest/services/Land_Areas_of_Federally_Recognized_Tribes/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson)) 
    
    *Note: All data are for illustrative and educational purposes only. **Intersections** shown here represent spatial overlaps between publicly available federal 
    datasets of pipeline routes and federally recognized Tribal land areas. They are meant to illustrate proximity and patterns, not to assert any claims about
    land ownership, legal authority, or environmental impact. For any decision-making or consultation, 
    authoritative data from Tribal governments should be used.*
    """
    )
