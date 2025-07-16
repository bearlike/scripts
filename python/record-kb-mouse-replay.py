#!/usr/bin/env python3
"""
# Keyboard and Mouse Recorder & Replayer

- This script records mouse left-clicks and keyboard press events along with the
time delays between them. When replaying, it reproduces the events in order.
- A new keystroke delay multiplier (a positive float, default 1) can be set to
speed up or slow down keyboard delays during replay.
- With a scrollable status area that logs events and displays progress.

## Usage:
pip install pyqt5 pyautogui pynput
python record-mouse-replay.py
"""

import sys
import time
import threading
import pyautogui
from pynput import mouse, keyboard

from PyQt5.QtCore import QThread, pyqtSignal, Qt, QRect
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QLineEdit,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QTextEdit,
)


# ======================================================
# Interaction class to hold event details.
# ======================================================
class Interaction:
    def __init__(self, event_type, data, delay):
        """
        event_type: "mouse" or "keyboard"
        data: For mouse, a dict with: x, y, button
              For keyboard, a dict with: key   (for example, "Key.enter" or "a")
        delay: Delay (in seconds) since the previous event.
        """
        self.event_type = event_type
        self.data = data
        self.delay = delay

    def __repr__(self):
        return f"Interaction(type={self.event_type}, data={self.data}, delay={self.delay:.3f})"


# ======================================================
# Recorder Worker: Records both mouse and keyboard events.
# ======================================================
class InteractionRecorderWorker(QThread):
    new_interaction = pyqtSignal(object)
    finished_recording = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.recorded_interactions = []
        self._running = True
        self._lock = threading.Lock()
        self.mouse_listener = None
        self.keyboard_listener = None

    def run(self):
        start_time = None

        def on_mouse_click(x, y, button, pressed):
            nonlocal start_time
            if pressed and button == mouse.Button.left:
                now = time.time()
                delay = 0 if start_time is None else now - start_time
                start_time = now
                data = {"x": x, "y": y, "button": str(button)}
                event = Interaction("mouse", data, delay)
                with self._lock:
                    self.recorded_interactions.append(event)
                self.new_interaction.emit(event)
            return self._running

        def on_key_press(key):
            nonlocal start_time
            now = time.time()
            delay = 0 if start_time is None else now - start_time
            start_time = now
            try:
                key_str = key.char
            except AttributeError:
                key_str = str(key)  # e.g., "Key.enter"
            data = {"key": key_str}
            event = Interaction("keyboard", data, delay)
            with self._lock:
                self.recorded_interactions.append(event)
            self.new_interaction.emit(event)
            if not self._running:
                return False

        self.mouse_listener = mouse.Listener(on_click=on_mouse_click)
        self.keyboard_listener = keyboard.Listener(on_press=on_key_press)
        self.mouse_listener.start()
        self.keyboard_listener.start()

        while self._running:
            time.sleep(0.1)

        # Stop the listeners.
        self.mouse_listener.stop()
        self.keyboard_listener.stop()
        self.finished_recording.emit(self.recorded_interactions)

    def stop(self):
        self._running = False


