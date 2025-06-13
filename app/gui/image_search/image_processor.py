"""Image processing and hash calculation functionality."""

import os
import imghdr
from PIL import Image, UnidentifiedImageError
import imagehash
from typing import Optional, Dict, Set
from functools import lru_cache
from .exceptions import ImageLoadError, ImageHashError, InvalidFileTypeError


class ImageProcessor:
    """Handles image processing and hash calculations.

    Supports image validation, hash calculation, and similarity comparison with
    caching to improve performance for repeated operations.
    """

    SUPPORTED_FORMATS: Set[str] = {"jpeg", "jpg", "png", "bmp", "gif"}

    def __init__(self):
        """Initialize the image processor."""
        self._hash_cache: Dict[str, imagehash.ImageHash] = {}

    @staticmethod
    def validate_image_file(image_path: str) -> bool:
        """Validate if a file is a supported image.

        Args:
            image_path: Path to the image file

        Returns:
            bool: True if file is a valid image, False otherwise

        Raises:
            InvalidFileTypeError: If file is not a supported image type
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        img_type = imghdr.what(image_path)
        if img_type is None or img_type.lower() not in ImageProcessor.SUPPORTED_FORMATS:
            raise InvalidFileTypeError(f"Unsupported image format: {image_path}")

        return True

    @lru_cache(maxsize=1000)  # Cache recent hash calculations
    def calculate_hash(
        self, image_path: str, hash_type: str = "phash"
    ) -> imagehash.ImageHash:
        """Calculate the perceptual hash of an image.

        Args:
            image_path: Path to the image file
            hash_type: Type of hash to calculate ("phash" or "ahash")

        Returns:
            ImageHash object for the image

        Raises:
            ImageLoadError: If the image cannot be loaded
            ImageHashError: If hash calculation fails
        """
        try:
            self.validate_image_file(image_path)
            img = Image.open(image_path)

            # Convert RGBA to RGB if needed for consistent hashing
            if img.mode == "RGBA":
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background

            if hash_type == "phash":
                return imagehash.phash(img)
            else:  # ahash
                return imagehash.average_hash(img)

        except UnidentifiedImageError as e:
            raise ImageLoadError(f"Failed to load image {image_path}: {str(e)}")
        except Exception as e:
            raise ImageHashError(f"Failed to calculate hash for {image_path}: {str(e)}")

    @staticmethod
    def calculate_similarity(
        hash1: imagehash.ImageHash, hash2: imagehash.ImageHash
    ) -> float:
        """Calculate similarity score between two image hashes.

        Args:
            hash1: First image hash
            hash2: Second image hash

        Returns:
            Similarity score (0-100, higher means more similar)
        """
        if hash1 is None or hash2 is None:
            return 0.0

        try:
            hash_size = len(hash1.hash) * len(hash1.hash[0])
            hamming_distance = hash1 - hash2
            similarity = 100.0 * (1 - (hamming_distance / hash_size))
            return max(0.0, min(100.0, similarity))
        except Exception:
            return 0.0
