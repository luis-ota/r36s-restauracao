import ctypes, fcntl, mmap, os, sys

def IOC(dir_, type_, nr, size):
    return (dir_ << 30) | (size << 16) | (type_ << 8) | nr

d = ord('d')
GETRES = IOC(3, d, 0xA0, 64)
GETCRTC = IOC(3, d, 0xA1, 100)
GETFB = IOC(3, d, 0xAD, 28)
MAPDUMB = IOC(3, d, 0xB3, 16)

class Res(ctypes.Structure):
    _fields_ = [("fb_id_ptr", ctypes.c_uint64), ("crtc_id_ptr", ctypes.c_uint64),
                ("conn_id_ptr", ctypes.c_uint64), ("enc_id_ptr", ctypes.c_uint64),
                ("count_fbs", ctypes.c_uint32), ("count_crtcs", ctypes.c_uint32),
                ("count_conn", ctypes.c_uint32), ("count_enc", ctypes.c_uint32),
                ("min_w", ctypes.c_uint32), ("max_w", ctypes.c_uint32),
                ("min_h", ctypes.c_uint32), ("max_h", ctypes.c_uint32)]

class ModeInfo(ctypes.Structure):
    _fields_ = [("clock", ctypes.c_uint32),
                ("hdisplay", ctypes.c_uint16), ("hsync_start", ctypes.c_uint16),
                ("hsync_end", ctypes.c_uint16), ("htotal", ctypes.c_uint16),
                ("vdisplay", ctypes.c_uint16), ("vsync_start", ctypes.c_uint16),
                ("vsync_end", ctypes.c_uint16), ("vtotal", ctypes.c_uint16),
                ("vrefresh", ctypes.c_uint16), ("flags", ctypes.c_uint32),
                ("type", ctypes.c_uint32), ("name", ctypes.c_char * 32)]

class Crtc(ctypes.Structure):
    _fields_ = [("set_conn_ptr", ctypes.c_uint64), ("count_conn", ctypes.c_uint32),
                ("crtc_id", ctypes.c_uint32), ("fb_id", ctypes.c_uint32),
                ("x", ctypes.c_uint32), ("y", ctypes.c_uint32),
                ("gamma_size", ctypes.c_uint32), ("mode_valid", ctypes.c_uint32),
                ("mode", ModeInfo)]

class FbCmd(ctypes.Structure):
    _fields_ = [("fb_id", ctypes.c_uint32), ("width", ctypes.c_uint32),
                ("height", ctypes.c_uint32), ("pitch", ctypes.c_uint32),
                ("bpp", ctypes.c_uint32), ("depth", ctypes.c_uint32),
                ("handle", ctypes.c_uint32)]

class MapDumb(ctypes.Structure):
    _fields_ = [("handle", ctypes.c_uint32), ("pad", ctypes.c_uint32),
                ("offset", ctypes.c_uint64)]

fd = os.open("/dev/dri/card0", os.O_RDWR)
res = Res()
fcntl.ioctl(fd, GETRES, res)
n_fb = max(res.count_fbs, 1); n_crtc = max(res.count_crtcs, 1)
n_conn = max(res.count_conn, 1); n_enc = max(res.count_enc, 1)
fbs = (ctypes.c_uint32 * n_fb)()
crtcs = (ctypes.c_uint32 * n_crtc)()
conns = (ctypes.c_uint32 * n_conn)()
encs = (ctypes.c_uint32 * n_enc)()
res.fb_id_ptr = ctypes.cast(fbs, ctypes.c_void_p).value
res.crtc_id_ptr = ctypes.cast(crtcs, ctypes.c_void_p).value
res.conn_id_ptr = ctypes.cast(conns, ctypes.c_void_p).value
res.enc_id_ptr = ctypes.cast(encs, ctypes.c_void_p).value
fcntl.ioctl(fd, GETRES, res)
print("crtcs:", res.count_crtcs, "fbs:", res.count_fbs, file=sys.stderr)

done = False
for cid in list(crtcs) + list(fbs):
    if not cid:
        continue
    for attempt in ("crtc",):
        c = Crtc(); c.crtc_id = cid
        try:
            fcntl.ioctl(fd, GETCRTC, c)
        except OSError as e:
            continue
        print("crtc", cid, "fb", c.fb_id, "ok", c.mode_valid, c.mode.hdisplay, c.mode.vdisplay, file=sys.stderr)
        if not c.fb_id:
            continue
        fb = FbCmd(); fb.fb_id = c.fb_id
        fcntl.ioctl(fd, GETFB, fb)
        print("fb", fb.width, fb.height, fb.pitch, fb.bpp, fb.handle, file=sys.stderr)
        m = MapDumb(); m.handle = fb.handle
        fcntl.ioctl(fd, MAPDUMB, m)
        size = fb.pitch * fb.height
        buf = mmap.mmap(fd, size, mmap.MAP_SHARED, mmap.PROT_READ, offset=m.offset)
        open("/tmp/shot.raw", "wb").write(buf[:])
        open("/tmp/shot.txt", "w").write("%d %d %d %d\n" % (fb.width, fb.height, fb.pitch, fb.bpp))
        print("gravado", size, file=sys.stderr)
        done = True
        break
    if done:
        break
