import os
import sys

import pandas as pd
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from image_analyzer import calculate_chromatic_aberration, calculate_sharpness
from metadata_extractor import extract_metadata_from_file
from visualizer import ChartCanvas, plot_ca_bar, plot_focal_length_bar, plot_sharpness_bar


class WorkerThread(QThread):
    progress = Signal(int)
    finished = Signal(object)

    def __init__(self, directory):
        super().__init__()
        self.directory = directory

    def run(self):
        valid_extensions = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}
        image_files = []
        for root, _, files in os.walk(self.directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in valid_extensions):
                    image_files.append(os.path.join(root, file))

        total = len(image_files)
        results = []

        if total == 0:
            self.finished.emit(pd.DataFrame())
            return

        for i, filepath in enumerate(image_files):
            meta = extract_metadata_from_file(filepath)
            meta["sharpness"] = calculate_sharpness(filepath)
            meta["ca_score"] = calculate_chromatic_aberration(filepath)
            results.append(meta)
            self.progress.emit(int((i + 1) / total * 100))

        self.finished.emit(pd.DataFrame(results))


class StatCard(QFrame):
    def __init__(self, title, value, accent="#4C7EDB"):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid #e7edf6;
                border-radius: 18px;
            }}
            QLabel#TitleLabel {{
                color: #7c8da6;
                font-size: 12px;
                font-weight: 600;
            }}
            QLabel#ValueLabel {{
                color: {accent};
                font-size: 24px;
                font-weight: 700;
            }}
            """
        )

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setXOffset(0)
        shadow.setYOffset(6)
        shadow.setColor(QColor(44, 63, 93, 26))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 18, 16, 18)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("TitleLabel")
        title_label.setAlignment(Qt.AlignCenter)

        self.value_label = QLabel(str(value))
        self.value_label.setObjectName("ValueLabel")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value):
        self.value_label.setText(str(value))


class PhotoAnalyzerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("사진 분석기 Pro")
        self.resize(1280, 850)
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #f8fbff,
                    stop: 1 #eef4fb
                );
            }
            QLabel {
                color: #33415c;
            }
            QFrame#HeroCard, QFrame#GraphContainer {
                background-color: #ffffff;
                border: 1px solid #e7edf6;
                border-radius: 24px;
            }
            QLabel#HeroTitle {
                color: #2f3d5c;
                font-size: 44px;
                font-weight: 800;
            }
            QLabel#HeroSubtitle {
                color: #6d7f9a;
                font-size: 18px;
                font-weight: 500;
            }
            QLabel#DashTitle {
                color: #2f3d5c;
                font-size: 30px;
                font-weight: 800;
            }
            QPushButton#PrimaryButton {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #6ca7ff,
                    stop: 1 #6fd6c2
                );
                color: white;
                border: none;
                border-radius: 30px;
                font-size: 19px;
                font-weight: 700;
                padding: 14px 26px;
            }
            QPushButton#PrimaryButton:hover {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #5f98ec,
                    stop: 1 #5dc3b3
                );
            }
            QPushButton#PrimaryButton:disabled {
                background-color: #b7c7dd;
            }
            QPushButton#SecondaryButton {
                background-color: #ffffff;
                color: #415676;
                border: 1px solid #d8e1ee;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton#SecondaryButton:hover {
                background-color: #f3f7fc;
            }
            QProgressBar {
                border: 1px solid #dce5f2;
                border-radius: 11px;
                background-color: #f6f9ff;
                text-align: center;
                color: #4c5f7d;
                font-weight: 600;
            }
            QProgressBar::chunk {
                border-radius: 10px;
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #7ebdff,
                    stop: 1 #7ad8c6
                );
            }
            QLabel#StatusLabel {
                color: #6c7f9b;
                font-size: 14px;
                font-weight: 500;
            }
            """
        )

        self.df = pd.DataFrame()
        self.init_ui()

    def init_ui(self):
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self._build_welcome_screen()
        self._build_dashboard_screen()
        self.stacked_widget.setCurrentIndex(0)

    def _build_welcome_screen(self):
        self.welcome_screen = QWidget()
        welcome_layout = QVBoxLayout(self.welcome_screen)
        welcome_layout.setContentsMargins(40, 30, 40, 30)
        welcome_layout.setAlignment(Qt.AlignCenter)

        hero_card = QFrame()
        hero_card.setObjectName("HeroCard")
        hero_shadow = QGraphicsDropShadowEffect()
        hero_shadow.setBlurRadius(30)
        hero_shadow.setColor(QColor(44, 63, 93, 22))
        hero_shadow.setYOffset(8)
        hero_card.setGraphicsEffect(hero_shadow)

        hero_layout = QVBoxLayout(hero_card)
        hero_layout.setContentsMargins(55, 60, 55, 48)
        hero_layout.setSpacing(18)
        hero_layout.setAlignment(Qt.AlignCenter)

        title_lbl = QLabel("사진 분석기 Pro")
        title_lbl.setObjectName("HeroTitle")
        title_lbl.setAlignment(Qt.AlignCenter)

        subtitle_lbl = QLabel("내 사진의 특징을 부드럽게 한눈에 확인해보세요")
        subtitle_lbl.setObjectName("HeroSubtitle")
        subtitle_lbl.setAlignment(Qt.AlignCenter)

        self.btn_start = QPushButton("사진 폴더 선택")
        self.btn_start.setObjectName("PrimaryButton")
        self.btn_start.setMinimumHeight(60)
        self.btn_start.setMinimumWidth(320)
        btn_shadow = QGraphicsDropShadowEffect()
        btn_shadow.setBlurRadius(22)
        btn_shadow.setYOffset(6)
        btn_shadow.setColor(QColor(71, 125, 204, 55))
        self.btn_start.setGraphicsEffect(btn_shadow)
        self.btn_start.clicked.connect(self.select_folder)

        self.welcome_progress = QProgressBar()
        self.welcome_progress.setMinimumWidth(460)
        self.welcome_progress.setVisible(False)

        self.welcome_status = QLabel("")
        self.welcome_status.setObjectName("StatusLabel")
        self.welcome_status.setAlignment(Qt.AlignCenter)

        hero_layout.addWidget(title_lbl)
        hero_layout.addWidget(subtitle_lbl)
        hero_layout.addSpacing(14)
        hero_layout.addWidget(self.btn_start, 0, Qt.AlignCenter)
        hero_layout.addSpacing(22)
        hero_layout.addWidget(self.welcome_progress)
        hero_layout.addWidget(self.welcome_status)

        welcome_layout.addStretch()
        welcome_layout.addWidget(hero_card, 0, Qt.AlignCenter)
        welcome_layout.addStretch()

        self.stacked_widget.addWidget(self.welcome_screen)

    def _build_dashboard_screen(self):
        self.dashboard_screen = QWidget()
        dash_layout = QVBoxLayout(self.dashboard_screen)
        dash_layout.setContentsMargins(30, 30, 30, 30)
        dash_layout.setSpacing(22)

        top_bar = QHBoxLayout()
        self.lbl_dash_title = QLabel("분석 결과")
        self.lbl_dash_title.setObjectName("DashTitle")

        self.btn_back = QPushButton("다른 폴더 분석하기")
        self.btn_back.setObjectName("SecondaryButton")
        self.btn_back.clicked.connect(self.go_back)

        top_bar.addWidget(self.lbl_dash_title)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_back)

        stats_layout = QGridLayout()
        stats_layout.setSpacing(18)

        self.card_focal = StatCard("평균 초점거리", "--", accent="#4e7ac7")
        self.card_aperture = StatCard("평균 조리개", "--", accent="#5f87d6")
        self.card_shutter = StatCard("대표 셔터속도", "--", accent="#6e92df")
        self.card_iso = StatCard("평균 ISO", "--", accent="#6580c5")
        self.card_camera = StatCard("가장 많이 쓴 카메라", "--", accent="#4f74b8")
        self.card_lens = StatCard("가장 많이 쓴 렌즈", "--", accent="#5682be")
        self.card_res = StatCard("가장 많은 해상도", "--", accent="#4c7aa4")

        stats_layout.addWidget(self.card_focal, 0, 0)
        stats_layout.addWidget(self.card_aperture, 0, 1)
        stats_layout.addWidget(self.card_shutter, 0, 2)
        stats_layout.addWidget(self.card_iso, 0, 3)
        stats_layout.addWidget(self.card_camera, 1, 0, 1, 2)
        stats_layout.addWidget(self.card_lens, 1, 2)
        stats_layout.addWidget(self.card_res, 1, 3)

        graphs_container = QFrame()
        graphs_container.setObjectName("GraphContainer")
        graphs_shadow = QGraphicsDropShadowEffect()
        graphs_shadow.setBlurRadius(26)
        graphs_shadow.setColor(QColor(44, 63, 93, 18))
        graphs_shadow.setYOffset(6)
        graphs_container.setGraphicsEffect(graphs_shadow)

        graphs_layout = QHBoxLayout(graphs_container)
        graphs_layout.setContentsMargins(16, 16, 16, 16)
        graphs_layout.setSpacing(14)

        self.canvas_sharpness = ChartCanvas(self)
        self.canvas_ca = ChartCanvas(self)
        self.canvas_focal = ChartCanvas(self)
        graphs_layout.addWidget(self.canvas_sharpness)
        graphs_layout.addWidget(self.canvas_ca)
        graphs_layout.addWidget(self.canvas_focal)

        dash_layout.addLayout(top_bar)
        dash_layout.addLayout(stats_layout)
        dash_layout.addWidget(graphs_container, stretch=1)

        self.stacked_widget.addWidget(self.dashboard_screen)

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "사진 폴더 선택")
        if folder_path:
            self.btn_start.setEnabled(False)
            self.welcome_progress.setVisible(True)
            self.welcome_progress.setValue(0)
            self.welcome_status.setText(f"{os.path.basename(folder_path)} 분석 중...")

            self.worker = WorkerThread(folder_path)
            self.worker.progress.connect(self.update_progress)
            self.worker.finished.connect(self.on_analysis_finished)
            self.worker.start()

    def update_progress(self, val):
        self.welcome_progress.setValue(val)

    def on_analysis_finished(self, df):
        self.df = df
        self.btn_start.setEnabled(True)
        self.welcome_progress.setVisible(False)
        self.welcome_status.setText("")

        if not df.empty:
            self.update_ui()
            self.stacked_widget.setCurrentIndex(1)
        else:
            self.welcome_status.setText("선택한 폴더에서 이미지를 찾지 못했습니다.")

    def go_back(self):
        self.welcome_status.setText("")
        self.stacked_widget.setCurrentIndex(0)

    def update_ui(self):
        df = self.df

        if "focal_length" in df.columns:
            avg_focal = df["focal_length"].mean()
            self.card_focal.set_value(f"{avg_focal:.1f} mm" if pd.notnull(avg_focal) else "--")

        if "aperture" in df.columns:
            avg_aperture = df["aperture"].mean()
            self.card_aperture.set_value(f"f/{avg_aperture:.1f}" if pd.notnull(avg_aperture) else "--")

        if "iso" in df.columns:
            avg_iso = df["iso"].mean()
            self.card_iso.set_value(f"{avg_iso:.0f}" if pd.notnull(avg_iso) else "--")

        if "camera_model" in df.columns:
            top_camera = df["camera_model"].mode()
            self.card_camera.set_value(top_camera[0] if not top_camera.empty else "--")

        if "lens_model" in df.columns:
            top_lens = df["lens_model"].mode()
            self.card_lens.set_value(top_lens[0] if not top_lens.empty else "--")

        if "resolution" in df.columns:
            top_res = df["resolution"].mode()
            self.card_res.set_value(top_res[0] if not top_res.empty else "--")

        if "shutter_speed" in df.columns:
            top_shutter = df["shutter_speed"].mode()
            self.card_shutter.set_value(f"{top_shutter[0]}s" if not top_shutter.empty else "--")

        plot_sharpness_bar(self.canvas_sharpness, df)
        plot_ca_bar(self.canvas_ca, df)
        plot_focal_length_bar(self.canvas_focal, df)


def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def load_app_font_family():
    font_path = resource_path(os.path.join("assets", "fonts", "NotoSansKR-VF.ttf"))
    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                return families[0]
    return "Malgun Gothic"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    font_family = load_app_font_family()
    app.setFont(QFont(font_family, 10))

    window = PhotoAnalyzerApp()
    window.show()
    sys.exit(app.exec())
