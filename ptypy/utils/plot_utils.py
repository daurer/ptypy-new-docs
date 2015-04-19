"""
Plotting utilities.

This file is part of the PTYPY package.

    :copyright: Copyright 2014 by the PTYPY team, see AUTHORS.
    :license: GPLv2, see LICENSE for details.
"""
import numpy as np
import time
import sys
from PIL import Image
import weakref
import matplotlib as mpl
import matplotlib.cm
import matplotlib.pyplot as plt
import pylab
from .verbose import logger
 
__all__ = ['pause','rmphaseramp','plot_storage','imsave','imload',\
         'complex2hsv', 'complex2rgb', 'hsv2rgb','rgb2complex', 'rgb2hsv',\
         'hsv2complex', 'franzmap']
# importing pyplot may fail when no display is available.
import os
if os.getenv("DISPLAY") is None:
    NODISPLAY = True
    matplotlib.use('agg')
    import matplotlib.pyplot
else:
    import matplotlib.pyplot
    NODISPLAY = False

# Improved interactive behavior or matplotlib 
import threading
if matplotlib.get_backend().lower().startswith('qt4'):
    mpl_backend = 'qt'
    from PyQt4 import QtGui
    gui_yield_call = QtGui.qApp.processEvents
elif matplotlib.get_backend().lower().startswith('wx'):
    mpl_backend = 'wx'
    import wx
    gui_yield_call = wx.Yield
elif matplotlib.get_backend().lower().startswith('gtk'):
    mpl_backend = 'gtk'
    import gtk
    def gui_yield_call():
        gtk.gdk.threads_enter()
        while gtk.events_pending():
            gtk.main_iteration(True)
        gtk.gdk.flush()
        gtk.gdk.threads_leave()
else:
    mpl_backend = None

# Fix tif import problem
Image._MODE_CONV['I;16'] = (Image._ENDIAN + 'u2', None)

# Grayscale + alpha should also work
Image._MODE_CONV['LA'] = (Image._ENDIAN + 'u1', 2)

if mpl_backend is not None:
    class _Pause(threading.Thread):
        def __init__(self, timeout, message):
            self.message = message
            self.timeout = timeout
            self.ct = True
            threading.Thread.__init__(self)
        def run(self):
            sys.stdout.flush()
            if self.timeout < 0:
                raw_input(self.message)
            else:
                if self.message is not None:
                    print self.message
                time.sleep(self.timeout)
            self.ct = False

    def pause(timeout=-1, message=None):
        """\
        Pause the execution of a script while leaving matplotlib figures 
        responsive.
        *Gui aware*
        
        Parameters
        ----------
        timeout : float, optional
            By default, execution is resumed only after hitting return. 
            If timeout >= 0, the execution is resumed after timeout seconds.
            
        message : str, optional
            Message to diplay on terminal while pausing
        
        """
        if message is None:
            if timeout < 0:
                message = 'Paused. Hit return to continue.'
        h = _Pause(timeout, message)
        h.start()
        while h.ct:
            gui_yield_call()
            time.sleep(.01)

else:
    def pause(timeout=-1, message=None):
        """\
        Pause the execution of a script while leaving matplotlib figures 
        responsive.
        **Not** *Gui aware*
        
        Parameters
        ----------
        timeout : float, optional
            By default, execution is resumed only after hitting return. 
            If timeout >= 0, the execution is resumed after timeout seconds.
            
        message : str, optional
            Message to diplay on terminal while pausing
        
        """
        if timeout < 0:
            if message is None:
                message = 'Paused. Hit return to continue.'
            raw_input(message)
        else:
            if message is not None:
                print message
            time.sleep(timeout)


