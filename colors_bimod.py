#!/usr/bin/env python

# Gimp plugin Bimodal Threshold
# Public Domain Mark 1.0
#  No Copyright

from gimpfu import *
import time
from array import array

gettext.install("gimp20-python", gimp.locale_directory, unicode=True)

def colors_bimod(img, layer, tcount, tfore, tgray):
    gimp.progress_init("Processing" + layer.name + "...")
    pdb.gimp_undo_push_group_start(img)
    pdb.gimp_layer_add_alpha(layer)

    layername = "bimod " + layer.name
    Tmax = 768

    toffset = 0
    if tgray is True:
        toffset = 1

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

    # Histogram:
    hist = [0] * int(Tmax)
    for x in xrange(0, srcWidth) :
        for y in xrange(0, srcHeight) :
            src_pos = (x + srcWidth * y) * p_size
            dest_pos = src_pos
            pixel = src_pixels[src_pos: src_pos + p_size]
            pval = pixel[0] + pixel[1] + pixel[2]
            hist[pval] = hist[pval] + 1
    gimp.progress_update(0.5)
    # Threshold:
    thres = [0] * int(tcount + 1)
    for tt in xrange(1, int(tcount)) :
        part = 1.0 * tt / tcount
        T = Tmax * part
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
            for c in xrange(int(T + 1), int(Tmax)) :
                Tw += hist[c] * c
                iw += hist[c]
                if ((iw + ib) == 0):
                    T = Tn
                elif (iw == 0) :
                    T = Tb / ib
                elif (ib == 0) :
                    T = Tw / iw
                else :
                    T = ((Tw / iw) * part + (Tb / ib) * (1.0 - part))
        thres[tt] = int(T + 0.5)
    newval = [0] * int(tcount + 1)
    for tt in xrange(0, int(tcount)) :
        newval[tt] = int(255 * (tt + toffset) / (tcount + toffset + toffset - 1))
    gimp.progress_update(0.6)
    # Final loop:
    for x in xrange(0, srcWidth) :
        for y in xrange(0, srcHeight) :
            src_pos = (x + srcWidth * y) * p_size
            dest_pos = src_pos
            pixel = src_pixels[src_pos: src_pos + p_size]
            pval = pixel[0] + pixel[1] + pixel[2]
            newpix = pixel
            for tt in xrange(0, int(tcount)) :
                if (pval > thres[tt]) :
                    newpix[0] = newval[tt]
                    newpix[1] = newval[tt]
                    newpix[2] = newval[tt]
            dest_pixels[dest_pos : dest_pos + p_size] = newpix
    gimp.progress_update(1.0)

    # Copy the whole array back to the pixel region:
    dstRgn[X0:X0+srcWidth, Y0:Y0+srcHeight] = dest_pixels.tostring()

    destDrawable.flush()
    destDrawable.merge_shadow(True)
    destDrawable.update(0, 0, srcWidth,srcHeight)

    if tfore is True:
        layerforename = "foreground " + layer.name
        layer_copy = pdb.gimp_layer_copy (layer, 1)
        pdb.gimp_image_add_layer(img, layer_copy, -1)
        pdb.gimp_layer_set_name(layer_copy, layerforename)
        pdb.gimp_layer_set_mode(layer_copy, 13)

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
        (PF_TOGGLE, "tfore", "Foreground", False),
        (PF_TOGGLE, "tgray", "Gray", False),
    ],
    [],
    colors_bimod,
    menu="<Image>/Colors/Map",
    domain=("gimp20-python", gimp.locale_directory)
    )

main()
