import pandas as pd
import pyqtgraph as pg
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QVBoxLayout, QWidget


TITLE_COLOR = "#3A4A66"
AXIS_COLOR = "#7F90AA"


def _trim_label(label, max_len=16):
    if len(label) <= max_len:
        return label
    return f"{label[: max_len - 1]}…"


def _apply_common_plot_style(plot_widget, title):
    plot_widget.clear()
    plot_widget.setTitle(title, color=TITLE_COLOR, size="11pt")
    plot_widget.setBackground("#FCFDFE")
    plot_widget.showGrid(x=False, y=True, alpha=0.16)
    plot_widget.setMenuEnabled(False)

    for axis_name in ("left", "bottom"):
        axis = plot_widget.getAxis(axis_name)
        axis.setPen(pg.mkPen(AXIS_COLOR, width=1))
        axis.setTextPen(pg.mkPen(AXIS_COLOR, width=1))

    plot_widget.getAxis("bottom").setStyle(tickTextOffset=10, tickFont=QFont("Noto Sans KR", 8))
    plot_widget.getAxis("left").setStyle(tickFont=QFont("Noto Sans KR", 8))


class ChartCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        pg.setConfigOption("antialias", True)
        pg.setConfigOption("foreground", AXIS_COLOR)
        pg.setConfigOption("background", "#FCFDFE")

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#FCFDFE")
        self.layout.addWidget(self.plot_widget)


def plot_sharpness_bar(canvas, df):
    _apply_common_plot_style(canvas.plot_widget, "선명도 TOP 10")

    if "filename" not in df.columns or "sharpness" not in df.columns:
        return

    df_sorted = df.sort_values(by="sharpness", ascending=False).head(10)
    if df_sorted.empty:
        return

    x = list(range(len(df_sorted)))
    y = df_sorted["sharpness"].values
    labels = [_trim_label(str(name)) for name in df_sorted["filename"].tolist()]

    bars = pg.BarGraphItem(
        x=x,
        height=y,
        width=0.56,
        brush=pg.mkBrush("#8EC2FF"),
        pen=pg.mkPen("#6EA6E8", width=1.2),
    )
    canvas.plot_widget.addItem(bars)
    canvas.plot_widget.getAxis("bottom").setTicks([list(zip(x, labels))])


def plot_ca_bar(canvas, df):
    _apply_common_plot_style(canvas.plot_widget, "색수차 점수 TOP 10")

    if "filename" not in df.columns or "ca_score" not in df.columns:
        return

    df_sorted = df.sort_values(by="ca_score", ascending=False).head(10)
    if df_sorted.empty:
        return

    x = list(range(len(df_sorted)))
    y = df_sorted["ca_score"].values
    labels = [_trim_label(str(name)) for name in df_sorted["filename"].tolist()]

    bars = pg.BarGraphItem(
        x=x,
        height=y,
        width=0.56,
        brush=pg.mkBrush("#FFB8AE"),
        pen=pg.mkPen("#EB9286", width=1.2),
    )
    canvas.plot_widget.addItem(bars)
    canvas.plot_widget.getAxis("bottom").setTicks([list(zip(x, labels))])


def plot_focal_length_bar(canvas, df):
    _apply_common_plot_style(canvas.plot_widget, "초점거리 사용 분포")

    if "focal_length" not in df.columns:
        return

    fl_data = df["focal_length"].dropna()
    if len(fl_data) == 0:
        return

    counts = fl_data.value_counts().sort_index()
    if len(counts) > 15:
        bins = pd.cut(fl_data, bins=8)
        counts = bins.value_counts().sort_index()
        labels = [f"{int(b.left)}-{int(b.right)}" for b in counts.index]
    else:
        labels = [f"{fl}" for fl in counts.index]

    if counts.empty:
        return

    x = list(range(len(counts)))
    bars = pg.BarGraphItem(
        x=x,
        height=counts.values,
        width=0.56,
        brush=pg.mkBrush("#A6DDCC"),
        pen=pg.mkPen("#7BC1AA", width=1.2),
    )
    canvas.plot_widget.addItem(bars)
    canvas.plot_widget.getAxis("bottom").setTicks([list(zip(x, labels))])
