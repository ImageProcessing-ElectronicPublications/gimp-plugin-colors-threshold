#!/usr/bin/env python

# Gimp plugin Bimodal Threshold
# Public Domain Mark 1.0
#  No Copyright

from gimpfu import *
import time
from array import array

gettext.install("gimp20-python", gimp.locale_directory, unicode=True)

def byteclamp(c):
    if (c < 0):
        c = 0
    elif (c > 255):
        c = 255
    return c

def threshold_bimod(hist, tsize, tpart):
    T = tsize * tpart
    Tn = 0
    while (T != Tn) :

        Tn = T
        Tb = 0
        Tw = 0
        ib = 0
        iw = 0
        for c in xrange(0, int(T + 0.5)) :
            Tb += hist[c] * c
            ib += hist[c]
        for c in xrange(int(T + 0.5), int(tsize)) :
            Tw += hist[c] * c
            iw += hist[c]
        if ((iw + ib) == 0):
            T = Tn
        elif (iw == 0) :
            T = Tb / ib
        elif (ib == 0) :
            T = Tw / iw
        else :
            T = ((Tw / iw) * tpart + (Tb / ib) * (1.0 - tpart))
    return T

def colors_bimod(img, layer, tcount, tdelta, tmedian):
    gimp.progress_init("Processing " + layer.name + "...")
    pdb.gimp_undo_push_group_start(img)
    pdb.gimp_layer_add_alpha(layer)

    layername = layer.name + "-bimod-" + str(int(tcount))

    # Create the new layer:
    srcWidth, srcHeight = layer.width, layer.height

    destDrawable = gimp.Layer(img, layername, srcWidth, srcHeight,
                              layer.type, layer.opacity, layer.mode)
    img.add_layer(destDrawable, 0)
    xoff, yoff = layer.offsets

    destDrawable.translate(xoff, yoff)
    if pdb.gimp_selection_is_empty(img) :
        X0 = 0
        Y0 = 0
    else :
        X0 = pdb.gimp_selection_bounds(img)[1]
        Y0 = pdb.gimp_selection_bounds(img)[2]
        XE = pdb.gimp_selection_bounds(img)[3]
        YE = pdb.gimp_selection_bounds(img)[4]
        srcWidth = XE - X0
        srcHeight = YE - Y0

    srcRgn = layer.get_pixel_rgn(X0, Y0, srcWidth, srcHeight, False, False)
    src_pixels = array("B", srcRgn[X0:X0+srcWidth, Y0:Y0+srcHeight])

    dstRgn = destDrawable.get_pixel_rgn(X0, Y0, srcWidth, srcHeight, True, True)
    p_size = len(srcRgn[X0, Y0])
    dest_pixels = array("B", [0] * (srcWidth * srcHeight * p_size))
    progress = 0.1
    gimp.progress_update(progress)

    Tmax = 256
    pstep = (1.0 - progress) / srcHeight / p_size / 2.0
    for d in xrange(0, p_size) :
        hist = [0] * int(Tmax)
        pmin = int(Tmax)
        pmax = 0
        src_pos = d
        for y in xrange(0, srcHeight) :
            for x in xrange(0, srcWidth) :
                pixel = src_pixels[src_pos]
                pval = int(pixel)
                hist[pval] = hist[pval] + 1
                if pmin > pval :
                    pmin = pval
                if pmax < pval :
                    pmax = pval
                src_pos = src_pos + p_size
            progress = progress + pstep
            gimp.progress_update(progress)
        # Threshold:
        thres = [-1] * int(tcount + 1)
        for tt in xrange(1, int(tcount)) :
            part = 1.0 * tt / tcount
            thres[tt] = int(threshold_bimod(hist, Tmax, part) + 0.5 + tdelta)
        newval = [0] * int(tcount + 1)
        if tmedian is True:
            thres[0] = int(pmin)
            thres[int(tcount)] = int(pmax + 1)
            for tt in xrange(0, int(tcount)) :
                sgti = 0
                sgi = 0
                t0 = thres[tt]
                if (t0 < 0):
                    t0 = 0
                t1 = thres[tt + 1]
                if (t1 > Tmax):
                    t1 = Tmax
                for ti in xrange(t0, t1) :
                    sgi = sgi + hist[ti]
                    sgti = sgti + hist[ti] * ti
                if sgi > 0 :
                    newval[tt] = byteclamp(int(sgti / sgi + 0.5))
                else :
                    newval[tt] = byteclamp(int((thres[tt] + thres[tt + 1]) / 2))
        else :
            for tt in xrange(0, int(tcount)) :
                newval[tt] = byteclamp(int(255 * tt / (tcount - 1)))
        thresval = [0] * int(Tmax)
        for tt in xrange(0, int(tcount + 1)) :
            thres[tt] = thres[tt] - 1
        for t in xrange(0, Tmax) :
            for tt in xrange(0, int(tcount)) :
                if (t > thres[tt]) :
                   thresval[t] = newval[tt]
        # Final loop:
        src_pos = d
        for y in xrange(0, srcHeight) :
            for x in xrange(0, srcWidth) :
                pixel = src_pixels[src_pos]
                newpix = thresval[int(pixel)]
                dest_pixels[src_pos] = newpix
                src_pos = src_pos + p_size
            progress = progress + pstep
            gimp.progress_update(progress)

    # Copy the whole array back to the pixel region:
    dstRgn[X0:X0+srcWidth, Y0:Y0+srcHeight] = dest_pixels.tostring()

    destDrawable.flush()
    destDrawable.merge_shadow(True)
    destDrawable.update(0, 0, srcWidth,srcHeight)

    pdb.gimp_image_undo_group_end(img)


register(
    "python-fu-colors_bimod",
    N_("Bimodal threshold color\n version 0.3.6\n Public Domain Mark 1.0"),
    "Adds a new layer to the image",
    "zvezdochiot",
    "zvezdochiot",
    "2021",
    N_("_Color BiMod..."),
    "*",
    [
        (PF_IMAGE, "image", "Input image", None),
        (PF_DRAWABLE, "drawable", "Input drawable", None),
        (PF_SPINNER, "tcount", _("Count"), 2, (2, 255, 1)),
        (PF_SPINNER, "tdelta", _("Delta"), 0, (-255, 255, 1)),
        (PF_TOGGLE, "tmedian", "Median", False),
    ],
    [],
    colors_bimod,
    menu="<Image>/Colors/Map",
    domain=("gimp20-python", gimp.locale_directory)
    )

main()
