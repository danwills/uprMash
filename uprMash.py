#!/usr/bin/env python

# !/cygdrive/c/dev/Python2.4.3/python.exe
# /usr/bin/python

# a little bit of python intended to be used to mash UltraFractal 'UPR' files to do such things as :
#
# generate any number of differently time-shifted layers for the animated layers found in the input UPR
# layer ramps with opacity levels overridden (to simulate a camera shutter(
# alternating layer merge-modes
#
# this script is not guaranteed to do anything!!
# ie it's not my problem if it breaks your stuff!! The uprs it creates can request a lot of computer resources!! beware!! ':D use at your own risk
#
# dan wills - for fractal fun, October 2006-2008 
# please let me know if you use this tool!!!
#    gdanzo#gmail.com
#
# done:
#	* auto generation of BG layer 
#		prob kinda went away because of allowing layers underneath the interp layers
#	* background-is-special flag.. either change it or not..
#		done (-g flag)
#	* mergemode alternation patterns 
#		done, multiple -m flags allows alternation
#	* opacity ramp in/out 
#		done with float ramp length parameter eg ( 0.0 - 1.0 ) to cover 0 to all of interp range
#	* set the new fractalname from the output filename
#	* minimal initial tkinter gui
#	* improved gui
#	* decode compressed UPR
#	* read one fractal from a file containing multiple
#	* animation mode - parse and regenerate time-shifted UF anim curves
#	* group support (UF5) - makes some interesting compositing possible
#	* copy to clipboard
#	* generate animation (sines to start with)
#	* detection and ignore of BG layers based on name containing the string 'background' (ignores case)
#
# todo/notes:
#	more modes involving complex interpolation around a circle in the complex plane
#	loops and spirals of smoothly noisey complex plane interpolation / traversal
#	randomization (with various kernels including disc) of specified parameters, ramping in/out of opacities
#	auto balancing of opacities so that changing number of layers doesn't change look too much
#	a gui, with copy-to-clipboard capability (button) and visualisation of the interpolations
#	animation mode? it does kinda suggest itself.. tho this is mainly a still image project so far
#	animation could be achieved by detecting and preserving the key-values
#	grad interpolation is broken.. seems that rotation of the grad actually reorders the keys - need special interpolator for that tag
#	float/int detection is not perfect.. some things can still break the resulting UPR (eg floats interpolated as ints, or floats where its illegal in the UPR)
#	clean up all the prints - debug level it
#	use sets to form a dictionary of key->value pairs, use the union of all keys in both layers to generate all interlayers
#	more complex interpolation types:
#		'orbit-matching' - use the complex co-ords for the two (or more) input layers as targets in a search thru an orbit space, then generate 'numlayers' iterations of it
#		'orbit generation' - use the existing point(s) as parameters to a fractal formula
#		'randomization' - distribute samples around the input
#    detecting and allowing multiple UPRs per file (read and write)
#    animation mode - work with animated UPRs - done
#    compressed UPR mode (read /and/ write) - done
#    standalone exe conversion - tested
#    GUI improvements - some done
#    solid implementation of frame selection parseing (aka da ritz stuff from cweb, eg no troubles here: -9--4,35-65@3,77,80,500-512, -15-12 )
#
# example input UPR name
# C:\Documents and Settings\dan\My Documents\Ultra Fractal 5\Parameters\ultraInter.upr

import os, sys, getopt, time, re, copy, binascii, zlib, types, operator, math
import tooltip
import wave, wavReader
from Tkinter import *

