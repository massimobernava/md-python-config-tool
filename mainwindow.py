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

import serial
import time
import thread
import struct
import sys
import rtmidi_python as rtmidi
import serial.tools.list_ports
from PyQt4 import uic
from PyQt4 import QtGui
from PyQt4.QtCore import QObject, pyqtSignal
from ctypes import *

try:
        import fluidsynth
        fluidsynth_available = True
except ImportError:
	fluidsynth_available = False
	
( Ui_MainWindow, QMainWindow ) = uic.loadUiType( 'microdrum.ui' )

midi_out = rtmidi.MidiOut()

#serialSpeed=31250
serialSpeed=115200

if fluidsynth_available:
        fs = fluidsynth.Synth()
        fs.start()

        sfid = fs.sfload("example.sf2")
        fs.program_select(0, sfid, 0, 0)


class PIN(Structure):
	_fields_ = [("name", c_char*20),("type", c_int),("note", c_int),("thresold", c_int),("scantime", c_int),("masktime", c_int),("retrigger", c_int),\
                    ("gain", c_int),("curve", c_int),("curveform", c_int),("xtalk", c_int),("xtalkgroup", c_int),("channel", c_int)]

pinArray=PIN*48
noteArray="C","C#","D","D#","E","F","F#","G","G#","A","A#","B"

Permutation = [ 0x72, 0x32, 0x25, 0x64, 0x64, 0x4f, 0x1e, 0x26, 0x2a, 0x74, 0x37, 0x09, 0x57, 0x02, 0x28,\
                0x08, 0x14, 0x23, 0x49, 0x10, 0x62, 0x02, 0x1e, 0x7e, 0x5d, 0x1b, 0x27, 0x76, 0x7a, 0x76, 0x05, 0x2e ]


