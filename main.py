import sys

from PyQt5.QtCore import QTimer, QPoint, pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, \
                            QFileDialog, QGroupBox, QGridLayout, QLabel
from PyQt5.QtWidgets import (QHBoxLayout, QOpenGLWidget, QSlider,
                             QWidget)
from Windows.MainWindowTemplate import Ui_MainWindow


from Canvas import Canvas
from Canvas3D import Canvas3D

from Parser import Parser
from Windows.ChooseWidget import ChooseWidget
from Windows.animationSettings import AnimationSettings
from Windows.PlotSettings import PlotSettings

from spin_gl import GLWidget
import threading

class MainWindow(QMainWindow, Ui_MainWindow, QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.odt_data = ""
        self.setupUi(self)
        self.setWindowTitle("ESE - Early Spins Enviroment")
        self.setGeometry(10,10,1280, 768) #size of window
        self.gridLayoutWidget.setGeometry(0, 0, self.width(), self.height())

        self.groupBox = [] #we store here groupBoxes for all widgets one Widget in one groupBox
        self.button = [] #we need to store these globaly to set event listeners
        self.gridSize = 0 # how many windows visible
        self.makeGrid() #create grid (4 Widgets) and stores them in arrays
        self.make1WindowGrid() #shows default 1 widget Window
        self.events() #create event listeners

    def events(self):
        '''Creates all listeners for Main Window'''
        #FILE SUBMENU
        self.actionLoad_Directory.triggered.connect(self.loadDirectory)

        #EDIT SUBMENU
        self.actionPlot.triggered.connect(self.showPlotSettings)
        self.actionAnimation.triggered.connect(self.showAnimationSettings)

        #VIEW SUBMENU
        self.action1_Window_Grid.triggered.connect(self.make1WindowGrid)
        self.action2_Windows_Grid.triggered.connect(self.make2WindowsGrid)
        self.action4_Windows_Grid.triggered.connect(self.make4WindowsGrid)

        #GRID BUTTONS
        #lambda required to pass parameter - which button was pressed
        self.button[0].clicked.connect(lambda: self.showChooseWidgetSettings(0))
        self.button[1].clicked.connect(lambda: self.showChooseWidgetSettings(1))
        self.button[2].clicked.connect(lambda: self.showChooseWidgetSettings(2))
        self.button[3].clicked.connect(lambda: self.showChooseWidgetSettings(3))

    def refreshScreen(self):
        '''weird stuff is happening when u want to update window u need to
        resize i think this is a bug'''
        self.resize(self.width()-1, self.height())
        self.resize(self.width()+1, self.height())

    def resizeEvent(self, event):
        '''What happens when window is resized'''
        self.gridLayoutWidget.setGeometry(0, 0, self.width(), self.height()-25)

    def loadDirectory(self):
        '''Loads whole directory based on Parse class as simple as BHP'''
        directory = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        if directory == None or directory == "":
            return 0

        #should be thrown into separate thread by pyqt
        self.rawVectorData, self.omf_header, self.odt_data, \
                        self.stages =  Parser.readFolder(directory)

    def showAnimationSettings(self):
        '''Shows window to change animations settings'''
        self.animationSettingsWindow = AnimationSettings()

    def showPlotSettings(self):
        """Spawns window for plot settings"""
        self.plotSettingsWindow = PlotSettings(list(self.odt_data), self.gridSize)
        self.plotSettingsWindow.setEventHandler(self.plotSettingsReceiver)
        #plotSettingsWindow.show()

    def plotSettingsReceiver(self, value):
        self.picked_column = value[0][0]
        if self.plot_active: #check what plot window is active
            self.autorun_plot(plot_type='2d plot')
        elif self.layer_plot_active: #check if layering plot is active
            self.autorun_plot(plot_type='2d layer')

    def autorun_plot(self, plot_type):
        """
        initiates a plot runner, creates canvas and distributes threads
        @plot_type is a plot type necessary to initate proper procedure
        @return void
        """
        if plot_type == '2d plot':
            data_dict = self.compose_dict()
            ### check all needed exceptions here
            if self.gridSize > 1:
                self.groupBoxCanvas.shareData(**data_dict)
                self.groupBoxCanvas.createPlotCanvas()
                try:
                    threading.Thread(target=self.groupBoxCanvas.loop).start()
                except RuntimeError:
                    print("THREADS CLOSED DUE RuntimeError")
        elif plot_type == '2d layer':
            data_dict = self.compose_dict(plot_type='2d layer')
            ### check all needed exceptions here
            if self.gridSize > 1:
                self.groupBoxCanvasLayer.shareData(**data_dict)
                self.groupBoxCanvasLayer.createPlotCanvas()
                try:
                    threading.Thread(target=self.groupBoxCanvasLayer.loop).start()
                except RuntimeError:
                    print("THREADS CLOSED DUE RuntimeError")
        else:
            msg = "Wrong plot_type argument"
            raise ValueError(msg)

    def compose_dict(self, plot_type='2d plot'):
        """
        composes a proper dictionary to pass to a given function shareData(**dict)
        @param plot_type is a plot type, can be '2d plot' or '2d layer'
        @return a dict of shareData parameters to pass
        """
        data_dict = None
        if plot_type == '2d plot':
            data_dict = {
                        'i': 0,
                        'iterations': self.stages,
                        'graph_data': self.odt_data[self.picked_column].tolist(),
                        'title' : self.picked_column
                        }
        elif plot_type == '2d layer':
            data_dict = {
                        'omf_header':  self.omf_header,
                        'multiple_data': self.rawVectorData,
                        'iterations': self.stages,
                        'current_layer': 0,
                        'title': '3dgraph',
                        'i': 0
                        }
        else:
            msg = "Wrong plot_type argument"
            raise ValueError(msg)
        return data_dict

    def showChooseWidgetSettings(self, number):
        '''Spawns Window for choosing widget for this pane'''
        self.new = ChooseWidget(number)
        self.new.setHandler(self.choosingWidgetReceiver)

    def choosingWidgetReceiver(self, value):
        '''Data receiver for choosingWidget action'''
        self.groupBox[value[0]].children()[1].deleteLater()
        self.groupBox[value[0]].children()[1].setParent(None)

        if value[1] == "OpenGL":
            self.openGLWidget = GLWidget()
            self.groupBox[value[0]].children()[0].addWidget(self.openGLWidget)
            self.refreshScreen()
            print(self.groupBox[value[0]].children())
        if value[1] == '2dPlot':
            #create canvas
            self.groupBoxCanvas = Canvas()
            self.groupBox[value[0]].children()[0].addWidget(self.groupBoxCanvas)
            self.refreshScreen()
            print(self.groupBox[value[0]].children())
            self.plot_active = True

        elif value[1] == '2dLayer':
            #create canvas
            self.groupBoxLayer = Canvas3D()
            self.groupBox[value[0]].children()[0].addWidget(self.groupBoxLayer)
            self.refreshScreen()
            print(self.groupBox[value[0]].children())
            self.layer_plot_active = True

    def createNewSubWindow(self):
        '''Helper function creates layout and button for widget selection'''
        self.button.append(QPushButton("Add Widget", self))
        self.button[-1].setFixedSize(150, 50)

        self.groupBox.append(QGroupBox("Window " + str(len(self.groupBox)), self))

        layout = (QGridLayout())
        self.groupBox[-1].setLayout(layout)
        layout.addWidget(self.button[-1])

    def makeGrid(self):
        '''Initialize all subwindows'''
        self.createNewSubWindow()
        self.gridLayout.addWidget(self.groupBox[-1], 0, 0)
        self.createNewSubWindow()
        self.gridLayout.addWidget(self.groupBox[-1], 0, 1)
        self.createNewSubWindow()
        self.gridLayout.addWidget(self.groupBox[-1], 1, 0)
        self.createNewSubWindow()
        self.gridLayout.addWidget(self.groupBox[-1], 1, 1)

    def make1WindowGrid(self):
        '''Splits window in 1 pane.'''
        self.gridSize = 1
        self.groupBox[-1].hide()
        self.groupBox[-2].hide()
        self.groupBox[-3].hide()

        self.gridSize = 1
        #self.refreshScreen()

    def make2WindowsGrid(self):
        '''Splits window in 2 panes.'''
        self.gridSize = 2
        self.groupBox[-1].hide()
        self.groupBox[-2].hide()
        self.groupBox[-3].show()

        self.gridSize = 2
        #self.refreshScreen()

    def make4WindowsGrid(self):
        '''Splits window in 4 panes.'''
        self.gridSize = 4
        self.groupBox[-1].show()
        self.groupBox[-2].show()
        self.groupBox[-3].show()

        self.gridSize = 4
        #self.refreshScreen()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
