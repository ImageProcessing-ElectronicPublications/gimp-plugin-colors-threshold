#!/usr/bin/env python

# Gimp plugin Dith
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

def colors_quant(img, layer, red, green, blue, alpha):
    gimp.progress_init("Processing " + layer.name + "...")
    pdb.gimp_undo_push_group_start(img)
    pdb.gimp_layer_add_alpha(layer)

    layername = layer.name + "-quant-" + str(int(red)) + "-" + str(int(green)) + "-" + str(int(blue))

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
    pixt = [0] * p_size
    pixt[0] = red
    if (p_size > 1) :
        pixt[1] = green
    if (p_size > 2) :
        pixt[2] = blue
    if (p_size > 3) :
        pixt[3] = alpha
    progress = 0.1
    gimp.progress_update(progress)

    # Finally, loop over the region:
    pstep = (1.0 - progress) / srcHeight / p_size
    for d in xrange(0, p_size) :
        src_pos = d
        color_div = pixt[d] / 256.0
        color_mult = 255.0 / (pixt[d] - 1)
        for y in xrange(0, srcHeight) :
            for x in xrange(0, srcWidth) :
                dest_pos = src_pos
                newval = src_pixels[src_pos]
                newval = int(int(newval * color_div) * color_mult)
                dest_pixels[src_pos] = byteclamp(newval)
                src_pos = src_pos + p_size
            progress = progress + pstep
            gimp.progress_update(progress)

    # Copy the whole array back to the pixel region:
    dstRgn[X0:X0+srcWidth, Y0:Y0+srcHeight] = dest_pixels.tostring()

    destDrawable.flush()
    destDrawable.merge_shadow(True)
    destDrawable.update(0, 0, srcWidth,srcHeight)

    # Remove the old layer
    #img.remove_layer(layer)
    #layer.visible = False

    pdb.gimp_selection_none(img)
    pdb.gimp_image_undo_group_end(img)


register(
    "python-fu-colors_quant",
    N_("reduce colors to simulate a different palettes.\n version 0.3.5\n Public Domain Mark 1.0\n\n2bit = 4 colors\n3bit = 8 colors\n4bit = 16 colors\n5bit = 32 colors\n8bit = 256 colors"),
    "Adds a new layer to the image",
    "William Bell",
    "William Bell",
    "2015",
    N_("_Color Quant..."),
    "*",
    [
        (PF_IMAGE, "image",       "Input image", None),
        (PF_DRAWABLE, "drawable", "Input drawable", None),
        (PF_SPINNER, "red", _("Red"), 8, (2, 256, 1)),
        (PF_SPINNER, "blue", _("Green"), 8, (2, 256, 1)),
        (PF_SPINNER, "green", _("Blue"), 8, (2, 256, 1)),
        (PF_SPINNER, "alpha", _("Alpha"), 8, (2, 256, 1)),
    ],
    [],
    colors_quant,
    menu="<Image>/Colors/Map",
    domain=("gimp20-python", gimp.locale_directory)
    )

main()
