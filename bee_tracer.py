#!/usr/bin/env python3


# -----------------------------------------------------------------------------
# Parse command-line arguments to track bees in video images.
#
def track():
    doc = '''
This program displays the flight paths of bees exiting and entering a hive by analyzing
a sequence of video image frames.  It can combine the video frame images to make a single
images showing lines tracking each bee, and it can make a copy of the video frames with
lines added that trace the bee flight paths.
'''
    details = '''
This program reads image files (e.g. png, jpeg, ppm formats) and cannot read video formats
directly.  To convert video to individual images frames you can use the ffmpeg program
with a command like "ffmpeg -i beevideo.mp4 image-%04d.png".  This program writes images.
To assemble a video with animated tracks use "ffmpeg -i track-%04d.png track.mp4"

This program requires Python (tested with version 2.7.5), and two Python libraries:
the Python Image Library (tested with version 1.1.7) for reading and writing images,
and numpy (tested with version 1.6.2) for doing the image analysis.  The Python Image
Library is currently (2014) not available for Python 3.  I tested on Mac OS 10.6 and 10.9.
The code should work on Linux and Windows as Python, PIL, numpy and ffmpeg are available
on all 3 operating systems.

The method for finding bee tracks is to compute an average image which represents the
static background of the video (hive box, plants, ...) then compare each video frame to
the average looking for differences which are flying bees.  A bee is identified by looking
for pixel positions in frames that differ from the average background by more than a specified
threshold.  The difference image is first smoothed to reduce false detections due to noise.
Then local maxima in the difference image are found.  Weaker maxima are eliminated if they
are too close to another maxima.  This avoids having one bee produce several maxima in a given
image frame.  Then maxima in consecutive frames and close in space are joined to form a path.
The average image uses a moving window, typically consisting of 30 frames before and 30 frames
after the analyzed image frame or 1 second before and after for video at 30 frames / second.
A short time average is desirable to avoid changes in brightness due to moving clouds.
The method for tracking a bee from frame to frame is very basic.  It starts at a bee position
in one frame and looks for the nearest bee position in the next frame. From that next frame
position it looks back to see if the nearest position in the current frame is the position
we started with, if not it rejects that connection.  It also does not accept bee motions
from one frame to the next greater than 4 times the motion for that bee in the previous frame.
If a next frame position for a bee is not found it will look ahead one more frame, to account
for cases where a bee was not seen in a frame most likely because it was against a similar
color background.  Paths are extended forward and backward in time and a bee position can
only be used in one path.  If an extrapolated path goes outside the image frame, then the
nearest position in the next frame is not used and the path terminates.  No momentum requirement
that prevents the bee from reversing direction too fast is imposed.  There is currently no
code that rejects small plant motions -- so they are often seen as bee tracks when the wind
blows small leaves or flowers.

This code was tested with video at 640 x 480 pixels (small to speed up processing) with
the camera about 2 meters from the hive entrance. The camera is on a tripod.  Hand-held video
is unlikely to work due to small camera motions.  This code does not do any image stabilization.
Example output is shown at

  http://sonic.net/~goddard/home/bees/bees.html

This program was just a weekend experiment, so its algorithm is primitive, and the implementation
is sloppy and slow.  It will probably require fiddling with parameters such as the threshold and
spacing to work with videos with different resolution, lighting, or distance from bees.
'''

    import argparse
    p = argparse.ArgumentParser(description=doc, epilog=details,
                                formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument('image_file_pattern', metavar='image_pattern',
                   help='File name pattern for input images.')
    p.add_argument('--start', dest='first_frame', metavar='i',
                   type=int, default=1,
                   help='First image frame file suffix number. Default %(default)s.')
    p.add_argument('--end', dest='last_frame', metavar='j',
                   type=int, default=60,
                   help='Last image frame file suffix number. Default %(default)s.')
    p.add_argument('--window', dest='averaging_window', metavar='n',
                   type=int, default=61,
                   help='Number of frames in moving average for background image. Default %(default)s.')
    p.add_argument('--smooth', dest='smoothing_steps', metavar='n',
                   type=int, default=8, help=
                   '''
                   Difference images (image minus average image) are smoothed where
                   each smoothing step sums adds to each pixel 1/4 times the four closest
                   neighbor pixels and divides by 2. Default %(default)s.
                   ''')
    p.add_argument('--threshold', dest='threshold', metavar='level',
                   type=float, default=10.0, help=
                   '''
                   Minimum color variation from background for detection.
                   Variation is sqrt(r*r + g*g + b*b) where r,g,b = color difference.
                   Color component range is usually 0-255. Default %(default)s.
                   ''')
    p.add_argument('--spacing', dest='maxima_spacing', metavar='d',
                   type=float, default=12.0, help=
                   '''
                   Minimum number of pixels between detected maxima in difference images.
                   A maximum position is removed if some higher maximum is closer
                   than this number of pixels. Default %(default)s.
                   ''')
    p.add_argument('--color', dest='color_mode', choices=('same', 'solid', 'time'),
                   default='same', help=
                   '''
                   How the color is chosen for coloring spots on the images where
                   variation is above the threshold.  Choices are "same", "solid", or "time".
                   Solid colors high variation pixels red.  Time colors
                   pixels by the frame number where highest variation
                   was seen proceeding from first to last frame using rainbow colors
                   red, orange, yellow, green, cyan, blue.  Same means colors
                   the spot using the color from the image having largest variation from average.
                   This superimposes the bees from all frames in one image. Default %(default)s.
                   ''')
    p.add_argument('--nolines', dest='draw_lines',
                   action='store_false', default=True, help=
                   '''
                   Draw line tracks tracing bee paths on average image.  Green lines are
                   used for accelerating motions, usually bees flying away from hive, otherwise red.
                   Bee locations for each frame are shown with yellow dots, with a yellow square
                   at the end of tracks where bees are in the final image frame.
                   ''')
    p.add_argument('--animate', dest='animate', action='store_true',
                   default=False, help=
                   '''
                   Output each image frame with colored lines added for bee tracks.
                   The line shows the start of the bee track up to the position in the current frame.
                   The current end of a track (current bee location) is marked with a yellow square.
                   For frames after a bee track ends, the track line will be shortened
                   from where the track starts by N segments if the current frame is N frames beyond
                   the end frame of the track.  This makes the tracks gradually disappear instead
                   of suddenly vanishing.
                   ''')
    p.add_argument('--ave', dest='average_image_file', metavar='file', help=
    'File to save average of images with no smoothing or windowing. Default %(default)s.')
    p.add_argument('--var', dest='variation_image_file', metavar='file', help=
    'File to save variation of images with no smoothing or windowing. Default %(default)s.')
    p.add_argument('--out', dest='tracks_image_file', metavar='file', default='tracks.png', help=
    'File for image of all tracks superimposed on average image. Default %(default)s.')
    p.add_argument('--vidout', dest='animation_image_file_pattern', metavar='file_pat',
                   default='track-%04d.png', help=
                   'File pattern for output frames with bee track lines. Default %(default)s.')
    p.add_argument('--verbose', dest='verbose', metavar='n', type=int, default=0,
                   help='Print diagnostic output for values 1 or larger. Default %(default)s.')

    a = p.parse_args()

    image_files = [a.image_file_pattern % i for i in range(a.first_frame, a.last_frame + 1)]

    if a.average_image_file or a.variation_image_file:
        image_average_and_variation(image_files, a.average_image_file, a.variation_image_file)

    if a.tracks_image_file or a.animate:
        anim_pat = a.animation_image_file_pattern if a.animate else None
        ti = tracks_image(image_files, a.averaging_window, a.threshold,
                          a.smoothing_steps, a.maxima_spacing,
                          a.color_mode, a.draw_lines, anim_pat, a.verbose)
        if a.tracks_image_file:
            ti.save(a.tracks_image_file)


# -----------------------------------------------------------------------------
# Color average image in regions where maximum variation from average is above a threshold.
# Can use "same", "solid", or "time" to color pixels with variation above threshold.
# If show_tracks is true then draw tracks between maxima in variation above threshold.
#
def tracks_image(image_files, averaging_window, threshold, smoothing_steps=8, maxima_spacing=10,
                 color_mode='same', draw_lines=True, animation_image_files='track-%04d.png',
                 verbose=0):
    c, f, vmax, maxima = variation(image_files, averaging_window, threshold,
                                   smoothing_steps, maxima_spacing, verbose)
    mask = (vmax >= threshold)
    vari = composite_image(c, f, mask, color_mode)

    if draw_lines:
        plist = trace_paths(maxima, vari.size, verbose)
        if verbose:
            print('Drawing tracks')
        draw_tracks(vari, plist, maxima, len(image_files))
        if animation_image_files:
            animate_tracks(image_files, plist, animation_image_files, verbose)

    return vari


# -----------------------------------------------------------------------------
# Compute maximum color variation among all images from average image
# at each pixel and record color of maximum variation.  Variation is
# computed as sum of squares of RGB change.  For each image compute positions
# of maximum variation after smoothing.  Exclude positions that are close
# to maximum positions in same image.
#
def variation(image_files, averaging_window, threshold,
              smoothing_steps, maxima_spacing, verbose=0):
    from PIL import Image
    from numpy import zeros, float32, int32, empty, array
    from numpy import subtract, multiply, sum, putmask, sqrt

    # Initialize averaging window image data.
    n = len(image_files)
    ia = averaging_window / 2  # Window images after current image
    ib = (averaging_window - 1) - ia  # Window images before current image
    ie = max(ia - n, 0)  # Window images beyond end of image list
    imr = [array(Image.open(p)) for p in image_files[:ia + 1 - ie]]  # Read images
    im = [None] * ib + imr + [None] * ie  # Window images
    im0 = imr[0]
    asum = im0.astype(int32)  # Sum of window images.
    for a in imr[1:]:
        asum += a

    size = im0.shape[:2]
    vmax = zeros(size, float32)  # Maximum variation
    imax = zeros(size, int32)  # Image index of max variation
    c = im0.copy()  # Color for largest variation
    da = empty(im0.shape, float32)  # Temporary array
    sda2 = empty(size, float32)  # Temporary array
    maxima = []  # Maximum points for each image.
    for i, file in enumerate(image_files):
        # Compute window image average
        off_end = max(0, ib - i) + max(0, ia - (n - 1 - i))
        ic = averaging_window - off_end
        avef = asum / float(ic)

        # Compute maximum variation per pixel.
        a = im[ib]
        subtract(a, avef, da)
        sda = smooth_image(da, smoothing_steps)
        multiply(sda, sda, sda)
        sum(sda, axis=2, out=sda2)
        v = (sda2 > vmax)
        putmask(imax, v, i)
        for k in (0, 1, 2):
            putmask(c[:, :, k], v, a[:, :, k])
        putmask(vmax, v, sda2)

        # Compute maxima of image variation.
        mp = maximum_positions(sda2, threshold * threshold, maxima_spacing)
        if verbose >= 1:
            print ('Image %d has %d maxima' % (i, len(mp)))
        maxima.append(mp)

        # Read next image and update image sum.
        il = i + ia + 1
        if il < n:
            l = array(Image.open(image_files[il]))
            asum += l
        else:
            l = None
        if not im[0] is None:
            asum -= im[0]
        im = im[1:] + [l]

    vmax = sqrt(vmax)
    return c, imax, vmax, maxima


# -----------------------------------------------------------------------------
# Color masked image region either a constant color, or color
# coded by frame number f, or colored from maximum variation image c.
#
def composite_image(c, f, mask, color_mode):
    if color_mode in ('time', 'solid'):
        if color_mode == 'time':
            fmin, fmax = f.min(), f.max()
            colors = ((1, 0, 0), (1, 0.5, 0), (1, 1, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1))
            cmap = color_map(colors, fmax - fmin + 1, c.dtype, offset=fmin)
            vc = cmap[f]
        elif color_mode == 'solid':
            from numpy import empty
            vc = empty(c.shape, c.dtype)
            vc[:, :] = (255, 0, 0)  # red
        var = c.copy()
        from numpy import putmask
        for k in range(c.shape[2]):
            putmask(var[:, :, k], mask, vc[:, :, k])
    elif color_mode == 'same':
        var = c
    else:
        raise ValueError('Unknown color mode "%s"' % color_mode)

    from PIL import Image
    vari = Image.fromarray(var)
    return vari


# -----------------------------------------------------------------------------
#
def color_map(colors, size, dtype, rgb_max=255, offset=0):
    n = len(colors)
    import numpy
    cmap = numpy.zeros((size + offset, 3), dtype)
    for i in range(size):
        j = float((n - 1) * i) / size
        j0 = int(j)
        f = j - j0
        c = tuple(int(rgb_max * ((1 - f) * c0 + f * c1))
                  for c0, c1 in zip(colors[j0], colors[j0 + 1]))
        cmap[i, :] = c
    return cmap


# -----------------------------------------------------------------------------
#
def image_average_and_variation(image_files, ave_file=None, var_file=None):
    from PIL import Image
    import numpy
    asum = asum2 = None
    for file in image_files:
        pi = Image.open(file)
        pa = numpy.array(pi)
        paf = pa.astype(numpy.float32)
        if asum is None:
            asum = paf
            asum2 = paf * paf
        else:
            asum += paf
            asum2 += paf * paf
    n = len(image_files)
    asum /= n
    aave = asum.astype(pa.dtype)
    asum2 /= n
    var = numpy.sqrt(asum2 - asum * asum)
    avar = var.astype(pa.dtype)
    if ave_file:
        avei = Image.fromarray(aave)
        avei.save(ave_file)
    if var_file:
        vari = Image.fromarray(avar)
        vari.save(var_file)
    return aave, avar


# -----------------------------------------------------------------------------
#
def maximum_positions(a, threshold, spacing=0):
    m = (a[:, :] >= threshold)
    from numpy import logical_and, array
    logical_and(m[:-1, :], a[:-1, :] > a[1:, :], m[:-1, :])
    logical_and(m[1:, :], a[1:, :] > a[:-1, :], m[1:, :])
    logical_and(m[:, :-1], a[:, :-1] > a[:, 1:], m[:, :-1])
    logical_and(m[:, 1:], a[:, 1:] > a[:, :-1], m[:, 1:])
    y, x = m.nonzero()
    points = array((x, y)).transpose()
    p = remove_nearby_points(points, spacing, a)
    return p


# -----------------------------------------------------------------------------
#
def remove_nearby_points(points, dmin, a):
    if dmin <= 0:
        return points
    remove = set()
    ap = a[points[:, 1], points[:, 0]]
    s = ap.argsort()
    n = len(points)
    for i in range(n):
        if not s[i] in remove:
            for j in range(i + 1, n):
                if not s[j] in remove:
                    step = points[s[j]] - points[s[i]]
                    if (step * step).sum() < dmin * dmin:
                        remove.add(s[j])
    from numpy import array, int32
    p = array(tuple(points[i] for i in range(n) if not i in remove), int32)
    return p


# -----------------------------------------------------------------------------
#
def smooth_image(a, n=1):
    from numpy import float32, empty, multiply, add
    dtype = a.dtype
    f = a.astype(float32)
    s = empty(a.shape, float32)
    st, sb, sr, sl = s[1:, :], s[:-1, :], s[:, 1:], s[:, :-1]
    ft, fb, fr, fl = f[1:, :], f[:-1, :], f[:, 1:], f[:, :-1]
    for i in range(n):
        multiply(f, 4.0, s)
        add(st, fb, st)
        add(sb, ft, sb)
        add(sr, fl, sr)
        add(sl, fr, sl)
        multiply(s, 1.0 / 8, f)

    return f.astype(dtype)


# -----------------------------------------------------------------------------
#
def trace_paths(maxima, bounds, verbose):
    plist = []
    used = set()
    n = len(maxima)
    from numpy import array
    for f in range(n - 1):
        if verbose:
            print('Connecting paths in frame %d' % f)
        pl = len(maxima[f])
        for i in range(pl):
            if not (f, i) in used:
                x, y = maxima[f][i]
                p = [(f, x, y, i)]
                trace_path(p, maxima, bounds, used)
                if len(p) >= 3:
                    plist.append(array(p)[:, :3])
                else:
                    for fxyi in p:
                        used.remove((fxyi[0], fxyi[3]))
    return plist


# -----------------------------------------------------------------------------
#
def trace_path(path, maxima, bounds, used):
    for dir in (1, -1):
        while (trace_step(path, maxima, bounds, used, dir) or
                   (len(path) >= 3 and
                        trace_step(path, maxima, bounds, used, 2 * dir))):
            continue


# -----------------------------------------------------------------------------
#
def trace_step(path, maxima, bounds, used, dir=1):
    f, x, y, i = path[-1] if dir > 0 else path[0]
    used.add((f, i))
    pf = maxima[f]
    fn = f + dir
    if fn < 0 or fn >= len(maxima):
        return False
    pfn = maxima[fn]
    if len(path) == 1:
        k = nearest(pf[i], pfn)
        if (fn, k) in used:
            return False
        i2 = nearest(pfn[k], pf)
        if i2 != i:
            return False
    else:
        fp, xp, yp, ip = path[-2] if dir > 0 else path[1]
        pfp = maxima[fp]
        step = (pf[i] - pfp[ip]) * (float(dir) / (f - fp))
        xt, yt = pt = pf[i] + step
        if xt < 0 or xt >= bounds[0] or yt < 0 or yt >= bounds[1]:
            return False
        k = nearest(pt, pfn)
        if (fn, k) in used:
            return False
        e = pfn[k] - pt
        if length(e) > 4 * length(step):
            return
        if length(e) > 0.5 * length(step):
            i2 = nearest(pfn[k] - step, pf)
            if i2 != i:
                return False

    txy = (fn, pfn[k][0], pfn[k][1], k)
    if dir > 0:
        path.append(txy)
    else:
        path.insert(0, txy)
    return True


# -----------------------------------------------------------------------------
#
def length(v):
    from math import sqrt
    return sqrt((v * v).sum())


# -----------------------------------------------------------------------------
#
def nearest(p, plist):
    d = plist - p
    d *= d
    i = d.sum(axis=1).argmin()
    return i


# -----------------------------------------------------------------------------
#
def draw_tracks(vari, plist, maxima, n):
    from PIL import ImageDraw
    d = ImageDraw.Draw(vari)
    for p in plist:
        color = '#00ff00' if accelerating(p) else '#ff0000'
        xy = list(p[:, 1:])
        fs, fe = p[0][0], p[-1][0]
        extend_path_ends(xy, fs > 0, fe < n - 1, vari.size)
        d.line(tuple(tuple(p) for p in xy), fill=color)
        if fe == n - 1:
            xe, ye = xy[-1]
            d.rectangle((xe - 1, ye - 1, xe + 2, ye + 2), fill='#ffff00')
    for points in maxima:
        for x, y in points:
            d.point((x, y), fill='#ffff00')


# -----------------------------------------------------------------------------
#
def animate_tracks(image_files, plist, output='track-%04d.png', verbose=0):
    paths = [(p[0][0], p[-1][0], accelerating(p), p) for p in plist]

    from numpy import concatenate
    from PIL import Image, ImageDraw
    from os.path import dirname, join
    for i, f in enumerate(image_files):
        if verbose:
            print('Drawing lines on image %d' % i)
        im = Image.open(f)
        dir = dirname(f)
        d = None
        for fs, fe, accel, p in paths:
            if i > fs and i <= fe + (fe - fs):
                color = '#00ff00' if accel else '#ff0000'
                if d is None:
                    d = ImageDraw.Draw(im)
                ds, de = (fs + (i - fe), fe) if i > fe else (0, i)
                xy = [(x, y) for t, x, y in p if t >= ds and t <= de]
                extend_path_ends(xy, i <= fe, i > fe, im.size)
                d.line(tuple(tuple(p) for p in xy), fill=color)
                if i == de:
                    xe, ye = xy[-1]
                    d.rectangle((xe - 1, ye - 1, xe + 2, ye + 2), fill='#ffff00')
                for x, y in xy:
                    d.point((x, y), fill='#ffff00')
        im.save(join(dir, output % i))


# -----------------------------------------------------------------------------
#
def accelerating(txy):
    return segment_speed(txy, len(txy) - 2) > segment_speed(txy, 0)


# -----------------------------------------------------------------------------
#
def segment_speed(txy, i):
    step = txy[i + 1] - txy[i]
    from math import sqrt
    v = sqrt((step[1:] * step[1:]).sum()) / step[0]
    return v


# -----------------------------------------------------------------------------
#
def extend_path_ends(xy, start, end, size):
    if len(xy) < 3:
        return
    if start:
        p = extend_path_end(xy[2], xy[1], xy[0], size)
        if p:
            xy.insert(0, p)
    if end:
        p = extend_path_end(xy[-3], xy[-2], xy[-1], size)
        if p:
            xy.append(p)


# -----------------------------------------------------------------------------
#
def extend_path_end(p0, p1, p2, size, pad=1.2, maxe=2.0):
    x0, y0 = p0
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    from math import sqrt
    d2 = sqrt(dx * dx + dy * dy)
    d1 = sqrt((x1 - x0) * (x1 - x0) + (y1 - y0) * (y1 - y0))
    f = d2 / d1 if d1 > 0 else 1
    f *= pad
    f = min(maxe, f)
    x, y = x2 + int(f * dx), y2 + int(f * dy)
    w, h = size
    if x < 0 or x >= w or y < 0 or y >= h:
        return (x, y)
    return None


# -----------------------------------------------------------------------------
#
if __name__ == "__main__":
    track()
