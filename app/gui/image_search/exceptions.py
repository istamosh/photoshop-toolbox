"""Custom exceptions for the image search module."""


class ImageProcessingError(Exception):
    """Base exception for image processing errors."""

    pass


class ImageLoadError(ImageProcessingError):
    """Raised when an image file cannot be loaded."""

    pass


class ImageHashError(ImageProcessingError):
    """Raised when image hash calculation fails."""

    pass


class InvalidFileTypeError(ImageProcessingError):
    """Raised when file is not a supported image type."""

    pass