class uprMashWindow( Frame ):
	
	uprMashGlobals = None
	uprMashParse = None
	
	aboutButton = None
	outTextField = None
	browseUPRButton = None
	browseWAVButton = None
	
	#inFractalField = None
	
	fractalNameVar = None
	fractalNameOptionBox = None
	outFractalField = None
	fractalDict = { "untitled":0 }
	
	inFileField = None
	wavFileField = None
	
	#saveMashButton = None
	# saveAsUPRButton = None
	
	
	numLayersIntVar = None
	layerScale = None
	
	opacScaleFloatVar = None
	opacScale = None
	
	opacRampLengthFloatVar = None
	opacRampLengthScale = None
	
	fps = None
	frameRange = None
	
	interleaveCheckbox = None
	interleaveCheckboxVar = 0
	
	shutterLength = None
	shutterOffset = None
	
	layerModesField = None
	interpModeField = None
	
	resampleCurvesCheckbox = None
	resampleCurvesCheckboxVar = 0
	
	animModeCheckbox = None
	animModeCheckboxVar = 0
	
	useAudioCheckbox = None
	useAudioCheckboxVar = 0
	
	animFreq = None
	animAmp = None
	animPhase = None
	
	ignoreBGCheckbox = None
	ignoreBGCheckboxVar = 0
	
	verboseCheckbox = None
	verboseCheckboxVar = 0
	
	openUPRButton = None
	doMashButton = None
	copyToClipboardButton = None
	
	quitButton = None
	# frameOffset = None
	# outFileField = None
	
	windowYScroll = None
	
	textXScroll = None
	textYScroll = None
	
	# forceOverwriteCheckbox = None
	# forceOverwriteCheckboxVar = 0
	
	# iconButton = None
	
	def copySettingsFromGUI( self ) :
		
		# backToFwdSlashesAll -> localToFwdSlashesAll
		# fwdToBackSlashesAll -> fwdToLocalSlashesAll
		
		inFileNameStr = str( self.inFileField.get( "1.0", END) ).strip()
		self.uprMashGlobals.setInFileName( localToFwdSlashesAll( inFileNameStr ) )
		
		inWavFileNameStr = str( self.wavFileField.get( "1.0", END) ).strip()		
		self.uprMashGlobals.setWavFileName( localToFwdSlashesAll( inWavFileNameStr ) )
		
		inFractalName = str( self.fractalNameVar.get() )
		inFractalNumber = self.fractalDict[ inFractalName ]
		
		self.uprMashGlobals.setInFractalNumber( inFractalNumber )
		
		# outFileNameStr = str( self.outFileField.get( "1.0", END) ).strip()
		# self.uprMashGlobals.setOutFileName( outFileNameStr )
		
		outFractalName = str( self.outFractalField.get( "1.0", END) ).strip()
		self.uprMashGlobals.setOutFractalName( outFractalName )
		
		layerint = int( self.layerScale.get() )
		self.uprMashGlobals.numExtraLayers = layerint
		
		opacint = int( self.opacScale.get() )
		self.uprMashGlobals.newLayerOpacity = opacint
		
		animFreqFloat = float( self.animFreq.get( "1.0", END ) )
		self.uprMashGlobals.animFreq = animFreqFloat
		
		animAmpStr = self.animAmp.get( "1.0", END )
		self.uprMashGlobals.animAmp = animAmpStr
		
		animPhaseFloat = float( self.animPhase.get( "1.0", END ) )
		self.uprMashGlobals.animPhase = animPhaseFloat
		
		fpsInt = int( self.fps.get( "1.0", END ) )
		self.uprMashGlobals.fps = fpsInt
		
		shutterLengthFloat = float( self.shutterLength.get( "1.0", END ) )
		self.uprMashGlobals.shutterLength = shutterLengthFloat
		
		shutterOffsetFloat = float( self.shutterOffset.get( "1.0", END ) )
		self.uprMashGlobals.shutterOffset = shutterOffsetFloat
		
		interleave = self.interleaveCheckboxVar.get()
		if interleave : 
			self.uprMashGlobals.interleave = True
		else :
			self.uprMashGlobals.interleave = False
		
		modeExtractor = re.compile( "[a-z]+" )
		layerModes = self.layerModesField.get( "1.0", END ).strip()
		layerModesList = modeExtractor.findall( layerModes )
		
		imodeExtractor = re.compile( "[A-Z]+" )
		interpModes = self.interpModeField.get( "1.0", END ).strip()
		interpModesList = imodeExtractor.findall( interpModes )
		
		# print( "got interpmodesStr: " + str( interpModes ) )
		
		# print( "got layermodesList: " + str( layerModesList ) )
		
		for lm in range( len( layerModesList ) ) :
			layerModesList[ lm ] = layerModesList[ lm ].strip()
		
		for lm in range( len( interpModesList ) ) :
			interpModesList[ lm ] = interpModesList[ lm ].strip()
		
			
		#print( "got STRIPPED layermodesList: " + str( layerModesList ) )
		
		self.uprMashGlobals.newLayerMode = layerModesList
		self.uprMashGlobals.interpMode = interpModesList
		
		verb = self.verboseCheckboxVar.get()
		if verb : 
			self.uprMashGlobals.verboseMode = True
		else :
			self.uprMashGlobals.verboseMode = False
			
		igbg = self.ignoreBGCheckboxVar.get()
		if igbg : 
			self.uprMashGlobals.ignoreBG = True
		else :
			self.uprMashGlobals.ignoreBG = False
		
		resamp = self.resampleCurvesCheckboxVar.get()
		if resamp : 
			self.uprMashGlobals.resampleCurves = True
		else :
			self.uprMashGlobals.resampleCurves = False
		
		animode = self.animModeCheckboxVar.get()
		if animode : 
			self.uprMashGlobals.animMode = True
		else :
			self.uprMashGlobals.animMode = False
		
		useau = self.useAudioCheckboxVar.get()
		if useau : 
			self.uprMashGlobals.useAudio = True
		else :
			self.uprMashGlobals.useAudio = False
		
		
		# force = self.forceOverwriteCheckboxVar.get()
		# if force : 
		# 	self.uprMashGlobals.forceOverwrite = True
		# else :
		# 	self.uprMashGlobals.forceOverwrite = False
			
		opacrampfloat = float( self.opacRampLengthScale.get() )
		self.uprMashGlobals.opacityRampLength = opacrampfloat
		
		# shoul recognize 1-10x2 to do a key on every 2nd frame for example
		framerangestr = self.frameRange.get( "1.0", END )
		self.uprMashGlobals.frameRange = framerangestr
		
	
	def doMash( self ):
		#print "here goes! ..."
		#print( "key is: " + str( key ) )
		
		#clear output field
		self.outTextField.delete( "1.0", END )
		
		self.copySettingsFromGUI()
		
		self.uprMashParse = uprParse()
		
		self.uprMashParse.loadAndParseUPRText( self.uprMashGlobals )
		
		if self.uprMashParse.parsedOK :
			if self.uprMashGlobals.verboseMode : print("Opening any auxhilliary data now..")
			self.uprMashGlobals.loadAuxData()
			
			#select a fractal from the UPR
			self.uprMashParse.getFractal(-1).addExtraLayers( self.uprMashGlobals )
			self.uprMashParse.getFractal( -1).setFractalName( self.uprMashGlobals.outFractalName, self.uprMashGlobals )
			
			mashStr = self.uprMashParse.getFractal(-1).getAsString( self.uprMashGlobals )
			self.outTextField.insert( "1.0", mashStr )
			return mashStr
		else :
			print( "could not parse UPR text (check file name or contents)" )
	
	def mashAndSave( self ) :
		mashStr = self.doMash( )
		
		if self.uprMashGlobals.verboseMode : print("writing UPR (if possible)..")
		
		if not self.uprMashGlobals.outFileAlreadyExists or self.uprMashGlobals.forceOverwrite :
		
			openStub = open( self.uprMashGlobals.outFileName, "w" )
			if self.uprMashGlobals.verboseMode : print("got open UPR file for writing: \n" + str( openStub ) )
					
			openStub.writelines( mashStr )
					
			openStub.flush()
			if self.uprMashGlobals.verboseMode : print("wrote mashed upr file : " + str( self.uprMashGlobals.outFileName ) )
		else :
			print("could not write UPR, does the output file already exist? if so you need to use the force flag: '-f'")
	
	def browseUPR( self ) :
		
		import Tkinter,tkFileDialog
		root = self 
		
		formats = [
		    ('UltraFractal Parameter File','*.upr'),
		     ('Any File','*.*')		  
		    ]
		file = tkFileDialog.askopenfile( parent=root, mode='rb', title='Choose a UPR file', filetypes=formats )
		
		if file:
			self.inFileField.delete( "1.0", END )
		    	#self.inFileField.insert( "1.0", os.sep.join( file.name.split("/") ) )
		    	backToFront = "/".join( file.name.split("\\") )
		    	frontToBack = "\\".join( backToFront.split("/") )
		    	
		    	
		    	self.inFileField.insert( "1.0", frontToBack )
	    		self.openUPR()
	    	
	    	else :
	    		self.openUPR()
	    		return file
	
	def browseWAV( self ) :
		
		import Tkinter,tkFileDialog
		root = self 
		
		formats = [
		    ('Audio Wav File','*.wav'),
		     ('Any File','*.*')
		    ]
		file = tkFileDialog.askopenfile( parent=root, mode='rb', title='Choose a WAV file', filetypes=formats )
		
		if file:
			self.wavFileField.delete( "1.0", END )
		    	self.wavFileField.insert( "1.0", file.name )
	    		self.openWAV()
	    	else :
	    		self.openWAV()
	    		return file
	
	
	def openWAV( self ) :
		
		#should check if selected one is already open.. and skip the needless work
		
		def ok( value ) :
			if self.uprMashGlobals.verboseMode: print "input WAV file selected: " + str( value )
		
		infile = self.wavFileField.get( "1.0", END).strip()
		
		if self.uprMashGlobals.verboseMode: print "input file WAV file field says: " + str( infile )
		
		file = None
		
		if os.path.isfile( infile ) :
			
			if self.uprMashGlobals.verboseMode: print "input wav file exists, good!"
			
			self.browseWAVButton.configure( foreground="green" )
			
		else :
			
			self.browseWAVButton.configure( foreground="red" )
			print "ERROR: WAV file cannot be opened: " + str( infile )
					
	def openUPR( self ) :
		
		def ok( value ) :
			self.outFractalField.delete( "1.0", END )
			self.outFractalField.insert( "1.0", value + "_mashed" )
			
			if self.uprMashGlobals.verboseMode: print "input fractal selected: " + str( value )
		
		infile = self.inFileField.get( "1.0", END).strip()
		
		# if self.uprMashGlobals.verboseMode: print "input file text field says: " + str( infile )
		
		file = None
		
		if os.path.isfile( infile ) :
			
			if self.uprMashGlobals.verboseMode: print "input file exists, good!"
			file = open( infile, "r" )
			self.browseUPRButton.configure( foreground="green" )
			
		else :
			self.browseUPRButton.configure( foreground="red" )
			print "ERROR: UPR file cannot be opened: " + str( infile )

		if file != None:
		
		    # file.name = os.sep.join( file.name.split("/") )
		    if self.uprMashGlobals.verboseMode: print "got file: " + str( os.sep.join( file.name.split("/") ) )
		    
		    data = file.read()
		    file.close()
		    
		    fractalNames = []
		    
		    for line in data.split("\n") :
		    	if "{" in line :
		    		fname = line.strip().strip("{").strip()
		    		fractalNames.append( fname )
		    
		    # print( "got fractalNames: " + str( fractalNames ) )
		    
		    if fractalNames :
		    
		    	from Tkinter import _setit
			self.fractalNameOptionBox['menu'].delete( 0, END )
			
			count = 0
			self.fractalDict = {}
			
			for name in fractalNames :
				#self.fractalNameVar = StringVar()
				self.fractalNameOptionBox['menu'].insert('end', 'command', label=name, command=_setit( self.fractalNameVar, name, ok ))
	    			self.fractalNameVar.set( name )
	    			self.outFractalField.delete( "1.0", END )
				self.outFractalField.insert( "1.0", name + "_mashed" )
				
				self.fractalDict[name] = count
				count += 1
	    		
	    		# print "built fractal dict: " + str( self.fractalDict )
	    		
		    #print "Got %d bytes from file." % len(data)
    		
    		#v = StringVar()
		#v.set('a')
		#def ok(*args):
		#    print v.get()
		#v.trace('w', ok)
		##'-1216076380ok'
		#om = OptionMenu(r, v, 'a', 'b', 'c')
		#om.pack()
		#om['menu'].insert('end', 'command', label='foo', command=lambda : v.set('foo'))


		
	def saveAsUPR( self ) :
		import Tkinter,tkFileDialog
		root = self 
		formats = [
		    ('UltraFractal Parameter File','*.upr'),
		     ('Any File','*.*')
		    ]
		fileName = tkFileDialog.asksaveasfilename(parent=root,filetypes=formats, title="Save the image as...")
		print "Saving as : " + fileName
		self.uprMashGlobals.outFileName = fileName
		
		self.outFileField.delete("1.0", END )
		self.outFileField.insert( "1.0", fileName )
	
	def quit( self ) :
		# print "QUIT - saving settings"
		# save globals
		
		self.copySettingsFromGUI()
		self.uprMashGlobals.saveSettings()
		
		Frame.quit( self )
	
	def about( self ) :
		print self.uprMashGlobals.aboutStr
	
	def copyToClipboard( self ) :
		try :
			import win32clipboard, win32con
		
			text = self.outTextField.get( "1.0", END )
			split = text.split("\n")
			text = os.linesep.join( split )
			
			win32clipboard.OpenClipboard()
			win32clipboard.SetClipboardData(win32con.CF_TEXT, text)
			win32clipboard.CloseClipboard()
		except ImportError :
			print "Error whilst importing win32clipboard or win32con modules, can not copy to clipboard. (you could try just copying the text from the field in the gui instead)"
		
	def createWidgets( self ) :
		
		mainWidth = 85
		scalerWidth = 512
		tipdelay = 600
		
		self.quitButton = Button( self )
		self.quitButton["text"] = "Exit"
		#self.QuitButton["fg"]   = "red"
		self.quitButton["command"] =  self.quit
		self.quitButton.pack({"side": "bottom", "fill":"x"})
		qtip = tooltip.ToolTip(self.quitButton, text="Enough of this! Thanks to Mike Lange for the tooltip code! ;D", delay=tipdelay)
	        
	        #  self.saveMashButton = Button( self )
		#  self.saveMashButton["text"] = "Save",
		#  self.saveMashButton["command"] = self.mashAndSave
		#  self.saveMashButton.pack({"side": "bottom", "fill":"x"})

	        #  self.saveAsUPRButton = Button( self )
		#  self.saveAsUPRButton["text"] = "SaveAs",
		#  self.saveAsUPRButton["command"] = self.saveAsUPR
		#  self.saveAsUPRButton.pack({"side": "bottom", "fill":"x"})
		
		labelframex = LabelFrame(self, text="Actions")
		labelframex.pack( {"side": "bottom"}, expand=1, fill=X, padx = 5, pady=5)
		
		self.copyToClipboardButton = Button( labelframex )
		self.copyToClipboardButton["text"] = "CopyToClipboard",
		self.copyToClipboardButton["command"] = self.copyToClipboard
		self.copyToClipboardButton.pack({"side": "bottom", "fill":"x"}, padx = 5, pady=5)
		copytip = tooltip.ToolTip(self.copyToClipboardButton, text='Copy the mashed UPR to the clipboard for pasting into UltraFractal', delay=tipdelay)
		
		self.doMashButton = Button( labelframex )
		self.doMashButton["text"] = "Mash",
		self.doMashButton["command"] = self.doMash
		self.doMashButton.pack({"side": "bottom", "fill":"x"}, padx = 5, pady=5)
		domashtip = tooltip.ToolTip(self.doMashButton, text='Do the UPR mashing based on current settings', delay=tipdelay)
		
		self.openUPRButton = Button( labelframex )
		self.openUPRButton["text"] = "Refresh",
		self.openUPRButton["command"] = self.openUPR
		self.openUPRButton.pack({"side": "bottom", "fill":"x"}, padx = 5, pady=5)
	        refreshtip = tooltip.ToolTip(self.openUPRButton, text='Reload changes to the input UPR', delay=tipdelay)
	        
	        
	        # self.forceOverwriteCheckboxVar = IntVar()
		# self.forceOverwriteCheckbox = checkboxWithLabelOnLeft( "Overwrite", self, self.forceOverwriteCheckboxVar, self.uprMashGlobals.forceOverwrite )
		
	        self.verboseCheckboxVar = IntVar( )
	        self.verboseCheckbox = checkboxWithLabelOnLeft( "Verbosity", self, self.verboseCheckboxVar, self.uprMashGlobals.verboseMode, "Print verbose status messages to the terminal.", tipdelay )
	        #verbosetip = tooltip.ToolTip(self.verboseCheckbox, text="Do printouts to the terminal.", delay=tipdelay)
	        
		self.ignoreBGCheckboxVar = IntVar( )
	        self.ignoreBGCheckbox = checkboxWithLabelOnLeft( "Ignore Background Layers", self, self.ignoreBGCheckboxVar, self.uprMashGlobals.ignoreBG, "Ignore layers named starting with 'background*' (even if they are animated)", tipdelay )
	        #igbgtip = tooltip.ToolTip(self.ignoreBGCheckbox, text="Ignore layers named 'background (even if they are animated)*' ", delay=tipdelay)
	        
	        labelframe = LabelFrame(self, text="Additional Animation")
		labelframe.pack( {"side": "bottom"}, expand=1, fill=X)
	        
	        self.animPhase = textFieldWithLabelOnLeft( "Add Anim Phase", labelframe, str( self.uprMashGlobals.animPhase ), "Offset in phase for signal generated by added anim", tipdelay )
		# self.animPhase.insert( "1.0", str( self.uprMashGlobals.animPhase ) )
		# phasetip = tooltip.ToolTip(self.animPhase, text="Offset in phase for signal generated by added anim", delay=tipdelay)
		
		self.animAmp = textFieldWithLabelOnLeft( "Add Anim Amp", labelframe, str( self.uprMashGlobals.animAmp ), "List of amplitudes for signal(s) generated by added anim", tipdelay )
		#self.animAmp.insert( "1.0", str( self.uprMashGlobals.animAmp ) )
		#amptip = tooltip.ToolTip(self.animAmp, text="List of amplitudes for signal(s) generated by added anim", delay=tipdelay)
		
		self.animFreq = textFieldWithLabelOnLeft( "Add Anim Loop Length", labelframe, str( self.uprMashGlobals.animFreq ), "Set the loop length (in frames) for the signal(s) generated by the added anim", tipdelay )
		#self.animFreq.insert( "1.0", str( self.uprMashGlobals.animFreq ) )
		#amptip = tooltip.ToolTip(self.animFreq, text="Set the loop length (in frames) for the signal(s) generated by the added anim", delay=tipdelay)
		
	        self.useAudioCheckboxVar = IntVar( )
	        self.useAudioCheckbox = checkboxWithLabelOnLeft( "Use Audio Data", labelframe, self.useAudioCheckboxVar, self.uprMashGlobals.useAudio, "Toggle the usage of audio wave data by uprMash", tipdelay )
	        
	        self.animModeCheckboxVar = IntVar( )
	        self.animModeCheckbox = checkboxWithLabelOnLeft( "Add Animation", labelframe, self.animModeCheckboxVar, self.uprMashGlobals.animMode, "Toggle the addition of value-based animation to existing (float, int or complex) anim curves by uprMash", tipdelay )
	        
	        #animtip = tooltip.ToolTip(self.animModeCheckbox, text="Toggle the addition of value-based animation to existing (float, int or complex) anim curves by uprMash", delay=tipdelay)
	        
	        
	        self.About = Button( self )
		self.About["text"] = "About",
		self.About["command"] = self.about
		self.About.pack({"side": "top", "fill":"x", "anchor":"s" })
		abouttip = tooltip.ToolTip( self.About, text=self.uprMashGlobals.aboutStr, delay=200 )
	        
		self.outTextField = Text( self, width=mainWidth, height=10 )
		self.outTextField.pack( {"side": "top","anchor":"s"}, expand=1, fill=BOTH )
		outtip = tooltip.ToolTip(self.outTextField, text="The 'mashed' UPR code will be shown herte in the GUI once you press 'mash'", delay=tipdelay)
		
		self.fractalNameVar = StringVar( self )
		self.fractalNameVar.set( self.uprMashGlobals.fractalNames[0] ) # default value	
		
		labelframeo = LabelFrame(self, text="Open UPR")
		labelframeo.pack( {"side": "top"}, expand=1, fill=X, padx = 5, pady=5)
		
		self.browseUPRButton = Button( labelframeo, foreground="red", background="black" )
		self.browseUPRButton["text"] = "OpenUPR",
		self.browseUPRButton["command"] = self.browseUPR
		self.browseUPRButton.pack({"side": "top", "fill":"x"}, padx = 5, pady=5)
		browserefreshtip = tooltip.ToolTip(self.browseUPRButton, text='Browse for an input UPR file', delay=tipdelay)
		
		self.browseWAVButton = Button( labelframeo, foreground="red", background="black" )
		self.browseWAVButton["text"] = "OpenWAV",
		self.browseWAVButton["command"] = self.browseWAV
		self.browseWAVButton.pack({"side": "top", "fill":"x"}, padx = 5, pady=5)
		browseWAVtip = tooltip.ToolTip(self.browseWAVButton, text='Browse for an input WAV file to drive animation using audio data', delay=tipdelay)
		
		self.fractalNameOptionBox = apply( OptionMenu, (self, self.fractalNameVar) + tuple( self.uprMashGlobals.fractalNames ) )
		self.fractalNameOptionBox.pack( {"side":"top", "anchor":"w" }, expand=1, fill=X  )
		fractaltip = tooltip.ToolTip(self.fractalNameOptionBox, text="Which fractal in the input UPR file to seed a new mash from (the last one is always re-selected after refreshing)", delay=tipdelay)
		
		labelframexx = LabelFrame(self, text="Shutter Controls")
		labelframexx.pack( {"side": "bottom"}, expand=1, fill=X, padx = 5, pady=5)
		
		self.resampleCurvesCheckboxVar = IntVar( )
	        self.resampleCurvesCheckbox = checkboxWithLabelOnLeft( "Resample Anim Curves", labelframexx, self.resampleCurvesCheckboxVar, self.uprMashGlobals.resampleCurves, "Toggle the conversion of sparse-key curves into 'baked' curves with a key on every frame (which gives much more accurate motionblur)", tipdelay )
	        #resampletip = tooltip.ToolTip(self.resampleCurvesCheckbox, text="Toggle the conversion of sparse-key curves into 'baked' curves with a key on every frame (which is much more accurate in terms of motionblur)", delay=tipdelay)
		
		self.interpModeField = textFieldWithLabelOnLeft( "Key-Interp Mode Overrides", labelframexx, ", ".join( self.uprMashGlobals.interpMode ), "A list of interp modes (eg 'L C S N') to override interpolation modes on animation keys.\nAny list of string values can be used here, for example: to override all interpolation to 'smooth' you could enter a single 'S' here", tipdelay  )
		#self.interpModeField.insert( "1.0", ", ".join( self.uprMashGlobals.interpMode ) )
		#interptip = tooltip.ToolTip(self.interpModeField, text="A list of interp modes (eg 'L C S N') to override interpolation modes on animation keys.\nAny list of string values can be used here, for example: to override all interpolation to 'smooth' you could enter a single 'S' here", delay=tipdelay)
		
		
		self.layerModesField = textFieldWithLabelOnLeft( "Layer Mode Overrides", labelframexx, ", ".join( self.uprMashGlobals.newLayerMode ), "A list of layer modes that may be used to override the layer modes used in the mashed upr, leave the field blank to inherit the modes set in the seed.", tipdelay )
		# self.layerModesField.insert( "1.0", ", ".join( self.uprMashGlobals.newLayerMode ) )
		# layermodestip = tooltip.ToolTip(self.layerModesField, text="A list of layer modes that may be used to override the layer modes used in the mashed upr, leave the field blank to inherit the modes set in the seed.", delay=tipdelay)
		
		
		self.shutterOffset = textFieldWithLabelOnLeft( "Shutter Offset", labelframexx, str( self.uprMashGlobals.shutterOffset ), "Offset the shutter, to change the centering of the interpolation range, a value of 0 is interpreted as 'centered-on-frame' motion here", tipdelay )
		# self.shutterOffset.insert( "1.0", str( self.uprMashGlobals.shutterOffset ) )
		# shutterOffsetTip = tooltip.ToolTip(self.shutterOffset, text="Offset the shutter, to change the centering of the interpolation range, a value of 0 is interpreted as 'centered-on-frame' motion here.", delay=tipdelay)
		
		self.shutterLength = textFieldWithLabelOnLeft( "Shutter Length", labelframexx, str( self.uprMashGlobals.shutterLength ), "The 'shutter length' of the mash. Use this control to set the spread of 'time' settings that each new layer in a mash will use to get its new value", tipdelay )
		#self.shutterLength.insert( "1.0", str( self.uprMashGlobals.shutterLength ) )
		#shutterLengthTip = tooltip.ToolTip(self.shutterLength, text="The 'shutter length' of the mash. Use this control to set the spread of 'time' settings that each new layer in a mash will use to get its new value", delay=tipdelay)
		
		self.interleaveCheckboxVar = IntVar( )
	        self.interleaveCheckbox = checkboxWithLabelOnLeft( "Interleave New Layers", labelframexx, self.interleaveCheckboxVar, self.uprMashGlobals.interleave, "Interleave the generated layers, eg 'abcabcabc' rather than 'aaabbbccc' ", tipdelay )
	        #interleavetip = tooltip.ToolTip(self.ignoreBGCheckbox, text="Interleave the generated layers, eg 'abcabcabc' rather than 'aaabbbccc' ", delay=tipdelay)
		
		# shoul recognize 1-10x2 to do a key on every 2nd frame for example
		
		self.frameRange = textFieldWithLabelOnLeft( "Output Frame Range", labelframexx, str( self.uprMashGlobals.frameRange ), "The frame range of the animation output (eg 7-10,54,77-92), leave this blank to use the existing animation start and end points.", tipdelay )
		# self.frameRange.insert( "1.0", str( self.uprMashGlobals.frameRange ) )
		#frameRangeTip = tooltip.ToolTip( self.frameRange, text="The frame range of the animation output (eg 7-10,54,77-92), leave this blank to use the existing animation start and end points.", delay=tipdelay)
		
		#self.frameOffset = textFieldWithLabelOnLeft( "Output Frame Offset", labelframexx, str( self.uprMashGlobals.frameRange ), "Offset for output frames, (for example if you want to see frame 50 on frame 1, enter -50 here).", tipdelay )
		#self.frameOffset.insert( "1.0", str( self.uprMashGlobals.frameRange ) )
		#frameRangeTip = tooltip.ToolTip( self.frameOffset, text="Offset for output frames, (for example if you want to see frame 50 on frame 1, enter -50 here).", delay=tipdelay)

		self.fps = textFieldWithLabelOnLeft( "Frames Per Second", labelframexx, str( self.uprMashGlobals.fps ), "The fps of the fractal that you are mashing - (only tested with 30fps)", tipdelay )
		#self.fps.insert( "1.0", str( self.uprMashGlobals.fps ) )
		#fpsTip = tooltip.ToolTip(self.fps, text="The fps of the fractal that you are mashing - (only tested withh 30 so far!)", delay=tipdelay)
		
		self.opacRampLengthFloatVar = DoubleVar( self )
		self.opacRampLengthScale = scaleWithEntryField(  "Shutter Opacity Ramp Width", labelframexx, 1.5, 0.001, self.opacRampLengthFloatVar, self.uprMashGlobals.opacityRampLength, "The 'softness' of the opacity ramping in and out for the virtual 'fractal-camera-shutter'. A value of 0 will do no opacity fading, 0.5 is quite smooth but still reaches full opacity in the center, 1.0 and more is very soft.", tipdelay )
		#self.opacRampLengthFloatVar.set( self.uprMashGlobals.opacityRampLength )
		#opacRampTip = tooltip.ToolTip(self.opacRampLengthScale, text="The 'softness' of the opacity ramping in and out for the virtual 'fractal-camera-shutter'. A value of 0 will do no opacity fading, 0.5 is quite smooth but still reaches full opacity in the center, 1.0 and more is very soft.", delay=tipdelay)
		
		self.opacScaleFloatVar = DoubleVar( self )
		self.opacScale = scaleWithEntryField(  "Opacity Scale", labelframexx, 150, 0.1, self.opacScaleFloatVar, self.uprMashGlobals.newLayerOpacity, "The overall opacity multiplication for the layer opacites.", tipdelay )
		#self.opacScaleFloatVar.set( self.uprMashGlobals.newLayerOpacity )
		#opacScaleTip = tooltip.ToolTip(self.opacScale, text="The overall opacity multiplication for the layer opacites.", delay=tipdelay)
		
		self.numLayersIntVar = IntVar( self )
		self.layerScale = scaleWithEntryField( "Num Layers", labelframexx, 320, 1, self.numLayersIntVar, self.uprMashGlobals.numExtraLayers, "The number of extra layers to time-shift and create for each animated input fractal layer. Set small numbers here for 'preview' mode and larger values for smother (and of course slower) results.", tipdelay )
		#self.numLayersIntVar.set( self.uprMashGlobals.numExtraLayers )
		#numLayersTip = tooltip.ToolTip(self.layerScale, text="The number of extra layers to time-shift and create for each animated input fractal layer. Set small numbers here for 'preview' mode and larger values for smother (and slower of course) results.", delay=tipdelay)

		self.outFractalField =  textFieldWithLabelOnLeft( "New Fractal Name", self, self.uprMashGlobals.outFractalName, "The 'mashed' fractal will be named this un UF (this automatically updates to inputName_mashed, on refresh)", tipdelay )
		#self.outFractalField.insert( "1.0", self.uprMashGlobals.outFractalName )
		#outFracTip = tooltip.ToolTip( self.outFractalField, text="The 'mashed' fractal will be named this un UF (this automatically updates to inputName_mashed, on refresh)", delay=tipdelay)
		
		# self.outFileField =  textFieldWithLabelOnLeft( "Out Filename", self )
		# self.outFileField.insert( "1.0", self.uprMashGlobals.outFileName )
		
		self.inFileField =  textFieldWithLabelOnLeft( "Input UPR Filename", self,  fwdToLocalSlashesAll( self.uprMashGlobals.inFileName ), "The name of the input UPR to load. You can press the 'Browse' button to change this value, and you can also paste a new filename in", tipdelay )
		self.wavFileField =  textFieldWithLabelOnLeft( "Input WAV Filename", self,  fwdToLocalSlashesAll( self.uprMashGlobals.inWavName ), "The name of the input WAV to load for sound-driven effects.", tipdelay )
		
		#self.inFileField.insert( "1.0", self.uprMashGlobals.inFileName )
		#inFileTip = tooltip.ToolTip(self.inFileField, text="The name of the input UPR to load. You can press the 'Browse' button to change this value, and you can also paste a new filename in", delay=tipdelay)
		
		self.pack( expand=1, fill=X )
	
	def __init__( self, master, uprGlobals ) :
		
		self.uprMashGlobals = uprGlobals
		
        	Frame.__init__(self, master)
        	
        	self.pack()
        	
        	self.createWidgets()

