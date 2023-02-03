/* GIMP Plug-in Template
 * Copyright (C) 2000  Michael Natterer <mitch@gimp.org> (the "Author").
 * All Rights Reserved.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included
 * in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
 * OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
 * THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
 * IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 *
 * Except as contained in this notice, the name of the Author of the
 * Software shall not be used in advertising or otherwise to promote the
 * sale, use or other dealings in this Software without prior written
 * authorization from the Author.
 */

#include "config.h"

#include <assert.h>
#include <gtk/gtk.h>
#include <libgimp/gimp.h>

#include "main.h"
#include "render.h"
#include "plugin-intl.h"

static gint ImageQuant (guchar* src, guchar* dst, guint width, guint height, guint channels, guint tcount, guint ch)
{
    guint y, x, k, im;

    k = ch;
    for (y = 0; y < height; y++ )
    {
        for (x = 0; x < width; x++)
        {
            im = src[k];
            im *= tcount;
            im += 127;
            im /= 255;
            im *= 255;
            im /= tcount;
            dst[k] = (guchar)(im < 255) ? im : 255;
            k += channels;
        }
    }

    return (256 / tcount);
}

static guint HistCreate (guchar* src, guint64* histogram, guint width, guint height, guint channels, guint histsize, guint ch)
{
    guint y, x, k, im;

    for (k = 0; k < histsize; k++)
    {
        histogram[k] = 0;
    }
    k = ch;
    for (y = 0; y < height; y++)
    {
        for (x = 0; x < width; x++)
        {
            im = src[k];
            histogram[im]++;
            k += channels;
        }
    }

    return histsize;
}

static guint HistBiMod (guint64* histogram, guint histsize, gdouble part)
{
    guint k, T, Tn;
    guint64 im, iw, ib, Tw, Tb;
    guint threshold = 0;

    part = (part < 0.0 || part > 1.0) ? 0.5 : part;
    T = (guint)(part * (gdouble)histsize + 0.5);
    Tn = 0;
    while ( T != Tn )
    {
        Tn = T;
        Tb = Tw = ib = iw = 0;
        for (k = 0; k < T; k++)
        {
            im = histogram[k];
            Tb += (im * k);
            ib += im;
        }
        for (k = T; k < histsize; k++)
        {
            im = histogram[k];
            Tw += (im * k);
            iw += im;
        }
        Tb /= (ib > 1) ? ib : 1;
        Tw /= (iw > 1) ? iw : 1;
        if (iw == 0 && ib == 0)
        {
            T = Tn;
        }
        else if (iw == 0)
        {
            T = (guint)Tb;
        }
        else if (ib == 0)
        {
            T = (guint)Tw;
        }
        else
        {
            T = (guint)(part * (gdouble)Tw + (1.0 - part) * (gdouble)Tb + 0.5f);
        }
    }
    threshold = (guint)T;

    return threshold;
}

static gint ImageThreshold (guchar* src, guchar* dst, guint width, guint height, guint channels, guint threshold, guint cwhite, guint ch)
{
    guint y, x, k, im;

    k = ch;
    for (y = 0; y < height; y++ )
    {
        for (x = 0; x < width; x++)
        {
            im = src[k];
            dst[k] = (guchar)((im < threshold) ? dst[k] : cwhite);
            k += channels;
        }
    }

    return threshold;
}

guint ImageTDith (guchar* src, guchar* dst, guint width, guint height, guint channels, guint wwidth, gint kpg, gint delta, guint ch)
{
    guint x, y, i, j, k, l, lmin = 0;
    guint whg, wwn, iy0, ix0, iy, ix, tt;
    guint herrmin, ww, kw;
    guint val;
    gint tx, imm, threshold = 0;
    // Knuth D.E. dither matrix
    gint dithh[16] = {1, 5, 10, 14, 3, 7, 8, 12, 13, 9, 6, 2, 15, 11, 4, 0};
    gint ditht[9] = {1, 5, 7, 3, 6, 2, 8, 4, 0};
    gint dithq[4] = {1, 2, 3, 0};
    gint dith[16], hdithy[34], hdithx[34];
    gint herr, herrp, herrg;
    wwidth = (wwidth < 2) ? 2 : (wwidth < 4) ? wwidth : 4;
    ww = wwidth * wwidth;
    kw = 256 / ww;
    k = 0;
    if (wwidth == 2)
    {
        for (y = 0; y < wwidth; y++)
        {
            for (x = 0; x < wwidth; x++)
            {
                dith[k] = dithq[k];
                k++;
            }
        }
    }
    else if (wwidth == 3)
    {
        for (y = 0; y < wwidth; y++)
        {
            for (x = 0; x < wwidth; x++)
            {
                dith[k] = ditht[k];
                k++;
            }
        }
    }
    else
    {
        for (y = 0; y < wwidth; y++)
        {
            for (x = 0; x < wwidth; x++)
            {
                dith[k] = dithh[k];
                k++;
            }
        }
    }
    k = 0;
    for (y = 0; y < wwidth; y++)
    {
        for (x = 0; x < wwidth; x++)
        {
            l = dith[k] + 1;
            hdithy[l] = y;
            hdithx[l] = x;
            hdithy[l + 17] = y;
            hdithx[l + 17] = wwidth - x - 1;
            k++;
        }
    }
    whg = (height + wwidth - 1) / wwidth;
    wwn = (width + wwidth - 1) / wwidth;
    for (y = 0; y < whg; y++)
    {
        iy0 = y * wwidth;
        for (x = 0; x < wwn; x++)
        {
            ix0 = x * wwidth;
            k = (y + x) % 2;
            imm = 0;
            for (l = 1; l < (ww + 1); l++)
            {
                j = hdithy[k * 17 + l];
                i = hdithx[k * 17 + l];
                iy = iy0 + j;
                ix = ix0 + i;
                tx = (iy < height && ix < width) ? src[(iy * width + ix) * channels + ch] : 255;
                tx += delta;
                imm += tx;
            }
            imm /= ww;
            herrp = herrg = 0;
            for (l = 1; l < (ww + 1); l++)
            {
                j = hdithy[k * 17 + l];
                i = hdithx[k * 17 + l];
                iy = iy0 + j;
                ix = ix0 + i;
                tx = (iy < height && ix < width) ? src[(iy * width + ix) * channels + ch] : 255;
                tx += delta;
                herrg += (255 - tx);
                tx -= imm;
                tx *= kpg;
                tx += imm;
                herrp += (255 - tx);
            }
            herrmin = herrp + herrg;
            lmin = 0;
            for (l = 1; l < (ww + 1); l++)
            {
                j = hdithy[k * 17 + l];
                i = hdithx[k * 17 + l];
                iy = iy0 + j;
                ix = ix0 + i;
                tx = (iy < height && ix < width) ? src[(iy * width + ix) * channels + ch] : 255;
                tx += delta;
                tx += delta;
                tx -= imm;
                tx *= kpg;
                tx += imm;
                herrp += (tx + tx - 255);
                herrg -= 255;
                herr = (herrp < 0) ? (-herrp) : herrp;
                herr += (herrg < 0) ? (-herrg) : herrg;
                if (herr < herrmin)
                {
                    herrmin = herr;
                    lmin = l;
                }
            }
            for (l = 1; l < (ww + 1); l++)
            {
                j = hdithy[k * 17 + l];
                i = hdithx[k * 17 + l];
                iy = iy0 + j;
                ix = ix0 + i;
                if (iy < height && ix < width)
                {
                    val = (l > lmin) ? 255 : 0;
                    dst[(iy * width + ix) * channels + ch] = val;
                }
            }
            tt = kw * (ww - lmin);
            threshold += tt;
        }
    }
    threshold /= whg;
    threshold /= wwn;

    return threshold;
}

