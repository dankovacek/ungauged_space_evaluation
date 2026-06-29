"""PyQGIS helper: style DKL points and create a print layout.

Usage in QGIS Python Console:
1) Load your point layer (e.g., ungauged_kld_overview or ungauged_kld_region).
2) Adjust settings below.
3) Run this file in the Python Console editor.
"""

import os

from qgis.PyQt.QtGui import QColor, QFont
from qgis.core import (
    QgsApplication,
    QgsCategorizedSymbolRenderer,
    QgsFillSymbol,
    QgsLegendStyle,
    QgsLayoutItemLabel,
    QgsLayoutItemLegend,
    QgsLayoutItemMap,
    QgsLayoutItemPicture,
    QgsLayoutItemScaleBar,
    QgsLayoutPoint,
    QgsLayoutSize,
    QgsMarkerSymbol,
    QgsPrintLayout,
    QgsProject,
    QgsRendererCategory,
    QgsRuleBasedRenderer,
    QgsSingleSymbolRenderer,
    QgsUnitTypes,
    QgsVectorFileWriter,
    QgsVectorLayerJoinInfo,
    QgsVectorLayer,
)

# Settings
DKL_LAYER_NAME = None
DKL_CLASSIFICATION_FIELD = "kld_class"
APPLY_CLASS_FILTER = True
KLD_CLASSES = ["1–2", "2–5", "5+"]
EXPORT_FILTERED = False
EXPORT_PATH = "data/results/plots/qgis/kld_lt1.gpkg"
EXPORT_LAYER_NAME = "ungauged_kld_lt1"
STATIONS_ACTIVE_LAYER = None
STATIONS_DISCONT_LAYER = None
STATIONS_LAYER = "filtered_station_set"
STATIONS_LAYER_PATH = "data/filtered_station_set.geojson"
STATIONS_STATUS_FIELD = "active"
STATIONS_ID_FIELD = "official_id"
STATIONS_STATUS_CSV_PATH = "data/Watershed_descriptors_20260203_with_stats.csv"
REGION_BOUNDARY_LAYER = None
LAYOUT_NAME = "DKL_Auto_Layout"
PAGE_SIZE = "A4"
PAGE_ORIENTATION = "Landscape"
TITLE_TEXT = "Predicted KL Divergence (bits)"
FONT_FAMILY = "EB Garamond"


def _layer_or_none(layer_name):
    if not layer_name:
        return None
    matches = QgsProject.instance().mapLayersByName(layer_name)
    return matches[0] if matches else None


def _layer_by_name_or_path(layer_name, layer_path):
    """Return existing layer by name or load from file path."""
    layer = _layer_or_none(layer_name)
    if layer:
        return layer
    if not layer_path:
        return None

    candidate_path = layer_path
    if not os.path.isabs(candidate_path):
        project_root = QgsProject.instance().readPath("./")
        candidate_path = os.path.join(project_root, candidate_path)

    display_name = layer_name or os.path.splitext(os.path.basename(candidate_path))[0]
    loaded = QgsVectorLayer(candidate_path, display_name, "ogr")
    if not loaded.isValid():
        raise RuntimeError(f"Unable to load station layer from '{candidate_path}'.")
    QgsProject.instance().addMapLayer(loaded)
    return loaded


def _first_layer_with_field(field_name):
    """Return first loaded vector layer containing field_name."""
    for layer in QgsProject.instance().mapLayers().values():
        if not isinstance(layer, QgsVectorLayer):
            continue
        names = {f.name() for f in layer.fields()}
        if field_name in names:
            return layer
    return None


def _resolve_path(path_value):
    if not path_value:
        return None
    if os.path.isabs(path_value):
        return path_value
    project_root = QgsProject.instance().readPath("./")
    return os.path.join(project_root, path_value)


