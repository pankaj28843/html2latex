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
    with open(path, "rb") as f:
        # Read the first 24 bytes, which is enough for PNG or to detect JPEG markers
        head = f.read(24)

        # --- PNG ---
        # Check the 8-byte PNG signature (b"\x89PNG\r\n\x1a\n")
        # Then, width and height are 4 bytes each starting at offset 16
        if head.startswith(b"\x89PNG\r\n\x1a\n") and len(head) >= 24:
            width, height = struct.unpack(">LL", head[16:24])
            return (width, height)

        # --- JPEG ---
        # Check for JPEG SOI marker 0xFFD8 at the start
        elif head.startswith(b"\xff\xd8"):
            # Move back to start of file and scan JPEG segments.
            f.seek(0)
            f.read(2)  # Skip SOI marker.

            sof_markers = {
                0xC0,
                0xC1,
                0xC2,
                0xC3,
                0xC5,
                0xC6,
                0xC7,
                0xC9,
                0xCA,
                0xCB,
                0xCD,
                0xCE,
                0xCF,
            }

            while True:
                marker_prefix = f.read(1)
                if not marker_prefix:
                    raise ValueError("Invalid JPEG: no suitable SOF marker found.")

                if marker_prefix != b"\xff":
                    continue

                marker = f.read(1)
                while marker == b"\xff":
                    marker = f.read(1)
                if not marker:
                    raise ValueError("Invalid JPEG: no suitable SOF marker found.")

                marker_code = marker[0]
                if marker_code in sof_markers:
                    segment_length = struct.unpack(">H", f.read(2))[0]
                    if segment_length < 7:
                        raise ValueError("Invalid JPEG: SOF segment too short.")
                    f.read(1)  # Sample precision
                    height, width = struct.unpack(">HH", f.read(4))
                    return (width, height)

                segment_length = struct.unpack(">H", f.read(2))[0]
                if segment_length < 2:
                    raise ValueError("Invalid JPEG: segment length too short.")
                f.seek(segment_length - 2, 1)

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
