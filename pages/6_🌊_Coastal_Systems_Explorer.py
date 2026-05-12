import streamlit as st
import leafmap.foliumap as leafmap
import geopandas as gpd
import requests
import tempfile
import os
import json
from datetime import datetime
from folium.plugins import Draw, MeasureControl

st.set_page_config(layout="wide", page_title="Coastal Systems Explorer")

# -------------------------------------------------------------------
# Title and description
# -------------------------------------------------------------------
st.title("🌊 Coastal Systems Explorer: La Paz & Cabo Pulmo")

st.markdown(
    """
    An interactive geo-inquiry tool for exploring two coastal places along the **Baja California Sur** coast.
    Compare the mangrove and harbor systems of **La Paz Bay** with the community-led marine reserve at **Cabo Pulmo** —
    two places connected by the same sea, shaped by very different histories of protection and use.
    """
)

# -------------------------------------------------------------------
# Custom CSS
# -------------------------------------------------------------------
st.markdown(
    """
    <style>
    input[type="checkbox"] {
        transform: scale(1.3);
        margin-right: 8px;
    }
    .stCheckbox label {
        font-size: 1.05rem;
        font-weight: 500;
    }
    section[data-testid="stSidebar"] .stMarkdown h3 {
        font-size: 1.3rem;
        font-weight: 650;
        margin-bottom: 0.3rem;
    }
    .question-list {
        background: #f0f7f4;
        border-left: 4px solid #027433;
        border-radius: 6px;
        padding: 14px 20px;
        margin-bottom: 12px;
    }
    .question-list ol {
        margin: 0;
        padding-left: 1.3em;
    }
    .question-list li {
        font-size: 0.97rem;
        color: #1a3d2b;
        margin-bottom: 6px;
        line-height: 1.45;
    }
    .debrief-note {
        background: #e8f4fd;
        border-left: 4px solid #2980b9;
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 0.95rem;
        color: #1a2e3d;
    }
    .synthesis-note {
        background: #f3f0fa;
        border-left: 4px solid #7b52ab;
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 0.95rem;
        color: #2d1f44;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# ⚙️  GOOGLE APPS SCRIPT URL — paste your Web App URL here
# -------------------------------------------------------------------
# Steps to set up:
# 1. Open your Google Doc
# 2. Go to Extensions → Apps Script
# 3. Paste the Apps Script code from the bottom of this file into the editor
# 4. Deploy as Web App (Execute as: Me, Who has access: Anyone)
# 5. Copy the Web App URL and paste it below
GOOGLE_APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz8gwxkqgXi-3FNvRJJjl154AbQFE9ycb1L6EHmZZPkyHLgNuAFaEXY_wNq6BSrJimA/exec"   # ← paste your URL here, e.g. "https://script.google.com/macros/s/.../exec"

# -------------------------------------------------------------------
# Student-generated questions from Day 1
# -------------------------------------------------------------------
OPRE_QUESTIONS = [
    {
        "id": "q1",
        "question": "¿Hay impacto por los barcos hundidos en el área de la concesión?",
        "english": "Is there an impact from sunken ships in the concession area?",
        "layer_hint": "💡 Activa la capa de paradas del Manglitour — busca el punto marcado como 'Barco hundido'",
    },
    {
        "id": "q2",
        "question": "¿El proyecto ya es sostenible económicamente?",
        "english": "Is the project already economically sustainable?",
        "layer_hint": "💡 Considera las capas de acuacultura y las paradas del tour al pensar en fuentes de ingreso",
    },
    {
        "id": "q3",
        "question": "¿Cuál es el sistema de negocio del Manglitour?",
        "english": "What is the business model of the Manglitour?",
        "layer_hint": "💡 Observa las paradas del tour y las concesiones de acuacultura juntas",
    },
    {
        "id": "q4",
        "question": "¿Qué porcentaje de ingreso económico tiene el tour (turismo) vs. la venta del producto?",
        "english": "What percentage of income comes from tourism vs. product sales?",
        "layer_hint": "💡 Las capas de acuacultura muestran dónde se produce el producto",
    },
    {
        "id": "q5",
        "question": "¿Con quién colaboran para hacer medidas de calidad de agua?",
        "english": "Who do they collaborate with for water quality monitoring?",
        "layer_hint": "💡 Piensa en qué instituciones o actores del sistema podrían estar involucrados",
    },
    {
        "id": "q6",
        "question": "¿Hay un control del tráfico de embarcaciones en el área de la concesión?",
        "english": "Is there boat traffic control in the concession area?",
        "layer_hint": "💡 Observa la extensión de las concesiones y la cercanía al puerto",
    },
    {
        "id": "q7",
        "question": "¿Siguen teniendo problemáticas con los 'patitos'?",
        "english": "Do they still have issues with the 'patitos' (small unauthorized boats)?",
        "layer_hint": "💡 Relaciona con el tráfico del puerto y los límites de la concesión",
    },
    {
        "id": "q8",
        "question": "¿Qué estrategias tienen para fortalecer la organización a largo plazo?",
        "english": "What strategies do they have to strengthen the organization long-term?",
        "layer_hint": "💡 Piensa en qué elementos del sistema (social, ecológico, económico) sustentan la resiliencia",
    },
]

# -------------------------------------------------------------------
# Sidebar — layer controls and settings ONLY
# -------------------------------------------------------------------
with st.sidebar:

    site_choice = st.radio(
        "Active site:",
        ["La Paz harbor", "Cabo Pulmo", "Compare both"],
        index=0,
    )

    st.markdown("---")

    if site_choice in ["La Paz harbor", "Compare both"]:
        st.markdown("### La Paz layers")
        show_mangroves  = st.checkbox("Mangrove habitat", value=True)
        show_lapaz_mpa  = st.checkbox("Bay of La Paz biosphere reserve", value=False)
        show_manglitour = st.checkbox("Manglitour stops", value=True)
        show_concesiones = st.checkbox("Aquaculture concessions", value=True)
    else:
        show_mangroves   = False
        show_lapaz_mpa   = False
        show_manglitour  = False
        show_concesiones = False

    if site_choice in ["Cabo Pulmo", "Compare both"]:
        st.markdown("### Cabo Pulmo layers")
        show_cabo_mpa = st.checkbox("Marine park boundary", value=True)
    else:
        show_cabo_mpa = False

    st.markdown("---")
    st.markdown("### Map settings")

    basemap_choice = st.selectbox(
        "Select a basemap:",
        list(leafmap.basemaps.keys()),
        index=list(leafmap.basemaps.keys()).index("SATELLITE"),
    )

    show_draw    = st.checkbox(
        "Drawing tools", value=True,
        help="Sketch polygons, lines, and markers directly on the map. Drawings are not saved when the page reloads."
    )
    show_measure = st.checkbox(
        "Measure distances & areas", value=False,
        help="Click points on the map to measure distances in km or areas in km²."
    )

    st.markdown("---")
    with st.expander("About the data"):
        st.markdown(
            """
            **Mangroves:** The Nature Conservancy (TNC) — clipped to the Port of La Paz area.  
            **Marine park:** CONANP / WDPA (Protected Planet).  
            **Harbor development:** Illustrative — derived from satellite imagery.  
            **Community settlement:** Illustrative — approximate extent.  

            *Layers marked as illustrative use approximate geometries and should not
            be used for legal or decision-making purposes.*
            """
        )

# -------------------------------------------------------------------
# Fallback / illustrative GeoJSON
# -------------------------------------------------------------------
LAPAZ_MPA_GEOJSON = {
    "type": "FeatureCollection",
    "features": [{"type": "Feature",
                  "properties": {"name": "Bay of La Paz biosphere reserve (approx.)"},
                  "geometry": {"type": "Polygon", "coordinates": [[
                      [-110.520, 24.280], [-110.350, 24.300], [-110.250, 24.100],
                      [-110.280, 24.040], [-110.450, 24.050], [-110.550, 24.150],
                      [-110.520, 24.280]]]}}]
}

# -------------------------------------------------------------------
# Data loading with fallback
# -------------------------------------------------------------------
MANGROVE_URL = (
    "https://raw.githubusercontent.com/asivitskis/EarthInquiryLab/"
    "main/data/bcs_coastal_ed_data/LP_TNC_mangrove.json"
)
CABO_MPA_URL = (
    "https://raw.githubusercontent.com/asivitskis/EarthInquiryLab/"
    "main/data/bcs_coastal_ed_data/CaboPulmo_Boundary_CONANP.json"
)
MANGLITOUR_URL = (
    "https://raw.githubusercontent.com/asivitskis/EarthInquiryLab/"
    "main/data/bcs_coastal_ed_data/Manglitour_Stops.geojson"
)
CONCESIONES_URL = (
    "https://raw.githubusercontent.com/asivitskis/EarthInquiryLab/"
    "main/data/bcs_coastal_ed_data/Concesiones.geojson"
)

# Color map keyed on the "Type" field
STOP_COLOR_DICT = {
    "Inicio de reccorido": "#FFD700",
    "Barco hundido":       "#1E90FF",
    "Malvinas":            "#FF6347",
    "Acuacultura":         "#9B59B6",
    "Alimentos":           "#2ECC71",
}
STOP_COLOR_DEFAULT = "#AAAAAA"

def manglitour_style_callback(feature):
    stop_type = feature["properties"].get("Type", "")
    color = STOP_COLOR_DICT.get(stop_type, STOP_COLOR_DEFAULT)
    return {
        "radius": 8,
        "color": "white",
        "weight": 1.5,
        "fillColor": color,
        "fillOpacity": 0.95,
    }

manglitour_hover_style = {"radius": 11, "weight": 2.5, "color": "#FFFFFF", "fillOpacity": 1.0}

@st.cache_data(show_spinner="Loading spatial data…")
def load_geojson_with_fallback(url, fallback_dict):
    try:
        if not url:
            raise ValueError("No URL provided")
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        gdf = gpd.GeoDataFrame.from_features(r.json()["features"], crs="EPSG:4326")
        if gdf.empty:
            raise ValueError("Empty dataset returned")
        return gdf, False
    except Exception:
        gdf = gpd.GeoDataFrame.from_features(fallback_dict["features"], crs="EPSG:4326")
        return gdf, True

# Mangrove color map — keyed on Cmbio81_20 field
MANGROVE_COLOR_DICT = {
    "Pérdida de manglar":   "#ea0c00",
    "Manglar sin cambios":  "#027433",
    "Ganancia de manglar":  "#00fb15",
}

def mangrove_style_callback(feature):
    value = feature["properties"].get("Cmbio81_20", "")
    return {
        "color": "black",
        "weight": 0.5,
        "fillColor": MANGROVE_COLOR_DICT.get(value, "#888888"),
        "fillOpacity": 0.8,
    }

mangrove_hover_style = {"weight": 2, "color": "yellow", "fillOpacity": 0.9}

# -------------------------------------------------------------------
# Map center & zoom
# -------------------------------------------------------------------
if site_choice == "La Paz harbor":
    center, zoom = [24.14, -110.36], 13
elif site_choice == "Cabo Pulmo":
    center, zoom = [23.438124935783712, -109.42855096911228], 12
else:
    center, zoom = [23.85, -110.10], 9

# -------------------------------------------------------------------
# Styles
# -------------------------------------------------------------------
lapaz_mpa_style = {"color": "#18A550", "fillColor": "#DDC137", "fillOpacity": 0.08,
                   "weight": 2, "dashArray": "6 4"}

# -------------------------------------------------------------------
# Build map
# -------------------------------------------------------------------
m = leafmap.Map(center=center, zoom=zoom)
m.add_basemap(basemap_choice)

legend_dict = {}

if show_mangroves:
    m.add_vector(
        MANGROVE_URL,
        layer_name="Mangrove habitat",
        style_callback=mangrove_style_callback,
        hover_style=mangrove_hover_style,
        info_mode="on_hover",
        zoom_to_layer=False,
    )
    legend_dict["Mangrove habitat (1981-2020) — loss"]      = "#ea0c00"
    legend_dict["Mangrove habitat (1981-2020) — no change"] = "#027433"
    legend_dict["Mangrove habitat (1981-2020) — gain"]      = "#00fb15"

if show_lapaz_mpa:
    m.add_geojson(LAPAZ_MPA_GEOJSON, layer_name="La Paz biosphere reserve",
                  style=lapaz_mpa_style, info_mode=None, zoom_to_layer=False)
    legend_dict["La Paz biosphere reserve"] = "#378ADD"

if show_cabo_mpa:
    m.add_vector(
        CABO_MPA_URL,
        layer_name="Marine park boundary",
        style={"color": "#000000", "fillColor": "#FF6B35", "fillOpacity": 0.30,
               "weight": 2, "dashArray": "6 4"},
        hover_style={"fillOpacity": 0.25, "weight": 3},
        info_mode="on_hover",
        zoom_to_layer=False,
    )
    legend_dict["Marine park boundary"] = "#FF6B35"

if show_concesiones:
    m.add_vector(
        CONCESIONES_URL,
        layer_name="Aquaculture concessions",
        style={
            "color": "#4AA8D8",
            "weight": 0.8,
            "fillColor": "#ADE0F5",
            "fillOpacity": 0.05,
            "opacity": 0.6,
        },
        hover_style={"fillOpacity": 0.45, "weight": 1.5},
        info_mode="on_hover",
        zoom_to_layer=False,
    )
    legend_dict["Aquaculture concessions"] = "#ADE0F5"

if show_manglitour:
    m.add_vector(
        MANGLITOUR_URL,
        layer_name="Manglitour stops",
        style_callback=manglitour_style_callback,
        hover_style=manglitour_hover_style,
        info_mode="on_hover",
        zoom_to_layer=False,
    )
    legend_dict["Manglitour stop"] = "#1E90FF"

if legend_dict:
    m.add_legend(title="Map key", legend_dict=legend_dict, position="bottomright")

# Drawing tools — added to underlying Folium map object
if show_draw:
    Draw(
        export=False,
        draw_options={
            "polyline":     {"shapeOptions": {"color": "#e63946", "weight": 3}},
            "polygon":      {"shapeOptions": {"color": "#e63946", "weight": 2, "fillOpacity": 0.15}},
            "rectangle":    {"shapeOptions": {"color": "#e63946", "weight": 2, "fillOpacity": 0.15}},
            "circle":       {"shapeOptions": {"color": "#e63946", "weight": 2, "fillOpacity": 0.10}},
            "marker":       True,
            "circlemarker": False,
        },
        edit_options={"edit": True, "remove": True},
    ).add_to(m)

if show_measure:
    MeasureControl(
        primary_length_unit="kilometers",
        secondary_length_unit="miles",
        primary_area_unit="sqkilometers",
        secondary_area_unit="acres",
    ).add_to(m)

# -------------------------------------------------------------------
# Render map via HTML export (preserves Draw plugin correctly)
# -------------------------------------------------------------------
map_html = m.to_html()
st.components.v1.html(map_html, height=680, scrolling=False)

# Download map button
with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
    f.write(map_html)
    tmp_path = f.name

with open(tmp_path, "rb") as f:
    st.download_button(
        label="⬇️ Download map as HTML",
        data=f,
        file_name=f"coastal_explorer_{site_choice.lower().replace(' ', '_')}.html",
        mime="text/html",
        help="Download the current map as a standalone HTML file — open it in any browser, even offline.",
    )
os.unlink(tmp_path)


# -------------------------------------------------------------------
# DEBRIEF SECTION — only shown for La Paz harbor (OPRE context)
# -------------------------------------------------------------------
if site_choice == "La Paz harbor":

    st.markdown("---")
    st.subheader("🌿 Debrief del Manglitour — OPRE")

    st.markdown(
        """
        <div class="debrief-note">
        Estas son las preguntas que <strong>su grupo generó</strong> durante el Día 1.
        Discutan en equipo lo que aprendieron durante la visita con OPRE y designen un
        <strong>escribano</strong> para capturar las respuestas del equipo abajo.
        Sus respuestas se enviarán al documento compartido del grupo.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("&nbsp;")

    # Two-column layout: questions on left, response box on right
    col_q, col_r = st.columns([1, 1], gap="large")

    with col_q:
        st.markdown("**📋 Preguntas de la visita**")
        questions_html = "<div class='question-list'><ol>"
        for q in OPRE_QUESTIONS:
            questions_html += f"<li>{q['question']}</li>"
        questions_html += "</ol></div>"
        st.markdown(questions_html, unsafe_allow_html=True)

    with col_r:
        st.markdown("**✏️ Respuestas del equipo**")

        # Pre-populate numbered lines matching the questions
        default_text = "\n\n".join([f"{i}. " for i in range(1, len(OPRE_QUESTIONS) + 1)])

        team_answers = st.text_area(
            "Respuestas del equipo",
            value=default_text,
            height=320,
            key="team_answers",
            label_visibility="collapsed",
            help="El escribano del equipo anota las respuestas aquí. No es necesario tener respuesta completa — capturen lo que aprendieron y lo que sigue siendo duda.",
        )

    # Team name field — compact, below the two columns
    st.markdown("**👥 Nombre del equipo**")
    team_name = st.text_input(
        "Nombre del equipo",
        placeholder="Ej. Equipo Corales, Equipo Tiburón…",
        label_visibility="collapsed",
    )

    # Systems synthesis — full width, separate section
    st.markdown("---")
    st.markdown("### 🕸️ Conexiones del sistema")
    st.markdown(
        """
        <div class="synthesis-note">
        ¿Qué conexiones ven <em>entre</em> las respuestas?
        ¿Qué actores, recursos o tensiones aparecen en múltiples preguntas? ¿Dónde están los puntos de apalancamiento?
        </div>
        """,
        unsafe_allow_html=True,
    )
    systems_synthesis = st.text_area(
        "Conexiones del sistema",
        placeholder=(
            "Ej: La sostenibilidad económica (P2, P3, P4) parece depender de la calidad del ecosistema (P1, P5). "
            "El control del territorio (P6, P7) afecta tanto la ecología como la economía...\n\n"
            "¿Qué patrones ven? ¿Qué tensiones? ¿Qué sorpresas?"
        ),
        height=130,
        key="systems_synthesis",
    )

    # -------------------------------------------------------------------
    # Submit to Google Doc
    # -------------------------------------------------------------------
    st.markdown("---")

    col_submit, col_tip = st.columns([2, 1])

    with col_tip:
        st.info(
            "📄 Al hacer clic en **Enviar**, las respuestas de su equipo se agregarán "
            "al documento compartido del grupo. Asegúrense de haber escrito el nombre del equipo."
        )

    with col_submit:
        submit_btn = st.button("✅ Enviar respuestas del equipo al documento compartido", type="primary")

        if submit_btn:
            if not team_name.strip():
                st.error("⚠️ Por favor escriban el nombre de su equipo antes de enviar.")
            elif not GOOGLE_APPS_SCRIPT_URL:
                st.warning(
                    "⚙️ **Modo de prueba:** No se ha configurado la URL de Google Apps Script. "
                    "Aquí está lo que se enviaría al documento:"
                )
                st.markdown(f"**Equipo:** {team_name}")
                st.markdown(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                st.markdown("**Respuestas:**")
                st.text(team_answers)
                st.markdown("**Conexiones del sistema:**")
                st.text(systems_synthesis.strip() or "(sin respuesta)")
                st.caption(
                    "Para activar el envío real, configura un Google Apps Script Web App "
                    "y pega la URL en la variable `GOOGLE_APPS_SCRIPT_URL` al inicio del archivo."
                )
            else:
                payload = {
                    "team": team_name.strip(),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "site": "La Paz — Manglitour OPRE",
                    "answers": team_answers.strip(),
                    "systems_synthesis": systems_synthesis.strip(),
                }
                try:
                    resp = requests.post(GOOGLE_APPS_SCRIPT_URL, json=payload, timeout=15)
                    if resp.status_code == 200:
                        st.success(
                            f"✅ ¡Listo, {team_name}! Sus respuestas fueron enviadas al documento compartido."
                        )
                    else:
                        st.error(
                            f"❌ Algo salió mal (código {resp.status_code}). "
                            "Intenten de nuevo o avisen al facilitador."
                        )
                except Exception as e:
                    st.error(f"❌ No se pudo conectar al documento: {e}")

# -------------------------------------------------------------------
# Inquiry prompts — La Paz (Day 1 reference), Cabo Pulmo, Compare both
# -------------------------------------------------------------------

if site_choice == "La Paz harbor":
    st.markdown("---")
    st.subheader("🔍 Inquiry & Questions — Día 1")
    st.caption("These prompts guided your exploration on Day 1 and helped generate the questions above.")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            """
            **Observe the map**
            - Where do mangrove patches remain, and where have they been displaced by development?
            - Which mangrove areas appear most isolated or fragmented?
            - What patterns do you notice about the relationship between the port and the mangroves?
            """
        )
    with col_b:
        st.markdown(
            """
            **Go deeper**
            - Mangroves are sometimes called "nurseries of the sea." What does their fragmentation mean for the broader bay system?
            - What questions does this map raise that you'd want to explore during the OPRE mangrove tour?
            - What data is *missing* from this map that would help you understand this system better?
            """
        )

    st.markdown("---")
    st.subheader("📝 Record your questions")
    obs_col, tip_col = st.columns([2, 1])
    with obs_col:
        st.text_area(
            "Your questions — La Paz harbor",
            placeholder="What questions does the map raise for you? What do you want to find out?",
            height=140,
            key="observation_box",
        )
    with tip_col:
        st.info(
            "💡 Use the **drawing tools** on the map above to sketch patterns you notice — "
            "trace mangrove edges, mark interesting intersections, or drop a pin on something worth discussing.\n\n"
            "*Drawings are visible during your session but are not saved when the page reloads.*"
        )

elif site_choice == "Cabo Pulmo":
    st.markdown("---")
    st.subheader("🔍 Inquiry prompts")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            """
            **Observe the map**
            - Where does the marine park boundary fall relative to reef habitat?
            - How does the community settlement relate spatially to the protected area?
            - Where would you place a no-take zone, based on what you can see?
            """
        )
    with col_b:
        st.markdown(
            """
            **Go deeper**
            - In 1995, the Cabo Pulmo community stopped fishing and advocated for marine park status. Reef biomass has increased by over 460% since then. What spatial patterns might reflect that recovery?
            - What would this place look like without the marine park? What systems thinking tools help you reason about that counterfactual?
            - What can't this map tell you about what happened here?
            """
        )

    st.markdown("---")
    st.subheader("📝 Record your observations")
    obs_col, tip_col = st.columns([2, 1])
    with obs_col:
        st.text_area(
            "Your observations — Cabo Pulmo",
            placeholder="What do you notice? What patterns stand out? What questions does the map raise for you?",
            height=140,
            key="observation_box_cabo",
        )
    with tip_col:
        st.info(
            "💡 Use the **drawing tools** on the map above to sketch patterns you notice — "
            "trace reef edges, mark interesting intersections, or drop a pin on something worth discussing.\n\n"
            "*Drawings are visible during your session but are not saved when the page reloads.*"
        )