class MainWindow ( QMainWindow ):
	"""MainWindow inherits QMainWindow"""
	ser=serial.Serial()
	
	pins=pinArray()
	pinType=dict()

        pbPinArray=[]

	updateMonitor = pyqtSignal(int,int,int)
	
	def __init__ ( self, parent = None ):
		QMainWindow.__init__( self, parent )
		self.ui = Ui_MainWindow()
		self.ui.setupUi( self )
        
		self.pinType[0]="Piezo"
		self.pinType[1]="Switch"
		self.pinType[2]="HHC"
		self.pinType[127]="Disabled"

                self.pbPinArray=self.ui.pbPin0,self.ui.pbPin1,self.ui.pbPin2,self.ui.pbPin3,self.ui.pbPin4,self.ui.pbPin5,self.ui.pbPin6,self.ui.pbPin7,\
                self.ui.pbPin0_2,self.ui.pbPin1_2,self.ui.pbPin2_2,self.ui.pbPin3_2,self.ui.pbPin4_2,self.ui.pbPin5_2,self.ui.pbPin6_2,self.ui.pbPin7_2,\
                self.ui.pbPin0_3,self.ui.pbPin1_3,self.ui.pbPin2_3,self.ui.pbPin3_3,self.ui.pbPin4_3,self.ui.pbPin5_3,self.ui.pbPin6_3,self.ui.pbPin7_3,\
                self.ui.pbPin0_4,self.ui.pbPin1_4,self.ui.pbPin2_4,self.ui.pbPin3_4,self.ui.pbPin4_4,self.ui.pbPin5_4,self.ui.pbPin6_4,self.ui.pbPin7_4,\
                self.ui.pbPin0_5,self.ui.pbPin1_5,self.ui.pbPin2_5,self.ui.pbPin3_5,self.ui.pbPin4_5,self.ui.pbPin5_5,self.ui.pbPin6_5,self.ui.pbPin7_5,\
                self.ui.pbPin0_6,self.ui.pbPin1_6,self.ui.pbPin2_6,self.ui.pbPin3_6,self.ui.pbPin4_6,self.ui.pbPin5_6,self.ui.pbPin6_6,self.ui.pbPin7_6
        #Pin
		try:
			f = open("pins.ini", "r")
			try:
				i=0
				for line in f:
					data=line.rstrip().split(';')
					self.pins[i].name=data[0]
					self.pins[i].type=int(data[1])
					self.pins[i].note=int(data[2])
					self.pins[i].thresold=int(data[3])
					self.pins[i].scantime=int(data[4])
					self.pins[i].masktime=int(data[5])
					self.pins[i].retrigger=int(data[6])
					self.pins[i].gain=int(data[7])
					self.pins[i].curve=int(data[8])
					self.pins[i].curveform=int(data[9])
					self.pins[i].xtalk=int(data[10])
					self.pins[i].xtalkgroup=int(data[11])
					self.pins[i].channel=int(data[12])
					i=i+1
			finally:
				f.close()
		except IOError:
			pass
	
		self.updateList()
        
		for note in range(100):
			self.ui.cbNote.addItem(self.getNoteString(note))

                self.updateMonitor.connect(self.handle_updateMonitor)
                
		#MIDI OUT
		for port_name in midi_out.ports:
			self.ui.cbMIDI.addItem(port_name)

                #Serial
		serialports=serial.tools.list_ports.comports()#self.availableSerialPort()
		for port in serialports:
			self.ui.cbSerial.addItem(port[0])

		self.ui.tPinList.setCurrentCell(0,0)
                            
		
	def __del__ ( self ):
		self.ui = None
		if self.ser.isOpen():
			self.ser.close()
		if fluidsynth_available:	
                        fs.delete()
		

	def closeEvent(self, event):
		f = open("pins.ini", "w")
		try:
			for pin in self.pins:
				f.write(pin.name+';'+str(pin.type)+';'+str(pin.note)+';'+str(pin.thresold)+';'+str(pin.scantime)+';'+str(pin.masktime)+';'+str(pin.retrigger)+';'+str(pin.gain)+';'+str(pin.curve)+';'+str(pin.curveform)+';'+str(pin.xtalk)+';'+str(pin.xtalkgroup)+';'+str(pin.channel)+'\n')
		finally:
			f.close()
			
	#------------------------------------------------------------------------------
	# UTILITY
	#------------------------------------------------------------------------------

				
	def enableSerial(self,bool):
		if bool:
                        thread.start_new_thread( self.read_midi, ("MIDI_Thread", 2, ) )
			port=str(self.ui.cbSerial.currentText())
			#print(port)
			self.ser = serial.Serial(port, serialSpeed, 8, "N", 1, timeout=None)

		elif self.ser.isOpen():
			self.ser.close()
			
	def getNoteString(self,note):
		return noteArray[note%12]+str((note/12)-2)+' ('+str(note)+')';

        def handle_updateMonitor(self,data1,data2,data3):
                for i in range(0,len(self.pbPinArray)):
                        if self.pins[i].note==data2:
                                self.pbPinArray[i].setFormat("    "+self.pins[i].name+" %v    ")
                                self.pbPinArray[i].setValue(data3)
                
                if (data1&0xF0)==0x90:
                    self.ui.lMIDIHistory.addItem("NOTE ON ("+str(data2)+","+str(data3)+")")
                elif (data1&0xF0)==0xB0:
                    self.ui.lMIDIHistory.addItem("CC ("+str(data2)+","+str(data3)+")")
                if self.ui.lMIDIHistory.count() > 20:
                        self.ui.lMIDIHistory.takeItem(0)
                self.ui.lMIDIHistory.setCurrentRow(self.ui.lMIDIHistory.count()-1)
                        
        
	def updateList(self):
		i=0
		for pin in self.pins:
			self.ui.tPinList.setItem(i,0,QtGui.QTableWidgetItem(pin.name))
			self.ui.tPinList.setItem(i,1,QtGui.QTableWidgetItem(self.pinType[pin.type]))
			self.ui.tPinList.setItem(i,2,QtGui.QTableWidgetItem(self.getNoteString(pin.note)))
			self.ui.tPinList.setItem(i,3,QtGui.QTableWidgetItem(str(pin.thresold)))
			self.ui.tPinList.setItem(i,4,QtGui.QTableWidgetItem(str(pin.scantime)))
			self.ui.tPinList.setItem(i,5,QtGui.QTableWidgetItem(str(pin.masktime)))
			i=i+1
			
	def getPearsonHash(self,input):
                h=0
                for i in input:
                        index=i ^ h
                        h=Permutation[index % len(Permutation)]
                return h;

        def reloadMIDI(self):
                self.ui.cbMIDI.clear()
                for port_name in midi_out.ports:
			self.ui.cbMIDI.addItem(port_name)
			
	#------------------------------------------------------------------------------
	# CONTROLS
	#------------------------------------------------------------------------------
	def selectPin(self):
		#print(self.pins[self.ui.tPinList.currentRow()].name)
		self.ui.lName.setText(self.pins[self.ui.tPinList.currentRow()].name)

		if self.pins[self.ui.tPinList.currentRow()].type==127:
			self.ui.cbType.setCurrentIndex(3)
		else:
			self.ui.cbType.setCurrentIndex(self.pins[self.ui.tPinList.currentRow()].type)

		self.ui.cbNote.setCurrentIndex(self.pins[self.ui.tPinList.currentRow()].note)

		self.ui.hsThresold.setValue(self.pins[self.ui.tPinList.currentRow()].thresold)
                self.ui.lThresold.setText(str(self.pins[self.ui.tPinList.currentRow()].thresold))

		self.ui.hsScantime.setValue(self.pins[self.ui.tPinList.currentRow()].scantime)
                self.ui.lScantime.setText(str(self.pins[self.ui.tPinList.currentRow()].scantime))

                self.ui.hsMasktime.setValue(self.pins[self.ui.tPinList.currentRow()].masktime)
                self.ui.lMasktime.setText(str(self.pins[self.ui.tPinList.currentRow()].masktime))

                self.ui.hsRetrigger.setValue(self.pins[self.ui.tPinList.currentRow()].retrigger)
                self.ui.lRetrigger.setText(str(self.pins[self.ui.tPinList.currentRow()].retrigger))

                self.ui.cbCurve.setCurrentIndex(self.pins[self.ui.tPinList.currentRow()].curve)

                self.ui.hsCurveform.setValue(self.pins[self.ui.tPinList.currentRow()].curveform)
                self.ui.lCurveform.setText(str(self.pins[self.ui.tPinList.currentRow()].curveform))

                self.ui.hsXtalk.setValue(self.pins[self.ui.tPinList.currentRow()].xtalk)
                self.ui.lXtalk.setText(str(self.pins[self.ui.tPinList.currentRow()].xtalk))

                self.ui.hsGain.setValue(self.pins[self.ui.tPinList.currentRow()].gain)
                self.ui.lGain.setText(str(self.pins[self.ui.tPinList.currentRow()].gain))

                self.ui.spXtalkgroup.setValue(self.pins[self.ui.tPinList.currentRow()].xtalkgroup)
                
                self.ui.spChannel.setValue(self.pins[self.ui.tPinList.currentRow()].channel)
                
	def editedName(self):
		self.pins[self.ui.tPinList.currentRow()].name=str(self.ui.lName.text())
		self.updateList()
		
	def editedType(self,int):
		if int==3:
			self.pins[self.ui.tPinList.currentRow()].type=127
		else:
			self.pins[self.ui.tPinList.currentRow()].type=int
		self.updateList()

	def editedThresold(self,int):
		self.pins[self.ui.tPinList.currentRow()].thresold=int
		self.ui.lThresold.setText(str(int))
		self.updateList()

	def editedScantime(self,int):
		self.pins[self.ui.tPinList.currentRow()].scantime=int
		self.ui.lScantime.setText(str(int))
		self.updateList()

	def editedMasktime(self,int):
		self.pins[self.ui.tPinList.currentRow()].masktime=int
		self.ui.lMasktime.setText(str(int))
		self.updateList()

	def editedRetrigger(self,int):
		self.pins[self.ui.tPinList.currentRow()].retrigger=int
		self.ui.lRetrigger.setText(str(int))
		#self.updateList()
		
	def editedNote(self,int):
		self.pins[self.ui.tPinList.currentRow()].note=int
		self.updateList()

	def editedCurve(self,int):
		self.pins[self.ui.tPinList.currentRow()].curve=int
		#self.updateList()

	def editedCurveform(self,int):
		self.pins[self.ui.tPinList.currentRow()].curveform=int
		self.ui.lCurveform.setText(str(int))
		#self.updateList()

	def editedXtalk(self,int):
		self.pins[self.ui.tPinList.currentRow()].xtalk=int
		self.ui.lXtalk.setText(str(int))
		#self.updateList()

	def editedXtalkgroup(self,int):
		self.pins[self.ui.tPinList.currentRow()].xtalkgroup=int
		#self.updateList()

	def editedChannel(self,int):
		self.pins[self.ui.tPinList.currentRow()].channel=int
		#self.updateList()

	def editedGain(self,int):
		self.pins[self.ui.tPinList.currentRow()].gain=int
		self.ui.lGain.setText(str(int))
		#self.updateList()
		
	def uploadAll(self):
		data = 0xF0,0x77,0x02,self.ui.tPinList.currentRow(),0x7F,0x00,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)
			
	def downloadAll(self):
                self.downloadType()
                time.sleep(1)
                self.downloadNote()
                time.sleep(1)
                
	def uploadType(self):
		data = 0xF0,0x77,0x02,self.ui.tPinList.currentRow(),0x0D,0x00,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)
			
	def downloadType(self):
                code=0x03
                if self.ui.ckSave.isChecked()==True :
                        code=0x04
		data = 0xF0,0x77,code,self.ui.tPinList.currentRow(),0x0D,self.pins[self.ui.tPinList.currentRow()].type,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)

	def uploadNote(self):
		data = 0xF0,0x77,0x02,self.ui.tPinList.currentRow(),0x00,0x00,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)
			
        def uploadCurve(self):
                data = 0xF0,0x77,0x02,self.ui.tPinList.currentRow(),0x05,0x00,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)

        def uploadCurveform(self):
                data = 0xF0,0x77,0x02,self.ui.tPinList.currentRow(),0x08,0x00,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)

        def uploadXtalk(self):
                data = 0xF0,0x77,0x02,self.ui.tPinList.currentRow(),0x06,0x00,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)

        def uploadXtalkgroup(self):
                data = 0xF0,0x77,0x02,self.ui.tPinList.currentRow(),0x07,0x00,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)

        def uploadChannel(self):
                data = 0xF0,0x77,0x02,self.ui.tPinList.currentRow(),0x0E,0x00,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)

        def uploadGain(self):
                data = 0xF0,0x77,0x02,self.ui.tPinList.currentRow(),0x09,0x00,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)

 			
        def downloadCurve(self):
                code=0x03
                if self.ui.ckSave.isChecked()==True :
                        code=0x04
                data = 0xF0,0x77,code,self.ui.tPinList.currentRow(),0x05,self.pins[self.ui.tPinList.currentRow()].curve,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)

        def downloadCurveform(self):
                code=0x03
                if self.ui.ckSave.isChecked()==True :
                        code=0x04
                data = 0xF0,0x77,code,self.ui.tPinList.currentRow(),0x08,self.pins[self.ui.tPinList.currentRow()].curveform,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)

        def downloadXtalk(self):
                code=0x03
                if self.ui.ckSave.isChecked()==True :
                        code=0x04
                data = 0xF0,0x77,code,self.ui.tPinList.currentRow(),0x06,self.pins[self.ui.tPinList.currentRow()].xtalk,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)

        def downloadXtalkgroup(self):
                code=0x03
                if self.ui.ckSave.isChecked()==True :
                        code=0x04
                data = 0xF0,0x77,code,self.ui.tPinList.currentRow(),0x07,self.pins[self.ui.tPinList.currentRow()].xtalkgroup,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)

        def downloadChannel(self):
                code=0x03
                if self.ui.ckSave.isChecked()==True :
                        code=0x04
                data = 0xF0,0x77,code,self.ui.tPinList.currentRow(),0x0E,self.pins[self.ui.tPinList.currentRow()].channel,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)

        def downloadGain(self):
                code=0x03
                if self.ui.ckSave.isChecked()==True :
                        code=0x04
                data = 0xF0,0x77,code,self.ui.tPinList.currentRow(),0x09,self.pins[self.ui.tPinList.currentRow()].gain,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)
        
	def downloadNote(self):
                code=0x03
                if self.ui.ckSave.isChecked()==True :
                        code=0x04
		data = 0xF0,0x77,code,self.ui.tPinList.currentRow(),0x00,self.pins[self.ui.tPinList.currentRow()].note,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)

	def uploadThresold(self):
		data = 0xF0,0x77,0x02,self.ui.tPinList.currentRow(),0x01,0x00,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)

	def downloadThresold(self):
                code=0x03
                if self.ui.ckSave.isChecked()==True :
                        code=0x04
		data = 0xF0,0x77,code,self.ui.tPinList.currentRow(),0x01,self.pins[self.ui.tPinList.currentRow()].thresold,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)

        def uploadScantime(self):
                data = 0xF0,0x77,0x02,self.ui.tPinList.currentRow(),0x02,0x00,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)
			
        def downloadScantime(self):
                code=0x03
                if self.ui.ckSave.isChecked()==True :
                        code=0x04
                data = 0xF0,0x77,code,self.ui.tPinList.currentRow(),0x02,self.pins[self.ui.tPinList.currentRow()].scantime,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)

        def uploadMasktime(self):
                data = 0xF0,0x77,0x02,self.ui.tPinList.currentRow(),0x03,0x00,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)
			
        def downloadMasktime(self):
                code=0x03
                if self.ui.ckSave.isChecked()==True :
                        code=0x04
                data = 0xF0,0x77,code,self.ui.tPinList.currentRow(),0x03,self.pins[self.ui.tPinList.currentRow()].masktime,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)

        def uploadRetrigger(self):
                data = 0xF0,0x77,0x02,self.ui.tPinList.currentRow(),0x04,0x00,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)
			
        def downloadRetrigger(self):
                code=0x03
                if self.ui.ckSave.isChecked()==True :
                        code=0x04
                data = 0xF0,0x77,code,self.ui.tPinList.currentRow(),0x04,self.pins[self.ui.tPinList.currentRow()].retrigger,0xF7
		print(data)
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)
        
	def changeMode(self,int):
		if int==0:
			data = 0xF0,0x77,0x01,0x01,0x00,0x00,0xF7
			print("SETUP")
		elif int==1:
			data = 0xF0,0x77,0x01,0x03,0x00,0x00,0xF7
			print("LOG")
		else:
			data = 0xF0,0x77,0x01,0x02,0x00,0x00,0xF7
			print("MIDI")
		
		txData = struct.pack("B"*len(data), *data)
		if self.ser.isOpen():
			self.ser.write(txData)
	
	def selectMIDI(self,port):
                if port>=0:
                        midi_out.close_port()
                        midi_out.open_port(port)
	
	#------------------------------------------------------------------------------
	# MIDI
	#------------------------------------------------------------------------------
	def read_midi(self, threadName, delay):
		while 1:
			if self.ser.isOpen():
				rxData = self.ser.read(1)
				if len(rxData) <= 0:
                                        return
				cmd=rxData[0]
				if cmd==chr(0xF0):
					rxData = self.ser.read(6)
					data = struct.unpack("B"*len(rxData), rxData)
					if data[1]==0x02: #ASKPARAM
						if data[3]==0x0D: #TYPE
							self.pins[data[2]].type=data[4]
						if data[3]==0x00: #NOTE
							self.pins[data[2]].note=data[4]
						if data[3]==0x01: #THRESOLD
							self.pins[data[2]].thresold=data[4]
						if data[3]==0x02: #SCANTIME
							self.pins[data[2]].scantime=data[4]
						if data[3]==0x03: #MASKTIME
							self.pins[data[2]].masktime=data[4]
						if data[3]==0x04: #RETRIGGER
							self.pins[data[2]].retrigger=data[4]
						if data[3]==0x05: #CURVE
							self.pins[data[2]].curve=data[4]
						if data[3]==0x06: #XTALK
							self.pins[data[2]].xtalk=data[4]
						if data[3]==0x07: #XTALKGROUP
							self.pins[data[2]].xtalkgroup=data[4]
						if data[3]==0x08: #CURVEFORM
							self.pins[data[2]].curveform=data[4]
						if data[3]==0x09: #GAIN
							self.pins[data[2]].gain=data[4]
						if data[3]==0x0E: #CHANNEL
							self.pins[data[2]].channel=data[4]
							
						self.updateList()
						self.selectPin()
                                        if data[1]==0x60:#License
                                                dataSend = 0xF0,0x77,0x60,data[2],data[3],self.getPearsonHash(data[2:4]),0xF7
                                                #print(dataSend)
                                                txData = struct.pack("B"*len(dataSend), *dataSend)
                                                if self.ser.isOpen():
                                                        self.ser.write(txData)
				else:
					rxData = self.ser.read(2)
					note = ord(rxData[0])
					vel = ord(rxData[1])
					if self.ui.rbMIDI.isChecked():
						midi_out.send_message([ord(cmd), note, vel]) # Note on
					elif fluidsynth_available & self.ui.rbFluidsynth.isChecked():
						fs.noteon(0, 60, 30)
					self.updateMonitor.emit(cmd,note,vel)

				#print(data)
				#sys.stdout.flush()
			else:
				time.sleep(delay)