def textFieldWithLabelOnLeft( labelText, parent, value, tooltipstr, tipdelay ) :
	frameGroup = Frame( parent )
	layerModeLabel = Label( frameGroup, text=labelText, width = 22, anchor="e" )
	layerModeLabel.pack({"side": "left",  "padx":4})
	textField = Text( frameGroup, height=1 )
	textField.pack( {"side": "right"}, expand=1, fill=X  )
	frameGroup.pack({"side": "bottom"}, expand=1, fill=X )
	textField.insert( "1.0", value )
	tip = tooltip.ToolTip( textField, text=tooltipstr, delay=tipdelay)
	return textField


def scaleWithEntryField( labelText, parent, limit, res, tkvar, value, tooltipstr, tipdelay ) :
	frameGroup = Frame( parent )
	layerModeLabel = Label( frameGroup, text=labelText, width=22, anchor="e" )
	layerModeLabel.pack({"side": "left", "padx":2})

	anentry = Entry( frameGroup, textvariable=tkvar )
	anentry.pack( {"side": "bottom"}, expand=1, fill=X, padx=3  )
	
	ascale = Scale( frameGroup, orient=HORIZONTAL, to=limit, resolution=res, variable=tkvar )
	ascale.pack( {"side": "right"}, expand=1, fill=X  )
	
	frameGroup.pack({"side": "bottom"}, expand=1, fill=X )
	
	tkvar.set( value )
	tip = tooltip.ToolTip( ascale, text=tooltipstr, delay=tipdelay)
	
	return ascale



		

def scaleWithLabelOnLeft( labelText, parent, limit, res ) :
	frameGroup = Frame( parent )
	layerModeLabel = Label( frameGroup, text=labelText, width=22, anchor="e" )
	layerModeLabel.pack({"side": "left", "padx":2})
	scale = Scale( frameGroup, orient=HORIZONTAL, to=limit, resolution=res )
	scale.pack( {"side": "right"}, expand=1, fill=X  )
	frameGroup.pack({"side": "bottom"}, expand=1, fill=X )
	return scale

def checkboxWithLabelOnLeft( labelText, parent, intvar, state, tooltipstr, tipdelay ) :
	frameGroup = Frame( parent )
	layerModeLabel = Label( frameGroup, text=labelText, width=22, anchor="e" )
	layerModeLabel.pack({"side": "left", "padx":2})
	check = Checkbutton( frameGroup, var=intvar, anchor="w" )
	
	if state :
		 check.select()
	else :
		check.deselect()
	
	check.pack( {"side": "right"}, expand=1, fill=X  )
	frameGroup.pack({"side": "bottom"}, expand=1, fill=X )
	
	tooltip.ToolTip( check, text=tooltipstr, delay=tipdelay)
	
	return check
	

base64alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

#this is a bloody crap way of doing this.. but whatever
def getIndex( char ) :
	return base64alphabet.find( char )

def quadDecode( fourChars ) :

	i0 = getIndex( fourChars[0] )
	i1 = getIndex( fourChars[1] )
	i2 = getIndex( fourChars[2] )
	i3 = getIndex( fourChars[3] )
	
	#print "i0: " + str(i0) + " i1: " + str(i1) + " i2: " + str(i2) + " i3: " + str(i3) + "."
	
	csum = (i3 << 18) + (i2 << 12) + (i1 << 6) + i0
	
	#csum = (i0 << 18) + (i1 << 16) + (i2 << 6) + i3
	#cbin = "".join( [ str( strint ) for strint in digitlist( csum, 32, 2 ) ] )
	
	#print "csum is: " + str( csum )
	#print "cbin is: " + str( cbin )
	
	byte0 = csum & 0xff
	byte1 = ( csum >> 8 ) & 0xff
	byte2 = ( csum >> 16 ) & 0xff
	
	#print "byte0 is: " + str( byte0 )
	#print "byte1 is: " + str( byte1 )
	#print "byte2 is: " + str( byte2 )
	return [ byte0, byte1, byte2 ]

#lets just assume that everything has worked out great :D
def decodeAndUnzipUPR( instr ) :
	#print "decoding: " + str( instr )
	decoded = []
	for i in range( 0, len( instr ) / 4 ) :
		fourchars = instr[ i*4 : i*4 + 4 ]
		decoded.extend( quadDecode( fourchars ) )
	decodedchr = [ chr( x ) for x in decoded[4:] ]
	return zlib.decompress( "".join( decodedchr ) )

def checkAndDecompress( strlist ) :
	start = []
	mid = []
	end = []
	fracstarted = False
	
	# split into parts first, then determine if we are doing a compressed upr..
	# this is dodgey as hell.. ahem
	for line in strlist :
		if (line.strip()[0] == ";" or line.strip()[-1] == "{") :
			#print "we seem to have a start line: " + line
			start.append( line )
		elif (line.strip()[0] == "}") :
			#print "this line looks like the end: " + line
			end.append( line )
		else :
			#print "assuming we're on a middle line now" + line
			mid.append( line )
			
	#print "got start: " + str( start )
	#print "got mid: " + str( mid )
	#print "got end: " + str( end ) 
	
	if mid[0].strip()[0] == ":" and mid[0].strip()[1] == ":" :
		print "upr appears to be compressed.. decoding... "
		unz = decodeAndUnzipUPR( "".join( mid ).strip(":") )
		#print "got DECODE: " + unz
		
		mid = unz.strip("\n").split("\n")
		mid = [ hwarf.strip("\r") for hwarf in mid ]
		#print "got SPLIT DECODE: " + str( mid )
		
	concat = start + mid + end
	
	return concat
	

#little helper for visualising float values with stars
def getFloatAsStarsStr( floatValue, starWhitePoint, numStarsAtWhitePoint ) : 
	scaledFloat = floatValue
	
	if starWhitePoint != 0 :
		scaledFloat = scaledFloat / starWhitePoint
	
	scaledFloat = min( 1.0, max( 0.0, scaledFloat ) )
	numStars = int( scaledFloat * numStarsAtWhitePoint )
	star = "*" * numStars
	return star

def getIntAsStarsStr( intValue, maxStars ) : 
	numStars = int( max(0, min( maxStars, intValue ) ) )
	star = "*" * numStars
	return star

# ufLayerTagValue - a very basic class to hold and interpolate the values of upr file tags