'''\
def P1A_to_HSV(cin):
    """\
    Transform a complex array into an RGB image,
    mapping phase to hue, amplitude to value and
    keeping maximum saturation.
    """

    # HSV channels
    h = .5*np.angle(cin)/np.pi + .5
    s = np.ones(cin.shape)
    v = abs(cin)
    v /= v.max()

    i = (6.*h).astype(int)
    f = (6.*h) - i
    q = v*(1. - f)
    t = v*f
    i0 = (i%6 == 0)
    i1 = (i == 1)
    i2 = (i == 2)
    i3 = (i == 3)
    i4 = (i == 4)
    i5 = (i == 5)

    imout = np.zeros(cin.shape + (3,), 'uint8')
    imout[:,:,0] = 255*(i0*v + i1*q + i4*t + i5*v)
    imout[:,:,1] = 255*(i0*t + i1*v + i2*v + i3*q)
    imout[:,:,2] = 255*(i2*t + i3*v + i4*v + i5*q)

    return imout
'''
# aliases. maybe get deleted

def complex2hsv(cin, vmin=None, vmax=None):
    """\
    Transforms a complex array into an RGB image,
    mapping phase to hue, amplitude to value and
    keeping maximum saturation.
    
    Parameters
    ----------
    cin : ndarray
        Complex input. Must be two-dimensional.
    
    vmin,vmax : float
        Clip amplitude of input into this interval.
        
    Returns
    -------
    rgb : ndarray
        Three dimensional output.   
        
    See also
    --------
    complex2rgb
    hsv2rgb
    hsv2complex
    """
    # HSV channels
    h = .5*np.angle(cin)/np.pi + .5
    s = np.ones(cin.shape)

    v = abs(cin)
    if vmin is None: vmin = 0.
    if vmax is None: vmax = v.max()
    assert vmin < vmax
    v = (v.clip(vmin,vmax)-vmin)/(vmax-vmin)
    
    return np.asarray((h,s,v))

def complex2rgb(cin, **kwargs):
    """
    Executes `complex2hsv` and then `hsv2rgb`

    See also
    --------
    complex2hsv
    hsv2rgb
    rgb2complex
    """
    return hsv2rgb(complex2hsv(cin,**kwargs))
    
def hsv2rgb(hsv):
    """\
    HSV (Hue,Saturation,Value) to RGB (Red,Green,Blue) transformation.

    Parameters
    ----------
    hsv : array-like
        Input must be two-dimensional. **First** axis is interpreted
        as hue,saturation,value channels.
    
    Returns
    -------
    rgb : ndarray
        Three dimensional output. **Last** axis is interpreted as
        red, green, blue channels.  
        
    See also
    --------
    complex2rgb
    complex2hsv
    rgb2hsv
    """
    # HSV channels
    h,s,v = hsv

    i = (6.*h).astype(int)
    f = (6.*h) - i
    p = v*(1. - s)
    q = v*(1. - s*f)
    t = v*(1. - s*(1.-f))
    i0 = (i%6 == 0)
    i1 = (i == 1)
    i2 = (i == 2)
    i3 = (i == 3)
    i4 = (i == 4)
    i5 = (i == 5)

    rgb = np.zeros(h.shape + (3,), dtype=h.dtype)
    rgb[:,:,0] = 255*(i0*v + i1*q + i2*p + i3*p + i4*t + i5*v)
    rgb[:,:,1] = 255*(i0*t + i1*v + i2*v + i3*q + i4*p + i5*p)
    rgb[:,:,2] = 255*(i0*p + i1*p + i2*t + i3*v + i4*v + i5*q)

    return rgb
    

def rgb2hsv(rgb):
    """
    Reverse to :any:`hsv2rgb`
    """
    eps = 1e-6
    rgb=np.asarray(rgb).astype(float)
    maxc = rgb.max(axis=-1)
    minc = rgb.min(axis=-1)
    v = maxc
    s = (maxc-minc) / (maxc+eps)
    s[maxc<=eps]=0.0
    rc = (maxc-rgb[:,:,0]) / (maxc-minc+eps)
    gc = (maxc-rgb[:,:,1]) / (maxc-minc+eps)
    bc = (maxc-rgb[:,:,2]) / (maxc-minc+eps)
    
    h =  4.0+gc-rc
    maxgreen = (rgb[:,:,1] == maxc)
    h[maxgreen] = 2.0+rc[maxgreen]-bc[maxgreen]
    maxred = (rgb[:,:,0] == maxc)
    h[maxred] = bc[maxred]-gc[maxred]
    h[minc==maxc]=0.0
    h = (h/6.0) % 1.0

    return np.asarray((h, s, v))

