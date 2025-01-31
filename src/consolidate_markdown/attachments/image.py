import logging
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple

from PIL import Image

# Suppress PIL debug logging
pil_logger = logging.getLogger("PIL")
pil_logger.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class ImageProcessingError(Exception):
    """Error during image processing."""

    pass


def _get_heic_converter() -> Tuple[List[str], str]:
    """Get the appropriate HEIC converter command for the current platform."""
    system = platform.system().lower()

    # Try ImageMagick first as it's available on all platforms
    try:
        subprocess.run(["magick", "--version"], capture_output=True, check=True)
        return ["magick", "convert"], "imagemagick"
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    if system == "darwin":
        # macOS: Use built-in sips
        return ["sips", "-s", "format", "jpeg"], "sips"
    elif system == "linux":
        # Linux: Try heif-convert from libheif-tools
        try:
            subprocess.run(
                ["heif-convert", "--version"], capture_output=True, check=True
            )
            return ["heif-convert"], "libheif"
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    raise ImageProcessingError(
        "No HEIC converter found. Please install ImageMagick or platform-specific tools."
    )


def _get_svg_converter() -> List[str]:
    """Get the appropriate SVG converter command."""
    try:
        # Try rsvg-convert first
        subprocess.run(["rsvg-convert", "--version"], capture_output=True, check=True)
        return [
            "rsvg-convert"
        ]  # Basic command, we'll add output format in the process_image method
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    try:
        # Try inkscape as fallback
        subprocess.run(["inkscape", "--version"], capture_output=True, check=True)
        return [
            "inkscape"
        ]  # Basic command, we'll add output format in the process_image method
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    raise ImageProcessingError(
        "SVG converter not found. Please install librsvg (rsvg-convert) or inkscape."
    )


class ImageProcessor:
    """Handle image format conversions and metadata extraction."""

    SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".svg", ".heic"}

    def __init__(self, cm_dir: Path):
        self.cm_dir = cm_dir
        self.temp_dir = cm_dir / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def process_image(self, image_path: Path, force: bool = False) -> Tuple[Path, Dict]:
        """Process an image file and return its temporary path and metadata."""
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Create temp path preserving directory structure
        temp_path = self.temp_dir / image_path.name
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Check if we need to process
        if not force and temp_path.exists():
            if temp_path.stat().st_mtime >= image_path.stat().st_mtime:
                return temp_path, self._extract_metadata(temp_path)

        # Process based on file type
        suffix = image_path.suffix.lower()
        if suffix not in self.SUPPORTED_FORMATS:
            raise ImageProcessingError(f"Unsupported image format: {suffix}")

        try:
            # Handle SVG files - copy without conversion
            if suffix == ".svg":
                shutil.copy2(image_path, temp_path)
                return temp_path, self._extract_metadata(temp_path)

            # Handle HEIC files - convert to JPEG
            if suffix == ".heic":
                converter_cmd, converter_type = _get_heic_converter()
                temp_path = temp_path.with_suffix(".jpg")

                if converter_type == "sips":
                    # sips requires output path without extension
                    output_path = temp_path.with_suffix("")
                    cmd = [*converter_cmd, str(image_path), "-o", str(output_path)]
                elif converter_type == "libheif":
                    cmd = [*converter_cmd, str(image_path), str(temp_path)]
                else:  # imagemagick
                    cmd = [*converter_cmd, str(image_path), str(temp_path)]

                try:
                    subprocess.run(cmd, check=True, capture_output=True)
                except subprocess.CalledProcessError as e:
                    raise ImageProcessingError(
                        f"HEIC conversion failed: {e.stderr.decode()}"
                    )

            # Handle other image formats - copy with metadata
            else:
                shutil.copy2(image_path, temp_path)

            return temp_path, self._extract_metadata(temp_path)

        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise ImageProcessingError(f"Image processing failed: {str(e)}")

    def _extract_metadata(self, image_path: Path) -> Dict:
        """Extract metadata from an image file."""
        metadata: Dict[str, Any] = {
            "size_bytes": image_path.stat().st_size,
            "dimensions": None,
        }

        # For SVG files, don't try to get dimensions with PIL
        if image_path.suffix.lower() == ".svg":
            return metadata

        try:
            with Image.open(image_path) as img:
                metadata["dimensions"] = tuple(
                    int(x) for x in img.size
                )  # Convert to tuple of ints
        except Exception as e:
            logger.warning(f"Failed to extract image dimensions: {str(e)}")

        return metadata

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
