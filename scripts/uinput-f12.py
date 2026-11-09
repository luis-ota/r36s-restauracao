import fcntl, os, struct, time

UI_DEV_CREATE = 0x5501
UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565

fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
fcntl.ioctl(fd, UI_SET_EVBIT, 1)
fcntl.ioctl(fd, UI_SET_KEYBIT, 88)
dev = struct.pack("80sHHHHII", b"vkeyboard\0", 3, 0, 0, 0, 0, 0)
dev = dev.ljust(1116, b"\0")
os.write(fd, dev)
fcntl.ioctl(fd, UI_DEV_CREATE)
time.sleep(0.6)

def ev(t, c, v):
    return struct.pack("llHHi", 0, 0, t, c, v)

for value in (1, 0):
    os.write(fd, ev(1, 88, value))
    os.write(fd, ev(0, 0, 0))
    time.sleep(0.15)
time.sleep(0.3)
os.close(fd)
print("ok")
