#!/usr/bin/env python

# requires the PIL for rendering.
# but uses builtin module wave for reading wav format soundfiles.
import sys, os
import wave, math, Image, ImageDraw
from optparse import OptionParser


_PROG = "waveToImage.py"
_DESC = "generates a sound waveform image from an uncompressed wav file"
_VER = "%prog 0.1.0 by benp@rsp.com.au"
_USAGE = "%prog [options] inputfile.wav outputfile.<ext>\ninputfile.wav: assumes uncompressed wavs. untested with compressed wavs\noutputfile.<ext>: <ext> can be tif, png, jpg etc .."


samplerTypes = ["minmax","energy"]

#-----------------------------------------------------------------
# samplers:
#	to implement a new sampler: 
#	subclass sampleMethod,
#	implement __call__ on new sampler class
#	register new sampler to samplers container by binding class to a class-variable, like:
#		in samplers body:
#			myNewSampler = myNewSampler_sampler()
#	add sampler name to samplerTypes list, like:
#		samplerTypes = samplerTypes.append("myNewSampler")

# samplemethod abstract class
class sampleMethod:
	"""sampleMethod abstract class.
	To be subclassed by specific sampler implementations """
	name = None
	def __init__(self, ):
		pass

	def __call__( self, signal, position, width ):
		return NotImplemented

	def __str__(self):
		return self.name

#-----------------------------------------------------------------
# sample method implemetations
class minmax_sampler(sampleMethod):
	"""output looks like a classic waveform"""
	def __init__(self):
		sampleMethod.__init__( self )
		self.name = "minmax"

	def __call__(self, wdata, position, width ):
		startp = int( position - (width/2) )
		endp = startp + width
		mp = position

		positions = [ i for i in xrange( startp, endp ) ]

		ss = wdata.getWaveSamples( positions )
		
		mmin = 1
		mmax = 0
		for s in ss:
			mmin = min( mmin, s )
			mmax = max( mmax, s )

		return ( mmin, mmax )

class energy_sampler( sampleMethod ):
	"""output is based on absolute diference of consecutive samples within window width
	returns coordinates for something that looks more like an ampliude graph, a classic wave energy display.
	values are symmetrical about 0.5.
	"""
	def __init__( self ):
		sampleMethod.__init__( self )
		self.name = "energy"

	def __call__( self, wdata, position, width ):
		startp = int( position - (width/2) )
		endp = startp + (width-1)
		mp = position
		positions = [ i for i in xrange( startp, endp ) ]

		ss = wdata.getWaveSamples( positions )
		
		abd = 0
		for i in xrange(len(ss)):
			abd = abd + abs( (ss[i] ) - (ss[i-1] ) )
		
		abd = abd / len(ss)
		
		return ( (abd/2.0) + 0.5 , 0.5-(abd/2.0))

#-----------------------------------------------------------------
# samplers container
class samplers:
	"""samplers list object.
	samplers are passed to wavdata.sample method as
	samplers.minmax
	"""
	# register samplers here ..
	minmax = minmax_sampler()
	energy = energy_sampler()

	def __init__(self):
		pass

	def __getattribute__(self, name):
		return eval("self.%s"%name)