# ======================================================
# Replayer Worker: Replays recorded interactions.
# ======================================================
class InteractionReplayerWorker(QThread):
    progress = pyqtSignal(str)
    finished_replay = pyqtSignal()

    def __init__(
        self, interactions, replay_count, set_delay, keystroke_multiplier, parent=None
    ):
        """
        interactions: List of recorded Interaction objects.
        replay_count: How many full replay sets to perform.
        set_delay: Delay (in seconds) between replay sets.
        keystroke_multiplier: Float multiplier for keyboard event delays.
        """
        super().__init__(parent)
        self.interactions = interactions
        self.replay_count = replay_count
        self.set_delay = set_delay
        self.keystroke_multiplier = keystroke_multiplier

    def run(self):
        self.progress.emit("Starting replay...")
        # Precompute total expected time for a replay set (considering delay adjustments).
        total_set_time = 0
        for ev in self.interactions:
            if ev.event_type == "keyboard":
                total_set_time += ev.delay * self.keystroke_multiplier
            else:
                total_set_time += ev.delay

        total_events = len(self.interactions)
        for set_number in range(1, self.replay_count + 1):
            self.progress.emit(
                f"Starting replay set {set_number}/{self.replay_count}..."
            )
            cumulative_delay = 0
            for idx, interaction in enumerate(self.interactions):
                # Determine adjusted delay.
                if interaction.event_type == "keyboard":
                    adjusted_delay = interaction.delay * self.keystroke_multiplier
                else:
                    adjusted_delay = interaction.delay
                if adjusted_delay < 0:
                    adjusted_delay = 0
                time.sleep(adjusted_delay)
                cumulative_delay += adjusted_delay

                # Compute ETA for current replay set.
                eta_set = total_set_time - cumulative_delay
                # Add delay for subsequent sets.
                overall_eta = eta_set + (self.replay_count - set_number) * (
                    total_set_time + self.set_delay
                )
                current_step = idx + 1
                self.progress.emit(
                    f"[Set {set_number}/{self.replay_count}] Step {current_step}/{total_events}, ETA: {overall_eta:.1f} sec"
                )

                # Execute the event.
                if interaction.event_type == "mouse":
                    x = interaction.data["x"]
                    y = interaction.data["y"]
                    pyautogui.click(x, y)
                    self.progress.emit(f"Performed mouse click at ({x}, {y})")
                elif interaction.event_type == "keyboard":
                    key = interaction.data["key"]
                    if key.startswith("Key."):
                        key_to_press = key.replace("Key.", "")
                    else:
                        key_to_press = key
                    pyautogui.press(key_to_press)
                    self.progress.emit(f"Performed key press '{key_to_press}'")
            if set_number < self.replay_count:
                self.progress.emit(
                    f"Waiting {self.set_delay} seconds before next set..."
                )
                time.sleep(self.set_delay)
        self.progress.emit("Replay finished!")
        self.finished_replay.emit()


