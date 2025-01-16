#!/usr/bin/env python2
import struct

def get_image_size(path):
    """
    Return (width, height) of a PNG or JPEG image without using Pillow/PIL.

    - PNG:
      We look for the 8-byte signature followed by the IHDR chunk (width, height).

    - JPEG:
      We scan the file segment by segment until we find the SOFn marker
      that contains the size info (excluding markers like DHT, DAC, etc.).
    """
    with open(path, 'rb') as f:
        # Read the first 24 bytes, which is enough for PNG or to detect JPEG markers
        head = f.read(24)

        # --- PNG ---
        # Check the 8-byte PNG signature (b"\x89PNG\r\n\x1a\n")
        # Then, width and height are 4 bytes each starting at offset 16
        if head.startswith('\x89PNG\r\n\x1a\n') and len(head) >= 24:
            width, height = struct.unpack(">LL", head[16:24])
            return (width, height)

        # --- JPEG ---
        # Check for JPEG SOI marker 0xFFD8 at the start
        elif head.startswith('\xff\xd8'):
            # Move back to start
            f.seek(0)

            # Search for the segment containing the image height/width
            while True:
                b = f.read(1)
                # Look for 0xFF markers
                while b and ord(b) != 0xFF:
                    b = f.read(1)
                # Skip any padding 0xFF bytes
                while b and ord(b) == 0xFF:
                    b = f.read(1)

                # Check if we hit a Start Of Frame (SOF) marker (0xC0 - 0xCF),
                # but skip certain markers like 0xC4, 0xC8, 0xCC (they don't store size).
                if b and (0xC0 <= ord(b) <= 0xCF) and ord(b) not in [0xC4, 0xC8, 0xCC]:
                    # Skip the segment length bytes
                    f.read(3)
                    # Next 4 bytes are height (2 bytes) and width (2 bytes)
                    h, w = struct.unpack(">HH", f.read(4))
                    return (w, h)
                else:
                    # Not the SOF marker we want. Move back one byte and read segment length.
                    if b:
                        f.seek(-1, 1)
                        seg_size = struct.unpack(">H", f.read(2))[0]
                        # Skip the rest of this segment
                        f.seek(seg_size - 2, 1)

            # If the loop exits, we couldn't find a valid SOF marker
            raise ValueError("Invalid JPEG: no suitable SOF marker found.")

        # If neither PNG nor JPEG recognized
        else:
            raise ValueError("Unsupported or unrecognized image format: {}".format(path))


# Example usage:
if __name__ == "__main__":
    import sys
    path_to_image = sys.argv[1]
    w, h = get_image_size(path_to_image)
    print("Width={}, Height={}".format(w, h))
