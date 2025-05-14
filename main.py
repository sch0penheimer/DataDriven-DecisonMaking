if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    import sys
    import gui
    
    app = QApplication(sys.argv)
    window = gui.MainWindow()
    window.setup_ui()
    window.show()
    sys.exit(app.exec_())