void render(gint32 image_ID,
            GimpDrawable* drawable,
            PlugInVals* vals,
            PlugInImageVals* image_vals,
            PlugInDrawableVals* drawable_vals)
{
    gint x1, y1, x2, y2;
    gimp_drawable_mask_bounds(drawable->drawable_id, &x1, &y1, &x2, &y2);
    gint channels = gimp_drawable_bpp(drawable->drawable_id);
    gint width = x2 - x1;
    gint height = y2 - y1;
    guint histsize = 256;
    guint tpattern = vals->pattern;
    guint tcount = vals->threshold;
    gint d, t;
    gdouble part;
    gint *threshold, *tval;
    guint64 *histogram;
    threshold = g_new(guint, tcount + 1);
    tval = g_new(guint, tcount);
    histogram = g_new(guint64, histsize);

    GimpPixelRgn rgn_in, rgn_out;
    gimp_pixel_rgn_init(&rgn_in, drawable, x1, y1, width, height, FALSE, FALSE);
    gimp_pixel_rgn_init(&rgn_out, drawable, x1, y1, width, height, TRUE, TRUE);

    guchar* in_img_array = g_new(guchar, width * height * channels);
    gimp_pixel_rgn_get_rect(&rgn_in, in_img_array, x1, y1, width, height);

    gimp_image_undo_group_start(gimp_item_get_image(drawable->drawable_id));

    GimpDrawable* out_drawable = gimp_drawable_get(
        gimp_image_get_active_drawable(gimp_item_get_image(drawable->drawable_id)));

    GimpPixelRgn dest_rgn;
    gimp_pixel_rgn_init(&dest_rgn, out_drawable, 0, 0, width, height, TRUE, TRUE);

    const int img_array_size = width * height * channels;
    guchar* out_img_array = g_new(guchar, img_array_size);

    switch (tpattern)
    {
        case 0:
            for (d = 0; d < channels; d++)
            {
                (void)ImageQuant (in_img_array, out_img_array, width, height, channels, tcount, d);
            }
            break;
        case 1:
            for (d = 0; d < channels; d++)
            {
                for (t = 0; t < tcount + 1; t++)
                {
                    part = (gdouble)t / tcount;
                    histsize = HistCreate (in_img_array, histogram, width, height, channels, histsize, d);
                    threshold[t] = HistBiMod (histogram, histsize, part);
                }
                for (t = 0; t < tcount; t++)
                {
                    tval[t] = (threshold[t] + threshold[t + 1]) / 2;
                }
                for (t = 0; t < tcount; t++)
                {
                    (void)ImageThreshold (in_img_array, out_img_array, width, height, channels, threshold[t], tval[t], d);
                }
            }
            break;
        case 2:
        case 3:
        case 4:
            for (d = 0; d < channels; d++)
            {
                (void)ImageTDith (in_img_array, out_img_array, width, height, channels, tpattern, tcount, 0, d);
            }
            break;
        default:
            break;
    }

    gimp_pixel_rgn_set_rect(&dest_rgn, (guchar*)out_img_array, x1, y1, width, height);

    gimp_drawable_flush(out_drawable);
    gimp_drawable_merge_shadow(out_drawable->drawable_id, TRUE);
    gimp_drawable_update(out_drawable->drawable_id, x1, y1, width, height);
    gimp_drawable_detach(out_drawable);

    g_free(tval);
    g_free(threshold);
    g_free(histogram);
    g_free(out_img_array);
    g_free(in_img_array);
    gimp_image_undo_group_end(gimp_item_get_image(drawable->drawable_id));
}