class ufLayerTagValue :

	tagValue = ""
	parsedOK = False
	isAnimated = False
	
	def __init__( self, globals ) :
		self.tagValue = ""
		parsedOK = False
	
	def setTagValue( self, withString, globals ) :
		if withString : 
			paramValues = withString
			
			animCheck = paramValues.split("@#")
			
			#gotta have at least 2 keys to be 'animated'
			if len( animCheck ) > 1 :
				self.isAnimated = True
				
			self.parsedOK = True
			self.tagValue = withString
				
	def isValid( self ) :
		return self.parsedOK
		
	def getAsString( self, globals ) :
		return self.tagValue
		
	def getInterpolatedTagValue( self, targetTagValue, blendAmount, globals ) :
		
		if globals.debugMode :  print("interpolating tag value: " + str( targetTagValue.getAsString( globals ) ) )
		
		newTagValue = ufLayerTagValue( globals )
		thisTagValue = self.tagValue
		
		intCheck = re.compile("-{0,1}([0-9]+)(?!.)").match( thisTagValue )
		floatCheck = re.compile("(-{0,1}[0-9]*\.[0-9]+)").match( thisTagValue ) #also atches complex twice
		
		intCheckEnd = re.compile("-{0,1}([0-9]+)(?!.)").match( targetTagValue.tagValue )
		floatCheckEnd = re.compile("(-{0,1}[0-9]*\.[0-9]+)").match( targetTagValue.tagValue ) #also atches complex twice
		
		if globals.debugMode : 
			
			print( "intCheck: " + str( intCheck ) )
			print( "floatCheck: " + str( floatCheck ) )
			print( "intCheckEnd: " + str( intCheckEnd ) )
			print( "floatCheckEnd: " + str( floatCheckEnd ) )
		
		if targetTagValue :
			
			targetValueString = targetTagValue.tagValue
			targetSlashSplit = targetValueString.split("/")
			tagSlashSplit = thisTagValue.split("/")
			
			
			if thisTagValue[0] == '"' and thisTagValue[-1] == '"' : #it's a string, cant really interpolate but at least we'll swap between the 2 values
			
				if blendAmount <= 0.5 :
				
					newTagValue.setTagValue( thisTagValue, globals )
				else :
					newTagValue.setTagValue( targetValueString, globals )
				
				#\print("looks like a string or enum to 'interpolate': " + thisTagValue )
				
			
			elif len( tagSlashSplit ) == len( targetSlashSplit ) == 2 : #it's complex
				
				#then try to also split the target
				
					
				thisSplit = [ float( tagSlashSplit[0] ), float( tagSlashSplit[1] ) ]
				targetSplit = [ float( targetSlashSplit[0] ), float( targetSlashSplit[1] ) ]
				
				if thisSplit[0] != targetSplit[0] or thisSplit[1] != targetSplit[1] :
				
					interReal = (1.0 - blendAmount) * thisSplit[0] + blendAmount * targetSplit[0]
					interImag = (1.0 - blendAmount) * thisSplit[1] + blendAmount * targetSplit[1]
					
					newTagValue.setTagValue( str( interReal ) + "/" + str( interImag ), globals )
					
					#print("got interpolated complex tag value: " + newTagValue.getAsString( globals ) )
					#
				else :
					newTagValue.setTagValue( thisTagValue, globals )
					#print("complex value did not need interpolation (it was the same at both ends): " + str( tagSlashSplit  ) )
					
			elif floatCheck or floatCheckEnd:
			
				thisFloat = float( thisTagValue )
				targetFloat = float( targetValueString )
				
				if thisFloat != targetFloat :
					newFloat = (1.0 - blendAmount) * thisFloat + blendAmount * targetFloat
					newTagValue.setTagValue( str( newFloat ), globals  )
					if globals.debugMode : print("got interpolated float tag value: " + str( newFloat ) + " (" + thisTagValue + " to " + targetValueString + " by " + str( blendAmount ) + ")" )
				else :
					if globals.debugMode : print("float value did not need interpolation (same at both ends): " + str( thisFloat  ) )
					newTagValue.setTagValue( thisTagValue, globals )
				
			elif intCheck and intCheckEnd : 
				#lean towards float interpolation.. only do int when both ends are floaty
				
				doInt = True
				try :
					thisInt = int( thisTagValue )
					targetInt = int( targetValueString )
				except ValueError : #erk.. it gets a bit wierd but damn python makes it simple :D
					doInt = False
					thisInt = float( thisTagValue )
					targetInt = float( targetValueString )
				
				if thisInt != targetInt :
					#actually you can hardly ever tell when its an int rather than a truncated float.. lets just try always giving float shall we? :D
					if doInt : 
						newIntFloat = int( (1.0 - blendAmount) * thisInt + blendAmount * targetInt )
					else :
						newIntFloat = float( (1.0 - blendAmount) * thisInt + blendAmount * targetInt )
					
					newTagValue.setTagValue( str( newIntFloat ), globals )
					if globals.debugMode : print("got interpolated integer tag value: " + str( newIntFloat ) + " (" + thisTagValue + " to " + targetValueString + " by " + str( blendAmount ) + ")" )
				else :
					if globals.debugMode : print("integer value did not need interpolation (same at both ends): " + str( thisInt  ) )
					newTagValue.setTagValue( thisTagValue, globals )
					
			else :
				if blendAmount <= 0.5 :
				
					newTagValue.setTagValue( thisTagValue, globals )
				else :
					newTagValue.setTagValue( targetValueString, globals )
				
				#print("param is not complex or a string:" + str( self.tagValue ) )
				
		
		#print("new tag value: " + str( newTagValue.getAsString( globals ) ) )
		
		return newTagValue
		
	
	def getShiftedTagValue( self, offset, globals ) :
		
		#this string is used in afew  regexz below
		interpModes = "LCSNE"
		
		newTagValue = ufLayerTagValue( globals )
		thisTagValue = self.tagValue
		newTagValue.setTagValue( thisTagValue, globals )
		
		#print "shifting tag value: " + str( thisTagValue )
		
		splitTag = thisTagValue.split("@#")
		
		# make sure its not just a string tag with an LCS or N in the value (seems strings are all lowercase so all is good?).
		
		if len( splitTag ) > 1 :
		
			splitter = re.compile( "[\\A" + interpModes + "]{0,1}-{0,1}[0-9\.\-a-z]+/*-{0,1}[0-9\.\-e]*@#[0-9]+[" + interpModes + "\\Z]{0,1}" )
			
			tagSplit = splitter.findall( thisTagValue )
			
			# print "shifting animated tag value: " + str( thisTagValue )
			# print "tagSplit: " + str( tagSplit )
			
			keylist = [ ]
			curve = animCurve()
			
			# make an animcurve
			
			interModes = globals.interpMode
			# print "intermodes is : " + str( interModes )
			for i in range( 0, len( tagSplit ) ) :
				
				key = tagSplit[ i ]
				keyspl = key.split("@#")
				
				valget = re.compile( "-{0,1}[0-9\.\-a-z]+/*-{0,1}[0-9\.\-e]*" )
				frmget = re.compile( "[0-9]+" )
				
				inmodeget = re.compile( "\A[" + interpModes + "]{0,1}" )
				outmodeget = re.compile( "[" + interpModes + "]{0,1}\Z" )
				
				val = valget.findall( keyspl[0] )
				time = frmget.findall( keyspl[1] )
				inmode = inmodeget.findall( key )
				outmode = outmodeget.findall( key )
				
				if len( interModes ) > 0 :
				
					modeix = i % len( interModes )
					mode = interModes[ modeix ]
					
					if inmode != "" :
						inmode = mode
					if outmode != "" :
						outmode = mode
					
					# print "intermodes overridden to: IN=" + str( inmode ) + " OUT=" + str( outmode )
					
				# print "VAL: " + str( val ) + " AT: " + str( time )
				# print "IN: " + str( inmode ) + " OUT: " + str( outmode )
				
				newKey = keyframe( inmode[0], outmode[0], val[0], time[0] )
				
				curve.addKey( newKey )
			
			# curvekeys = curve.keyframes
			# sortedcurve = sorted( curvekeys.items(), key=operator.itemgetter(1), reverse=True )
			# for key in sortedcurve :
			#	print "KEY: " + str( key[0] )
			#	print "VALUE: " + str( key[1].value )
			
			shiftedCurve = animCurve()
			sortedtimes = sorted( curve.keyframes.keys() )
			
			if globals.resampleCurves :
			
				#need to get proper range here from min/max keys
				
				firstFrame = int( timecodeToFrames( sortedtimes[0], globals ) )
				lastFrame = int( timecodeToFrames( sortedtimes[-1], globals ) )
				
				if globals.frameRange :
					# print "output framerange is overridden: " + str( globals.frameRange )
					intExtractor = re.compile("-{0,1}[0-9]+")
					rangeStartExtractor = re.compile("^-{0,1}[0-9]+")
					rangeEndExtractor = re.compile("[-,a-z,A-Z]-{0,1}[0-9]+$")
					
					rangestart = rangeStartExtractor.findall( globals.frameRange.strip() )
					rangeend = rangeEndExtractor.findall( globals.frameRange.strip() )
					
					if len( rangestart ) == 1 :
						#rangeIntList = [ int ( x ) for x in rangestrs ]
						#print "got range START: " + str( rangestart[0] ) 
						firstFrame = int( rangestart[0] ) - 1
						
					if len( rangeend ) == 1:
						#print "got range END: " + str( rangeend[0][1:] )
						lastFrame = int( rangeend[0][1:] ) - 1
				
				if firstFrame > lastFrame :
					if globals.verboseMode : print "WARNING: firstframe was after lastframe: " + str( firstFrame+1 ) + " to " + str( lastFrame+1 ) + ", swapping them for sanity"
					fft = firstFrame
					firstFrame = lastFrame
					lastFrame = fft
					
				# print "got framerange: " + str( firstFrame ) + " to " + str( lastFrame )
				
				for frm in range( firstFrame, lastFrame + 1 ) :
					
					timecode = framesToTimecode( frm, globals )
					timecodeoffset = framesToTimecode( frm + offset, globals )
					
					# print "sampling curve at: " + str( frm + offset ) + " for key at frame: " + str( frm )
					
					time = float( frm ) / float( globals.fps )
					#print "sampling curve at time: " + str(  )
					
					shVal = curve.curveValue( timecodeoffset )
					
					if globals.animMode :
						floatExtractor = re.compile("-{0,1}[0-9\.\-e]+")
						animAmps = floatExtractor.findall( globals.animAmp )
						animAmpFloatList = [ float ( x ) for x in animAmps ]
						# print "got animAmpFloatList: " + str( animAmpFloatList )
						shVal = getSineOffsetValue( shVal, frm, globals.animFreq, animAmpFloatList , globals.animPhase + offset )
						
						if globals.useAudio :
							auVal = getAudioOffsetValue( shVal, time, globals )
						
					# print "shVal type is: " + str( type( shVal ) )
					
					shiftkey = keyframe( "S", "S", shVal, timecode )
					
					# print "frame : " + str( frm ).zfill(4) + " offset key pos : " + str( timecodeToFrames( timecode, globals ) )
					
					shiftedCurve.addKey( shiftkey )
					
					# print "frm : " + str( frm ) + " timecode = " + str( timecode ) + " shval : " + str( shVal.real )
					#stars = getFloatAsStarsStr( shVal.real, 4, 30 )
					#print stars
			
			else :
				for key in sortedtimes :
					
					thiskey = curve.keyframes[ key ]
					
					keyframepos = timecodeToFrames( key, globals )
					
					timecode = framesToTimecode( keyframepos + offset, globals )
					
					shiftVal = curve.curveValue( timecode )
					
					# print "key pos in frames is : " + str( keyframepos ) + " and shifted key pos is : " + str( timecodeToFrames( timecode, globals ) )
					
					# print "got shiftedvalue: " + str( shiftVal )
					
					shiftkey = keyframe( thiskey.inmode, thiskey.outmode, shiftVal, key )
					
					shiftedCurve.addKey( shiftkey )
				
			reCurve = shiftedCurve.getAsString()
			
			newTagValue.setTagValue( reCurve, globals )
						
		return newTagValue
				
def framesToTimecode( frame, globals ) :
	return frame * 4800.0 / float( globals.fps )

def timecodeToFrames( timecode, globals ) :
	return timecode * float( globals.fps ) / 4800.0

class keyframe :		
	modes = { "L" : "linear", "C" : "constant", "S" : "smooth", "N" : "none" }
	inmode  = "L"
	outmode = "L"
	value = None
	time = 0

	def __init__( self, inmode, outmode, value, time ) :
		# print "NEW KEY: IN: " + str( inmode ) + " OUT: " + str( outmode ) + " val: " + str( value ) + " time: " + str( time )
		self.inmode = inmode
		self.outmode = outmode
		self.value = detectType( value )[1]
		self.time = int( time )

class animCurve :

	curveType = None
	keyframes = { }
	init = False
	
	def __init__( self ) :
		self.curveType = None
		self.init = True
		#del( self.keyframes )
		self.keyframes = { }
	
	def addKey( self, key ) :
	
		if self.curveType :
			
			if type( key.value ) == self.curveType :
				
				time = key.time
				# print "adding key at time: " + str( time ) + " with value: " + str( key.value )
				
				self.keyframes[ key.time ] = key
			else :
				print "tried to add an incorrect key type: " + str( type( key.value ) ) + " to anim curve of type: " + str( self.curveType ) + " of value: " + str( key.value )
		else :
			time = key.time
			# print "adding FIRST key at time: " + str( time ) + " with value: " + str( key.value )
			
			self.keyframes[ key.time ] = key
			
			self.curveType = type( key.value )
			
	def getAsString( self ) :
		keytimes = sorted( self.keyframes.keys() )
		
		stresult = ""
		
		count = 0
		
		for keytime in  keytimes :
			thiskey = self.keyframes[ keytime ]
			
			if count > 0 :
				stresult += str( thiskey.inmode )
			
			if self.curveType == types.ComplexType :
				stresult += str( thiskey.value.real )
				stresult += "/"
				stresult += str( thiskey.value.imag )
				
			elif self.curveType == types.FloatType :
			
				stresult += str( thiskey.value )
			else :
				stresult += str( thiskey.value )
				
			stresult += "@#"
			stresult += str( keytime )
			
			if count < len( keytimes ) - 1 :
				stresult += thiskey.outmode
			
			count += 1
			
		return stresult
			
	def clear() :
		self.keyframes = {}
		self.curveType = None
		self.init = False
		
	
	def curveValue( self, atTime ) :
	
		keytimes = sorted( self.keyframes.keys() )
		
		#print str( keytimes )
		#print str( self.keyframes )
		
		rez = None
		
		if len( keytimes ) > 1 :
		
			#there are at least two keys
			
			if atTime < keytimes[0] :
				# before first key
				# check for linear mode and extrapolate
				# print "before first key"
				
				firstkey = keytimes[ 0 ]
				nextkey = keytimes[ 1 ]
				
				firstkeyobj = self.keyframes[ firstkey ]
				nextkeyobj = self.keyframes[ nextkey ]
				
				firstval = firstkeyobj.value
				nextval = nextkeyobj.value
						
				pos = float(atTime - firstkey) / float( nextkey - firstkey )
				
				#repeat the inmode?
				
				if firstkeyobj.outmode == "S" :
					result = firstval
				else :
					result = getInterpolatedValue( firstkeyobj.inmode, firstkeyobj.inmode, firstval, nextval, pos )
					
				rez = result 
				
			elif atTime >= keytimes[-1] :
				
				# after last key
				# check for linear mode and extrapolate
				# print "after last key"
				
				lastkey = keytimes[ -1 ]
				nexttolastkey = keytimes[ -2 ]
				
				lastkeyobj = self.keyframes[ lastkey ]
				nexttolastkeyobj = self.keyframes[ nexttolastkey ]
				
				lastval = lastkeyobj.value
				nexttolastval = nexttolastkeyobj.value
				
				# print "atTime: " + str( atTime ) + " nexttolastkey: " +  str( nexttolastkey ) + " lastkey: " + str( lastkey )
				pos = float(atTime - nexttolastkey) / float( lastkey - nexttolastkey )
				
				#repeat the inmode?
				# print "after-last pos: " + str( pos )
				
				# print "after-last pos: " + str( pos ) + " result: " + str( result )
				
				# hmm.. should probably check that outmode is empty string here too.. tho outmode doesn't appear to be supported atm anyway
				if lastkeyobj.inmode == "S" :
					result = lastval
				else :
					result = getInterpolatedValue( lastkeyobj.outmode, lastkeyobj.outmode, nexttolastval, lastval, pos )
				
				rez = result
			else:
				for ix in range( 0, len( keytimes ) - 1 ) :
				
					thiskey = keytimes[ ix ]
					nextkey = keytimes[ ix+1 ]
					
					if atTime >= thiskey and atTime < nextkey :
						
						# print "GOT SPAN FOR test time: " + str( atTime ) + " against (" + str( thiskey ) + "," + str( nextkey ) + ")"
						
						pos = float(atTime - thiskey) / float( nextkey - thiskey )
						
						
						thiskeyobj = self.keyframes[ thiskey ]
						nextkeyobj = self.keyframes[ nextkey ]
						
						inval = thiskeyobj.value
						outval = nextkeyobj.value
						
						# print "pos: " + str( pos ) + " inVal: " + str( inval ) + " outval: " + str( outval )
						
						# implement smooth key blending.. badly I might add :\
						
						if pos < 0.5 :
							if thiskeyobj.outmode == "S" :
								pos = smoothstep( pos, 0.0, 1.0 )
						elif pos >= 0.5 :
							if nextkeyobj.inmode == "S" :
								pos = smoothstep( pos, 0.0, 1.0 )
						
						result = getInterpolatedValue( thiskeyobj.outmode, nextkeyobj.inmode, inval, outval, pos )
						
						# print "RESULT!: " + str( result )
						
						#stresult = result
						# if self.curveType == types.ComplexType :
						#	stresult = str( result.real ) + "/" + str( result.imag )
						# elif self.curveType == types.FloatType :
						#	stresult = str( result )
						
						rez = result
					
					# print "keytime: " + str( key ) + " value: " + str( self.keyframes[ key ].value )
				
		elif len( self.keyframes ) > 0 :
			# then there is only one key.. just return that value
			keytimes = sorted( self.keyframes.keys() )
			rez = self.keyframes[ keytimes[0] ].value
		
		if self.curveType == types.IntType :
			# just need to coerce here coz the precision gets upped automatically sometimes
			return int( rez )
		else :
			return rez
		

def detectType( instring ) :
	
	if type( instring ) == types.StringType :
	
		# re.compile( "-{0,1}[0-9\.\-a-z]+/*-{0,1}[0-9\.\-e]*" )
		intTest = re.compile( "-{0,1}[0-9]+" )
		floatTest = re.compile( "-{0,1}[0-9]+\.[\-e0-9]+" )
		#floatTest = re.compile( "-{0,1}[0-9\.\-e]+" )
		strTest = re.compile( "[a-z]+[a-z0-9.]*" )
		
		#pity the foo that tries to put a slash inside a string or something similar..
		slashSplit = instring.split("/")
		
		if len( slashSplit ) > 1 :
			
			return ( types.ComplexType, complex( float( slashSplit[0] ), float( slashSplit[1] ) ) )
			
		elif floatTest.match( instring ) :
			
			return ( types.FloatType, float( instring ) )
			
		elif intTest.match( instring ) :
			
			return ( types.IntType, int( instring ) )
			
		elif strTest.match( instring ) :
		
			return ( types.StringType, instring )
			
		else :
			# print "whoops, using python 'eval' to establish the type of a value: " + instring +" this may cause trouble later!"
			val = eval( instring )
			return ( type( val ), val )
	else :
		return ( type( instring ), instring )