def hsv2complex(cin):
    """
    Reverse to :any:`complex2hsv`
    """
    h,s,v = cin
    return v * np.exp(np.pi*2j*(h-.5)) /v.max()

def rgb2complex(rgb):
    """
    Reverse to :any:`complex2rgb`
    """
    return hsv2complex(rgb2hsv(rgb))

HSV_to_RGB = hsv2rgb  
RGB_to_HSV = rgb2hsv    
P1A_to_HSV = complex2hsv
HSV_to_P1A = hsv2complex

def imsave(a, filename=None, vmin=None, vmax=None, cmap=None):
    """
    Take array `a` and transform to `PIL.Image` object that may be used
    by `pyplot.imshow` for example. Also save image buffer directly 
    without the sometimes unnecessary Gui-frame and overhead.
    
    Parameters
    ----------
    a : ndarray
        Two dimensional array. Can be complex, in which case the amplitude
        will be optionally clipped by `vmin` and `vmax` if set. 
    
    filename : str, optionsl
        File path to save the image buffer to. Use '\*.png' or '\*.png'
        as image formats.
    
    vmin,vmax : float, optional
        Value limits ('clipping') to fit the color scale.
        If not set, color scale will span from minimum to maximum value
        in array
        
    cmap : str, optional
        Name of the colormap for colorencoding.
        
    Returns
    -------
    im : PIL.Image
        a `PIL.Image` object.
         
    See also
    --------
    complex2rgb
    
    Examples
    --------
    >>> from ptypy.utils import imsave
    >>> from matplotlib import pyplot as plt
    >>> from ptypy.resources import flower_obj
    >>> a = flower_obj(512)
    >>> pil = imsave(a)
    >>> plt.imshow(pil)
    >>> plt.show()
    
    converts array a into, and returns a PIL image and displays it.
    
    >>> pil = imsave(a, /tmp/moon.png) 
    
    returns the image and also saves it to filename
    
    >>> imsave(a, vmin=0, vmax=0.5) 
    
    clips the array to values between 0 and 0.5.
    
    >>> imsave(abs(a), cmap='gray') 
    
    uses a matplotlib colormap with name 'gray'
    """
    if str(cmap) == cmap:
        cmap= mpl.cm.get_cmap(cmap)
        
    if a.dtype.kind == 'c':
        # Image is complex
        if cmap is not None:
            logger.info('imsave: Ignoring provided cmap - input array is complex')
        i = complex2rgb(a, vmin=None, vmax=None)
        im = Image.fromarray(np.uint8(i), mode='RGB')

    else:
        if vmin is None:
            vmin = a.min()
        if vmax is None:
            vmax = a.max()
        im = Image.fromarray((255*(a.clip(vmin,vmax)-vmin)/(vmax-vmin)).astype('uint8'))
        if cmap is not None:
            r = im.point(lambda x: cmap(x/255.0)[0] * 255)
            g = im.point(lambda x: cmap(x/255.0)[1] * 255)
            b = im.point(lambda x: cmap(x/255.0)[2] * 255)
            im = Image.merge("RGB", (r, g, b))
        #b = (255*(a.clip(vmin,vmax)-vmin)/(vmax-vmin)).astype('uint8')
        #im = Image.fromstring('L', a.shape[-1::-1], b.tostring())

    if filename is not None:
        im.save(filename)
    return im

