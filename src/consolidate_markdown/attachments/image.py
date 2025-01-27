import logging
import os
import subprocess
import shutil
from pathlib import Path
from typing import Tuple, Dict

from PIL import Image
# Suppress PIL debug logging
Image.logger.setLevel(logging.WARNING)  # Suppress all PIL logging below WARNING
logging.getLogger('PIL').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class ImageProcessingError(Exception):
    """Error during image processing."""
    pass

class ImageProcessor:
    """Handle image format conversions and metadata extraction."""

    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.svg', '.heic'}

    def __init__(self, cm_dir: Path):
        self.cm_dir = cm_dir
        self.temp_dir = cm_dir / "images"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def process_image(self, image_path: Path, force: bool = False) -> Tuple[Path, Dict]:
        """Process an image file and return its temporary path and metadata."""
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Create temp path preserving directory structure
        temp_path = self.temp_dir / image_path.name
        if image_path.suffix.lower() == '.heic':
            temp_path = self.temp_dir / f"{image_path.stem}.jpg"
        elif image_path.suffix.lower() == '.svg':
            temp_path = self.temp_dir / f"{image_path.stem}.png"
        temp_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if we need to process
        if not force and temp_path.exists():
            if temp_path.stat().st_mtime >= image_path.stat().st_mtime:
                return temp_path, self._extract_metadata(temp_path)

        # Convert HEIC to JPG if needed
        if image_path.suffix.lower() == '.heic':
            try:
                subprocess.run(
                    ['sips', '-s', 'format', 'jpeg', str(image_path), '--out', str(temp_path)],
                    check=True,
                    capture_output=True
                )
                return temp_path, self._extract_metadata(temp_path)
            except Exception as e:
                logger.warning(f"HEIC conversion failed for {image_path.name}, using basic copy: {str(e)}")
                raise ImageProcessingError(f"HEIC conversion failed: {str(e)}")

        # Convert SVG to PNG if needed
        if image_path.suffix.lower() == '.svg':
            try:
                # Try inkscape first
                try:
                    subprocess.run(
                        ['inkscape', str(image_path), '--export-type=png', f'--export-filename={temp_path}'],
                        check=True,
                        capture_output=True
                    )
                    return temp_path, self._extract_metadata(temp_path)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # Fallback to rsvg-convert if available
                    subprocess.run(
                        ['rsvg-convert', str(image_path), '-o', str(temp_path)],
                        check=True,
                        capture_output=True
                    )
                    return temp_path, self._extract_metadata(temp_path)
            except Exception as e:
                logger.warning(f"SVG conversion failed for {image_path.name}, using basic copy: {str(e)}")
                raise ImageProcessingError(f"SVG conversion failed: {str(e)}")

        # Just copy the file for other formats
        shutil.copy2(image_path, temp_path)
        return temp_path, self._extract_metadata(temp_path)

    def _extract_metadata(self, image_path: Path) -> Dict:
        """Extract metadata from an image file."""
        try:
            # For unsupported formats, return basic metadata
            if image_path.suffix.lower() == '.heic':  # Removed .svg since we convert it
                return {
                    'size_bytes': image_path.stat().st_size,
                    'format': image_path.suffix.lower().lstrip('.'),
                    'mode': 'unknown',
                    'dimensions': (0, 0)
                }

            # For supported formats, use PIL
            with Image.open(image_path) as img:
                metadata = {
                    'size_bytes': image_path.stat().st_size,
                    'format': img.format.lower() if img.format else 'unknown',
                    'mode': img.mode,
                    'dimensions': img.size
                }
                return metadata
        except Exception as e:
            # Fallback metadata for any errors
            return {
                'size_bytes': image_path.stat().st_size if image_path.exists() else 0,
                'format': image_path.suffix.lower().lstrip('.'),
                'mode': 'unknown',
                'dimensions': (0, 0)
            }

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
