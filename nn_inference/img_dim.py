from dataclasses import dataclass
import io
import math
from pathlib import Path
import struct


@dataclass(slots=True)
class ImageFormat:
    format: str
    height: int
    width: int
    channels: int = 0
    bpp: int = 0


_TIFF_DTYPES: dict[int, str] = {
    1:  "IB3B",
    2:  "Ic3B",
    3:  "IH2B",
    4:  "IL",
}

_TIFF_TAG_ID: dict[int, str] = {
    256: 'width',   # short or long
    257: 'height',  # short or long
    258: 'bpp',     # short
    262: 'photometric_configuration',     # short
    277: 'spp',     # short
}


def get_image_shape(filepath: str | Path) -> ImageFormat | None:
    # Multithreading is not efficient
    # TODO use C_types and struct ?
    format: str = ''
    h, w, c, bpp = (0, 0, 0, 8)

    # https://docs.fileformat.com/image/
    with io.open(filepath, "rb") as buffer:
        data: bytes = buffer.read(32)

        if data.startswith(b'\x89PNG\r\n\x1a\n') and data[12:16] == b'IHDR':
            w, h, bpp, c  = struct.unpack(">2I2B", data[16:26])
            if c == 0: c = 1
            elif c == 2: c = 3
            elif c == 6: c = 4
            format = 'png'

        elif data.startswith(b'\xFF\xD8\xFF'):
            buffer.seek(2)
            i = 0
            while i < 512:
                i += 1
                b = buffer.read(1)
                if b == b"\xFF":
                    b = buffer.read(1)
                    if b in (b"\xC0", b"\xC2"):
                        # S0Fx
                        bpp, h, w, c = struct.unpack(">HB2HB", buffer.read(8))[1:]
                        break
            format = 'jpg'

        elif data.startswith(b'BM'):
            format = 'bmp'
            dib_header_size = struct.unpack("<I", data[14:18])[0]
            if dib_header_size == 12:
                w, h, c, bpp = struct.unpack("<2I2H", data[18:26])
            elif dib_header_size == 40:
                w, h, c, bpp = struct.unpack("<2I2H", data[18:30])

        elif data[:4] in (b"II\x2A\x00", b"MM\x00\x2A"):
            byte_order = "<" if data[:2] == b"II" else ">"
            ifd_offset = struct.unpack(f"{byte_order}I", data[4:8])[0]

            buffer.seek(ifd_offset)
            tag_entry_count_b = buffer.read(2)
            tag_entry_count = struct.unpack(f"{byte_order}H", tag_entry_count_b)[0]
            tag_entry_size = 12
            tag_seek_offset = ifd_offset + 2

            tags_count: int = 5
            bits_per_sample = 0
            samples_per_pixel = 0
            photometric_interpretation = 0

            while tags_count < 5 and tag_entry_count > 0:
                # print(f"offset=0x{tag_seek_offset:08X}")
                tag_id_dtype_b = buffer.read(4)
                tag_id, dtype = struct.unpack(f"{byte_order}2H", tag_id_dtype_b)
                value_hex = buffer.read(8)

                if tag_id in _TIFF_TAG_ID:
                    value_format = _TIFF_DTYPES.get(dtype, "8B")
                    data_count, value = struct.unpack(
                        f"{byte_order}{value_format}", value_hex)[:2]
                    # print(f"offset=0x{tag_seek_offset:08X}, tag_id={tag_id},",
                    #       f"dtype={dtype}, value_format={value_format}, value={value}")
                    # print(f"\tdata_count={data_count}, value_hex=0x{value_hex}")
                    if tag_id == 256:
                        w = value
                    elif tag_id == 257:
                        h = value
                    elif tag_id == 258:
                        bits_per_sample = value
                    elif tag_id == 262:
                        photometric_interpretation = value
                    elif tag_id == 277:
                        samples_per_pixel = value
                    tags_count -= 1

                tag_entry_count -= 1
                tag_seek_offset += tag_entry_size

            c = 0
            if photometric_interpretation in (0, 1):
                c = 1
            elif photometric_interpretation in (2, 3):
                c = 3
            format = 'tiff'

        elif data[:6] == b'GIF89a':
            w, h = struct.unpack("<2H", data[6:10])
            format = 'gif'

        elif data[:8] == b'DDS \x7C\x00\x00\x00':
            w, h = struct.unpack("<2I", data[12:20])
            buffer.seek(76)
            ddp_pixel_format = struct.unpack("<32I", buffer.read(128))
            if ddp_pixel_format[0] == 32:
                if ddp_pixel_format[1] & (0x40 | 0x20000 | 0x200) != 0:
                    rgb_bit_count = ddp_pixel_format[3]
                    print(f"rgb_bit_count: {rgb_bit_count}")
                    raise NotImplementedError("TODO: detect bpp and c")
                    # ... use DXGI_FORMAT to detect c/bpp
                elif ddp_pixel_format[1] == 0x4:
                    dxt = struct.pack('I', ddp_pixel_format[2])
                    if dxt in (b'DXT1', b'DXT5'):
                        c = 4
                    else:
                        print(f"cannot decode{dxt}")
                format = 'dds'

    nbytes = math.prod((h, w, c, int(bpp/8)))
    return (h, w, c), nbytes

    # return ImageFormat(
    #     format=format,
    #     height=h,
    #     width=w,
    #     channels=c,
    #     bpp=bpp
    # ) if format != '' else None
