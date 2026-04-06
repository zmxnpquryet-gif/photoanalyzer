import pandas as pd
import pyqtgraph as pg
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget


TITLE_COLOR = "#1F2A44"
AXIS_COLOR = "#60708C"
GRID_COLOR = "#DCE6F2"
PLOT_BG = "#F8FBFF"


def _font(point_size: int, bold: bool = False) -> QFont:
    app = QApplication.instance()
    family = app.font().family() if app else "Malgun Gothic"
    font = QFont(family, point_size)
    font.setBold(bold)
    return font


def _trim_filename(label: str, max_len: int = 26) -> str:
    if len(label) <= max_len:
        return label
    return f"{label[: max_len - 1]}..."


def _wrap_label(label: str, line_length: int = 12) -> str:
    text = _trim_filename(str(label), max_len=line_length * 2)
    chunks = [text[i : i + line_length] for i in range(0, len(text), line_length)]
    return "\n".join(chunks[:2])


def _apply_common_plot_style(plot_widget, y_grid: bool = True):
    plot_widget.clear()
    plot_widget.setBackground(PLOT_BG)
    plot_widget.showGrid(x=False, y=y_grid, alpha=0.28)
    plot_widget.setMenuEnabled(False)
    plot_widget.hideButtons()
    plot_widget.setMouseEnabled(x=False, y=False)
    plot_widget.disableAutoRange()
    plot_widget.enableAutoRange()
    plot_widget.setContentsMargins(0, 0, 0, 0)

    for axis_name in ("left", "bottom"):
        axis = plot_widget.getAxis(axis_name)
        axis.setPen(pg.mkPen(AXIS_COLOR, width=1))
        axis.setTextPen(pg.mkPen(AXIS_COLOR, width=1))

    plot_widget.getAxis("bottom").setStyle(tickTextOffset=10, tickFont=_font(9))
    plot_widget.getAxis("left").setStyle(tickTextOffset=8, tickFont=_font(9))
    plot_widget.getAxis("left").setWidth(180)


class ChartCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        pg.setConfigOption("antialias", True)
        pg.setConfigOption("foreground", AXIS_COLOR)
        pg.setConfigOption("background", PLOT_BG)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(PLOT_BG)
        self.plot_widget.setMinimumHeight(250)
        self.layout.addWidget(self.plot_widget)


def _plot_ranked_horizontal_bar(canvas, values, labels, brush, pen):
    plot_widget = canvas.plot_widget
    _apply_common_plot_style(plot_widget)

    if len(values) == 0:
        return

    positions = list(range(len(values)))
    max_value = max(values) if len(values) else 0

    bars = pg.BarGraphItem(
        x0=0,
        y=positions,
        height=0.62,
        width=values,
        brush=pg.mkBrush(brush),
        pen=pg.mkPen(pen, width=1.2),
    )
    plot_widget.addItem(bars)
    plot_widget.getAxis("left").setTicks([list(zip(positions, labels))])
    plot_widget.getAxis("bottom").setTicks([])
    plot_widget.setYRange(-0.7, len(values) - 0.3, padding=0.02)
    plot_widget.setXRange(0, max_value * 1.12 if max_value else 1, padding=0.02)


def plot_sharpness_bar(canvas, df):
    if "filename" not in df.columns or "sharpness" not in df.columns:
        _apply_common_plot_style(canvas.plot_widget)
        return

    df_sorted = (
        df.dropna(subset=["filename", "sharpness"])
        .sort_values(by="sharpness", ascending=False)
        .head(8)
        .iloc[::-1]
    )
    if df_sorted.empty:
        _apply_common_plot_style(canvas.plot_widget)
        return

    labels = [_trim_filename(str(name)) for name in df_sorted["filename"].tolist()]
    values = df_sorted["sharpness"].astype(float).tolist()
    _plot_ranked_horizontal_bar(canvas, values, labels, "#6FAEFF", "#4B86D9")


def plot_ca_bar(canvas, df):
    if "filename" not in df.columns or "ca_score" not in df.columns:
        _apply_common_plot_style(canvas.plot_widget)
        return

    df_sorted = (
        df.dropna(subset=["filename", "ca_score"])
        .sort_values(by="ca_score", ascending=False)
        .head(8)
        .iloc[::-1]
    )
    if df_sorted.empty:
        _apply_common_plot_style(canvas.plot_widget)
        return

    labels = [_trim_filename(str(name)) for name in df_sorted["filename"].tolist()]
    values = df_sorted["ca_score"].astype(float).tolist()
    _plot_ranked_horizontal_bar(canvas, values, labels, "#FF9E8D", "#D97968")


def plot_focal_length_bar(canvas, df):
    plot_widget = canvas.plot_widget
    _apply_common_plot_style(plot_widget)

    if "focal_length" not in df.columns:
        return

    fl_data = df["focal_length"].dropna()
    if fl_data.empty:
        return

    counts = fl_data.value_counts().sort_index()
    if len(counts) > 12:
        bins = pd.cut(fl_data, bins=8)
        counts = bins.value_counts().sort_index()
        labels = [f"{int(bin_range.left)}-{int(bin_range.right)}mm" for bin_range in counts.index]
    else:
        labels = [f"{value:g}mm" for value in counts.index]

    x = list(range(len(counts)))
    bars = pg.BarGraphItem(
        x=x,
        height=counts.values,
        width=0.62,
        brush=pg.mkBrush("#7ED7B8"),
        pen=pg.mkPen("#53AA8C", width=1.2),
    )
    plot_widget.addItem(bars)
    plot_widget.getAxis("bottom").setTicks([list(zip(x, [_wrap_label(label) for label in labels]))])
    plot_widget.setXRange(-0.8, len(counts) - 0.2, padding=0.02)
    plot_widget.setYRange(0, max(counts.values) * 1.15 if len(counts) else 1, padding=0.02)