#-----------------------------------------------------------------
# wavdata object
class wavdata:
	"""Wave_read wrapper"""
	waveread = None
	def __init__(self, wavreadinst, ):
		self.waveread = wavreadinst
		self.samplers = samplers()
		self.channels = self.waveread.getnchannels()
		self.sampwidth = self.waveread.getsampwidth()
		self.data = self._setData()

	def _setData(self):
		ch = self.channels
		sw = self.sampwidth
		stride = ch*sw
		
		rdata = self.waveread.readframes( self.waveread.getnframes() )

		data = []
		for i in xrange( self.waveread.getnframes() ):
			data.append( ( wave.struct.unpack( 'h', rdata[int(i)*stride:(i*stride)+sw] )[0]+32767)/65535.0  )
		
		del(rdata)
		return data

	def sample( self, windowMethod, position, width=1, oversample = 1):
		"""sample the signal, using windowMethod, position and width"""
		self.windowMethod = windowMethod
		return self.windowMethod( self, position, width )

	def getWaveSamples( self, positions ):
		"""returns a list of unfiltered wav samples at wav positions"""
		if type(positions) == type(10):
			self.waveread.setpos(positions)
			if positions < 0 or positions > len(self.data)-1 :
				return 0.5
				return getWaveSample( positions )

		elif type(positions) == type([1,]):
			smps = []
			for i in positions:
				if i < 0 or i > len(self.data)-1:
					smps.append(0.5)
				else:
					smps.append(self.getWaveSample( i ) )
			return smps

	def getWaveSample( self, position ):	
		"""gets a simgle wave sample"""
		d = self.data[position]
		return d

	def getNormalisedPosition( self, position):
		"""returns a position in the wave (in samples) from normalised position"""
		p = self.waveread.getnframes() * position
		return int( p )

	def getNormalisedWidth( self, width ):
		"""returns a width in wave samples from normailsed width"""
		return int( self.waveread.getnframes() * float(width)  )
	
	
	def getResampledWavdata( self, newlength, normalize, sampler = "minmax", filterwidth = 1.0 ) :
	
		samples = 1
		
		# gather samples
		smp = []
		nsmp = []
		# iter x
		totalx = int( newlength * samples + 0.5 )

		# if options.verbose: print("sampling wavedata ..")
		
		perc = 1
		for i in xrange( totalx ):
			# if options.progress: 
				# percentage display
			#	p = math.modf( (i*5)/totalx ) 
			#	if p[1] <> perc:
			#		perc = p[1]
					# print( "sample x: %0.0f %%"% (perc*20) )		

			pos = self.getNormalisedPosition( i / float( totalx ) )
			
			width = self.getNormalisedWidth( float( filterwidth ) / totalx )

			# the actual sampler object is requested based on the -s "SAMPLER" cmdline arg.
			entry = self.sample( self.samplers.__getattribute__( sampler ), pos , width  )
			#print "s is : " + str( entry )
			
			smp.append( entry )


		# transforms
		norm = 1
		mag = 1
		mmin = 1
		mmax = 0
		#exp = options.gamma

		# magnitude multiplier from cmd line.
		# if options.magnitude != 1.0:
		# 	mag = options.magnitude

		#noramlise y value
		if normalize:
			for s in smp:
				mmin = min( mmin, s[0], s[1] )
				mmax = max( mmax, s[0], s[1] )

			norm = 0.5 / abs( min( mmin, 1 - mmax ) - 0.5 )
		
			#if options.verbose: 
			#print("min and max : %s : %s"% ( mmin, mmax ) )
			#print("normalize factor : %s"% norm )
			
			for s in smp:
				ns = ( (s[0] - mmin) * norm, (s[1] - mmin) * norm )
				nsmp.append(  ns )
				#print "ns is: " + str( ns )
				
				
			#for i in xrange( totalx ) :
			#	newsmp = smp[ i ]
			#	print "new sample is: " + str( newsmp )
			#	nsmp.append( newsmp )
		
		#gotta add  some averaging downsampling code here..
		return nsmp

def main():
	#-----------------------------------------------------------------
	# optparser stuff
	parser = OptionParser(version=_VER,
	description = _DESC,
	prog=_PROG,
	usage=_USAGE)


	# output reolution
	parser.add_option("-r", "--resolution", action="store", dest="imageRes",type = "int", default = (512,512),
	nargs=2, help="sets the output image resolution [default: %default]",)

	# oversample
	parser.add_option("-o", "--oversample", action="store", dest="oversample", type="float", default = 3, nargs=1, help="oversample factor for drawing before final output [default: %default]")

	# sampler
	parser.add_option("-s", "--sampler", action="store", dest="sampler",
	type="choice",default = "energy",
	help='define which sampler to use when sampling the wav data [default: "%default"]'+"\nchoices: %s"%str(samplerTypes),
	choices=samplerTypes)

	# multiply signal values before drawing
	parser.add_option( "-m", "--magnitude", action="store", dest="magnitude", type="float", default = 1.0, nargs=1, help="multiplies signal values before drawing [dafault: %default]" )

	# normalise y
	parser.add_option( "-n", "--normalise", action="store_false", dest="normalise", default = True, help="turn off normalised values for drawing [dafault: on]" )

	# gamma