def getInterpolatedValue( inmode, outmode, inval, outval, position ) :
	
	powerPosition = smoothstep( 0.0, 1.0, position );
	intype = detectType( inval )
	outtype = detectType( outval )
	
	# print "IN: " + str( intype )
	# print "OUT: " + str( intype )
	
	# print "INmode: " + str( inmode ) + " type: "  + str( intype )
	# print "OUTmode: " + str( outmode )+ " type: " + str( outtype )
	
	
	if intype[0] == outtype[0] == types.ComplexType :
		
		return (1.0 - position) * intype[1] + position * outtype[1]
		
	elif intype[0] == outtype[0] == types.FloatType :
	
		return (1.0 - position) * intype[1] + position * outtype[1]
		
	elif intype[0] == outtype[0] == types.IntType :
	
		# make sure we round by adding 0.5
		
		return int( (1.0 - position) * intype[1] + position * outtype[1] + 0.5 )
		
	else :
		# we probably can't do the interpolation then at the mo..
		if position > 0.5 :
			return outtype[1]
		else :
			return intype[1]


# amp is now a list so that complex values can be amped separately in real and imag
def getSineOffsetValue( inval, position, freq, amp, phase ) :
	
	# position is in frames
	# and freq is actually to be interpreted as a loop length here.. bad variable nomenclature
	
	if len(amp) > 0 :
		if type( inval ) == types.ComplexType :
		
			realAmp = amp[0]
			imagAmp = amp[0]
			
			if len( amp ) > 1 :
				imagAmp = amp[1]
			
			sinz = math.sin( ( position + phase) / freq * math.pi * 2.0 ) * realAmp
			cosz = math.cos( ( position + phase) / freq * math.pi * 2.0 ) * imagAmp
			
			return inval + complex( sinz, cosz )
			
		elif type( inval )  == types.FloatType :
			
			sinz = math.sin( ( position + phase ) / freq * math.pi * 2.0 ) * amp[0]
			
			return inval + sinz
			
		elif type( inval ) == types.IntType :
			
			sinz = math.sin( ( position + phase ) / freq * math.pi * 2.0 ) * amp[0]
			return int( inval + sinz + 0.5 )
		#'bad luck if it is an integer or anything else I suppose'

		
def getAudioOffsetValue( inval, time, globals ) :
	
	wparams = globals.waveData.waveread.getparams()
	samplepos = int( time * float( wparams[2] ) )
	# samplepos = clamp( samplepos, 0, wparams[3] )
	
	
	# make it loop
	samplepos = samplepos % wparams[3]
	if samplepos < 0 :
		samplepos += wparams[3]
	
	print "Time is: " + str( time) + " samplepos is: " + str( samplepos ) + " nsamples is: " + str( wparams[3] )
	
	return inval
				
# ufLayerTagSet - essentially a set of aforementioned tags.. as in the groups in a UPR, somekinda tuple-mashing class

def clamp( val, minval, maxval ) :
	return max( minval, min( val, maxval ) )

class ufLayerTagSet:

	#set name, eg 'layer:', "inside:", etc
	tagSetName = ""
	
	# an array of tuples ( string, ufLayerTagValue )
	tagSet = []
	
	isAnimated = False
	
	def __init__( self, name, globals ) :
		self.tagSetName = name
		self.tagSet = []
		#print("created a new tag set with name: " + name )
		
	def addTagToSet( self, name, tag ) :
		self.tagSet.append( ( name, tag ) )
		if tag.isAnimated :
			self.isAnimated = True
	
	def setWithStringList( self, tagText, globals) :
		
		# print( "setWithStringList for tag sets called: " + str( self.tagSetName ) )
		self.tagSet = [] 
		newTagSet = ufLayerTagSet( self.tagSetName, globals )
		
		currentLine = 0		
		while currentLine < len( tagText ) :
			#print( "tagLine number is: " + str( currentLine ) )
			stripLine = tagText[ currentLine ].strip()
			
			
			if len(stripLine) > 0 and stripLine[-1] == ":" :
				print ("looks like a group label.. wierd " + str( stripLine ) )
			
			stripWhittle = stripLine
			
			firstEquals = stripWhittle.find( "=" )
			count = 0
			
			while firstEquals > 0 and count < 150:
			
				paramName = stripWhittle[ 0 : firstEquals ].strip()
				paramValue = ""
				# print("got first paramName: " + paramName )
				
				if stripWhittle[ firstEquals+1 ] == '"' :
					
					afterQuote = stripWhittle[ firstEquals+2 : ]
					#print( "afterQuote: " + afterQuote )
					stringEnd = afterQuote.find( '"' )
					#print("stringEnd: " + str( stringEnd ) )
					
					paramValue = '"' + afterQuote[ 0 : stringEnd ] + '"'
					stripWhittle = afterQuote[ stringEnd + 1 : ]
					
					#print( "got stringVal: " + paramValue )
				else :
					
					afterEquals = stripWhittle[ firstEquals + 1 : ]
					#
					#print("afterEquals: " + afterEquals )
					nextSpace = afterEquals.find( " " )
					if nextSpace > 0:
						paramValue = afterEquals[ 0 : nextSpace ]
					else :
						paramValue = afterEquals
						
					#print( "got otherVal nextSpace: " + str( nextSpace ) + " paramVal: " + str( paramValue ) )
					stripWhittle = afterEquals[ nextSpace + 1 : ]
				
				#print( "stripWhitle is now: " + stripWhittle )
				#print( "paramValue: " + paramValue )
				
				tag = ufLayerTagValue( globals )
				tag.setTagValue( paramValue, globals )
				
				if tag.isValid() :
					self.addTagToSet( paramName.strip(), tag )
					if tag.isAnimated : self.isAnimated = True
					# print ("uuiue added tag: " + paramName.strip() + " = " + tag.getAsString( globals ) )
					
				firstEquals = stripWhittle.find( "=" )
				count += 1
					
			currentLine += 1
			
		#self.tagSet.append(  newTagSet )
		
	def getAsString( self, globals  ) :
		wrap = globals.wrapWidth
		
		tagString = ""
	
		if len( self.tagSet ) > 0 :
		
			firstTagTuple = self.tagSet[0]
			
			#print( "tagtest: " + str( firstTagTuple ) )
			
			tagString = "  " + firstTagTuple[0] + "=" +  firstTagTuple[1].getAsString( globals )
			
			count = 1
			
			for tag in self.tagSet[1:] :
				
				if (count % wrap) != 0 :
					tagString += " " + tag[0] + "=" + tag[1].getAsString( globals )
				else :
					tagString += "\n  " +  tag[0] + "=" + tag[1].getAsString( globals )
				count += 1
					
		return  ( self.tagSetName +"\n" + tagString )
	
	def getValueOfTag( self, tagName ) :
		#BAD !!!
		for tag in self.tagSet :
			if tagName in tag[0] :
				return tag[1]
	
	def setValueOfTag( self, tagName, newValue, globals ) :
		#BAD !!! show us yer dic tyanairy man! :P
		#this doesn't fail if the tag doesnt exist !!
		for tag in self.tagSet :
			if tagName in tag[0] :
				tag[1].setTagValue( newValue, globals )
	
	def addAndSetValueOfTag( self, tagName, newValue, globals ) :
		#BAD !!! show us yer dic tyanairy man! :P
		foundTag = False
		for tag in self.tagSet :
			if tagName in tag[0] :
				tag[1].setTagValue( newValue, globals )
				foundTag = True
		if not foundTag : 
			newTagVal = ufLayerTagValue( globals )
			newTagVal.setTagValue( newValue, globals )
			self.addTagToSet( tagName, newTagVal )
				
	
	def getInterpolatedTagSet( self, targetTagSet, blendAmount, layerNumber, globals ) :
	
		#need to handle the layer: 'caption' tag a bit differently.. so that we get a new layerName
		#nah who cares.. still works.. polish for later
		newTagSet = ufLayerTagSet( self.tagSetName, globals )
		
		#l1s =  str( self.tagSet ) # .getAsString( globals )
		#l2s = str( targetTagSet.tagSet ) #.getAsString( globals )
		#print("\n\nL1S=\n" + l1s + "\n--------------\nL2S=\n" + l2s )
		#print("\n\nlenL1S=\n" + str(len(l1s)) + "\n--------------\nlenL2S=\n" + str(len(l2s)) )
		
		#tag, blendTag in zip( self.tagSet, targetTagSet.tagSet )
					
		for i in range( 0, min( len( targetTagSet.tagSet ), len( self.tagSet ) ) ) :
			
			#this is super dodgey.. if the tag doesn't exist on the other side.. create it and initialise to zero?
			#need to use a dictionary..
			
			tag = self.tagSet[ i ]
				
			blendTag = targetTagSet.tagSet[i]
			
			if globals.debugMode : print( "interpolating tag: " + str( tag[0] ) )
			
			if tag[0] != blendTag[0] :
				print("WARNING: tag name mismatch, might not interpolate properly: " + str( tag[0] ) + " to " + str( blendTag[0] ) )
			#else :
				#print("tag names match: " + str( tag[0] ) + " to " + str( blendTag[0] ) )
			
			interTag = None
			
			if self.tagSetName == "layer:" and tag[0] == "caption" :
				layerName = ( "inter_" + str( layerNumber ) )
				
				# print( "trying to interpolate the caption tag, new layername will be: " + layerName )
				interTag = ufLayerTagValue( globals )
				interTag.setTagValue( layerName, globals )
			else :
				interTag = tag[1].getInterpolatedTagValue( blendTag[1], blendAmount, globals )
				
			if interTag :
				newTagSet.addTagToSet( tag[0], interTag )
			else :
				print("No good, the interpolator gave back None..")
		
		#print("got interTagSet: " + str( newTagSet.getAsString( globals ) ) )
		#fingers crossed ;D
		return newTagSet
	
	
	def getTimeShiftedTagSet( self, offset, layerNumber, globals ) :
		newTagSet = ufLayerTagSet( self.tagSetName, globals )
		
		for i in range( 0, len( self.tagSet ) ) :
				
			tag = self.tagSet[ i ]
			
			#print( "time-shifting tag: " + str( tag[0] ) )
			
			intertag = None
			
			if self.tagSetName == "layer:" and tag[0] == "caption" :
			
				currName = tag[1].tagValue.strip().strip("\"")
				layerName = ( "\"" + currName + "_shift_" + str( layerNumber ) + "\"" )
				
				interTag = ufLayerTagValue( globals )
				interTag.setTagValue( layerName, globals )
			else :
				interTag = tag[1].getShiftedTagValue( offset, globals )
				
			if interTag :
				newTagSet.addTagToSet( tag[0], interTag )
			else :
				print("No good, the interpolator gave back None..")
		
		return newTagSet

# hermite smoothstep
def smoothstep( x, min, max ) :
	lx = 0.0
	
	if max > min :
		lx = float( x - min ) / float( max - min )
		
	elif min > max :
		lx = float( x - max ) / float( min - max )
		
	else : 
		# max must be equal to min
		lx = float( x > min )
	
	# standard hermite
	
	if x >= max :
		return 1.0
	elif x <= min :
		return 0.0
	else :
		return -2*lx*lx*lx + 3*lx*lx
		
class ufLayer :
	
	parsedOK = False
	#actually a list of 'ufLayerTagSet' objects
	tagSetList =[]
	# isBG = False
	isAnimated = False
	layerNumber = -1
	
	#blank constructor, for the interpolator
	def __init__( self, globals ) :
		self.parsedOK = False
		self.tagSetList = []
		# self.isBG = isBGLayer
	
	def setLayerWithStringList( self, layerText, globals, layerNum ) :
		
		self.layerNumber = layerNum
		# print( "\n\nlayerText is: " + str( layerText ) + "\n\n")
		
		if layerText and globals.isValid and len( layerText ) > 0 :
			tagSetList =[]
			
			currentLine = 1 #skip the known, 'layer' line, and start ready to grab it's params
			
			stripzero = layerText[ 0 ].strip()
			# print "stripLine zero is: " + stripzero
			tagSet = ufLayerTagSet( stripzero, globals )
			
			
			#tagSet.setWithStringList( layerText[ 1: ], globals )
			
			tagLines = []
			
			while currentLine < len( layerText ) :
				
				stripLine = layerText[ currentLine ].strip()
				#print( "stripLine is: " + stripLine )
				
				#line ends in a colon, special (screws comments tho)
				if stripLine[-1] == ':' :
				
					#add on last tagset
					if len( tagLines ) > 0 :
						tagSet.setWithStringList( tagLines, globals )
						if tagSet.isAnimated : self.isAnimated = True
						# print("got tagSet: \n\n" + str( tagSet.getAsString( globals ) ) + "\n\n")
					else :
						print("taglines was empty at an inopportune moment")
						
								
					self.tagSetList.append( tagSet )
					
					#print("new tag for line: " + stripLine )
					tagSet = ufLayerTagSet( stripLine, globals )
					tagLines = []
				else :
					tagLines.append( stripLine )
					
				currentLine += 1
								
			#append the last one too..
			tagSet.setWithStringList( tagLines, globals )
			if tagSet.isAnimated:
				self.isAnimated = True
			self.tagSetList.append( tagSet )
			self.parsedOK = True
		else :
			print(" layer parse parameter was invalid." )
	
	def addTagSetList( self, tagSet, globals ) :
		#if tagSet and tagSet.isValid() :
		self.tagSetList.append( tagSet )
		
		if tagSet.isAnimated :
			self.isAnimated = True
	
	# set the value of a tag in all tagsets in the layer
	
	def setTagValue( self, tagname, tagvalue, globals ) :
		for tagset in self.tagSetList :
			tagset.setValueOfTag( tagname, tagvalue, globals )
			if tagset.isAnimated :
				self.isAnimated = True
	
	def getAsString( self, globals, layerNum ) :
		self.layerNumber = layerNum
		returnStr = ""
		# returnStr +=( "there are: " + str( len( self.tagSetList ) ) + " tagSets in this layer.\n" )
		
		for tag in self.tagSetList :
			returnStr += tag.getAsString( globals ) + "\n"
			
		return returnStr
	
	def setLayerNumber( self, num ) :
		self.layerNumber = num
	
	def getInterpolatedLayer( self, interpTarget, globals, blendAmount, layerNum ) :
		
		#print( "interlayer layerNumber: " + str( layerNum ) )
		
		# let this layer be the template for what tagSets are added to the interlayer
		#actually they need to be exactly the same at the moment to work.. hmm will eventualy fix that
		
		#the 'False' just says this layer is NOT the bg layer
		interLayer = ufLayer( globals ) 
		interLayer.layerNumber = layerNum
		
		for tag, blendTag in zip( self.tagSetList, interpTarget.tagSetList ) :
			
			if len( tag.tagSet ) != len( blendTag.tagSet ) :
				print( "\nWARNING! different number of tags on the two interpolating layers!!! this probably means it won't work like expected!!")
				print( "    please make sure all interpolating parameters are changed from their default value (eg try changing 0 to 0.0000000001)\n" )
			
			interLayer.addTagSetList( tag.getInterpolatedTagSet( blendTag, blendAmount, layerNum, globals ), globals )
			
		return interLayer
	
	def getTimeShiftedLayer( self, globals, factor, layerNum ) :
		
		interLayer = ufLayer( globals ) 
		interLayer.layerNumber = layerNum
		
		shift = (factor - 0.5) * globals.shutterLength + globals.shutterOffset
		
		# print "computing layer time-shifted by: " + str( shift )
		
		for tag in self.tagSetList :		
			interLayer.addTagSetList( tag.getTimeShiftedTagSet( shift, layerNum, globals ), globals )
			
		return interLayer
		
		
	#this doesn't work unless there is one.. of course
	def getCaptionString( self ) :
		layerTagSet = self.tagSetList[0]
		return layerTagSet.getValueOfTag( "caption" ).tagValue
	
	def isValid( self ) :
		return self.parsedOK



