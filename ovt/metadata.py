"""Image metadata extraction.

Pulls EXIF data relevant to verification work: capture time, device,
software (edit-detection hint), and GPS coordinates where present.
Absence of metadata is itself recorded, since stripped EXIF is a common
property of images that have passed through social platforms.
"""

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


VERIFICATION_TAGS = {
    "DateTime",
    "DateTimeOriginal",
    "DateTimeDigitized",
    "Make",
    "Model",
    "Software",
    "GPSInfo",
}


def extract(path):
    """Return a dict of verification-relevant metadata for an image."""
    result = {
        "file": path,
        "format": None,
        "dimensions": None,
        "exif_present": False,
        "capture_time": None,
        "device": None,
        "software": None,
        "gps": None,
        "raw": {},
    }

    with Image.open(path) as img:
        result["format"] = img.format
        result["dimensions"] = img.size
        exif = img.getexif()

        if not exif:
            return result

        result["exif_present"] = True

        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, str(tag_id))
            if tag in VERIFICATION_TAGS:
                result["raw"][tag] = str(value)

        # IFD lookups for the fields that matter most
        try:
            ifd = exif.get_ifd(0x8769)  # Exif IFD
            for tag_id, value in ifd.items():
                tag = TAGS.get(tag_id, str(tag_id))
                if tag in VERIFICATION_TAGS:
                    result["raw"][tag] = str(value)
        except KeyError:
            pass

        result["capture_time"] = result["raw"].get("DateTimeOriginal") or result["raw"].get("DateTime")
        make = result["raw"].get("Make", "").strip()
        model = result["raw"].get("Model", "").strip()
        result["device"] = f"{make} {model}".strip() or None
        result["software"] = result["raw"].get("Software")

        gps_ifd = _gps_ifd(exif)
        if gps_ifd:
            result["gps"] = _parse_gps(gps_ifd)

    return result


def _gps_ifd(exif):
    try:
        return exif.get_ifd(0x8825)
    except KeyError:
        return None


def _parse_gps(gps_ifd):
    data = {}
    for tag_id, value in gps_ifd.items():
        tag = GPSTAGS.get(tag_id, str(tag_id))
        data[tag] = value

    lat = _dms_to_decimal(data.get("GPSLatitude"), data.get("GPSLatitudeRef"))
    lon = _dms_to_decimal(data.get("GPSLongitude"), data.get("GPSLongitudeRef"))
    if lat is None or lon is None:
        return None
    return {"latitude": lat, "longitude": lon}


def _dms_to_decimal(dms, ref):
    if not dms or not ref:
        return None
    degrees, minutes, seconds = (float(x) for x in dms)
    decimal = degrees + minutes / 60 + seconds / 3600
    if ref in ("S", "W"):
        decimal = -decimal
    return round(decimal, 6)
