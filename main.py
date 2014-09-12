#============================================================
#=>             pyMicroDrum v0.2.1
#=>             www.microdrum.net
#=>              CC BY-NC-SA 3.0
#=>
#=> Massimo Bernava
#=> massimo.bernava@gmail.com
#=> 2014-09-12
#=>                                                      
#=============================================================

import sys

# import PyQt4 QtCore and QtGui modules
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from mainwindow import MainWindow

if __name__ == '__main__':

    # create application
    app = QApplication( sys.argv )
    app.setApplicationName( 'microDrum' )

    # create widget
    w = MainWindow()
    w.setWindowTitle( 'microDrum' )
    w.show()

    # connection
    QObject.connect( app, SIGNAL( 'lastWindowClosed()' ), app, SLOT( 'quit()' ) )

    # execute application
    sys.exit( app.exec_() )