class uprFractal :
	# topText - a special chunk of text for the top bit of the UPR and the 'fractal' tag
	# which I dont currently want to change at all.. so it will be preserved intact..
	# okay I take that back, I definately do need to change the 'layers' parameter!! :P
	
	topText = []
	comments = []
	topTagSet = None
	layerTags = []
	parsedOK = False
	
	groupTree = None
	
	# an array of ufLayer
	layers = []
	
	def __init__( self ) :
		# print("uprFractal konstruktor!" )
		self.layers = []
		self.topText = []
		self.comments = []
		self.topTagSet = None
		self.layerTags = []
		
	def parseUPRText( self, globals, stringList ) :
		
		self.layers = []
		
		if stringList :
			currentLine = 0
			firstBitDone = False
			breakTag = "layer:"
			
			while not firstBitDone and currentLine < len( stringList ) :
				#print("currentLine is: " + str( currentLine ) )
				
				strippedLine = stringList[ currentLine ].strip()
				# print "strippedLine is: " + strippedLine
				
				if strippedLine != "layer:" and strippedLine != "group:" :
					#don't add blank lines
					if  strippedLine.strip()[0] != ";" :
						if len( strippedLine ) > 1 : self.topText.append( stringList[ currentLine ].strip() )
					else : 
						self.comments.append( stringList[ currentLine ].strip() )
						if globals.verboseMode : print "found comment line: " + strippedLine
				else :
					breakTag = strippedLine
					self.topTagSet = ufLayerTagSet( "fractal:", globals )
					
					fracTagTextSlice = self.topText[ 2: ]
					if globals.debugMode :  print "fracTagTextSlice is: " + str( fracTagTextSlice )
					
					self.topTagSet.setWithStringList( fracTagTextSlice, globals )
					
					if globals.verboseMode : print("got Fractal : \n\n" + self.topTagSet.getAsString( globals ) + "\n" )
					firstBitDone = True
				
				currentLine += 1
			
			if globals.verboseMode: print( "got 'topBit'\n---->\n" + "\n".join( self.topText ) + "\n<----")
			
			#increment to enter the layer, so we dont bail out on the first while below
			#currentLine += 1
			
			layersDone = False
			
			while not layersDone and currentLine < len( stringList ) :
			
				nextLayer = False
				layerSet = [ breakTag + "\n", ]
				
				while not nextLayer and currentLine < len( stringList ):
				
					linestrip = stringList[ currentLine ].strip()
					
					if linestrip == "layer:" or linestrip == "group:":
					
						nextLayer = True
						breakTag = linestrip
						
					elif linestrip == "}" :
					
						if globals.verboseMode : print( "end of UPR found on line: " + str( currentLine + 1 ) )
						nextLayer = True
						layersDone = True
						
					else :
						
						layerSet.append( stringList[ currentLine ] )
					
					currentLine += 1
				
				#print( "got supposed layerSet: \n--------->" + "--------->".join( layerSet ) )
				self.layerTags.append( layerSet )
			
			if globals.verboseMode : print("looks like there were " + str( len( self.layerTags ) ) + " layers in that UPR" )
			
			# if globals.verboseMode : print("new UPR will contain: " + str( globals.numExtraLayers + globals.numExistingLayers ) + " layers total" )
			
			globals.numExistingLayers = len( self.layerTags )
			
			isLastCount = 0
			
			for layerText in self.layerTags :
			
				#print( "\n\nlayer text: " + str( layerText ) )
				
				#make this take all but the first two layers as BG, if in interpolate mode, if in anim mode, just the last layer is the BG
				
				isLastCount += 1
				layerParse = ufLayer( globals )
				
				layerNum =  isLastCount - 1
				
				#if isBG : 
				#	layerNum = globals.numExtraLayers + globals.numExistingLayers - 1
					# print( "isBG! layerNum is: " + str( layerNum ) )
					
				# isBG = False
				
				layerParse.setLayerWithStringList( layerText, globals, layerNum )
				
				#print( "\n\nparsed layer text: " + layerParse.getAsString( globals, isLastCount ) )
				
				if layerParse.isValid() :
					self.layers.append( layerParse )
					# if globals.verboseMode : print( "parsed and added layer: " + str( layerParse.getCaptionString() ) + " number: " + str( isLastCount - 1 ))
				else :
					print( "could not parse layer text: " + str( layerText ) )
					
			self.parsedOK = True
			return self
		
	def addStringToFractalName( self, addstr, globals ) :
		 
		 currentName = self.topTagSet.getValueOfTag( "title" ).getAsString( globals ).strip( '"' )
		 
		 newname = ( currentName + addstr )
		 
		 self.topTagSet.setValueOfTag( "title", newname , globals )
		 
		 if globals.verboseMode : 
		 	print( "changed fractal title to: " + newname )
		 	
	def setFractalName( self, newname, globals ) :
		 self.topTagSet.setValueOfTag( "title", newname , globals )
		 if globals.verboseMode : 
		 	print( "changed fractal title to: " + newname )
	
	def getAsString( self, globals ) :
		#print("YO!-------------------------------------------")
		
		outStr = globals.outFractalName
		
		outSplit = globals.outFileName.split(".")
		
		#if len( outSplit ) > 1 :
		#	outStr = ".".join( outSplit[ :-1] )
			
		if globals.verboseMode:  print "BIFFF! " + outStr
			
		result = outStr + " {\n"
		result += "\n".join( self.comments )
		result += "\n"
		# self.topText[0] + "\n"
		
		#collect everything from here to the end and compress it
		
		self.topTagSet.setValueOfTag( "layers", str( globals.totalNumLayers ) , globals )
		
		
		layersValue = self.topTagSet.getValueOfTag( "layers" )
		
		#print( "set layersValue: " + str( layersValue.getAsString( globals ) ) )
		
		result += self.topTagSet.getAsString( globals ) + "\n"
		
		#result += "\n---\n"
		#print("there are " + str( len( self.layers ) ) + " layers" )
		
		result += self.groupTree.getAsString( globals )
		
		#count = 0
		#for layer in self.layers :
		#	result += layer.getAsString( globals, count )
		#	count += 1
			#result += "\n---\n"
			
		result += "}\n"
		
		return result
		
	def addExtraLayers( self, globals ) :
		
		# print "\nAdding Extra Layers..."
		rampLength = globals.numExtraLayers + 1
			
		newlayers = [ ]
		
		self.groupTree = ufGroupTree()
		
		if globals.verboseMode: print "numLayers: " + str( len ( self.layers ) )
		
		if globals.interleave :
			count = 0
			print "doing interleaved layers: "
			
			for i in range( 1, rampLength ) :
				factor = float( i-1 ) / float ( rampLength - 2 )
				interpos = float( i - 1 ) / float ( rampLength - 2 )
				
				#interLayer = layer.getTimeShiftedLayer( globals, factor, i )
				
				rampLen = int( globals.opacityRampLength * float( rampLength ) * 0.5)
				layerOpac = globals.newLayerOpacity
				
				# set opacity and mergemode stuff
				
				#for tag in interLayer.tagSetList :
				#	if tag.tagSetName == "layer:" : 
						
				finalOpac = 1.0
				
				if rampLen > 0 : 
					opacRampUp = smoothstep( interpos, 0, globals.opacityRampLength )
					opacRampDown = 1.0 - smoothstep( interpos, 1.0 - globals.opacityRampLength, 1.0 )
					finalOpac = opacRampUp * opacRampDown
				# layerOpac = max( 1, int( float( layerOpac ) * finalOpac ) + 1 )
				
				#if globals.verboseMode : 
				#	print( "InterOpac: " + getIntAsStarsStr( layerOpac, 60 ) )
					
				for layer in self.layers :
					layerType = layer.tagSetList[0].tagSetName
					layername = layer.tagSetList[0].getValueOfTag( "caption" ).tagValue.lower().strip().strip("\"")
					
					if layerType == "group:":
						#print "layer is a group: " + layername
						opac = None
						
						if layer.isAnimated : 
							#print "found an animated group!"
							
							copac = layer.tagSetList[0].getValueOfTag( "opacity" ).tagValue
							
						 	#print "currOpac for group is: " + str( copac )
														
							currOpac = float( copac ) / 100.0
							#print "currOpac for group is: " + str( currOpac )
							
							layerOpac = max( 1, int( float( layerOpac ) * finalOpac * currOpac ) + 1 )
									
							#print "setting group opacity: " + str( layerOpac )
							
							opac = layerOpac
							#layer.tagSetList[0].setValueOfTag( "opacity", str( layerOpac ) , globals )
							sv = layer.tagSetList[0].getValueOfTag( "opacity" ).tagValue
							#print "SET group opacity: " + str( sv )
							
						numItems = int( layer.tagSetList[0].getValueOfTag( "items" ).tagValue )
						groupName = layer.tagSetList[0].getValueOfTag( "caption" ).tagValue
						
						self.groupTree.addGroup( layer, numItems, groupName, opac )
						
					elif layerType == "layer:" :
						
						nametest = ""
					
						if len( layername ) >= 10 :
							nametest = layername[ 0:10 ]
							# print "layer name test is: " + nametest
						
						if  nametest == "background" and globals.ignoreBG:
							# print "detected a background layer."
							# layer.isBG = True
							
							if i == rampLength-1 :
								self.groupTree.addItem( layer )
								newlayers.append( layer )
						elif nametest == "foreground" and globals.ignoreBG:
							if i == 1:
								self.groupTree.addItem( layer )
								newlayers.append( layer )
						else :
							if layer.isAnimated :
								#if self.groupTree.currGroup :
								#	currGroupSize = self.groupTree.currGroup.numItems
								interLayer = layer.getTimeShiftedLayer( globals, factor, i )
								
								for tag in interLayer.tagSetList :
									if tag.tagSetName == "layer:" :
										
										currOpac = float( tag.getValueOfTag( "opacity").tagValue ) / 100.0
										# print "currOpac is: " + str( currOpac )
										layerOpac = max( 1, int( float( layerOpac ) * finalOpac * currOpac ) + 1 )
										
										if globals.verboseMode : 
											print( "InterOpac: " + getIntAsStarsStr( layerOpac, 60 ) )
					
										tag.setValueOfTag( "opacity", str( layerOpac ) , globals )
										# go through the list that is formed.. this allows alternating layermode patterns
										# if there is no mergemode set, just use the original one
										
										if len( globals.newLayerMode ) > 0 :
											layerNumMod = i % len( globals.newLayerMode )
											print( "interleaved layerNumber: " + str( i ) + " numModes: " + str( len( globals.newLayerMode ) ) )
											if layerNumMod < 0 : layerNumMod = 0
											mergemode = globals.newLayerMode[ layerNumMod ]
											# print "setting mergemode: " + mergemode
											if mergemode: 
												tag.addAndSetValueOfTag( "mergemode", mergemode, globals )
								
								newlayers.append( interLayer )
								self.groupTree.addItem( interLayer )
								# print "interpos: " + str( interpos )
									
							else : # layer is not animated, just append
								newlayers.append( layer )
								self.groupTree.addItem( layer )
						
		else: #non-interleaved mode
			
			for layer in self.layers :
				
				# print "doing layer: " + str( layer.tagSetList[0].getValueOfTag( "caption" ).tagValue )
				layerType = layer.tagSetList[0].tagSetName
				
				# print "layerType: " + str( layerType )
				layername = layer.tagSetList[0].getValueOfTag( "caption" ).tagValue.lower().strip().strip("\"")
				
				if layerType == "group:" :
					
					numItems = int( layer.tagSetList[0].getValueOfTag( "items" ).tagValue )
					groupName = layer.tagSetList[0].getValueOfTag( "caption" ).tagValue
					
					self.groupTree.addGroup( layer, numItems, groupName, None )
					
					newlayers.append( layer )
					
				elif layerType == "layer:" :
				
					# print "layerName lower: " + layername
					nametest = ""
					
					if len( layername ) >= 10 :
						nametest = layername[ 0:10 ]
						# print "layer name test is: " + nametest
						
					if  nametest == "background" and globals.ignoreBG:
						
						# print "detected a background layer."
						# layer.isBG = True
						self.groupTree.addItem( layer )
						newlayers.append( layer )
							
					else :
						if layer.isAnimated :
							if self.groupTree.currGroup :
								currGroupSize = self.groupTree.currGroup.numItems
								self.groupTree.currGroup.numItems = currGroupSize + rampLength - 2
								
							for i in range( 1, rampLength ) :
								
								factor = float( i-1 ) / float ( rampLength - 2 )
								# print "factor: " + str( factor )
								interpos = float( i - 1 ) / float ( rampLength - 2 )
								
								interLayer = layer.getTimeShiftedLayer( globals, factor, i )
								
								rampLen = int( globals.opacityRampLength * float( rampLength ) * 0.5)
								layerOpac = globals.newLayerOpacity
								
								# set opacity and mergemode stuff
								
								for tag in interLayer.tagSetList :
									if tag.tagSetName == "layer:" : 
										finalOpac = 1.0
										if rampLen > 0 : 
											opacRampUp = smoothstep( interpos, 0, globals.opacityRampLength )
											# print("layernum: " + str( self.layerNumber ) + " totalnum: " + str( totalNumLayers ) )
											opacRampDown = 1.0 - smoothstep( interpos, 1.0 - globals.opacityRampLength, 1.0 )
											finalOpac = opacRampUp * opacRampDown
										
										# if globals.verboseMode : print("opacRamp: " + getFloatAsStarsStr( finalOpac, 1.0, 60 ) )
										currOpac = float( tag.getValueOfTag( "opacity").tagValue ) / 100.0
										
										layerOpac = max( 1, int( float( layerOpac ) * finalOpac * currOpac) + 1 )
									
										if globals.verboseMode : 
											print( "opac: " + getIntAsStarsStr( layerOpac, 60 ) )
											
								
										tag.setValueOfTag( "opacity", str( layerOpac ) , globals )
										# go through the list that is formed.. this allows alternating layermode patterns
										
										# if there is no mergemode set, just use the original one
										if len( globals.newLayerMode ) > 0 :
										
											layerNumMod = i % len( globals.newLayerMode )
											print( "layerNumber: " + str( i ) + " numModes: " + str( len( globals.newLayerMode ) ) )
											if layerNumMod < 0 : layerNumMod = 0
										
											mergemode = globals.newLayerMode[ layerNumMod ]
											print "setting mergemode: " + mergemode
											
											if mergemode: 
												tag.addAndSetValueOfTag( "mergemode", mergemode, globals )
								
								newlayers.append( interLayer )
								self.groupTree.addItem( interLayer )
								# print "interpos: " + str( interpos )
								
						else : # layer is not animated
							newlayers.append( layer )
							self.groupTree.addItem( layer )
											
						
						#newlayers.append( layer )
						#self.groupTree.addItem( layer )		
						
						# should check that the layer has animation here...
			
			#print "generated : " + str( len( newlayers ) ) + " layers."
		
		if globals.verboseMode: self.groupTree.printTree()
		
		#treeString = groupTree.getAsString( globals )
		
		# print "TREE STRING: \n" + treeString + "\n\n"
		
		self.layers = newlayers
		
		globals.totalNumLayers = len( self.groupTree.ungroupedItems )
		
		if globals.verboseMode: print "final number of ungrouped layers is : " + str( len( self.groupTree.ungroupedItems ) ) + "."