else:  # Compare both
    st.markdown("---")
    st.subheader("🔍 Inquiry prompts")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown(
            """
            **Compare the two places**
            - What is similar about the pressures La Paz and Cabo Pulmo face?
            - What looks different about how each place has responded?
            - Where do you see more fragmentation? More protection?
            """
        )
    with col_b:
        st.markdown(
            """
            **Systems thinking**
            - Where are the leverage points in each system?
            - What feedback loops might be reinforcing the current trajectory of each place?
            - How does community governance show up — or not — in each map?
            """
        )
    with col_c:
        st.markdown(
            """
            **Curriculum design**
            - What is the one tension you'd most want learners to sit with?
            - What local knowledge is entirely absent from these datasets?
            - How would you involve the Cabo Pulmo community in deciding what this map shows?
            """
        )

# -------------------------------------------------------------------
# Data note footer
# -------------------------------------------------------------------
st.markdown("---")
st.caption(
    "**Data sources:** La Paz mangroves — The Nature Conservancy (TNC), clipped to Port of La Paz area · "
    "CONANP / WDPA Protected Planet · "
    "Illustrative layers derived from satellite imagery and published survey data. "
    "All data are for educational purposes only and should not be used for legal or decision-making purposes."
)


# =============================================================================
# GOOGLE APPS SCRIPT CODE — paste this into your Apps Script editor
# =============================================================================
#
# function doPost(e) {
#   var doc = DocumentApp.openById("YOUR_GOOGLE_DOC_ID_HERE");
#   var body = doc.getBody();
#
#   try {
#     var data = JSON.parse(e.postData.contents);
#
#     // Team header
#     var header = body.appendParagraph("📋 " + data.team + " — " + data.timestamp);
#     header.setHeading(DocumentApp.ParagraphHeading.HEADING2);
#
#     // Numbered answers (single text block from the scribe)
#     body.appendParagraph("Respuestas del equipo:").setBold(true);
#     body.appendParagraph(data.answers || "(sin respuesta)").setBold(false);
#
#     // Systems synthesis
#     body.appendParagraph("🕸️ Conexiones del sistema:").setBold(true);
#     body.appendParagraph(data.systems_synthesis || "(sin respuesta)").setBold(false);
#
#     // Divider
#     body.appendParagraph("________________________________________________");
#
#     return ContentService.createTextOutput(
#       JSON.stringify({status: "ok"})
#     ).setMimeType(ContentService.MimeType.JSON);
#
#   } catch(err) {
#     return ContentService.createTextOutput(
#       JSON.stringify({status: "error", message: err.toString()})
#     ).setMimeType(ContentService.MimeType.JSON);
#   }
# }
#
# =============================================================================