def _ensure_station_status_field(stations_layer, status_field, id_field, status_csv_path):
    """Ensure status field exists directly or via join; return field name to style."""
    if not stations_layer:
        return None

    station_fields = {f.name() for f in stations_layer.fields()}
    if status_field in station_fields:
        return status_field

    if id_field not in station_fields:
        print(
            f"Skipping status join: field '{id_field}' not found on station layer '{stations_layer.name()}'."
        )
        return None

    csv_path = _resolve_path(status_csv_path)
    if not csv_path:
        print("Skipping status join: STATIONS_STATUS_CSV_PATH is empty.")
        return None

    csv_name = os.path.splitext(os.path.basename(csv_path))[0]
    status_table = _layer_or_none(csv_name)
    if not status_table:
        status_table = QgsVectorLayer(csv_path, csv_name, "ogr")
        if not status_table.isValid():
            print(f"Skipping status join: could not load '{csv_path}'.")
            return None
        QgsProject.instance().addMapLayer(status_table)

    table_fields = {f.name() for f in status_table.fields()}
    if id_field not in table_fields or status_field not in table_fields:
        print(
            f"Skipping status join: '{csv_name}' must include '{id_field}' and '{status_field}'."
        )
        return None

    join = QgsVectorLayerJoinInfo()
    join.setJoinLayerId(status_table.id())
    join.setJoinFieldName(id_field)
    join.setTargetFieldName(id_field)
    join.setUsingMemoryCache(True)
    join.setPrefix("status_")
    stations_layer.addJoin(join)

    joined_field = f"status_{status_field}"
    refreshed_fields = {f.name() for f in stations_layer.fields()}
    if joined_field in refreshed_fields:
        return joined_field

    print(f"Skipping status join: joined field '{joined_field}' not available.")
    return None


def _page_dimensions_mm(size_name, orientation):
    """Return (width, height) in mm for page size and orientation."""
    if size_name.lower() == "a4":
        w, h = 297.0, 210.0
    elif size_name.lower() == "letter":
        w, h = 279.4, 215.9
    else:
        raise ValueError("PAGE_SIZE must be 'A4' or 'Letter'.")

    if orientation.lower() == "portrait":
        return min(w, h), max(w, h)
    return max(w, h), min(w, h)


def apply_dkl_style(layer, field_name):
    """Apply categorized symbology based on text classes in kld_class."""
    categories = [
        ("1–2", "1-2", "#1a0530", 2.6, 0.7),
        ("2–5", "2-5", "#d3068f", 2.6, 0.7),
        ("5+", "5+", "#ff62cb", 2.6, 0.7),
    ]

    renderer_categories = []
    for value, label, color_hex, size, alpha in categories:
        symbol = QgsMarkerSymbol.createSimple({
            "name": "circle",
            "color": color_hex,
            "outline_style": "no",
            "outline_width": "0",
            "size": str(size),
        })
        symbol.setOpacity(alpha)
        renderer_categories.append(QgsRendererCategory(value, symbol, label))

    renderer = QgsCategorizedSymbolRenderer(field_name, renderer_categories)
    layer.setRenderer(renderer)
    layer.triggerRepaint()


def apply_station_style(active_layer, discont_layer):
    """Style active and discontinued station layers."""
    if active_layer:
        s_active = QgsMarkerSymbol.createSimple({
            "name": "triangle",
            "color": "#00e676",
            "outline_color": "#1b5e20",
            "outline_width": "0.3",
            "size": "3.2",
        })
        active_layer.setRenderer(QgsSingleSymbolRenderer(s_active))
        active_layer.triggerRepaint()

    if discont_layer:
        s_discont = QgsMarkerSymbol.createSimple({
            "name": "triangle",
            "color": "#ff8c42",
            "outline_color": "#7f2704",
            "outline_width": "0.3",
            "size": "3.0",
        })
        s_discont.setOpacity(0.45)
        discont_layer.setRenderer(QgsSingleSymbolRenderer(s_discont))
        discont_layer.triggerRepaint()


