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

def colors_dith(img, layer, tcount, tdelta, kpg):
    gimp.progress_init("Processing " + layer.name + "...")
    pdb.gimp_undo_push_group_start(img)
    pdb.gimp_layer_add_alpha(layer)
    hdith = [ 1,  5, 10, 14 ,  3,  7,  8, 12 , 13,  9,  6,  2 , 15, 11,  4,  0 ]
    tdith = [ 1, 5, 7 , 3, 6, 2 , 8, 4, 0 ]
    qdith = [ 1, 2, 3, 0 ]
    dithy = [0] * 34
    dithx = [0] * 34
    wwidth = int(tcount)
    if (wwidth < 2):
        wwidth = 2
    if (wwidth > 4):
        wwidth = 4
    ww = wwidth * wwidth
    kw = 256 / ww
    dith = qdith
    if (wwidth == 3):
        dith = tdith
    if (wwidth == 4):
        dith = hdith
    src_pos = 0;
    for y in xrange(0, wwidth) :
        for x in xrange(0, wwidth) :
            l = int(dith[src_pos] + 1)
            dithy[l] = y
            dithx[l] = x
            dithy[l + 17] = y
            dithx[l + 17] = wwidth - x - 1
            src_pos = src_pos + 1

    layername = layer.name + "-dith-" + str(int(tcount))

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

    # Finally, loop over the region:
    whg = int((srcHeight + wwidth - 1) / wwidth)
    wwn = int((srcWidth + wwidth - 1) / wwidth)
    pixh = [0] * srcHeight
    pixw = [0] * srcWidth
    yline = srcWidth * p_size
    yt = 0
    pstep = (1.0 - progress) / srcHeight * tcount
    for y in xrange(0, srcHeight) :
        pixh[y] = yt
        yt = yt + yline
    xt = 0
    for x in xrange(0, srcWidth) :
        pixw[x] = xt
        xt = xt + p_size
    iy0 = 0
    for y in xrange(0, whg) :
        ix0 = 0
        for x in xrange(0, wwn) :
            k = ((y + x) % 2) * 17
            for d in xrange(0, p_size) :
                imm = 0
                for l in xrange(1, (ww + 1)) :
                    j = dithy[k + l]
                    i = dithx[k + l]
                    iy = iy0 + j
                    ix = ix0 + i
                    tx = 255
                    if (iy < srcHeight) and (ix < srcWidth) :
                        src_pos = pixh[iy] + pixw[ix] + d
                        tx = src_pixels[src_pos]
                    tx = tx + tdelta
                    imm = imm + tx
                imm = imm / ww
                herrp = 0
                herrg = 0
                for l in xrange(1, (ww + 1)) :
                    j = dithy[k + l]
                    i = dithx[k + l]
                    iy = iy0 + j
                    ix = ix0 + i
                    tx = 255
                    if ((iy < srcHeight) and (ix < srcWidth)) :
                        src_pos = pixh[iy] + pixw[ix] + d
                        tx = src_pixels[src_pos]
                    tx = tx + tdelta
                    herrg = herrg + (255 - tx)
                    tx = (tx - imm) * kpg + imm
                    tx = byteclamp(int(tx))
                    herrp = herrp + (255 - tx)
                herrmin = herrp + herrg
                lmin = 0
                for l in xrange(1, (ww + 1)) :
                    j = dithy[k + l]
                    i = dithx[k + l]
                    iy = iy0 + j
                    ix = ix0 + i
                    tx = 255
                    if ((iy < srcHeight) and (ix < srcWidth)) :
                        src_pos = pixh[iy] + pixw[ix] + d
                        tx = src_pixels[src_pos]
                    tx = tx + tdelta
                    tx = (tx - imm) * kpg + imm
                    tx = byteclamp(int(tx))
                    herrp = herrp + (tx + tx - 255)
                    herrg = herrg - 255
                    herr = 0
                    if (herrp < 0) :
                        herr = herr - herrp
                    else :
                        herr = herr + herrp
                    if (herrg < 0) :
                        herr = herr - herrg
                    else :
                        herr = herr + herrg
                    if (herr < herrmin) :
                        herrmin = herr
                        lmin = l
                for l in xrange(1, (ww + 1)) :
                    j = dithy[k + l]
                    i = dithx[k + l]
                    iy = iy0 + j
                    ix = ix0 + i
                    tx = 255
                    if ((iy < srcHeight) and (ix < srcWidth)) :
                        src_pos = pixh[iy] + pixw[ix] + d
                        if (l > lmin) :
                            tx = 255
                        else :
                            tx = 0
                        dest_pixels[src_pos] = tx
            ix0 = ix0 + wwidth
        iy0 = iy0 + wwidth

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
    "python-fu-colors_dith",
    N_("Dither color\n version 0.3.5\n Public Domain Mark 1.0\n(Knuth D.E. dither matrix)"),
    "Adds a new layer to the image",
    "zvezdochiot",
    "zvezdochiot",
    "2021",
    N_("_Color Dith..."),
    "*",
    [
        (PF_IMAGE, "image", "Input image", None),
        (PF_DRAWABLE, "drawable", "Input drawable", None),
        (PF_SPINNER, "tcount", _("Count"), 2, (2, 4, 1)),
        (PF_SPINNER, "tdelta", _("Delta"), 0, (-255, 255, 1)),
        (PF_SPINNER, "kpg",  _("KPG"),   2, (-1, 10, 0.1)),
    ],
    [],
    colors_dith,
    menu="<Image>/Colors/Map",
    domain=("gimp20-python", gimp.locale_directory)
    )

main()