def imload(filename):
    """\
    Load an image and returns a numpy array. *May get deleted*
    """
    a = np.array(Image.open(filename))
    #a = np.fromstring(im.tostring(), dtype='uint8')
    #if im.mode == 'L':
    #    a.resize(im.size[-1::-1])
    #elif im.mode == 'LA':
    #    a.resize((2,im.size[1],im.size[0]))
    #elif im.mode == 'RGB':
    #    a.resize((3,im.size[1],im.size[0]))
    #elif im.mode == 'RGBA':
    #    a.resize((4,im.size[1],im.size[0]))
    #else:
    #    raise RunTimeError('Unsupported image mode %s' % im.mode)
    return a

# Franz map
mpl.cm.register_cmap(name='franzmap',data=
                   {'red': ((   0.,    0,    0),
                            ( 0.35,    0,    0),
                            ( 0.66,    1,    1),
                            ( 0.89,    1,    1),
                            (    1,  0.5,  0.5)),
                  'green': ((   0.,    0,    0),
                            ( 0.12,    0,    0),
                            ( 0.16,   .2,   .2),
                            (0.375,    1,    1),
                            ( 0.64,    1,    1),
                            ( 0.91,    0,    0),
                            (    1,    0,    0)),
                  'blue':  ((   0.,    0,    0),
                            ( 0.15,    1,    1),
                            ( 0.34,    1,    1),
                            (0.65,     0,    0),
                            (1, 0, 0)) },lut=256)
def franzmap():
    """\
    Set the default colormap to Franz's map and apply to current image if any.
    """
    mpl.pyplot.rc('image', cmap='franzmap')
    im = mpl.pyplot.gci()

    if im is not None:
        im.set_cmap(matplotlib.cm.get_cmap('franzmap'))
    mpl.pyplot.draw_if_interactive()
    
    
def _plot_3d_array(data, axis=0, title='3d', cmap='gray', interpolation='nearest', vmin=None, vmax=None,**kwargs):
    '''
    plots 3d data with a slider to change the third dimension
    unfortunately the number that the slider shows is rounded weirdly.. be careful!
    TODO: fix that!

    input:
        - data: 3d numpy array containing the data
        - axis: axis that should be changeable by the slider

    author: Mathias Marschner
    added: 30.10.2013
    '''
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.title(title)

    if vmin == None:
        vmin = data.min()
    if vmax == None:
        vmax = data.max()

    if axis == 0:
        cax = ax.imshow(data[data.shape[0]/2,:,:], cmap=cmap, vmin=vmin, vmax=vmax, interpolation=interpolation,**kwargs)
    elif axis == 1:
        cax = ax.imshow(data[:,data.shape[1]/2,:], cmap=cmap, vmin=vmin, vmax=vmax, interpolation=interpolation,**kwargs)
    elif axis == 2:
        cax = ax.imshow(data[:,:,data.shape[2]/2], cmap=cmap, vmin=vmin, vmax=vmax, interpolation=interpolation,**kwargs)

    cbar = fig.colorbar(cax)
    axcolor = 'lightgoldenrodyellow'
    ax4 = pylab.axes([0.1, 0.01, 0.8, 0.03], axisbg=axcolor)
    sframe = pylab.Slider(ax4, '', 0, data.shape[axis]-1, valinit=data.shape[axis]/2, closedmin = True, closedmax = True, valfmt = '%d')

    def update(val):
        frame = np.around(np.clip(sframe.val, 0, data.shape[axis]-1))
        if axis == 0:
            cax.set_data(data[frame,:,:])
        elif axis == 1:
            cax.set_data(data[:,frame,:])
        elif axis == 2:
            cax.set_data(data[:,:,frame])

    sframe.on_changed(update)
    return ax     