def apply_station_status_style(stations_layer, status_field):
    """Style one station layer with active/discontinued categories."""
    if not stations_layer:
        return

    field_names = {f.name() for f in stations_layer.fields()}
    if status_field not in field_names:
        s_default = QgsMarkerSymbol.createSimple({
            "name": "triangle",
            "color": "#00e676",
            "outline_color": "#1b5e20",
            "outline_width": "0.3",
            "size": "3.2",
        })
        stations_layer.setRenderer(QgsSingleSymbolRenderer(s_default))
        stations_layer.triggerRepaint()
        print(
            f"Applied fallback station style: '{status_field}' not found on '{stations_layer.name()}'."
        )
        return

    s_active = QgsMarkerSymbol.createSimple({
        "name": "triangle",
        "color": "#00e676",
        "outline_color": "#1b5e20",
        "outline_width": "0.3",
        "size": "3.2",
    })
    s_discont = QgsMarkerSymbol.createSimple({
        "name": "triangle",
        "color": "#ff8c42",
        "outline_color": "#7f2704",
        "outline_width": "0.3",
        "size": "3.0",
    })

    active_expr = (
        f"lower(to_string(\"{status_field}\")) IN ('1', 'true', 't', 'yes', 'y', 'active')"
    )

    root = QgsRuleBasedRenderer.Rule(None)
    active_rule = QgsRuleBasedRenderer.Rule(s_active, filterExpression=active_expr, label="Active stations")
    inactive_rule = QgsRuleBasedRenderer.Rule(
        s_discont,
        filterExpression="",
        label="Inactive (discontinued) stations",
    )
    inactive_rule.setIsElse(True)
    inactive_rule.symbol().setOpacity(0.65)
    root.appendChild(active_rule)
    root.appendChild(inactive_rule)

    stations_layer.setRenderer(QgsRuleBasedRenderer(root))
    stations_layer.triggerRepaint()


def apply_region_boundary_style(region_layer):
    """Style region boundary layer."""
    if not region_layer:
        return
    sym = QgsFillSymbol.createSimple({
        "color": "255,255,255,0",
        "outline_color": "#c05e5e",
        "outline_width": "0.8",
        "outline_style": "dash",
    })
    region_layer.setRenderer(QgsSingleSymbolRenderer(sym))
    region_layer.triggerRepaint()


