#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import pathlib

from PIL import Image


def convert_image_to_jpeg(image_path: pathlib.Path) -> bytes:
    """Converts any image format to JPEG and returns it as binary data."""
    with Image.open(image_path) as image:
        image = image.convert("RGB")
        image_buffer = io.BytesIO()
        image.save(image_buffer, format="JPEG", quality=90)
        return image_buffer.getvalue()
