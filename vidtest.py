import cv2
import os
import numpy as np
import sys
from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from time import sleep
import matplotlib.pyplot as plt


Form = uic.loadUiType(os.path.join(os.getcwd(), "mainwindow.ui"))[0]
cascade_Path = os.path.join(os.getcwd(), 'fist.xml')
fistCascade = cv2.CascadeClassifier(cascade_Path)


class ControlWindow(QMainWindow, Form):
    def __init__(self):
        QMainWindow.__init__(self)
        Form.__init__(self)
        self.setupUi(self)
        self.capture = None
        self.thread = PlotThread(0,0)
        self.fig = Figure(frameon=False)
        self.ax = self.fig.add_subplot(111, frameon=False)
        x = np.linspace(0, 2 * np.pi, 1000)
        self.line1, = self.ax.plot(x, np.cos(x), 'r', markersize=20)
        self.canvas = FigureCanvas(self.fig)
        self.navi = NavigationToolbar(self.canvas, self)

        self.start_capture()

        l = QVBoxLayout(self.matplotlib_widget)
        l.addWidget(self.canvas)
        l.addWidget(self.navi)

    def start_capture(self):
        if not self.capture:
            self.capture = QtCapture(0, self.vid_label)
        self.capture.start()
        if self.thread.isRunning():
            return
        self.thread = PlotThread(0, 0)
        self.thread.update_trigger.connect(self.update_plot)
        self.thread.start()

    def update_plot(self, x, y):
        self.line1.set_data(x, y)
        self.fig.canvas.draw()


class QtCapture(QMainWindow, Form):
    def __init__(self, *args):
        QMainWindow.__init__(self)
        self.fps = 24
        self.cap = cv2.VideoCapture(args[0])
    
        self.video_frame = args[1]
        lay = QVBoxLayout()
        lay.addWidget(self.video_frame)
        self.timer = QtCore.QTimer()

        self.xPos = []
        self.yPos = []

    def next_frame_slot(self):
        ret, frame = self.cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            fists = fistCascade.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=8,
                minSize=(40, 40),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            for (x, y, w, h) in fists:
                frame = cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                self.xPos.append(np.size(frame, 1) - x)
                self.yPos.append(np.size(frame, 0) - y)
                print(self.xPos, self.yPos)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.flip(frame, 1)
        img = QtGui.QImage(frame, frame.shape[1], frame.shape[0], QtGui.QImage.Format_RGB888)
        pix = QtGui.QPixmap.fromImage(img)
        self.video_frame.setPixmap(pix)
        self.video_frame.setScaledContents(True)

    def start(self):
        self.timer.timeout.connect(self.next_frame_slot)
        self.timer.start(1000./self.fps)

    def stop(self):
        self.timer.stop()

    def deleteLater(self):
        self.cap.release()
        super(QMainWindow, self).deleteLater()


class PlotThread(QtCore.QThread):
    update_trigger = QtCore.pyqtSignal(int, int)

    def __init__(self, new_x, new_y):
        QtCore.QThread.__init__(self)
        self.new_x = new_x
        self.new_y = new_y

    def run(self):
        self.update_trigger.emit(self.new_x, self.new_y)
        sleep(0.1)


app = QApplication(sys.argv)
app.setStyle("Plastic")
window = ControlWindow()
window.show()
sys.exit(app.exec_())