def rmphaseramp(a, weight=None, return_phaseramp=False):
    """\
    Attempts to remove the phase ramp in a two-dimensional complex array 
    ``a``.

    Parameters
    ----------
    a : ndarray
        Input image as complex 2D-array.
    
    weight : str, optional
        Use 'abs' for a modulus-weighted phaseramp and`None` for no weights.
        
    return_phaseramp : bool, optional
        Use True to get also the phaseramp array ``p``.
    
    Returns
    -------
    out : ndarray
        Modified 2D-array, ``out=a*p``
    p : ndarray, optional
        Phaseramp if ``return_phaseramp = True``, otherwise omitted 


    Examples
    --------
    >>> b = rmphaseramp(image)
    >>> b, p = rmphaseramp(image , return_phaseramp=True)
    """

    useweight = True
    if weight is None:
        useweight = False
    elif weight=='abs':
        weight = np.abs(a)

    ph = np.exp(1j*np.angle(a))
    [gx, gy] = np.gradient(ph)
    gx = -np.real(1j*gx/ph)
    gy = -np.real(1j*gy/ph)

    if useweight:
        nrm = weight.sum()
        agx = (gx*weight).sum() / nrm
        agy = (gy*weight).sum() / nrm
    else:
        agx = gx.mean()
        agy = gy.mean()

    (xx,yy) = np.indices(a.shape)
    p = np.exp(-1j*(agx*xx + agy*yy))

    if return_phaseramp:
        return a*p, p
    else:
        return a*p


def plot_storage(S,fignum=100,modulus='linear',slice_tupel=(slice(1),slice(None),slice(None)),**kwargs): #filename=None,vmin=None,vmax=None):
    """\
    Quickly displat the data buffer of a :any:`Storage` instance.

    Keyword arguments are those of :any:`imsave`
    
    Parameters
    ----------
    S : Storage
        Storage instance
        
    fignum : int, optional
        Number of the figure. 
        
    slice_tupel : tuple of slices, optional
        Determines what part of Storage buffer is displayed, i.e. which
        layers and which region-of-interest. Layers are subplotted 
        horizontically next to each other. Figsize is (6,6*layers)
    
    modulus : str, optional
        One of `sqrt`, `log` or `linear` to apply to modulus of array 
        buffer. Useful to reduce dynamic range for diffraction images.
        
    Returns
    -------
    fig : maplotlib.pyplot.figure
        
    See also
    --------
    imsave
    :any:`Storage`
    """
    slc = slice_tupel
    R,C = S.grids()
    R = R[slc][0]
    C = C[slc][0]   
    im = S.data[slc].copy()
    ext=[C[0,0],C[0,-1],R[0,0],R[-1,0]]
    
    if modulus=='sqrt':
        im=np.sqrt(np.abs(im)).astype(im.dtype)*np.exp(1j*np.pi*np.angle(im)).astype(im.dtype)
    elif modulus=='log':
        im=np.log10(np.abs(im)+1).astype(im.dtype)*np.exp(1j*np.pi*np.angle(im)).astype(im.dtype)
    else:
        modulus='linear'
    
    ttl= str(S.ID) +'#%d' + ', ' + modulus + ' scaled modulus'
    unit,mag,num=length_units(np.abs(ext[0]))
    ext2=[a*mag for a in ext]

    layers = im.shape[0]
    fig = plt.figure(fignum,figsize=(6*layers,6))
    for l in range(layers):
        ax = fig.add_subplot(1,layers,l+1)
        a = ax.imshow(imsave(im[l],**kwargs),extent=ext2)
        #a.axes.xaxis.get_major_formatter().set_powerlimits((-3,3))
        #a.axes.yaxis.get_major_formatter().set_powerlimits((-3,3))
        ax.title.set_text(ttl % l )
        ax.set_xlabel('x [' + unit +']')   
        ax.set_ylabel('y [' + unit +']')
    return fig


def length_units(number):
    """\
    Doc Todo
    """
    a = np.floor(np.log10(np.abs(number)))
    if a<-6.0:
        unit='nm'
        mag=1e9
    elif a<-3.0:
        unit='um'
        mag=1e6
    elif a<0.0:
        unit='mm'
        mag=1e3
    elif a<3.0:
        unit='m'
        mag=1e0
    else:
        unit='km'
        mag=1e-3
    num=number*mag
    return unit,mag,num


