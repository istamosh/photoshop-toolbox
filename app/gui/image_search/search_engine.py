"""Search engine for finding similar images.

This module provides the core search functionality for finding similar images
based on perceptual hashing. It supports parallel processing for improved
performance and early termination options.
"""

import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Optional, Iterator
from queue import Queue
from .image_processor import ImageProcessor
from .exceptions import ImageProcessingError

logger = logging.getLogger(__name__)


class SearchEngine:
    """Engine for searching similar images.

    This class handles the process of searching for similar images in a directory
    based on a reference image. It uses perceptual hashing for image comparison
    and supports parallel processing for improved performance.

    Features:
    - Parallel processing of images for faster search
    - Early termination option on first match
    - Progress reporting through a message queue
    - Error handling and logging
    """

    def __init__(
        self,
        reference_path: str,
        search_dir: str,
        threshold: float,
        hash_type: str,
        stop_on_first: bool,
        result_queue: Queue,
    ):
        """Initialize the search engine.

        Args:
            reference_path: Path to the reference image
            search_dir: Directory to search for similar images
            threshold: Minimum similarity threshold (0-100)
            hash_type: Type of hash to use ('phash' or 'ahash')
            stop_on_first: Whether to stop after finding first match
            result_queue: Queue for progress and result updates
        """
        self.reference_path = reference_path
        self.search_dir = search_dir
        self.threshold = threshold
        self.hash_type = hash_type
        self.stop_on_first = stop_on_first
        self.result_queue = result_queue
        self.is_searching = True
        self.processor = ImageProcessor()

    def search(self) -> None:
        """Execute the image search process using parallel processing."""
        try:
            # Process reference image
            self.result_queue.put(("status", "Processing reference image..."))
            ref_hash = self.processor.calculate_hash(
                self.reference_path, self.hash_type
            )

            # Start parallel search
            self.result_queue.put(("status", "Searching for similar images..."))
            self.result_queue.put(
                (
                    "result",
                    f"Using {self.hash_type}, minimum similarity threshold: {self.threshold}%\n\n",
                )
            )

            image_files = list(self._collect_image_files())
            self._parallel_search(ref_hash, image_files)

        except ImageProcessingError as e:
            logger.error("Image processing error: %s", str(e))
            self.result_queue.put(("error", str(e)))
        except Exception as e:
            logger.exception("Unexpected error during search")
            self.result_queue.put(("error", f"Search error: {str(e)}"))

    def _collect_image_files(self) -> Iterator[str]:
        """Collect all image files in the search directory."""
        for root_dir, _, files in os.walk(self.search_dir):
            if not self.is_searching:
                break

            for file in files:
                if not self.is_searching:
                    break

                if self._is_image_file(file):
                    img_path = os.path.join(root_dir, file)
                    if img_path != self.reference_path:
                        yield img_path

    def _parallel_search(self, ref_hash, image_files: List[str]) -> None:
        """Execute search in parallel using thread pool."""
        similar_images = []
        total_processed = 0
        batch_size = 100  # Process images in batches for better queue management

        def process_batch(file_batch):
            batch_results = []
            for img_path in file_batch:
                if not self.is_searching:
                    break
                try:
                    self.result_queue.put(
                        ("status", f"Processing: {os.path.basename(img_path)}")
                    )
                    img_hash = self.processor.calculate_hash(img_path, self.hash_type)
                    if img_hash:
                        similarity = self.processor.calculate_similarity(
                            ref_hash, img_hash
                        )
                        if similarity >= self.threshold:
                            batch_results.append((img_path, similarity))
                            if self.stop_on_first:
                                break
                except ImageProcessingError as e:
                    logger.warning("Failed to process %s: %s", img_path, str(e))
            return batch_results

        # Process images in parallel batches
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = []
            current_batch = []

            # Create batches of images
            for img_path in image_files:
                current_batch.append(img_path)
                total_processed += 1

                if len(current_batch) >= batch_size:
                    futures.append(executor.submit(process_batch, current_batch[:]))
                    current_batch = []

            # Process remaining images
            if current_batch:
                futures.append(executor.submit(process_batch, current_batch))

            # Collect results as they complete
            for future in as_completed(futures):
                matches = future.result()
                similar_images.extend(matches)

                if self.stop_on_first and similar_images:
                    self.is_searching = False
                    break

                if not self.is_searching:
                    break

        # Always report results, even if search was stopped
        self._report_results(similar_images, total_processed)

    def _is_image_file(self, filename: str) -> bool:
        """Check if a file is an image based on extension."""
        return filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif"))

    def _report_results(
        self, similar_images: List[Tuple[str, float]], total_processed: int
    ) -> None:
        """Report search results."""
        # Don't skip reporting just because search was stopped early
        similar_images.sort(key=lambda x: x[1], reverse=True)

        if similar_images:
            result_count = (
                "first matching image"
                if self.stop_on_first
                else f"{len(similar_images)} similar images"
            )
            self.result_queue.put(("result", f"Found {result_count}:\n\n"))

            # Always show the first match when stop_on_first is True
            if self.stop_on_first:
                path, similarity = similar_images[0]
                self.result_queue.put(
                    ("result", f"Similarity: {similarity:.1f}%\nPath: ")
                )
                self.result_queue.put(("path_link", path))
                self.result_queue.put(("result", "\n\n"))
            else:
                for path, similarity in similar_images:
                    self.result_queue.put(
                        ("result", f"Similarity: {similarity:.1f}%\nPath: ")
                    )
                    self.result_queue.put(("path_link", path))
                    self.result_queue.put(("result", "\n\n"))
        else:
            self.result_queue.put(
                ("result", f"No images found with similarity >= {self.threshold}%.\n")
            )

        status_msg = "Search complete. "
        if self.stop_on_first and similar_images:
            status_msg += f"Stopped after finding first match (processed {total_processed} images)."
        else:
            status_msg += f"Found {len(similar_images)} similar images out of {total_processed} processed."

        self.result_queue.put(("status", status_msg))
