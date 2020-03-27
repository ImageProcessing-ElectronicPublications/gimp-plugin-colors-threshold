#!/usr/bin/env python

# Gimp plugin Bimodal Threshold
# Public Domain Mark 1.0
#  No Copyright

from gimpfu import *
import time
from array import array

gettext.install("gimp20-python", gimp.locale_directory, unicode=True)

def threshold_bimod(hist, tsize, tpart):
    T = tsize * tpart
    Tn = 0
    while (T != Tn) :

        Tn = T
        Tb = 0
        Tw = 0
        ib = 0
        iw = 0
        for c in xrange(0, int(T)) :
            Tb += hist[c] * c
            ib += hist[c]
        for c in xrange(int(T + 1), int(tsize)) :
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

def colors_bimod(img, layer, tcount, tchannels, tgray):
    gimp.progress_init("Processing" + layer.name + "...")
    pdb.gimp_undo_push_group_start(img)
    pdb.gimp_layer_add_alpha(layer)

    layername = "bimod " + layer.name

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
    gimp.progress_update(0.2)

    if tchannels is True:
        # Histogram:
        Tmax = 256
        hist_r = [0] * int(Tmax)
        hist_g = [0] * int(Tmax)
        hist_b = [0] * int(Tmax)
        pmin_r = int(Tmax)
        pmax_r = 0
        pmin_g = int(Tmax)
        pmax_g = 0
        pmin_b = int(Tmax)
        pmax_b = 0
        for x in xrange(0, srcWidth) :
            for y in xrange(0, srcHeight) :
                src_pos = (x + srcWidth * y) * p_size
                dest_pos = src_pos
                pixel = src_pixels[src_pos: src_pos + p_size]
                pval = pixel[0]
                hist_r[pval] = hist_r[pval] + 1
                if pmin_r > pval :
                    pmin_r = pval
                if pmax_r < pval :
                    pmax_r = pval
                pval = pixel[1]
                hist_g[pval] = hist_g[pval] + 1
                if pmin_g > pval :
                    pmin_g = pval
                if pmax_g < pval :
                    pmax_g = pval
                pval = pixel[2]
                hist_b[pval] = hist_b[pval] + 1
                if pmin_b > pval :
                    pmin_b = pval
                if pmax_b < pval :
                    pmax_b = pval
        gimp.progress_update(0.5)
        # Threshold:
        thres_r = [-1] * int(tcount + 1)
        thres_g = [-1] * int(tcount + 1)
        thres_b = [-1] * int(tcount + 1)
        for tt in xrange(1, int(tcount)) :
            part = 1.0 * tt / tcount
            thres_r[tt] = int(threshold_bimod(hist_r, Tmax, part) + 0.5)
            thres_g[tt] = int(threshold_bimod(hist_g, Tmax, part) + 0.5)
            thres_b[tt] = int(threshold_bimod(hist_b, Tmax, part) + 0.5)
        newval_r = [0] * int(tcount + 1)
        newval_g = [0] * int(tcount + 1)
        newval_b = [0] * int(tcount + 1)
        if tgray is True:
            thres_r[0] = int(pmin_r)
            thres_g[0] = int(pmin_g)
            thres_b[0] = int(pmin_b)
            thres_r[int(tcount)] = int(pmax_r)
            thres_g[int(tcount)] = int(pmax_g)
            thres_b[int(tcount)] = int(pmax_b)
            for tt in xrange(0, int(tcount)) :
                newval_r[tt] = int((thres_r[tt] + thres_r[tt + 1]) / 2)
                newval_g[tt] = int((thres_g[tt] + thres_g[tt + 1]) / 2)
                newval_b[tt] = int((thres_b[tt] + thres_b[tt + 1]) / 2)
            thres_r[0] = -1
            thres_g[0] = -1
            thres_b[0] = -1
        else :
            for tt in xrange(0, int(tcount)) :
                newval_r[tt] = int(255 * tt / (tcount - 1))
                newval_g[tt] = newval_r[tt]
                newval_b[tt] = newval_r[tt]
        thresval_r = [0] * int(Tmax)
        thresval_g = [0] * int(Tmax)
        thresval_b = [0] * int(Tmax)
        for t in xrange(0, Tmax) :
            for tt in xrange(0, int(tcount)) :
                if (t > thres_r[tt]) :
                    thresval_r[t] = newval_r[tt]
                if (t > thres_g[tt]) :
                    thresval_g[t] = newval_g[tt]
                if (t > thres_b[tt]) :
                    thresval_b[t] = newval_b[tt]
        gimp.progress_update(0.6)
        # Final loop:
        for x in xrange(0, srcWidth) :
            for y in xrange(0, srcHeight) :
                src_pos = (x + srcWidth * y) * p_size
                dest_pos = src_pos
                pixel = src_pixels[src_pos: src_pos + p_size]
                newpix = pixel
                newpix[0] = thresval_r[int(pixel[0])]
                newpix[1] = thresval_g[int(pixel[1])]
                newpix[2] = thresval_b[int(pixel[2])]
                dest_pixels[dest_pos : dest_pos + p_size] = newpix
    else :
        # Histogram:
        Tmax = 768
        hist = [0] * int(Tmax)
        pmin = int(Tmax)
        pmax = 0
        for x in xrange(0, srcWidth) :
            for y in xrange(0, srcHeight) :
                src_pos = (x + srcWidth * y) * p_size
                dest_pos = src_pos
                pixel = src_pixels[src_pos: src_pos + p_size]
                pval = pixel[0] + pixel[1] + pixel[2]
                hist[pval] = hist[pval] + 1
                if pmin > pval :
                    pmin = pval
                if pmax < pval :
                    pmax = pval
        gimp.progress_update(0.5)
        # Threshold:
        thres = [-1] * int(tcount + 1)
        for tt in xrange(1, int(tcount)) :
            part = 1.0 * tt / tcount
            thres[tt] = int(threshold_bimod(hist, Tmax, part) + 0.5)
        newval = [0] * int(tcount + 1)
        if tgray is True:
            thres[0] = int(pmin)
            thres[int(tcount)] = int(pmax)
            for tt in xrange(0, int(tcount)) :
                newval[tt] = int((thres[tt] + thres[tt + 1]) / 6)
            thres[0] = -1
        else :
            for tt in xrange(0, int(tcount)) :
                newval[tt] = int(255 * tt / (tcount - 1))
        thresval = [0] * int(Tmax)
        for t in xrange(0, Tmax) :
            for tt in xrange(0, int(tcount)) :
                if (t > thres[tt]) :
                    thresval[t] = newval[tt]
        gimp.progress_update(0.6)
        # Final loop:
        for x in xrange(0, srcWidth) :
            for y in xrange(0, srcHeight) :
                src_pos = (x + srcWidth * y) * p_size
                dest_pos = src_pos
                pixel = src_pixels[src_pos: src_pos + p_size]
                pval = pixel[0] + pixel[1] + pixel[2]
                newpix = pixel
                newpt = thresval[int(pval)]
                newpix[0] = newpt
                newpix[1] = newpt
                newpix[2] = newpt
                dest_pixels[dest_pos : dest_pos + p_size] = newpix
    gimp.progress_update(1.0)

    # Copy the whole array back to the pixel region:
    dstRgn[X0:X0+srcWidth, Y0:Y0+srcHeight] = dest_pixels.tostring()

    destDrawable.flush()
    destDrawable.merge_shadow(True)
    destDrawable.update(0, 0, srcWidth,srcHeight)

    pdb.gimp_image_undo_group_end(img)


register(
    "python-fu-colors_bimod",
    N_("Bimodal threshold color"),
    "Adds a new layer to the image",
    "zvezdochiot",
    "zvezdochiot",
    "2020",
    N_("_BiMod..."),
    "RGB*",
    [
        (PF_IMAGE, "image",       "Input image", None),
        (PF_DRAWABLE, "drawable", "Input drawable", None),
        (PF_SPINNER, "tcount",    _("Count"),    2, (2, 765, 1)),
        (PF_TOGGLE, "tchannels", "Channels", False),
        (PF_TOGGLE, "tgray", "Gray", False),
    ],
    [],
    colors_bimod,
    menu="<Image>/Colors/Map",
    domain=("gimp20-python", gimp.locale_directory)
    )

main()