def build_layout(project, layout_name, map_layer):
    """Create or replace print layout with map, title, legend, scale, and north arrow."""
    manager = project.layoutManager()
    existing = manager.layoutByName(layout_name)
    if existing:
        manager.removeLayout(existing)

    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(layout_name)
    manager.addLayout(layout)

    page = layout.pageCollection().page(0)
    page_width, page_height = _page_dimensions_mm(PAGE_SIZE, PAGE_ORIENTATION)
    page.setPageSize(QgsLayoutSize(page_width, page_height, QgsUnitTypes.LayoutMillimeters))

    # Title
    title = QgsLayoutItemLabel(layout)
    title.setText(TITLE_TEXT)
    title.setFont(QFont(FONT_FAMILY, 20))
    title.setFontColor(QColor("#2b1d1d"))
    title.adjustSizeToText()
    title.attemptMove(QgsLayoutPoint(12, 6, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(title)

    # Map
    map_item = QgsLayoutItemMap(layout)
    map_item.attemptMove(QgsLayoutPoint(12, 18, QgsUnitTypes.LayoutMillimeters))
    map_item.attemptResize(
        QgsLayoutSize(page_width - 95, page_height - 30, QgsUnitTypes.LayoutMillimeters)
    )
    extent = map_layer.extent()
    extent.scale(1.05)
    map_item.setExtent(extent)
    layout.addLayoutItem(map_item)

    # Legend
    legend = QgsLayoutItemLegend(layout)
    legend.setTitle("Min predicted KLD (bits)")
    legend.setLinkedMap(map_item)
    legend.setResizeToContents(True)
    legend.setStyleFont(QgsLegendStyle.Title, QFont(FONT_FAMILY, 14))
    legend.setStyleFont(QgsLegendStyle.Group, QFont(FONT_FAMILY, 12))
    legend.setStyleFont(QgsLegendStyle.Subgroup, QFont(FONT_FAMILY, 12))
    legend.setStyleFont(QgsLegendStyle.SymbolLabel, QFont(FONT_FAMILY, 12))
    legend.attemptMove(QgsLayoutPoint(page_width - 78, 22, QgsUnitTypes.LayoutMillimeters))
    legend.attemptResize(QgsLayoutSize(64, 80, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(legend)

    # Scale bar
    scale = QgsLayoutItemScaleBar(layout)
    scale.setStyle("Single Box")
    scale.setLinkedMap(map_item)
    scale.setNumberOfSegments(4)
    scale.setUnits(QgsUnitTypes.DistanceKilometers)
    scale.setNumberOfSegmentsLeft(0)
    scale.setUnitsPerSegment(25)
    scale.setUnitLabel("km")
    scale.setFont(QFont(FONT_FAMILY, 12))
    scale.update()
    scale.attemptMove(QgsLayoutPoint(16, page_height - 18, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(scale)

    # North arrow
    north = QgsLayoutItemPicture(layout)
    north_svg = QgsApplication.defaultThemePath() + "/north_arrows/layout_default_north_arrow.svg"
    north.setPicturePath(north_svg)
    north.attemptMove(QgsLayoutPoint(page_width - 30, page_height - 38, QgsUnitTypes.LayoutMillimeters))
    north.attemptResize(QgsLayoutSize(14, 24, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(north)

    return layout


# Main
project = QgsProject.instance()

# Get DKL layer
if DKL_LAYER_NAME:
    matches = project.mapLayersByName(DKL_LAYER_NAME)
    if not matches:
        raise RuntimeError(f"Layer '{DKL_LAYER_NAME}' not found.")
    dkl_layer = matches[0]
else:
    if "iface" not in globals() or iface is None:  # noqa: F821
        dkl_layer = _first_layer_with_field(DKL_CLASSIFICATION_FIELD)
        if not dkl_layer:
            raise RuntimeError(
                f"Could not find any loaded layer with field '{DKL_CLASSIFICATION_FIELD}', set DKL_LAYER_NAME explicitly."
            )
    else:
        dkl_layer = iface.activeLayer()  # noqa: F821
        if not dkl_layer:
            dkl_layer = _first_layer_with_field(DKL_CLASSIFICATION_FIELD)
            if not dkl_layer:
                raise RuntimeError("No active layer selected.")
        else:
            field_names = {f.name() for f in dkl_layer.fields()}
            if DKL_CLASSIFICATION_FIELD not in field_names:
                fallback = _first_layer_with_field(DKL_CLASSIFICATION_FIELD)
                if fallback:
                    dkl_layer = fallback

# Validate field
field_names = {f.name() for f in dkl_layer.fields()}
if DKL_CLASSIFICATION_FIELD not in field_names:
    raise RuntimeError(f"Field '{DKL_CLASSIFICATION_FIELD}' not found on layer.")

if APPLY_CLASS_FILTER:
    if not KLD_CLASSES:
        raise RuntimeError("KLD_CLASSES is empty while APPLY_CLASS_FILTER=True.")
    escaped = [value.replace("'", "''") for value in KLD_CLASSES]
    quoted = ", ".join(f"'{value}'" for value in escaped)
    subset = f'"{DKL_CLASSIFICATION_FIELD}" IN ({quoted})'
    dkl_layer.setSubsetString(subset)
    dkl_layer.triggerRepaint()
    print(f"Applied: {subset}")
    print(f"Visible features: {dkl_layer.featureCount()}")

if EXPORT_FILTERED:
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = EXPORT_LAYER_NAME

    err_code, err_msg, new_path, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
        dkl_layer,
        EXPORT_PATH,
        QgsProject.instance().transformContext(),
        options,
    )
    if err_code != QgsVectorFileWriter.NoError:
        raise RuntimeError(f"Export failed: {err_msg}")

    loaded = QgsVectorLayer(f"{new_path}|layername={EXPORT_LAYER_NAME}", EXPORT_LAYER_NAME, "ogr")
    if loaded.isValid():
        QgsProject.instance().addMapLayer(loaded)
    print(f"Exported: {new_path}")

# Apply styles
active_layer = _layer_or_none(STATIONS_ACTIVE_LAYER)
discont_layer = _layer_or_none(STATIONS_DISCONT_LAYER)
region_layer = _layer_or_none(REGION_BOUNDARY_LAYER)

stations_layer = _layer_by_name_or_path(STATIONS_LAYER, STATIONS_LAYER_PATH)
station_style_field = _ensure_station_status_field(
    stations_layer,
    STATIONS_STATUS_FIELD,
    STATIONS_ID_FIELD,
    STATIONS_STATUS_CSV_PATH,
)

apply_dkl_style(dkl_layer, DKL_CLASSIFICATION_FIELD)
apply_station_style(active_layer, discont_layer)
apply_station_status_style(stations_layer, station_style_field or STATIONS_STATUS_FIELD)
apply_region_boundary_style(region_layer)
layout = build_layout(project, LAYOUT_NAME, dkl_layer)

print(f"Styled: {dkl_layer.name()}")
print(f"Layout: {layout.name()}")
print("Open Layout Manager to export.")
