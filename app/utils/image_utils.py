"""Image processing utilities."""

from PIL import Image
import imagehash
import numpy as np


def calculate_image_hash(image_path, hash_type="phash"):
    """Calculate perceptual hash of an image.

    Args:
        image_path (str): Path to the image file
        hash_type (str): Type of hash to calculate ('phash' or 'ahash')

    Returns:
        imagehash.ImageHash: Hash of the image
    """
    with Image.open(image_path) as img:
        if hash_type == "phash":
            return imagehash.phash(img)
        return imagehash.average_hash(img)


def compare_images(image1_path, image2_path, hash_type="phash"):
    """Compare two images using perceptual hashing.

    Args:
        image1_path (str): Path to first image
        image2_path (str): Path to second image
        hash_type (str): Type of hash to use for comparison

    Returns:
        int: Hamming distance between the image hashes
    """
    hash1 = calculate_image_hash(image1_path, hash_type)
    hash2 = calculate_image_hash(image2_path, hash_type)
    return hash1 - hash2


def get_image_info(image_path):
    """Get basic information about an image.

    Args:
        image_path (str): Path to the image file

    Returns:
        dict: Dictionary containing image information
    """
    with Image.open(image_path) as img:
        info = {
            "format": img.format,
            "mode": img.mode,
            "size": img.size,
            "width": img.width,
            "height": img.height,
        }
        if "dpi" in img.info:
            info["dpi"] = img.info["dpi"]
        return info