# ======================================================
# MainWindow GUI (with scrollable status area)
# ======================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interaction Recorder & Replayer")
        self.setFixedSize(450, 500)
        self.recorder = None
        self.replayer = None
        self.recorded_interactions = []
        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()

        # Instruction / status label.
        self.status_label = QLabel("Press 'Start Recording' to begin.")
        main_layout.addWidget(self.status_label)

        # Control buttons/layout.
        control_layout = QHBoxLayout()
        self.start_rec_btn = QPushButton("Start Recording")
        self.start_rec_btn.clicked.connect(self.start_recording)
        control_layout.addWidget(self.start_rec_btn)

        self.stop_rec_btn = QPushButton("Stop Recording")
        self.stop_rec_btn.setEnabled(False)
        self.stop_rec_btn.clicked.connect(self.stop_recording)
        control_layout.addWidget(self.stop_rec_btn)
        main_layout.addLayout(control_layout)

        # Steps recorded indicator.
        self.steps_label = QLabel("Steps Recorded: 0")
        main_layout.addWidget(self.steps_label)

        # Replay configuration area.
        replay_layout = QHBoxLayout()
        self.replay_count_input = QLineEdit()
        self.replay_count_input.setPlaceholderText("Replay count (e.g., 3)")
        replay_layout.addWidget(self.replay_count_input)

        self.set_delay_input = QLineEdit()
        self.set_delay_input.setPlaceholderText("Delay between sets (sec)")
        replay_layout.addWidget(self.set_delay_input)
        main_layout.addLayout(replay_layout)

        # New field: Keystroke delay multiplier.
        ks_multiplier_layout = QHBoxLayout()
        ks_label = QLabel("Keystroke multiplier:")
        ks_multiplier_layout.addWidget(ks_label)
        self.ks_multiplier_input = QLineEdit("1")
        self.ks_multiplier_input.setPlaceholderText(
            "Keystroke delay multiplier (float)"
        )
        ks_multiplier_layout.addWidget(self.ks_multiplier_input)
        main_layout.addLayout(ks_multiplier_layout)

        # Start Replay button.
        self.replay_btn = QPushButton("Start Replay")
        self.replay_btn.setEnabled(False)
        self.replay_btn.clicked.connect(self.start_replay)
        main_layout.addWidget(self.replay_btn)

        # Scrollable Status area.
        status_area_label = QLabel("Status / Log:")
        main_layout.addWidget(status_area_label)
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setPlaceholderText(
            "Live status messages appear here ...")
        main_layout.addWidget(self.status_text)

        central_widget.setLayout(main_layout)
        self.position_dock_like()

    def position_dock_like(self):
        """Position the window just above the taskbar at the bottom center."""
        screen_geometry = QApplication.desktop().availableGeometry()
        window_width = self.width()
        window_height = self.height()
        x = screen_geometry.x() + (screen_geometry.width() - window_width) // 2
        # Assume taskbar height ≈ 40 px.
        y = screen_geometry.y() + screen_geometry.height() - window_height - 40
        self.setGeometry(QRect(x, y, window_width, window_height))
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

    def append_status(self, message):
        """Append a message to the scrollable status area and auto-scroll."""
        self.status_text.append(message)

    def start_recording(self):
        self.status_label.setText("Recording... Use left-click or press keys.")
        self.start_rec_btn.setEnabled(False)
        self.stop_rec_btn.setEnabled(True)
        self.replay_btn.setEnabled(False)
        self.status_text.clear()
        self.recorded_interactions = []
        self.steps_label.setText("Steps Recorded: 0")

        self.recorder = InteractionRecorderWorker()
        self.recorder.new_interaction.connect(self.handle_new_interaction)
        self.recorder.finished_recording.connect(self.finish_recording)
        self.recorder.start()

    def handle_new_interaction(self, interaction):
        self.recorded_interactions.append(interaction)
        self.append_status(f"Recorded: {interaction}")
        self.steps_label.setText(
            f"Steps Recorded: {len(self.recorded_interactions)}")

    def stop_recording(self):
        if self.recorder:
            self.recorder.stop()
            self.stop_rec_btn.setEnabled(False)
            self.status_label.setText("Stopped recording. Ready for replay.")

    def finish_recording(self, interactions):
        self.append_status(
            "Recording finished. Total interactions: " + str(len(interactions))
        )
        if interactions:
            self.replay_btn.setEnabled(True)
        else:
            self.start_rec_btn.setEnabled(True)

    def start_replay(self):
        # Validate replay count.
        try:
            replay_count = int(self.replay_count_input.text())
            if replay_count <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(
                self, "Input Error", "Please provide a valid integer for replay count."
            )
            return

        # Validate delay between sets.
        try:
            set_delay = float(self.set_delay_input.text())
            if set_delay < 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(
                self,
                "Input Error",
                "Please provide a valid number for delay between sets.",
            )
            return

        # Validate keystroke delay multiplier.
        try:
            ks_multiplier = float(self.ks_multiplier_input.text())
            if ks_multiplier <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(
                self,
                "Input Error",
                "Please provide a valid positive number for the keystroke delay multiplier.",
            )
            return

        if not self.recorded_interactions:
            QMessageBox.warning(
                self, "No Interactions", "No recorded interactions to replay."
            )
            return

        self.status_label.setText("Replaying interactions...")
        self.replay_btn.setEnabled(False)
        self.start_rec_btn.setEnabled(False)
        self.stop_rec_btn.setEnabled(False)

        self.replayer = InteractionReplayerWorker(
            self.recorded_interactions, replay_count, set_delay, ks_multiplier
        )
        self.replayer.progress.connect(self.append_status)
        self.replayer.finished_replay.connect(self.finish_replay)
        self.replayer.start()

    def finish_replay(self):
        self.status_label.setText("Replay finished. You may record again.")
        self.start_rec_btn.setEnabled(True)
        self.replay_btn.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
