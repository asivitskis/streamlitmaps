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
    .question-card {
        background: #f0f7f4;
        border-left: 4px solid #027433;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }
    .question-text {
        font-size: 1.05rem;
        font-weight: 600;
        color: #1a3d2b;
        margin-bottom: 6px;
    }
    .debrief-note {
        background: #fff8e1;
        border-left: 4px solid #f4a100;
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 0.95rem;
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
GOOGLE_APPS_SCRIPT_URL = ""   # ← paste your URL here, e.g. "https://script.google.com/macros/s/.../exec"

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
    st.subheader("🌿 Preguntas del grupo — Debrief del Manglitour")
    st.markdown(
        """
        <div class="debrief-note">
        Estas son las preguntas que <strong>ustedes generaron</strong> durante el Día 1, antes de visitar el Manglitour.
        Ahora que regresaron de la experiencia con OPRE, documenten lo que aprendieron sobre cada una.
        Sus respuestas serán enviadas al documento compartido del grupo para usar como base en la construcción del
        <strong>diagrama de sistemas socio-ecológicos</strong>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Participant name field
    st.markdown("### 👤 Tu nombre")
    participant_name = st.text_input(
        "Nombre del participante",
        placeholder="Escribe tu nombre para identificar tus respuestas en el documento compartido",
        label_visibility="collapsed",
    )

    st.markdown("### 📋 Responde las preguntas de la visita")
    st.markdown(
        "Para cada pregunta, anota lo que escuchaste, observaste o todavía te preguntas. "
        "No necesitas tener la respuesta completa — captura lo que aprendiste."
    )

    # Collect per-question answers
    answers = {}
    for i, q in enumerate(OPRE_QUESTIONS, 1):
        st.markdown(
            f"""
            <div class="question-card">
                <div class="question-text">❓ {i}. {q['question']}</div>
                <div style="color:#555; font-size:0.88rem; margin-bottom:6px; font-style:italic;">{q['english']}</div>
                <div style="color:#027433; font-size:0.85rem;">{q['layer_hint']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        answers[q["id"]] = st.text_area(
            label=f"Respuesta — pregunta {i}",
            placeholder="¿Qué aprendiste? ¿Qué te dijeron? ¿Qué sigue siendo una duda?",
            height=100,
            key=f"ans_{q['id']}",
            label_visibility="collapsed",
        )

    # Systems connections synthesis field
    st.markdown("---")
    st.markdown("### 🕸️ Conexiones del sistema")
    st.markdown(
        """
        <div class="debrief-note">
        Antes de construir el diagrama socio-ecológico, tómate un momento para reflexionar:
        ¿Qué conexiones ves <em>entre</em> estas preguntas y respuestas?
        ¿Qué actores, recursos, o tensiones aparecen en múltiples preguntas?
        </div>
        """,
        unsafe_allow_html=True,
    )
    systems_synthesis = st.text_area(
        "Conexiones del sistema",
        placeholder=(
            "Ejemplo: La sostenibilidad económica (P2, P3, P4) parece depender de la calidad del ecosistema (P1, P5). "
            "El control del territorio (P6, P7) afecta tanto a la ecología como a la economía...\n\n"
            "¿Qué elementos se repiten? ¿Qué tensiones ves? ¿Dónde están los puntos de apalancamiento?"
        ),
        height=150,
        key="systems_synthesis",
    )

    # -------------------------------------------------------------------
    # Submit to Google Doc
    # -------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 📤 Enviar al documento compartido")

    col_submit, col_tip = st.columns([2, 1])

    with col_tip:
        st.info(
            "📄 Al hacer clic en **Enviar**, tus respuestas se agregarán automáticamente "
            "al documento compartido del grupo. Asegúrate de haber escrito tu nombre arriba."
        )

    with col_submit:
        submit_btn = st.button("✅ Enviar mis respuestas al documento compartido", type="primary")

        if submit_btn:
            if not participant_name.strip():
                st.error("⚠️ Por favor escribe tu nombre antes de enviar.")
            elif not GOOGLE_APPS_SCRIPT_URL:
                # Show a preview of what would be sent (useful during setup/testing)
                st.warning(
                    "⚙️ **Modo de prueba:** No se ha configurado la URL de Google Apps Script. "
                    "Aquí está lo que se enviaría al documento:"
                )
                preview_lines = [
                    f"**Participante:** {participant_name}",
                    f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "",
                ]
                for i, q in enumerate(OPRE_QUESTIONS, 1):
                    ans = answers[q["id"]].strip() or "_(sin respuesta)_"
                    preview_lines.append(f"**P{i}: {q['question']}**")
                    preview_lines.append(ans)
                    preview_lines.append("")
                preview_lines.append("**Conexiones del sistema:**")
                preview_lines.append(systems_synthesis.strip() or "_(sin respuesta)_")
                st.markdown("\n".join(preview_lines))
                st.caption(
                    "Para activar el envío real, configura un Google Apps Script Web App "
                    "y pega la URL en la variable `GOOGLE_APPS_SCRIPT_URL` al inicio del archivo."
                )
            else:
                # Build payload
                payload = {
                    "participant": participant_name.strip(),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "site": "La Paz — Manglitour OPRE",
                    "answers": [
                        {
                            "question_es": q["question"],
                            "answer": answers[q["id"]].strip(),
                        }
                        for q in OPRE_QUESTIONS
                    ],
                    "systems_synthesis": systems_synthesis.strip(),
                }
                try:
                    resp = requests.post(GOOGLE_APPS_SCRIPT_URL, json=payload, timeout=15)
                    if resp.status_code == 200:
                        st.success(
                            f"✅ ¡Listo, {participant_name}! Tus respuestas fueron enviadas al documento compartido. "
                            "El grupo podrá verlas al momento de construir el diagrama de sistemas."
                        )
                    else:
                        st.error(
                            f"❌ Algo salió mal (código {resp.status_code}). "
                            "Intenta de nuevo o avisa al facilitador."
                        )
                except Exception as e:
                    st.error(f"❌ No se pudo conectar al documento: {e}")

# -------------------------------------------------------------------
# Inquiry prompts — Cabo Pulmo and Compare both
# -------------------------------------------------------------------
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
#   var sheet = SpreadsheetApp.getActiveSpreadsheet();
#   var doc = DocumentApp.openById("YOUR_GOOGLE_DOC_ID_HERE");
#   var body = doc.getBody();
#
#   try {
#     var data = JSON.parse(e.postData.contents);
#
#     body.appendParagraph("").setHeading(DocumentApp.ParagraphHeading.HEADING2);
#     var header = body.appendParagraph(
#       "📋 " + data.participant + " — " + data.timestamp
#     );
#     header.setHeading(DocumentApp.ParagraphHeading.HEADING2);
#
#     data.answers.forEach(function(item, i) {
#       var qPara = body.appendParagraph((i+1) + ". " + item.question_es);
#       qPara.setBold(true);
#       body.appendParagraph(item.answer || "(sin respuesta)").setBold(false);
#     });
#
#     body.appendParagraph("🕸️ Conexiones del sistema:").setBold(true);
#     body.appendParagraph(data.systems_synthesis || "(sin respuesta)").setBold(false);
#     body.appendParagraph("---");
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
