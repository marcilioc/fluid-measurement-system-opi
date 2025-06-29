import sys
from PyQt5 import QtWidgets

# Import the main window class from your gui module
from gui.main_window import ScaleMonitorWindow

def main():
    """
    Main function to run the PyQt application.
    """
    app = QtWidgets.QApplication(sys.argv)
    window = ScaleMonitorWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
