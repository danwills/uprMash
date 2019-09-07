uprMash
=======

Disclaimer time: This is a fairly ancient project from a long time ago before I learned of better python ways. It's a monolith of code that I wrote using python in cygwin under some oldish type of Windows (98 or xp maybe?) I ended up distributing it as an exe file (some bundle-up-the-python thing). I don't really expect this to just work out-of-the-box, but mainly to provide some example-implementations of importing, modifying and re-saveing UPR data.

Now on with what the original Readme claimed it could do (back then):

=========================================================================

Adds extra layers to an animated UltraFractal fractal to create motion blurred fractals, add animation to create loops, and other cool time-blending effects.

The following is from the other README file:

UPRMash - a python script for mangling UltraFractal UPR files.

What does it do?

It adds extra layers to an animated UltraFractal fractal to create motion blurred fractals, add animation to create loops, and other cool time-blending effects.


Why would you want to do this? UF already has motion blur, doesn't it?

UF does add a motion blurring effect based on the animation of the 'location' settings of a layer, but only zooms, panning and rotation will create this blur, not fractal parameter changes.

I have always wanted to see what it would look like to motion blur a fractal as you vary the parameters, some fractals change in very interesting ways as their parameters vary.


It's also a nice departure from the rather digital artifact of being perfectly in focus everywhere. I am also interested in setting up some fractals with parameter-focal blur (aka Depth-of-Field) but I'll leave that for a future project :D


I am comitting it to gitHub because I noticed that the wiki is getting some traffic and only the py2exe (for windows) conversion is available.. hopefully making the source available will make it more useful to anyone wanting to play with it.

=========================================================================

Wow, it's 2019 now, and I still think that over-sampling a fractal as its parameters vary and essentially motion-blurring (or ~accumulating?) the result is still a really interesting idea that I haven't seen explored much.

This could definitely have potential as an idea to build a (glsl?) fragment shader or openCL-subsystem to get all the operations done (these days) in massive-parallel on the GPU. I think this could lead to some really interesting renderings!.

If anyone out there is interested to help to build a translation-tool that might help to bring the actual evaluation of UPR fractals into a GPU/shader context, I'm really interested to hear from you! :D