class ufGroup :
	
	groupLayer = None
	numItems = 0
	opac = None
	itemList = None
	depth = 0
	isComplete = False
	parentGroup = None
	groupName = None
	
	def __init__( self, groupLayer, numItems, groupName, parentGroup, opacity ) :
		
		self.groupLayer = groupLayer
		self.numItems = numItems
		self.opac = opacity
		self.itemList = []
		self.parentGroup = parentGroup
		if parentGroup :
			self.depth = parentGroup.depth + 1
		else :
			#init depth at 1
			self.depth = 1
		self.groupName = groupName
		
		# print "new group: " + groupName + " of " + str( numItems ) + " items, at depth:  " + str( self.depth )
		
		if self.numItems == 0 :
			self.isComplete = True
	
	def addItem( self, item ) :
	
		# print "ADD ITEM: " + str( item )
		
		if len( self.itemList ) < self.numItems :
			
			self.itemList.append( item )
			
			# print "group has: " + str( len( self.itemList ) ) + " of " + str( self.numItems ) + " items."
			
			if len( self.itemList ) == self.numItems :
				self.isComplete = True
				# print "Finished filling group: " + self.groupName
		else :
			self.isComplete = True
			# print "tried to add an item to a full group: " + self.groupName
	
	def addSelfToParentRecursive( self ) :
		if self.isComplete :
			if self.parentGroup != None :
				self.parentGroup.addItem( self )
				if self.parentGroup.isComplete :
					return self.parentGroup.addSelfToParentRecursive()
				else : return self.parentGroup
			else : return None
		else : return self
	
	def printGroup( self ) :
		parentName = None
		
		if self.parentGroup :
			parentName = self.parentGroup.groupName
			
		depthStr = " " * self.depth * 4
		print depthStr + "[ Group: " + self.groupName + " of " + str( self.numItems ) + " items"
		#, and parent: " + str( parentName )
		
		for item in self.itemList :
			if isinstance( item, ufGroup ) :
				item.printGroup()
			elif isinstance( item, ufLayer ) :
				depthStr = " " * ( self.depth + 1 ) * 4
				
				print depthStr + "> " + item.getCaptionString( )
				# + " anim: " + str( item.isAnimated )
	
	
	def getAsString( self, globals ) :
		self.groupLayer.setTagValue( "items", str( self.numItems ), globals )
		if self.opac : self.groupLayer.setTagValue( "opacity", str( self.opac ), globals )
		
		result = self.groupLayer.getAsString( globals, 0 )
		count = 0
		
		for item in self.itemList :
			
			if isinstance( item, ufGroup ) :
				result += item.getAsString( globals )
				
			elif isinstance( item, ufLayer ) :
			
				result +=  item.getAsString( globals, count )
				# result += "\n"
				
		return result

class ufGroupTree :
	
	ungroupedItems = []
	groups = []
	
	groupDepth = 0
	currGroup = None
	
	def __init__( self ) :
		self.ungroupedItems = []
		self.groups = []
		self.groupDepth = 0
		self.currGroup = None
	
	def addGroup( self, groupItem, numItems, groupName, opacity ) :
		
		parent = None
		if self.groupDepth > 0 :
			parent = self.currGroup
			
		newGroup = ufGroup( groupItem, numItems, groupName, self.currGroup, opacity )
		
		if self.groupDepth == 0 and self.currGroup == None:	
			self.ungroupedItems.append( newGroup )
		
		if newGroup != None:
		
			if newGroup.isComplete :
			
				# print "new group: " + groupName + " is already complete... must be an empty group."
				
				if self.currGroup :
					self.currGroup.addItem( newGroup )
					if self.currGroup.isComplete :
						next = self.currGroup.addSelfToParentRecursive()
						
						if next == None :
							# print "EGRP back to Root.."
							# self.ungroupedItems.append( self.currGroup )
							self.currGroup = None
							self.groupDepth = 0
						else :
							self.currGroup = next
							self.groupDepth = next.depth
							# print "EGRP back to depth: " + str( next.depth )
					
				# print "depth is now: " + str( self.groupDepth )
			else :
				#group will be added on completion
				self.currGroup = newGroup
				self.groupDepth = self.currGroup.depth
		
	
	def addItem( self, item ) :
		# print "TREE ADD ITEM, groupDepth: " + str( self.groupDepth )
		
		if self.groupDepth > 0 and self.currGroup != None:
		
			# print "got currGroup: " + str( self.currGroup.groupName )
			
			self.currGroup.addItem( item )
			
			name = self.currGroup.groupName	
				
			if self.currGroup.isComplete :
			
				# print "item appears to have completed the group: " + name + ", adding it to parent.."
				
				next = self.currGroup.addSelfToParentRecursive()
				
				if next == None :
					# print "back to Root.."
					# self.ungroupedItems.append( self.currGroup )
					self.currGroup = None
					self.groupDepth = 0
				else :
					self.currGroup = next
					self.groupDepth = next.depth
					# print "back to depth: " + str( next.depth )
					
			# print ".. now at depth: " + str ( self.groupDepth )
			
		else :
			# print "groupDepth is zero, adding item at root.. "
			self.ungroupedItems.append( item )
			
	def printTree( self ) :
		print "UF LAYER GROUP TREE KILLING PUUUNCH!!!"
		print "|"
		for item in self.ungroupedItems :
			
			#print "is a uflayer: " + str( isinstance( item, ufLayer ) )
			#print "is a ufGroup: " + str(  )
			
			if isinstance( item, ufGroup ) :
				item.printGroup()
			elif isinstance( item, ufLayer ) :
				print "> " + item.getCaptionString( )
				# + " anim: " + str( item.isAnimated )
	
	def getAsString( self, globals ) :
		result = ""
		count  = 0
		for item in self.ungroupedItems :
			
			if isinstance( item, ufGroup ) :
				result += item.getAsString( globals )
				# result += "\n"
				
			elif isinstance( item, ufLayer ) :
				result += item.getAsString( globals, count )
				# result += "\n"
		
		return result

class uprParse :
	# an array of uprFractal
	fractals = []
	parsedOK = False
	
	def __init__( self ) :
		#print("uprParse konstruktor!" )
		self.parsedOK = False
	
	def getFractal( self, which ) :
		return self.fractals[ which ]
	
	def loadAndParseUPRText( self, globals ) :
		
		inFileName = os.path.join( globals.sourcePath, globals.inFileName )
		
		chunks = []
		
		if os.path.isfile( inFileName ) :
			
			inFileHandle = open( inFileName, "r" )
			
			#if globals.verboseMode : print("got open UPR file for reading: \n" + str( inFileHandle ) )
			
			stringList = None
				
			if inFileHandle :
				stringList = inFileHandle.readlines()
				
				if globals.debugMode :
					print( "\ninput UPR: -------------------->" )
					for f in stringList :
						print f.strip( "\n" )
					print( "<--------------------\n" )
			else :
				print("error opening file.. perhaps you don't have read permissions? (chmod +r)")
			
			if globals.verboseMode : print("got " + str( len( stringList ) ) + " lines from UPR file")
			
					
			if stringList :
				
				currentLine = 0
				currentChunk = 0
				inChunk = False
				chunk = [ ]
				dictmap = {}
				joinLine = False
				
				while currentLine < len( stringList ) :
					
					# print("currentLine is: " + str( currentLine ) )
					# print("currentChunk is: " + str( currentChunk ) )
					
					#could cater for ignoring comment blocks here..
					
					strippedLine = stringList[ currentLine ].strip()
					
					if "{" in strippedLine :
						currentChunk += 1
						# print "fractal count is now: " + str( currentChunk )
						inChunk = True
					
					if inChunk :
						if joinLine :
							# print "JOINING: " + chunk[-1] + " and " + strippedLine
							
							lastLine = chunk[-1]
							chunk[-1] = lastLine.strip().strip("\\") + strippedLine.strip().strip("\\")
							
							# print "JOINED RESULT: " + chunk[-1]
							
						else :
							chunk.append( strippedLine )
					
					if len( strippedLine ) > 1 and strippedLine[-1] == "\\" :
						# print "detected a multi-line line: " + strippedLine
						joinLine = True
					else :
						joinLine = False
					
					
					if stringList[ currentLine ].strip() == "}" :
						#if globals.verboseMode : print( "end of chunk found on line: " + str( currentLine + 1 ) )
						chunks.append( chunk )
						# print "appended chunk: " + str( chunk )
						chunk = [ ]
						inChunk = False
					
					currentLine += 1
			
			#print "got " + str( len( chunks ) ) + " chunks: " + str( chunks )
			
			if globals.verboseMode: print "got " + str( len( chunks ) ) + " fractals"
			
			if globals.verboseMode:  print "selected fractal: " + str( globals.selectedFractal + 1 )
			
			#print "parseing fractal: " + str( chunks[ globals.selectedFractal ] )
			
			# detect an encoded/compressed chunk (first two characters are colon '::')
			# uninterleave the bytes, as per Fred's advice, then decode
			# FredSays: They are base64-encoded, but I made an error here and reversed the first and third bytes of each triplet (if I remember correctly). So any off-the-shelf base64 code won't work. After decoding, the entry starts with a 4-byte CRC value, and then zlib-compressed UPR data.
			
			#need to handle and discard comments too
			
			selectedFractal = checkAndDecompress( chunks[ globals.selectedFractal ] )
			
			# print "SELFRAC: \n\n" + "\n".join( selectedFractal ) + "\n\n"
			
			afrac = uprFractal().parseUPRText( globals, selectedFractal )
			self.fractals.append( afrac )
			self.parsedOK = afrac.parsedOK
		else :
			print( "specified file does not exist: " + str( inFileName ) )
		

def checkAndAddExt( filename, globals ) :
	if len( filename ) > 4 :
		extCheck = filename[ -4: ]
		
		if  str.lower( extCheck ) != ".upr" :
			if globals.verboseMode : print( "extCheck added upr extension: " + (filename + ".upr") )
			return filename + ".upr"
		else : 
			return filename
	else : #not possible to contain the entire string anyway, so add it
		if globals.verboseMode : print( "extCheck added upr extension: " + (filename + ".upr") )
		return filename + ".upr"

def getBasePath() :
	basepath = sys.path[0]
	
        if len( basepath ) > 4 :
        	if basepath[-4:].lower() == ".zip" :
        		# print "basepath is a zip file! must be in py2exe.. "
        		basepath = os.sep.join( basepath.split( os.sep )[:-1] )
        		# print "chopped off the last part of the path: " + basepath
        		
        return basepath	

def localToFwdSlashesAll( onstr ) :
	frontToBack = os.sep.join( onstr.split("/") )
	backToFront = "/".join( frontToBack.split( os.sep ) )
	return backToFront

def fwdToLocalSlashesAll( onstr ) :
	backToFront = "/".join( onstr.split( os.sep ) )
	frontToBack = os.sep.join( backToFront.split("/") )
	return frontToBack

