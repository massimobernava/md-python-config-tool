#============================================================
#=>             pyMicroDrum v0.1
#=>             www.microdrum.net
#=>              CC BY-NC-SA 3.0
#=>
#=> Massimo Bernava
#=> massimo.bernava@gmail.com
#=> 2012-06-09
#=>                                                      
#=> RtMidi wrapper: https://github.com/superquadratic/rtmidi-python
#=============================================================

import sys
import rtmidi_python as rtmidi
import os
import time

midi_out = rtmidi.MidiOut()
midi_in = rtmidi.MidiIn()
global_string=""
Permutation = [ 0x72, 0x32, 0x25, 0x64, 0x64, 0x4f, 0x1e, 0x26, 0x2a, 0x74, 0x37, 0x09, 0x57, 0x02, 0x28, 0x08, 0x14, 0x23, 0x49, 0x10, 0x62, 0x02, 0x1e, 0x7e, 0x5d, 0x1b, 0x27, 0x76, 0x7a, 0x76, 0x05, 0x2e ]
save_mode=False

def cls():
    os.system(['clear','cls'][os.name == 'nt'])
	
def callback(message, time_stamp):
	if message[0]==0xf0 and message[1]==0x77:
		#Vari tipi di sysex
		if message[2]==0x60:#License
			message[5]=getPearsonHash(message[3:4])
			midi_out.send_message(message) 
		elif message[2]==0x02:#AskParam
			global global_string
			if message[4]==0x00:#Note
				global_string="   Note(%d)=%d"%(message[3],message[5])
			if message[4]==0x01:#Thresold
				global_string="   Thresold(%d)=%d"%(message[3],message[5])
			if message[4]==0x02:#ScanTime/SwitchTime
				global_string="   ScanTime/SwitchTime(%d)=%d"%(message[3],message[5])
			if message[4]==0x03:#MaskTime/ChokeTime
				global_string="   MaskTime/ChokeTime(%d)=%d"%(message[3],message[5])
			if message[4]==0x04:#Retrigger
				global_string="   Retrigger(%d)=%d"%(message[3],message[5])
			if message[4]==0x05:#Curve
				global_string="   Curve(%d)=%d"%(message[3],message[5])
			if message[4]==0x06:#XTalk
				global_string="   XTalk(%d)=%d"%(message[3],message[5])	
			if message[4]==0x07:#XTalkGroup
				global_string="   XTalkGroup(%d)=%d"%(message[3],message[5])
			if message[4]==0x08:#CurveForm
				global_string="   CurveForm(%d)=%d"%(message[3],message[5])
			if message[4]==0x09:#ChokeNote
				global_string="   ChokeNote(%d)=%d"%(message[3],message[5])
			if message[4]==0x0A:#Dual
				global_string="   Dual(%d)=%d"%(message[3],message[5])
			if message[4]==0x0B:#DualNote
				global_string="   DualNote(%d)=%d"%(message[3],message[5])	
			if message[4]==0x0C:#DualThresold
				global_string="   DualThresold(%d)=%d"%(message[3],message[5])	
			if message[4]==0x0D:#Type
				global_string="   Type(%d)=%d"%(message[3],message[5])
			if message[4]==0x0E:#Channel
				global_string="   Channel(%d)=%d"%(message[3],message[5])	
	elif (message[0] & 0xf0)==0x90:#NoteOn
		global_string="   NoteOn(%d,%d)"%(message[1],message[2])
	elif (message[0] & 0xf0)==0xb0:#CC
		global_string="   CC(%d,%d)"%(message[1],message[2])
	else:
		print message

def getPearsonHash(input):
	h=0
	for i in input:
		index=i ^ h
		h=Permutation[index % len(Permutation)]
	return h;

def printheader():
	print "======================="
	print "=  pyMICRODRUM  v0.1  ="
	print "=   Massimo Bernava   ="
	print "======================="

def printParam():
	print "  0 - Note"
	print "  1 - Thresold"
	print "  2 - ScanTime"
	print "  3 - MaskTime"
	print "  4 - Retrigger"
	print "  5 - Curve"
	print "  6 - XTalk"
	print "  7 - XTalkGroup"
	print "  8 - CurveForm"
	print "  9 - ChokeNote"
	print " 10 - Dual"
	print " 11 - DualNote"
	print " 12 - DualThresold"
	print " 13 - Type"
	print " 14 - Channel"

