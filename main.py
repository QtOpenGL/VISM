import sys

from PyQt5.QtCore import QTimer, QPoint, pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog
from PyQt5.QtWidgets import (QHBoxLayout, QOpenGLWidget, QSlider,
                             QWidget)
from Windows.MainWindowTemplate import Ui_MainWindow

#from mainWindow import GLWidget, Helper
from Canvas import Canvas
from Parser import Parser
from Windows.animationSettings import AnimationSettings
from spin_gl import GLWidget

class MainWindow(QMainWindow, Ui_MainWindow, QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.openGLWidget = GLWidget()
        '''IT IS CRUCIAL TO COMMENT OUT IN MainWindowTemplate.py THIS LINE:
        self.openGLWidget = QtWidgets.QOpenGLWidget(self.verticalLayoutWidget)
        IT IS AUTOGENERATED AND IT WON'T WORK WITHOUT DELETING IT! I WILL DELETE THIS COMMENT AS SOON AS I WILL BE ABLE TO FIX THAT IN GUI GENERATOR. FOR NOW EVERY TIME YOU RECOMPILE GUI IT HAS TO BE COMMENTED.'''

        self.setupUi(self) #setting up UI from MainWindowTemplate.py File (generated by gui generator)

        self.setWindowTitle("ESE - Early Spins Enviroment")
        self.setGeometry(10,10,1280, 768) #size of window
        self.gridSize = 1 #grid is to keep to how many pieces split workspace availiable: (1,2,4)

        self.make1WindowGrid()
        self.events()

    def tests(self):
        pass

    def events(self):
        '''creates listeners for all menu buttons'''
        #FILE SUBMENU
        #self.actionLoad_File.clicked.connect()
        self.actionLoad_Directory.triggered.connect(self.loadDirectory)

        #EDIT SUBMENU
        #self.actionPlot.clicked.connect()
        self.actionAnimation.triggered.connect(self.showAnimationSettings)

        #VIEW SUBMENU
        self.action1_Window_Grid.triggered.connect(self.make1WindowGrid)
        self.action2_Windows_Grid.triggered.connect(self.make2WindowsGrid)
        self.action4_Windows_Grid.triggered.connect(self.make4WindowsGrid)

    def resizeEvent(self, event):
        '''What happens when window is resized'''
        self.verticalLayoutWidget.setGeometry(0, 0, self.width(), self.height()-5)
        self.verticalLayoutWidget.setGeometry(0,0,self.width(), self.height())
        #self.progressBar.setGeometry(5, (self.height()-35), (self.width()-10), self.height()-25)
        #self.statusBar_label.setGeometry(5, self.height()-45, self.width()-10, self.height()-35)

        if self.gridSize == 1:
            self.make1WindowGrid()
        elif self.gridSize == 2:
            self.make2WindowsGrid()
        elif self.gridSize == 4:
            self.make4WindowsGrid()

    def loadDirectory(self):
        '''Loads whole directory based on Parse class as simple as BHP'''
        #directory = str(QFileDialog.getExistingDirectory(self, "Select Directory"))



        directory = "/Users/pawelkulig/Desktop/spintronics-visual/data/firstData"

        if directory == None or directory == "":
            return 0
        #Parser.set_event_handler()


        #Parser.show_progress_window()

        #_, _, self.odt_data =  Parser.readFolder(directory)
        self.odt_data = Parser.getOdtData("data/firstData/voltage-spin-diode.odt")
        picked_column = 'MR::Energy'

        if self.gridSize > 1:

            data_dict = {
                        'i': 0,
                        'iterations': self.odt_data[1],
                        'graph_data': self.odt_data[0][picked_column].tolist(),
                        'title' : picked_column
                        }

            self.canvasPlot1.shareData(**data_dict)
            self.canvasPlot1.createPlotCanvas()
            self.canvasPlot1.runCanvas()




    def showAnimationSettings(self):
        '''Shows window to change animations settings'''
        self.animationSettingsWindow = AnimationSettings()

    def showPlotSettings(self):
        pass

    def make1WindowGrid(self):
        '''Splits windows into 1 window :P just to show only OpenGLWidget and hide all plots.'''
        self.gridSize = 1
        try:
            self.canvasPlot1.hide()
        except:
            pass

        try:
            self.canvasPlot2.hide()
        except:
            pass

        try:
            self.canvasPlot3.hide()
        except:
            pass

        self.openGLWidget.setGeometry(0, 0, self.width(), self.height())

    def make2WindowsGrid(self):
        '''Splits window in 2 panes one is OpenGLWidget and second one is Plot'''
        self.gridSize = 2
        middlePos = (self.width())/2
        self.openGLWidget.setGeometry(0,0, middlePos-5, self.height())

        #create matplotlib window
        try:
            self.canvasPlot1.show()
        except:
            self.canvasPlot1 = Canvas(self)
        self.canvasPlot1.setGeometry(middlePos+5, 0, self.width()/2-5, self.height())
        #self.canvasPlot1.resize((, self.height()-25)
        self.canvasPlot1.show()

        try:
            self.canvasPlot2.hide()
            self.canvasPlot3.hide()
        except:
            pass

    def make4WindowsGrid(self):
        '''Splits window in 4 panes one openGLWidget and 3 Plots'''
        self.gridSize = 4
        middleWidthPos = (self.width())/2
        middleHeightPos = (self.height())/2

        self.openGLWidget.setGeometry(0, 0, middleWidthPos - 5, middleHeightPos - 5)

        #create matplotlib window right top corner
        try:
            self.canvasPlot1.show()
        except:
            self.canvasPlot1 = Canvas(self)
        self.canvasPlot1.setGeometry(middleWidthPos + 5, 0, (self.width()/2 - 5), (self.height()/2)-5)
        self.canvasPlot1.show()

        #create matplotlib window left bottom corner
        try:
            self.canvasPlot2.show()
        except:
            self.canvasPlot2 = Canvas(self)
        self.canvasPlot2.setGeometry(0, middleHeightPos + 5, (self.width()/2-5), (self.height()/2)-50)
        self.canvasPlot2.show()

        #create matplotlib window left bottom corner
        try:
            self.canvasPlot3.show()
        except:
            self.canvasPlot3 = Canvas(self)
        self.canvasPlot3.setGeometry(middleWidthPos + 5, middleHeightPos + 5, (self.width()/2-5), (self.height()/2)-50)
        self.canvasPlot3.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())