class ufParaMashGlobals :
	
	aboutStr = "uprMash:  An experiment in plaintext UPR file mashing. This tool has helped to achieve fractal-motion composite effects in ultraFractal. Some of the experiments are on the web to check out. Written in python by Dan Wills, 2006-2008"
			
	helpStr = ("\n------------------------------------\n\n",
			"\tuprMash.py\n"
			"\t\tA little experiment in plaintext UPR file mashing\n",
			"\t\tTo help achieve various interpolation effects\n",
			"\t\tWritten by Dan Wills, 2006\n\n",
			"\tUsage:\n",
			"\t\tufParaMash -u inFile.upr -o outFile.upr <other flags>\n\n",
			"\tOther Flags:\n\n",
			
			"\t\t-i or --info\n\n",
			"\t\t\tinfo mode :\n",
			"\t\t\tthis prints the UPR and some other info\n\n",
			
			"\t\t-d or --debug\n\n",
			"\t\t\tdebug mode :\n",
			"\t\t\tprint even more info\n\n",
			
			"\t\t-h or --help\n\n",
			"\t\t\thelp mode :\n",
			"\t\t\tprint what you're currently reading\n\n", 
			
			"\t\t-u or --uprfile <FILENAME.upr>\n\n",
			"\t\t\tset input UPR filename :\n",
			"\t\t\tcan be specified without extension\n\n", 
			
			"\t\t-o or --outputfile <FILENAME.upr>\n\n",
			"\t\t\tset output UPR filename :\n",
			"\t\t\tupr extension will be added if not specified\n\n",
			
			"\t\t-l or --layers <INTEGER>\n\n",
			"\t\t\tnum layers :\n",
			"\t\t\tset the number of interpolating layers to generate\n\n",
			
			"\t\t-f or --force\n\n",
			"\t\t\toverwrite mode :\n",
			"\t\t\tallow overwriting existing files\n\n", 
			
			"\t\t-p or --opacity\n\n",
			"\t\t\tset opacity <INTEGER>:\n",
			"\t\t\tset the opacity of ALL layers\n\n", 
			
			"\t\t-m or -layermode\n\n",
			"\t\t\tset layermode <UFMERGEMODE>:\n",
			"\t\t\tset the layermode (mergemode) for all layers\n\n",
			"\t\t\tmultiple layermode flags may be specified\n",
			"\t\t\tand they will be cycled through accross the layers\n\n",
			"\t\t\teg: normal, multiply, screen, \n",
			"\t\t\tsoftlight, hardlight, darken, lighten, \n",
			"\t\t\tdifference, hue, saturation, color,\n",
			"\t\t\tluminance, addition, hsladd, red, green, blue\n\n",
			
			"\t\t-r or -rampopacity <FLOAT>\n\n",
			"\t\t\tset length of opacity ramp:\n",
			"\t\t\tas a fraction of the entire range (0.0,1.0) \n"
			"\t\t\tfade in and out the opacity accross \n",
			"\t\t\tthe interpolated range (like a camera shutter)\n\n",
			
			"\t\t-g or --gui\n\n",
			"\t\t\tstart in gui mode (EXPERIMENTAL!)\n\n",
			
			"\t\t-b or --dobackground\n\n",
			"\t\t\tenable setting opacity and layermode on BG layers\n",
			
			"\n\tExample:\n\n",
			"\t./uprMash.py -v -f -i infile.upr -o outfile.upr\n",
			"\t-l 105 -p 14 -m multiply -m screen -r 0.7\n",
			"\n------------------------------------\n\n" )
			
			# "outputfile=", "uprfile=","layers=","force","opacity=","layermode=
	
	
	configFile = "uprMash.config"
	sourcePath = "./"
	preStr = ""
	infoMode = False
	debugMode = False
	verboseMode = True #for the moment!
	#inFileName = "paraMashInput.upr"
	inFileName = ""
	inWavName = ""
	waveData = None
	
	inFractalName = "untitled fractal"
	inFileLines = None
	outFileName = "uprMashOutput.upr"
	outFractalName = "untitled fractal"
	outFileAlreadyExists = True
	forceOverwrite = False
	isValid = True #for now
	wrapWidth = 4
	numExistingLayers = 0
	numExtraLayers = 16
	totalNumLayers = 16
	newLayerOpacity = 52
	opacityRampLength = 0.35
	ready = False
	newLayerMode = [ ]
	interpMode = [ "" ]
	ignoreBG = False
	animMode = False
	resampleCurves = True
	
	shutterOffset = 0
	shutterLength = 62
	fps = 30
	
	interleave = False
	frameRange = ""
	
	animFreq = 100.0
	animAmp = "0.0, 0.0"
	animPhase = 0.0
	useAudio = False
	
	
	guiMode= False
	fractalNames = [ "untitled" ]
	selectedFractal = -1
	
	
	def setInFileName( self, fname ) :
		fname = checkAndAddExt( localToFwdSlashesAll( fname ), self )
		try:
			if fname and os.path.isfile( fname ) :
				# if self.verboseMode :
					# print( "got valid inFileName: " + str( fname ) )
				
				
				self.inFileName = fname
				
				self.ready = True
			else :
				# print("looks like an invalid input filename was specified... please make sure the file is definately there and that you have permissions to read it.")
				pass
				# self.inFileName = "None"
		except :
			print("\n!!!!!!\nerror opening file: " + str( fname ) + " perhaps you don't have read permissions? (chmod +r)\n")
	
	def setWavFileName( self, fname ) :
		
		# fname = checkAndAddExt( fname, self )
		fname = localToFwdSlashesAll( fname )
		
		try:
			if os.path.isfile( fname ) :
				
				if self.verboseMode :
					print( "got valid inFileName: " + str( fname ) )
					
				self.inWavName = fname
				#self.ready = True
			else :
				# print("looks like an invalid input filename was specified... please make sure the file is definately there and that you have permissions to read it.")
				print("looks like an invalid input wav filename was specified... please make sure the file is definately there and that you have permissions to read it.")
				# self.inWavName = "None"
				
		except :
			print("\n!!!!!!\nerror opening file: " + str( fname ) + " perhaps you don't have read permissions? (chmod +r)\n")
	
	def loadAuxData( self ) :
		
		# print"loading WAV if poss: " + str( self.inWavName )
		
		if os.path.isfile( self.inWavName ) and self.useAudio :
			
			if self.verboseMode : print "Loading wav file data (this may take a while)..."
			
			self.waveData = wavReader.wavdata( wave.open( self.inWavName, 'r' ) )
				
			if self.verboseMode :
					
				print("wav info:         %s"% self.inWavName )
				wparams = self.waveData.waveread.getparams()
				print("n channels:       %s"%wparams[0])
				print("sample width:     %s"%wparams[1])
				print("frame rate:       %s"%wparams[2])
				print("n frames:         %s (%0.3f secs.)"%( wparams[3], wparams[3] / float(wparams[2] ) ) )
				print("compression type: %s"%wparams[4])
				print("compression name: %s"%wparams[5])
			
				if self.verboseMode : print("creating wavdata .. ")
			
				# if self.verboseMode: print(".. done. Now resampling wave data, please wait")
				
			#print "getting resized wavData: " + str( 
			#newData = self.waveData.getResampledWavdata( 150, True )
			
			#for smp in newData :
			#	stars = getFloatAsStarsStr( math.fabs( smp[0] - smp[1] ), 1.0, 60 )
				# print "wave" + stars
			
	def setInFractalNumber( self, number ) :
		self.selectedFractal = number
		
	def setOutFileName( self, fname ) :
		if fname :
			fname = checkAndAddExt( fname, self )
		
			if os.path.isdir( fname )  :
				if __self.verboseMode : 
					print( "output file is a directory, wierd.. don't write anything? or write to the inFileName in the dir?" )
					print("checking if the infilename: " + str(self.inFileName) + " exists in the dir..")
					self.outFileName = os.path.join( fname, self.inFileName )
					if os.path.isfile( self.outFileName ) :
						self.outFileAlreadyExists = True
					else :
						self.outFileAlreadyExists = False
			elif os.path.isfile( fname ) :
				# if self.verboseMode : 
					# print( "output file already exists! no output will be written unless in force mode!" )
				self.outFileName = fname
				self.outFileAlreadyExists = True
			else :
				self.outFileName = fname
				self.outFileAlreadyExists = False
				if self.verboseMode :
					print( "outFile does not exist: " + str( fname ) )
				
		else :
			print("filename specified to setOutFileName was None!")
			
	def setOutFractalName( self, fname ) :
		# print "setting out fractal name: " + str( fname )
		self.outFractalName = fname
	
	def saveSettings( self ) :
		writeSettingsStub = None
		
		configPath = getBasePath() + os.sep + self.configFile
		
		if self.verboseMode: print "saving settings to: " + configPath
		
		try :
			writeSettingsStub = open( configPath , "w" )
		except IOError :
			print "whoops, couldn't open config file for writing."
			
		if writeSettingsStub :
			globalsStr = [ ]
			
			globalsDir = dir( self )
			
			for glob in globalsDir :
				if len( glob ) > 2 :
					
					# (exclude builtins)
					
					if glob[0:2] != "__" :
					
						blob = getattr( self, glob )
						
						itemtype = type( blob )
						
						oktypes = [ types.BooleanType, types.StringType, types.FloatType, types.IntType, types.ListType ]
						
						if itemtype in oktypes :
							
							# print "writing globals entry: " + str( glob ) + " value: " + str( blob ) + " type: " + str( itemtype )
							blobstr = str( blob )
							
							if itemtype == types.StringType :
								blobstr = "\"" + blobstr.strip() + "\""
							
							globalsStr.append( str( glob ) + " = " + blobstr + "\n" )
			
			writeSettingsStub.writelines( ["# uprMash config file\n", "\n"] + globalsStr )
			writeSettingsStub.flush()
			# print "settings saved."

	def loadSettings( self ) :
	
		readSettingsStub = None
		configPath = getBasePath() + os.sep + self.configFile
		
		print "loading settings from: " + configPath
		
		try :
			readSettingsStub = open( configPath , "r" )
		except IOError :
			print "whoops, couldn't open config file for reading."
		
		if readSettingsStub :
			lines = readSettingsStub.readlines()
			cnt = 0
			for line in lines:
				stripline = line.strip()
				
				if len( stripline ) > 0 :
					if stripline[0] != "#" :
						stripsplit = stripline.split( "=" )
						if len( stripsplit )== 2 :
							
							var = stripsplit[0].strip()
							
							val = stripsplit[1].strip()
							
							try:
								vart = getattr( self, var )
							except AttributeError :
								pass
								
							# print "set var: " + str( vart ) + " to value: " + val
							
							execthis = "self." + var + " = " + val
							
							# if vart :
							# print "EXEC: " + execthis
							exec( execthis )
							#else :
							#	print "Ignored value for var: " + str( var) + " cannot restore setting."
		else :
			print "couldn't read settings file from disk, using defaults."
		
	
def usage() :
	paraMash = ufParaMashGlobals()
	print str( "".join( paraMash.helpStr ) )

def main( ) :

	# print str( detectType( "0" ) )
	# print str( detectType( "( 0, 5 )" ) )
	# print str( detectType( "0.5" ) )
	# print str( detectType( "1000" ) )
	
	#testcurve = animCurve()
	#newKey = keyframe( "", "S", 0.5, 0 )
	#tewKey = keyframe( "S", "S", 10.0, 100 )
	#yewKey = keyframe( "S", "S", 0.0, 200 )
	#testcurve.addKey( newKey )
	#testcurve.addKey( tewKey )
	#testcurve.addKey( yewKey )
	#newKey = keyframe( "S", "S", 5.0, 300 )
	#tewKey = keyframe( "S", "S", 10.0, 400 )
	#yewKey = keyframe( "L", "", 5.0, 500 )
	#testcurve.addKey( newKey )
	#testcurve.addKey( tewKey )
	#testcurve.addKey( yewKey )
	
	#for i in range( -10, 110 ) :
	#	stars = getFloatAsStarsStr( testcurve.curveValue(  i * 5 ), 10.0, 60 )
	#	print stars
	
	try:
		#force overwrite mode
		opts, args = getopt.getopt(sys.argv[1:], "idvho:u:l:fp:m:r:bg", [ "info", "debug", "verbose", "help", "outputfile=", "uprfile=","layers=","force","opacity=","layermode=","rampopacity=","dobackground", "gui"])
		
	except getopt.GetoptError:
		# print help information and exit:
		usage()
		sys.exit(2)

	verbose = False
	paraMash = ufParaMashGlobals()
	parseObject = uprParse()
	
	configText = None
	
	for o, a in opts:
	
		if o in ("-v", "--verbose"):
			paraMash.verboseMode = True
			verbose = True
			print( paraMash.preStr + "verbosity is ON" )
			
		if o in ("-i", "--info"):
			if verbose : print( paraMash.preStr + "info mode ON")
			paraMash.infoMode = True
		
		if o in ["-h", "--help"] :
			usage()
		
		if o in ["-u", "--uprfile"] :
			if a :
				paraMash.setInFileName( a )
				if verbose : print( paraMash.preStr + "got input uprFileName: " + paraMash.inFileName )
			elif verbose :
				print "-u  or --uprfile flag specified but no input filename given!"
		if o in ["-l","--layers"] :
			if a:
				paraMash.numExtraLayers = int( a )
				if verbose : print( paraMash.preStr + "got number of extra layers: " + str( paraMash.numExtraLayers ) )
			elif verbose :
				print "-l or --layers flag specified but no parameter given!"
		
		if o in ["-p","--opacity"] :
			if a:
				paraMash.newLayerOpacity = int( a )
				if verbose : print( paraMash.preStr + "got opacity of extra layers: " + str( paraMash.newLayerOpacity ) )
			else :
				print "-p or --opacity flag specified but no parameter given!"
				usage()
				exit()
		
		if o in ["-r","--rampopacity"] :
			if a:
				paraMash.opacityRampLength = float( a )
				if verbose : print( paraMash.preStr + "got opacity ramp length: " + str( paraMash.opacityRampLength ) )
			else :
				print "-r or --rampopacity flag specified but no parameter given!"
				usage()
				exit()
		
		if o in ["-m","--layermode"] :
			if a:
				paraMash.newLayerMode.append( a )
				if verbose : print( paraMash.preStr + "got layermode of extra layers: " + str( paraMash.newLayerMode ) )
			else :
				# now an initialised member: paraMash.newLayerMode = "normal"
				print "-m or --layermode flag specified but no parameter given!"
				usage()
				exit()
				
		if o in ["-o", "--outputfile"] :
			if a :
				paraMash.setOutFileName( a )
				if verbose : print( paraMash.preStr + "got output uprFileName: " + paraMash.outFileName )
			else :
				print "-o flag specified but no output filename given!"
				usage()
				exit()
				
		if o in [ "-f", "--force" ] :
			if verbose :
				print "force overwrite mode ON"
			paraMash.forceOverwrite = True
			
		if o in [ "-b", "--dobackground" ] :
			if verbose :
				print "Do background mode ON"
			paraMash.ignoreBG = False
		
		if o in [ "-g", "-gui" ] :
			if verbose :
				print "gui mode ON"
			paraMash.guiMode = True
			
	if len( opts ) == 0 :
		# print("no args, going into gui mode..")
		paraMash.guiMode = True
	
	paraMash.loadSettings()
	
	# print "\n\nloaded settng for wavName: " + str( paraMash.inWavName + "\n")
	
	# this is breaking the config save-load thingo.. you can't save with none
	# if len( paraMash.newLayerMode ) == 0 : paraMash.newLayerMode.append( "addition" )
	
	if not paraMash.guiMode :
		try :
			if paraMash.ready :
				if paraMash.verboseMode : print("loading and parsing UPR file...")
				
				parseObject.loadAndParseUPRText( paraMash )
				
				if parseObject.parsedOK :
					if paraMash.verboseMode : print("adding interpolated layers..")
					parseObject.getFractal( -1).addExtraLayers( paraMash )
					
					parseObject.getFractal( -1).addStringToFractalName( "_mashed", paraMash )
					
					if paraMash.verboseMode : print("getting new UPR as a string..")
					print("opacity scale is: " + str( paraMash.newLayerOpacity ) )	
					fullStr = parseObject.getFractal( -1).getAsString( paraMash )
					
					if paraMash.verboseMode : print("writing UPR (if possible)..")
					if not paraMash.outFileAlreadyExists or paraMash.forceOverwrite :
					
						openStub = open( paraMash.outFileName, "w" )
						if paraMash.verboseMode : print("got open UPR file for writing: \n" + str( openStub ) )
								
						openStub.writelines( fullStr )
								
						openStub.flush()
						print("wrote mashed upr file : " + str( paraMash.outFileName ) )
					else :
						print("could not write UPR, does the output file already exist? if so you need to use the force flag: '-f'")
							
					if paraMash.infoMode : 
						print("full str:\n---------------------8<--------------------" )
						print( fullStr + "--------------------->8--------------------\n")
				else :
					print( "could not parse inputFile for some reason.." )
			else :
				if paraMash.verboseMode : print( "it appears that something is not ready.. please check the inputfile flag is correct:  [ -u filename.upr ]")
			
		except KeyboardInterrupt :
			print( "UPR parse interrupted by user" )
	else :
		# print( "it appears that we're going into gui mode..")
		
		root = Tk()
		
		iconName = getBasePath() + os.sep + 'uprMash_icon_64.ico'
		
		#if os.path.isfile( iconName ) :
		#	root.iconbitmap( iconName )
		#else :
		#	print("Could not see window icon file: " + iconName )
		
		app = uprMashWindow( root, paraMash )
		app.master.title("uprMash")
		
		#open UPR on startup
		app.openUPR()
		app.openWAV()
		
		root.protocol("WM_DELETE_WINDOW", app.quit )
		
		#logobmp = PhotoImage(file='uprMash_icon.bmp',format='bmp')
		
		#app.wm_iconbitmap( "@uprMash_icon.bmp" )
		#app.master.iconbitmap( "uprMash_icon_32.gif" )
		
		try :
			app.mainloop()
		except KeyboardInterrupt :
			print( "uprMash GUI interrupted by user" )
			app.quit()
			
		#root.destroy()
	
	#if no upr found in params, find all uprs in current dir?
	#if no output name, add "_inter" to the input filename

if __name__ == '__main__':
	main( )
