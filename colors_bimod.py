#!/usr/bin/env python

# Gimp plugin Bimodal Threshold
# Public Domain Mark 1.0
#  No Copyright

from gimpfu import *
import time
from array import array

gettext.install("gimp20-python", gimp.locale_directory, unicode=True)

def colors_bimod(img, layer, tcount):
    gimp.progress_init("Processing" + layer.name + "...")
    pdb.gimp_undo_push_group_start(img)
    layer_copy = pdb.gimp_layer_copy (layer, 1)
    pdb.gimp_image_add_layer(img, layer_copy, -1)

    layername = "bimod " + layer.name

    # Create the new layer:
    srcWidth, srcHeight = layer.width, layer.height

    destDrawable = gimp.Layer(img, layername, srcWidth, srcHeight,
                              layer_copy.type, layer_copy.opacity, layer_copy.mode)
    img.add_layer(destDrawable, 1)
    pdb.gimp_layer_set_mode(layer_copy, 13)
    xoff, yoff = layer.offsets

    destDrawable.translate(xoff, yoff)

    srcRgn = layer_copy.get_pixel_rgn(0, 0, srcWidth, srcHeight, False, False)
    src_pixels = array("B", srcRgn[0:srcWidth, 0:srcHeight])

    dstRgn = destDrawable.get_pixel_rgn(0, 0, srcWidth, srcHeight, True, True)
    p_size = len(srcRgn[0,0])
    dest_pixels = array("B", [0] * (srcWidth * srcHeight * p_size))
    gimp.progress_update(0.2)

    # Histogram:
    hist = [0] * 768
    for x in xrange(0, srcWidth - 1) :
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
        T = 765 * part
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
            for c in xrange(int(T + 1), 765) :
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
    gimp.progress_update(0.6)
    # Final loop:
    for x in xrange(0, srcWidth - 1) :
        for y in xrange(0, srcHeight) :
            src_pos = (x + srcWidth * y) * p_size
            dest_pos = src_pos
            pixel = src_pixels[src_pos: src_pos + p_size]
            pval = pixel[0] + pixel[1] + pixel[2]
            newval = 0
            for tt in xrange(0, int(tcount)) :
                if (pval > thres[tt]) :
                    newval = int(255 * tt / (tcount - 1))
            newpix = pixel
            newpix[0] = newval
            newpix[1] = newval
            newpix[2] = newval
            dest_pixels[dest_pos : dest_pos + p_size] = newpix
    gimp.progress_update(1.0)

    # Copy the whole array back to the pixel region:
    dstRgn[0:srcWidth, 0:srcHeight] = dest_pixels.tostring()

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
    ],
    [],
    colors_bimod,
    menu="<Image>/Colors/Map",
    domain=("gimp20-python", gimp.locale_directory)
    )

main()
