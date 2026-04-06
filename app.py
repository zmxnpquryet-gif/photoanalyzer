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
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from image_analyzer import calculate_chromatic_aberration, calculate_sharpness
from metadata_extractor import extract_metadata_from_file
from visualizer import ChartCanvas, plot_ca_bar, plot_focal_length_bar, plot_sharpness_bar


def create_shadow(blur=28, y_offset=10, alpha=30):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setXOffset(0)
    shadow.setYOffset(y_offset)
    shadow.setColor(QColor(22, 34, 55, alpha))
    return shadow


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


class InfoBadge(QFrame):
    def __init__(self, label, value="--"):
        super().__init__()
        self.setObjectName("InfoBadge")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        self.label = QLabel(label)
        self.label.setObjectName("BadgeLabel")

        self.value = QLabel(value)
        self.value.setObjectName("BadgeValue")
        self.value.setWordWrap(True)

        layout.addWidget(self.label)
        layout.addWidget(self.value)

    def set_value(self, value):
        self.value.setText(str(value))


class StatCard(QFrame):
    def __init__(self, title, value="--", accent="#4C7EDB"):
        super().__init__()
        self.setObjectName("StatCard")
        self.setGraphicsEffect(create_shadow(blur=24, y_offset=8, alpha=24))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName("StatTitle")

        self.value_label = QLabel(str(value))
        self.value_label.setObjectName("StatValue")
        self.value_label.setWordWrap(True)
        self.value_label.setStyleSheet(f"color: {accent};")

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()

    def set_value(self, value):
        self.value_label.setText(str(value))


class ChartSection(QFrame):
    def __init__(self, title, subtitle):
        super().__init__()
        self.setObjectName("ChartSection")
        self.setGraphicsEffect(create_shadow(blur=24, y_offset=8, alpha=20))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 22)
        layout.setSpacing(14)

        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("SectionSubtitle")
        subtitle_label.setWordWrap(True)

        self.canvas = ChartCanvas(self)

        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addWidget(self.canvas)


class PhotoAnalyzerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_folder = ""
        self.df = pd.DataFrame()

        self.setWindowTitle("Photo Analyzer Pro")
        self.resize(1360, 920)
        self.setMinimumSize(1100, 760)
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #f6f8fc,
                    stop: 0.45 #eef5ff,
                    stop: 1 #f6fbf7
                );
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QWidget {
                color: #26344f;
            }
            QFrame#HeroCard, QFrame#SummaryCard, QFrame#StatCard, QFrame#ChartSection, QFrame#InfoBadge {
                background-color: rgba(255, 255, 255, 0.96);
                border: 1px solid #dbe5f0;
                border-radius: 24px;
            }
            QLabel#Eyebrow {
                color: #4f78c7;
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }
            QLabel#HeroTitle {
                color: #16233c;
                font-size: 44px;
                font-weight: 800;
            }
            QLabel#HeroSubtitle {
                color: #61708d;
                font-size: 17px;
                font-weight: 500;
                line-height: 1.45em;
            }
            QLabel#FeaturePill {
                background-color: #eef4ff;
                color: #4062a8;
                border: 1px solid #d5e3fb;
                border-radius: 16px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: 700;
            }
            QLabel#DashTitle {
                color: #16233c;
                font-size: 32px;
                font-weight: 800;
            }
            QLabel#DashSubtitle {
                color: #64738f;
                font-size: 15px;
                font-weight: 500;
            }
            QLabel#BadgeLabel {
                color: #6d7b96;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
            }
            QLabel#BadgeValue {
                color: #1f2a44;
                font-size: 15px;
                font-weight: 700;
            }
            QLabel#StatTitle {
                color: #6c7b96;
                font-size: 12px;
                font-weight: 700;
            }
            QLabel#StatValue {
                color: #1f2a44;
                font-size: 24px;
                font-weight: 800;
            }
            QLabel#SectionTitle {
                color: #1b2842;
                font-size: 20px;
                font-weight: 800;
            }
            QLabel#SectionSubtitle {
                color: #677692;
                font-size: 13px;
                font-weight: 500;
            }
            QLabel#StatusLabel {
                color: #62718e;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton#PrimaryButton {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #458fff,
                    stop: 1 #3fc5a0
                );
                color: #ffffff;
                border: none;
                border-radius: 28px;
                padding: 15px 28px;
                font-size: 18px;
                font-weight: 800;
            }
            QPushButton#PrimaryButton:hover {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #357fe9,
                    stop: 1 #2fb48f
                );
            }
            QPushButton#PrimaryButton:disabled {
                background-color: #b8c6de;
            }
            QPushButton#SecondaryButton {
                background-color: #ffffff;
                color: #314463;
                border: 1px solid #d8e1ee;
                border-radius: 18px;
                padding: 11px 18px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton#SecondaryButton:hover {
                background-color: #f4f7fb;
            }
            QProgressBar {
                border: 1px solid #d7e0ec;
                border-radius: 11px;
                background-color: #f3f7fd;
                text-align: center;
                color: #3d4c67;
                font-weight: 700;
                min-height: 22px;
            }
            QProgressBar::chunk {
                border-radius: 10px;
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #5fa6ff,
                    stop: 1 #55d0af
                );
            }
            """
        )

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
        welcome_layout.setContentsMargins(40, 32, 40, 32)
        welcome_layout.setSpacing(24)
        welcome_layout.addStretch()

        hero_card = QFrame()
        hero_card.setObjectName("HeroCard")
        hero_card.setGraphicsEffect(create_shadow(blur=34, y_offset=14, alpha=26))

        hero_layout = QVBoxLayout(hero_card)
        hero_layout.setContentsMargins(54, 52, 54, 46)
        hero_layout.setSpacing(18)

        eyebrow = QLabel("PHOTO ANALYZER")
        eyebrow.setObjectName("Eyebrow")
        eyebrow.setAlignment(Qt.AlignCenter)

        title_lbl = QLabel("사진 폴더를 한눈에 정리해드릴게요")
        title_lbl.setObjectName("HeroTitle")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setWordWrap(True)

        subtitle_lbl = QLabel(
            "EXIF 메타데이터, 선명도, 색수차 지표를 한 번에 읽어서\n"
            "보기 편한 요약 카드와 차트로 정리합니다."
        )
        subtitle_lbl.setObjectName("HeroSubtitle")
        subtitle_lbl.setAlignment(Qt.AlignCenter)

        feature_row = QHBoxLayout()
        feature_row.setSpacing(10)
        feature_row.setAlignment(Qt.AlignCenter)
        for text in ("메타데이터 요약", "선명도 랭킹", "색수차 비교", "초점거리 분포"):
            pill = QLabel(text)
            pill.setObjectName("FeaturePill")
            feature_row.addWidget(pill)

        self.btn_start = QPushButton("사진 폴더 선택")
        self.btn_start.setObjectName("PrimaryButton")
        self.btn_start.setMinimumHeight(58)
        self.btn_start.setMinimumWidth(300)
        self.btn_start.setGraphicsEffect(create_shadow(blur=24, y_offset=8, alpha=36))
        self.btn_start.clicked.connect(self.select_folder)

        self.welcome_progress = QProgressBar()
        self.welcome_progress.setVisible(False)
        self.welcome_progress.setMaximumWidth(520)

        self.welcome_status = QLabel("")
        self.welcome_status.setObjectName("StatusLabel")
        self.welcome_status.setAlignment(Qt.AlignCenter)

        hero_layout.addWidget(eyebrow)
        hero_layout.addWidget(title_lbl)
        hero_layout.addWidget(subtitle_lbl)
        hero_layout.addLayout(feature_row)
        hero_layout.addSpacing(10)
        hero_layout.addWidget(self.btn_start, 0, Qt.AlignCenter)
        hero_layout.addWidget(self.welcome_progress, 0, Qt.AlignCenter)
        hero_layout.addWidget(self.welcome_status)

        welcome_layout.addWidget(hero_card)
        welcome_layout.addStretch()

        self.stacked_widget.addWidget(self.welcome_screen)

    def _build_dashboard_screen(self):
        self.dashboard_screen = QWidget()
        dashboard_root = QVBoxLayout(self.dashboard_screen)
        dashboard_root.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        dashboard_content = QWidget()
        content_layout = QVBoxLayout(dashboard_content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(22)

        summary_card = QFrame()
        summary_card.setObjectName("SummaryCard")
        summary_card.setGraphicsEffect(create_shadow(blur=28, y_offset=10, alpha=22))

        summary_layout = QVBoxLayout(summary_card)
        summary_layout.setContentsMargins(24, 22, 24, 22)
        summary_layout.setSpacing(18)

        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        title_col = QVBoxLayout()
        title_col.setSpacing(6)

        self.lbl_dash_title = QLabel("분석 결과")
        self.lbl_dash_title.setObjectName("DashTitle")

        self.lbl_dash_subtitle = QLabel("폴더를 분석하면 중요한 수치와 흐름을 보기 좋게 보여줍니다.")
        self.lbl_dash_subtitle.setObjectName("DashSubtitle")
        self.lbl_dash_subtitle.setWordWrap(True)

        title_col.addWidget(self.lbl_dash_title)
        title_col.addWidget(self.lbl_dash_subtitle)

        self.btn_back = QPushButton("다른 폴더 분석")
        self.btn_back.setObjectName("SecondaryButton")
        self.btn_back.clicked.connect(self.go_back)

        top_row.addLayout(title_col, stretch=1)
        top_row.addWidget(self.btn_back, 0, Qt.AlignTop)

        badges_row = QHBoxLayout()
        badges_row.setSpacing(14)

        self.badge_folder = InfoBadge("현재 폴더", "--")
        self.badge_count = InfoBadge("이미지 수", "--")
        self.badge_camera_count = InfoBadge("카메라 종류", "--")
        self.badge_lens_count = InfoBadge("렌즈 종류", "--")

        badges_row.addWidget(self.badge_folder)
        badges_row.addWidget(self.badge_count)
        badges_row.addWidget(self.badge_camera_count)
        badges_row.addWidget(self.badge_lens_count)

        summary_layout.addLayout(top_row)
        summary_layout.addLayout(badges_row)

        stats_layout = QGridLayout()
        stats_layout.setHorizontalSpacing(18)
        stats_layout.setVerticalSpacing(18)

        self.card_focal = StatCard("평균 초점거리", "--", accent="#427DD6")
        self.card_aperture = StatCard("평균 조리개", "--", accent="#568AE7")
        self.card_shutter = StatCard("대표 셔터속도", "--", accent="#5A8FD1")
        self.card_iso = StatCard("평균 ISO", "--", accent="#4F79C3")
        self.card_camera = StatCard("가장 많이 쓴 카메라", "--", accent="#2A7B8C")
        self.card_lens = StatCard("가장 많이 쓴 렌즈", "--", accent="#2B9281")
        self.card_res = StatCard("가장 흔한 해상도", "--", accent="#407E62")

        stats_layout.addWidget(self.card_focal, 0, 0)
        stats_layout.addWidget(self.card_aperture, 0, 1)
        stats_layout.addWidget(self.card_shutter, 0, 2)
        stats_layout.addWidget(self.card_iso, 0, 3)
        stats_layout.addWidget(self.card_camera, 1, 0, 1, 2)
        stats_layout.addWidget(self.card_lens, 1, 2)
        stats_layout.addWidget(self.card_res, 1, 3)

        self.chart_sharpness = ChartSection(
            "선명도 상위 사진",
            "파일명이 긴 경우에도 읽기 쉽게 가로 막대로 보여줍니다.",
        )
        self.chart_ca = ChartSection(
            "색수차가 큰 사진",
            "테두리 번짐이 두드러지는 컷을 같은 방식으로 빠르게 비교합니다.",
        )
        self.chart_focal = ChartSection(
            "초점거리 사용 분포",
            "어떤 화각을 주로 썼는지 구간별 흐름을 한눈에 확인할 수 있습니다.",
        )

        content_layout.addWidget(summary_card)
        content_layout.addLayout(stats_layout)
        content_layout.addWidget(self.chart_sharpness)
        content_layout.addWidget(self.chart_ca)
        content_layout.addWidget(self.chart_focal)
        content_layout.addStretch()

        scroll_area.setWidget(dashboard_content)
        dashboard_root.addWidget(scroll_area)

        self.stacked_widget.addWidget(self.dashboard_screen)

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "사진 폴더 선택")
        if folder_path:
            self.current_folder = folder_path
            folder_name = os.path.basename(folder_path) or folder_path

            self.btn_start.setEnabled(False)
            self.welcome_progress.setVisible(True)
            self.welcome_progress.setValue(0)
            self.welcome_status.setText(f"{folder_name} 분석 중...")

            self.worker = WorkerThread(folder_path)
            self.worker.progress.connect(self.update_progress)
            self.worker.finished.connect(self.on_analysis_finished)
            self.worker.start()

    def update_progress(self, value):
        self.welcome_progress.setValue(value)

    def on_analysis_finished(self, df):
        self.df = df
        self.btn_start.setEnabled(True)
        self.welcome_progress.setVisible(False)
        self.welcome_status.setText("")

        if not df.empty:
            self.update_ui()
            self.stacked_widget.setCurrentIndex(1)
        else:
            self.welcome_status.setText("선택한 폴더에서 분석할 이미지를 찾지 못했습니다.")

    def go_back(self):
        self.welcome_status.setText("")
        self.stacked_widget.setCurrentIndex(0)

    def update_ui(self):
        df = self.df
        folder_name = os.path.basename(self.current_folder) or self.current_folder or "--"

        self.lbl_dash_title.setText("분석 결과")
        self.lbl_dash_subtitle.setText(
            f"{len(df)}장의 사진을 분석했습니다. 자주 사용한 장비와 품질 지표를 아래에서 바로 확인해보세요."
        )

        self.badge_folder.set_value(folder_name)
        self.badge_count.set_value(f"{len(df)}장")
        self.badge_camera_count.set_value(f"{self._unique_count(df, 'camera_model')}종")
        self.badge_lens_count.set_value(f"{self._unique_count(df, 'lens_model')}종")

        avg_focal = self._mean_value(df, "focal_length")
        avg_aperture = self._mean_value(df, "aperture")
        avg_iso = self._mean_value(df, "iso")

        self.card_focal.set_value(f"{avg_focal:.1f} mm" if avg_focal is not None else "--")
        self.card_aperture.set_value(f"f/{avg_aperture:.1f}" if avg_aperture is not None else "--")
        self.card_iso.set_value(f"{avg_iso:.0f}" if avg_iso is not None else "--")
        self.card_shutter.set_value(self._mode_value(df, "shutter_speed", suffix="s"))
        self.card_camera.set_value(self._mode_value(df, "camera_model"))
        self.card_lens.set_value(self._mode_value(df, "lens_model"))
        self.card_res.set_value(self._mode_value(df, "resolution"))

        plot_sharpness_bar(self.chart_sharpness.canvas, df)
        plot_ca_bar(self.chart_ca.canvas, df)
        plot_focal_length_bar(self.chart_focal.canvas, df)

    @staticmethod
    def _mean_value(df, column):
        if column not in df.columns:
            return None
        values = pd.to_numeric(df[column], errors="coerce").dropna()
        if values.empty:
            return None
        return float(values.mean())

    @staticmethod
    def _mode_value(df, column, suffix=""):
        if column not in df.columns:
            return "--"
        values = df[column].dropna()
        if values.empty:
            return "--"
        mode = values.mode()
        if mode.empty:
            return "--"
        return f"{mode.iloc[0]}{suffix}"

    @staticmethod
    def _unique_count(df, column):
        if column not in df.columns:
            return 0
        values = df[column].dropna()
        return int(values.nunique()) if not values.empty else 0


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