#	parser.add_option( "-g", "--gamma", action="store", dest="gamma", type="float", default = 1.0, help="apply gamma to value [default: %default]" )

	# wavinfo
	parser.add_option("-i", "--info", action="store_true", dest="info", default = False, help="prints wav file info and exits [default: %default]")

	# progress
	parser.add_option("-p", "--progress", action="store_true", dest="progress", default = False, help="prints draw progress (units are in oversampled x resolution) [default: %default]")

	# verbosity
	parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="operates verbosely")

	# draw options

	# frames-per-second
	parser.add_option("-f", "--fps",
	action="store", dest="fps", default=24.0, nargs=1,
	help="sets the frames-per-second to map sound-frames-per-second to [default: %default]")

	# mark seconds
	parser.add_option("", "--mark-seconds", action="store_true", dest ="markseconds", default = False, help ="marks second intervals [default: %default]")

	# mark frames
	parser.add_option("", "--mark-frames", action="store_true", dest ="markframes", default = False, help ="marks frame intervals [default: %default]")


	(options, args) = parser.parse_args()

	
	#-----------------------------------------------------------------

	# check positional args ..
	if len(args) < 1:
		return 1
	elif len(args) == 2:
		inputWavPath = args[0]
		outputImagePath = args[1]
	elif len(args) == 1:
		inputWavPath = args[0]
		outputImagePath = None

	# print settings
	if options.verbose:
		print("input: %s"%inputWavPath)
		print("output: %s"%outputImagePath)
		print("output resolution: %sx%s"%(options.imageRes[0],options.imageRes[1]))

	# get input wave_read object ..
	if os.path.exists( inputWavPath ):
		if options.verbose: print("creating wavdata .. ")
		wdata = wavdata( wave.open( inputWavPath, 'r' ) )
		if options.verbose: print(".. done")
	else:
		if options.verbose:
			print("unable to load %s. Does not exist. exiting .."%inputWavPath)
		return 1

	# print info
	if options.info:
		print("wav info:         %s"%inputWavPath)
		wparams = wdata.waveread.getparams()
		print("n channels:       %s"%wparams[0])
		print("sample width:     %s"%wparams[1])
		print("frame rate:       %s"%wparams[2])
		print("n frames:         %s (%0.3f secs.)"%(wparams[3], wparams[3]/float(wparams[2]) ) )
		print("compression type: %s"%wparams[4])
		print("compression name: %s"%wparams[5])

	#-----------------------------------------------------------------
	# main renderer block ..

	# check output:
	outBasePath = os.path.dirname(outputImagePath)
	if os.path.exists( outBasePath ):

		# begin render ...

		#print("output base path exists: %s"%outBasePath )
		res = options.imageRes
		res = ( int(res[0]*options.oversample), int(res[1]*options.oversample) )
		#im = Image.new( "1", (res[0],res[1] ) )
		im = Image.new( "RGB", (res[0],res[1] ) )

		dim = ImageDraw.Draw( im )

		# gather samples
		smp = []
		# iter x
		totalx = int( res[0]*options.oversample )

		if options.verbose: print("sampling wavedata ..")
		
		perc = 1
		for i in xrange( totalx ):
			if options.progress: 
				# percentage display
				p = math.modf( (i*5)/totalx ) 
				if p[1] <> perc:
					perc = p[1]
					print( "sample x: %0.0f %%"% (perc*20) )
				
			swidth = 1

			pos = wdata.getNormalisedPosition( i/float(res[0]) )
			width = wdata.getNormalisedWidth( float(swidth)/res[0] )


			# the actual sampler object is requested based on the -s "SAMPLER" cmdline arg.
			smp.append( wdata.sample( wdata.samplers.__getattribute__(options.sampler), pos , width  ) )


		# transforms
		norm = 1
		mag = 1
		mmin = 1
		mmax = 0
		#exp = options.gamma

		# magnitude multiplier from cmd line.
		if options.magnitude != 1.0:
			mag = options.magnitude

		#noramlise y value
		if options.normalise:
			for s in smp:
				mmin = min( mmin, s[0], s[1] )
				mmax = max( mmax, s[0], s[1] )

			norm = 0.5/abs( min( mmin, 1-mmax ) - 0.5 )

			if options.verbose: 
				print("min and max : %s : %s"%(mmin, mmax))
				print("normalise factor : %s"%norm)

		# draw in x
		if options.verbose: print("drawing wavedata ..")		
		x = 0
		#totalx = len(smp)
		perc = 1

		# timing
		nframes = wdata.waveread.getnframes()
		frate = wdata.waveread.getframerate()
		
		# seconds
		secr = (nframes/float(frate)) *options.oversample
		sec=1

		# frames
		framw = (((nframes/float(frate))/options.fps )/options.oversample)*res[0]*0.5
		framr = secr* float( options.fps )
		fram = 1
		frams = 1

		for s in smp:

			if options.markframes:
			# draw frame marker
				f = math.modf( (x*framr)/float(totalx) )

				if f[1] <> fram:
					dim.rectangle( [x, 0 , x+(2*options.oversample), res[1]], fill = (20, 16, 16 ) )
					fram = f[1]
#					if frams == 1:
#						frams = 0
#						#print("on")
#						dim.rectangle( [x, 0 , x+(framw), res[1]], fill = (20, 16, 16 ) )
#					else:
#						frams = 1
#						#print("off")


			if options.markseconds:
			#draw second marker
				p = math.modf( (x*secr)/float(totalx) )
				if p[1] <> sec:
					sec = p[1]
					dim.rectangle( [ x, 0, x+(5*options.oversample), res[1] ], fill = (32, 32, 64) )


			if options.progress: 
			# print % done
				p = math.modf( (x*5)/totalx ) 
				if p[1] <> perc:
					perc = p[1]
					print( "draw x: %0.0f %%"% (perc*20) )					
					
			y1 = (((s[0]-0.5)*norm)*mag+0.5)*res[1]
			y2 = (((s[1]-0.5)*norm)*mag +0.5)*res[1]
			
			dim.line( [ x, y1, x, y2 ] , fill = (255,255,255) )
			x+=1

		im = im.convert( "RGB" )
		im = im.resize( options.imageRes, Image.ANTIALIAS )

		if options.verbose: 
			print("writing to: %s"%outputImagePath)

		im.save( outputImagePath )

		if options.verbose: 
			print(".. done")

	#-------------------------------------------------------

	else:
		print("output path %s does not exist"%outBasePath)
		return 1 

	return 0

# used to be a commandline bizzle
#if __name__ == "__main__":
#
#	sys.exit( main() )