def printGeneral():
	print "  0 - Delay"
	print "  1 - Version"
	print "  2 - NSensor"
	print "  3 - XTalk"
	
def printValue(param):
	if param=="13":#Type
		print "  0 - Piezo"
		print "  1 - Switch"
		print "  2 - HHC"
		print "  3 - HH"
		print "  4 - Hhs"
		print "  5 - YSwitch"
		print " 127 - Disable"
		
def main(*args):
    try:
		cls()
		printheader()
		
		i=0
		#MIDI IN
		print "MIDI IN:"
		for port_name in midi_in.ports:
			print i,"-",port_name
			i=i+1

		n_midi_in = raw_input("Select: ")
		midi_in.callback = callback
		midi_in.open_port(int(n_midi_in))		
		midi_in.ignore_types(False,True,True)
		
		i=0
		#MIDI OUT
		print "MIDI OUT:"
		for port_name in midi_out.ports:
			print i,"-",port_name
			i=i+1
		
		n_midi_out = raw_input("Select: ")
		midi_out.open_port(int(n_midi_out))
		
		#State OFF
		midi_out.send_message([0xF0, 0x77, 01, 00, 00, 00, 0xF7]) 
		
		#MENU
		sel=0
		mode=0 #off
		while sel!="e":
			cls()
			printheader()
			print "1 - Change Mode"
			if mode=="1":
				print "2 - Set Param"
				print "3 - Get Param"
				print "4 - Set General"
				print "5 - Get General"
				#print "6 - Set HH"
				#print "7 - Get HH"
				print "d - Disable Pins"
				if save_mode==False:
					print "s - Save Mode: OFF"
				else:
					print "s - Save Mode: ON"

			elif mode=="2":
				print "---"
			elif mode=="3":
				print "---"
				
			print "e - Exit"
			while global_string!="":
				print global_string
				global global_string
				global_string=""
				
			sel=raw_input("Select: ")
			
			if sel=="1":
				print "1 - SetupMode"
				print "2 - ToolMode"
				print "3 - MonitorMode"
				mode=raw_input("Select: ")
				#Send Midi
				if mode=="1":
					midi_out.send_message([0xF0, 0x77, 01, 01, 00, 00, 0xF7]) 
				if mode=="2":
					midi_out.send_message([0xF0, 0x77, 01, 03, 00, 00, 0xF7]) 
				if mode=="3":
					midi_out.send_message([0xF0, 0x77, 01, 02, 00, 00, 0xF7]) 
				
			#SETUP MODE=========================
			if mode=="1" and sel=="2":#Set Param
				pin=raw_input("Pin: ")
				printParam()
				param=raw_input("Param: ")
				printValue(param)
				value=raw_input("Value: ")
				#Send Midi
				if save_mode==True:
					Cmd=04
				else:
					Cmd=03
				midi_out.send_message([0xF0, 0x77, Cmd, int(pin), int(param), int(value), 0xF7])	
				
			if mode=="1" and sel=="3":#Get Param
				pin=raw_input("Pin: ")
				printParam()
				param=raw_input("Param: ")
				#Send Midi
				midi_out.send_message([0xF0, 0x77, 02, int(pin), int(param), 00, 0xF7])			
				time.sleep(1)
				
			if mode=="1" and sel=="4":#Set General
				printGeneral()
				param=raw_input("Param: ")
				value=raw_input("Value: ")
				#Send Midi
				if save_mode==True:
					Cmd=04
				else:
					Cmd=03
				midi_out.send_message([0xF0, 0x77, Cmd, 0x7E, int(param), int(value), 0xF7])	
				
			if mode=="1" and sel=="5":#Get General
				printGeneral()
				param=raw_input("Param: ")
				#Send Midi
				midi_out.send_message([0xF0, 0x77, 02, 0x7E, int(param), 00, 0xF7])			
				time.sleep(1)
				
			if mode=="1" and sel=="8": #Disable PIN	
				pin_from=raw_input("From:")
				pin_to=raw_input("To:")
				for pin in range(int(pin_from),int(pin_to)):
					midi_out.send_message([0xF0, 0x77, 03, int(pin), 0x0D, 127, 0xF7])
			
			if mode=="1" and sel=="s": #Save Mode
				global save_mode
				save_mode= not save_mode	
			#===================================
			
		return 0
    except:
		print "Errore:", sys.exc_info()[0]

		return 1
    else:
        return 0
 
if __name__ == '__main__':
    sys.exit(main(*sys.argv))