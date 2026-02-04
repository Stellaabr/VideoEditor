import sys
from PyQt6 import QtWidgets, QtMultimedia, QtCore
import cv2
import tempfile
import os
import shutil
from gui import Ui_MainWindow
import video_processing as vp


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        #Видео виджет
        self.mediaPlayer = QtMultimedia.QMediaPlayer()
        self.mediaPlayer.setVideoOutput(self.ui.videoWidget)
        self.ui.videoWidget.mousePressEvent = self.toggle_video_playback
        self._user_seeking = False
        self._was_playing = False

        self.size = 20
        self.threshold = 255
        self.current_filter = "median"
        self.setup_filter_buttons()
        self.file_path = ""

        self.showing_clean = False
        self.showing_noisy = False

        self.setup_connections()



    def setup_connections(self):
        self.mediaPlayer.durationChanged.connect(self.ui.horizontalScrollBar.setMaximum)
        self.mediaPlayer.positionChanged.connect(self.update_scrollbar_position)
        self.mediaPlayer.mediaStatusChanged.connect(self.handle_media_status)

        self.ui.selectFileButton.clicked.connect(self.select_file)
        self.ui.horizontalScrollBar.sliderMoved.connect(self.mediaPlayer.setPosition)
        self.ui.horizontalScrollBar.sliderPressed.connect(lambda: self.handle_seeking(True))
        self.ui.horizontalScrollBar.sliderReleased.connect(lambda: self.handle_seeking(False))

        self.ui.FilterSizeSlider.valueChanged.connect(self.on_filter_size_changed)
        self.ui.PorogSlider.valueChanged.connect(self.on_threshold_changed)
        self.ui.medianButton.toggled.connect(self.filter_change)
        self.ui.GaussianButton.toggled.connect(self.filter_change)


        self.ui.processButton.clicked.connect(self.process_video)
        self.ui.previewButton.clicked.connect(self.show_preview)
        self.ui.PredSPom.clicked.connect(self.show_noisy)

        self.ui.downloadCleanButton.clicked.connect(lambda: self.download_clean())
        self.ui.CrushButton.clicked.connect(lambda: self.download_noisy())

    def process_video(self):
        try:
            self.clean_frames, self.noisy_frames, self.video_info = vp.analyze_video_noise(
                self.file_path, self.threshold, self.current_filter, self.size)
        except Exception as e:
            print(f"Ошибка при обработке видео: {e}")
    def show_preview(self):
        if not hasattr(self, 'clean_frames') or not self.clean_frames:
            QtWidgets.QMessageBox.warning(self, "Предупреждение", "Сначала обработайте видео")
            return
        if hasattr(self, 'showing_clean') and self.showing_clean:
            # Возвращаем оригинал
            url = QtCore.QUrl.fromLocalFile(self.file_path)
            self.mediaPlayer.setSource(url)
            self.showing_clean = False
            self.ui.previewButton.setText("Показать чистые кадры")
            self.ui.statusLabel.setText("Оригинальное видео")
        else:
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                temp_path = temp_file.name

            sorted_frames = sorted(self.clean_frames, key=lambda x: x['frame_number'])
            height, width = sorted_frames[0]['frame'].shape[:2]
            fps = self.video_info.get('fps', 30)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))

            for frame_data in sorted_frames:
                out.write(frame_data['frame'])
            out.release()

            url = QtCore.QUrl.fromLocalFile(temp_path)
            self.mediaPlayer.setSource(url)
            self.showing_clean = True
            self.ui.previewButton.setText("Показать оригинал")
            self.ui.statusLabel.setText("Очищенные кадры")

            self.temp_clean_video_path = temp_path

        self.mediaPlayer.play()

    def show_noisy(self):
        if not hasattr(self, 'noisy_frames') or not self.noisy_frames:
            QtWidgets.QMessageBox.warning(self, "Предупреждение", "Сначала обработайте видео")
            return

        if hasattr(self, 'showing_noisy') and self.showing_noisy:

            url = QtCore.QUrl.fromLocalFile(self.file_path)
            self.mediaPlayer.setSource(url)
            self.showing_noisy = False
            self.ui.PredSPom.setText("Показать шумные кадры")
            self.ui.statusLabel.setText("Оригинальное видео")
        else:
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                temp_path = temp_file.name


            sorted_frames = sorted(self.noisy_frames, key=lambda x: x['frame_number'])  # Исправлено
            height, width = sorted_frames[0]['frame'].shape[:2]
            fps = self.video_info.get('fps', 30)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))

            for frame_data in sorted_frames:
                out.write(frame_data['frame'])
            out.release()

            url = QtCore.QUrl.fromLocalFile(temp_path)
            self.mediaPlayer.setSource(url)
            self.showing_noisy = True
            self.ui.PredSPom.setText("Показать оригинал")
            self.ui.statusLabel.setText("Шумные кадры")

            self.temp_noisy_video_path = temp_path

        self.mediaPlayer.play()


    #Все с боксом фильтров
    def filter_change(self):
        if self.ui.medianButton.isChecked():
            self.current_filter = "median"
        elif self.ui.GaussianButton.isChecked():
            self.current_filter = "gaussian"
    def on_filter_size_changed(self, value):
        self.size = value
        self.ui.FilterSizeSliderValue.setText(str(value))
    def on_threshold_changed(self, value):
        self.threshold = value
        self.ui.PorogSliderValue.setText(str(value))
    def update_slider_display(self):
        self.ui.FilterSizeSliderValue.setText(str(self.size))
        self.ui.PorogSliderValue.setText(str(self.threshold))
    def setup_filter_buttons(self):
        self.filter_button_group = QtWidgets.QButtonGroup(self)
        self.filter_button_group.addButton(self.ui.medianButton)
        self.filter_button_group.addButton(self.ui.GaussianButton)
        self.ui.medianButton.setChecked(True)


    #Все с виджет боксом
    def handle_seeking(self, is_starting):
        if is_starting:
            self._user_seeking = True
            self._was_playing = self.mediaPlayer.playbackState() == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState
            if self._was_playing:
                self.mediaPlayer.pause()
        else:
            self._user_seeking = False
            if self._was_playing:
                self.mediaPlayer.play()
    def update_scrollbar_position(self, position):
        if not self._user_seeking:
            self.ui.horizontalScrollBar.setValue(position)
    def toggle_video_playback(self, event):
        if self.mediaPlayer.playbackState() == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()
        event.accept()
    def handle_media_status(self, status):
        if status == QtMultimedia.QMediaPlayer.MediaStatus.EndOfMedia:
            self.mediaPlayer.setPosition(0)
            self.ui.horizontalScrollBar.setValue(0)

    #Все с первым боксом
    def select_file(self):
        self.file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Выберите видеофайл",
            "",
            "Видео файлы (*.mp4 *.avi *.mov *.mkv);;Все файлы (*)"
        )

        if self.file_path:
            filename = self.file_path.split('/')[-1]
            self.ui.filePathEdit.setText(self.file_path)
            self.ui.infoLabel.setText(f"Загружено: {filename}")
            self.ui.statusLabel.setText("Файл загружен")

            url = QtCore.QUrl.fromLocalFile(self.file_path)
            self.mediaPlayer.setSource(url)
            self.ui.horizontalScrollBar.setValue(0)
            self.mediaPlayer.play()


    #Скачивание
    def download_clean(self):
        if not hasattr(self, 'temp_clean_video_path'):
            QtWidgets.QMessageBox.warning(self, "Предупреждение", "Сначала создайте видео с чистыми кадрами")
            return
        self.download(self.temp_clean_video_path, "clean_video")
    def download_noisy(self):
        if not hasattr(self, 'temp_noisy_video_path'):
            QtWidgets.QMessageBox.warning(self, "Предупреждение", "Сначала создайте видео с шумными кадрами")
            return
        self.download(self.temp_noisy_video_path, "noisy_video")
    def download(self, temp_path, default_name="video"):
        if not temp_path or not os.path.exists(temp_path):
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Файл не найден. Сначала обработайте видео.")
            return

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Сохранить видео",
            f"{default_name}.mp4",
            "Видео файлы (*.mp4);;Все файлы (*)"
        )
        if file_path:
            try:
                # Копируем временный файл в выбранное место
                shutil.copy2(temp_path, file_path)
                QtWidgets.QMessageBox.information(self, "Успех", f"Видео сохранено как:\n{file_path}")
                self.ui.statusLabel.setText(f"Файл сохранен: {os.path.basename(file_path)}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
                self.ui.statusLabel.setText("Ошибка сохранения")


    def closeEvent(self, event):
        temp_files = []
        if hasattr(self, 'temp_clean_video_path'):
            temp_files.append(self.temp_clean_video_path)
        if hasattr(self, 'temp_noisy_video_path'):
            temp_files.append(self.temp_noisy_video_path)

        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Видео обработчик помех")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())