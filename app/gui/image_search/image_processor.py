"""Image processing and hash calculation functionality."""

import os
import imghdr
import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError
import imagehash
from typing import Optional, Dict, Set, Tuple, List
from functools import lru_cache
from skimage import feature, measure
from skimage.metrics import structural_similarity as ssim
from .exceptions import ImageLoadError, ImageHashError, InvalidFileTypeError


class ImageProcessor:
    """Handles image processing and hash calculations.

    Supports image validation, hash calculation, similarity comparison with
    caching to improve performance for repeated operations. Includes advanced
    crop-resistant matching techniques using feature detection and template matching.
    """

    SUPPORTED_FORMATS: Set[str] = {"jpeg", "jpg", "png", "bmp", "gif"}

    def __init__(self):
        """Initialize the image processor."""
        self._hash_cache: Dict[str, imagehash.ImageHash] = {}
        # Initialize feature detectors
        self._sift = cv2.SIFT_create(nfeatures=500)
        self._orb = cv2.ORB_create(nfeatures=500)

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

    def load_image_as_cv2(self, image_path: str) -> Optional[np.ndarray]:
        """Load image as OpenCV array for advanced processing.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            OpenCV image array in BGR format, or None if loading fails
        """
        try:
            self.validate_image_file(image_path)
            img = cv2.imread(image_path)
            return img
        except Exception as e:
            raise ImageLoadError(f"Failed to load image as CV2 array {image_path}: {str(e)}")

    def calculate_crop_resistant_similarity(
        self, ref_path: str, target_path: str, method: str = "combined"
    ) -> float:
        """Calculate similarity using crop-resistant techniques.
        
        Args:
            ref_path: Path to reference image (potentially cropped)
            target_path: Path to target image (potentially full image)
            method: Method to use ('sift', 'template', 'histogram', 'combined')
            
        Returns:
            Similarity score (0-100, higher means more similar)
        """
        try:
            ref_img = self.load_image_as_cv2(ref_path)
            target_img = self.load_image_as_cv2(target_path)
            
            if ref_img is None or target_img is None:
                return 0.0
                
            if method == "sift":
                return self._sift_matching(ref_img, target_img)
            elif method == "template":
                return self._template_matching(ref_img, target_img)
            elif method == "histogram":
                return self._histogram_comparison(ref_img, target_img)
            elif method == "combined":
                return self._combined_matching(ref_img, target_img)
            else:
                return 0.0
                
        except Exception as e:
            return 0.0

    def _sift_matching(self, ref_img: np.ndarray, target_img: np.ndarray) -> float:
        """Use SIFT features for crop-resistant matching.
        
        Args:
            ref_img: Reference image (potentially cropped)
            target_img: Target image to search in
            
        Returns:
            Similarity score based on feature matching
        """
        try:
            # Convert to grayscale
            ref_gray = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)
            target_gray = cv2.cvtColor(target_img, cv2.COLOR_BGR2GRAY)
            
            # Detect keypoints and descriptors
            kp1, des1 = self._sift.detectAndCompute(ref_gray, None)
            kp2, des2 = self._sift.detectAndCompute(target_gray, None)
            
            if des1 is None or des2 is None or len(des1) < 10 or len(des2) < 10:
                return 0.0
            
            # FLANN matcher
            FLANN_INDEX_KDTREE = 1
            index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
            search_params = dict(checks=50)
            flann = cv2.FlannBasedMatcher(index_params, search_params)
            
            matches = flann.knnMatch(des1, des2, k=2)
            
            # Apply Lowe's ratio test
            good_matches = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < 0.7 * n.distance:
                        good_matches.append(m)
            
            # Calculate similarity based on good matches
            if len(good_matches) > 10:
                # Use homography to verify geometric consistency
                src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                
                M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                if M is not None:
                    # Count inliers
                    inliers = np.sum(mask)
                    similarity = min(100.0, (inliers / len(good_matches)) * 100.0)
                    return similarity
            
            # Fallback: simple ratio of good matches
            match_ratio = len(good_matches) / len(des1)
            return min(100.0, match_ratio * 100.0)
            
        except Exception:
            return 0.0

    def _template_matching(self, ref_img: np.ndarray, target_img: np.ndarray) -> float:
        """Use template matching at multiple scales.
        
        Args:
            ref_img: Reference image (template)
            target_img: Target image to search in
            
        Returns:
            Best similarity score from multi-scale template matching
        """
        try:
            ref_gray = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)
            target_gray = cv2.cvtColor(target_img, cv2.COLOR_BGR2GRAY)
            
            ref_h, ref_w = ref_gray.shape
            target_h, target_w = target_gray.shape
            
            # Skip if reference is larger than target
            if ref_h > target_h or ref_w > target_w:
                return 0.0
            
            best_score = 0.0
            
            # Try multiple scales
            scales = [1.0, 0.9, 0.8, 0.7, 0.6, 1.1, 1.2]
            
            for scale in scales:
                # Resize template
                new_w = int(ref_w * scale)
                new_h = int(ref_h * scale)
                
                if new_w > target_w or new_h > target_h or new_w < 20 or new_h < 20:
                    continue
                    
                scaled_template = cv2.resize(ref_gray, (new_w, new_h))
                
                # Template matching
                result = cv2.matchTemplate(target_gray, scaled_template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                
                score = max_val * 100.0
                best_score = max(best_score, score)
            
            return best_score
            
        except Exception:
            return 0.0

    def _histogram_comparison(self, ref_img: np.ndarray, target_img: np.ndarray) -> float:
        """Compare images using sliding window histogram analysis.
        
        Args:
            ref_img: Reference image
            target_img: Target image to search in
            
        Returns:
            Best similarity score from histogram comparison
        """
        try:
            ref_h, ref_w = ref_img.shape[:2]
            target_h, target_w = target_img.shape[:2]
            
            if ref_h > target_h or ref_w > target_w:
                return 0.0
            
            # Calculate reference histogram
            ref_hist = cv2.calcHist([ref_img], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
            cv2.normalize(ref_hist, ref_hist)
            
            best_score = 0.0
            step_size = max(20, min(ref_w, ref_h) // 4)
            
            # Sliding window approach
            for y in range(0, target_h - ref_h + 1, step_size):
                for x in range(0, target_w - ref_w + 1, step_size):
                    # Extract window
                    window = target_img[y:y+ref_h, x:x+ref_w]
                    
                    # Calculate histogram for window
                    window_hist = cv2.calcHist([window], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
                    cv2.normalize(window_hist, window_hist)
                    
                    # Compare histograms
                    correlation = cv2.compareHist(ref_hist, window_hist, cv2.HISTCMP_CORREL)
                    score = max(0.0, correlation * 100.0)
                    best_score = max(best_score, score)
            
            return best_score
            
        except Exception:
            return 0.0

    def _combined_matching(self, ref_img: np.ndarray, target_img: np.ndarray) -> float:
        """Combine multiple matching techniques for robust results.
        
        Args:
            ref_img: Reference image
            target_img: Target image to search in
            
        Returns:
            Combined similarity score
        """
        try:
            # Get scores from different methods
            sift_score = self._sift_matching(ref_img, target_img)
            template_score = self._template_matching(ref_img, target_img)
            hist_score = self._histogram_comparison(ref_img, target_img)
            
            # Weighted combination (SIFT gets higher weight for geometric accuracy)
            combined_score = (
                sift_score * 0.5 +
                template_score * 0.3 +
                hist_score * 0.2
            )
            
            return min(100.0, combined_score)
            
        except Exception:
            return 0.0

    def detect_crop_region(self, ref_path: str, target_path: str) -> Optional[Tuple[int, int, int, int]]:
        """Detect the region in target image that matches the reference crop.
        
        Args:
            ref_path: Path to reference (cropped) image
            target_path: Path to target (full) image
            
        Returns:
            Tuple of (x, y, width, height) of matching region, or None if not found
        """
        try:
            ref_img = self.load_image_as_cv2(ref_path)
            target_img = self.load_image_as_cv2(target_path)
            
            if ref_img is None or target_img is None:
                return None
                
            ref_gray = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)
            target_gray = cv2.cvtColor(target_img, cv2.COLOR_BGR2GRAY)
            
            # Use template matching to find the best location
            result = cv2.matchTemplate(target_gray, ref_gray, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            if max_val > 0.7:  # High confidence threshold
                x, y = max_loc
                h, w = ref_gray.shape
                return (x, y, w, h)
                
            return None
            
        except Exception:
            return None
