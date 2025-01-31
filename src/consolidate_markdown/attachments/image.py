import logging
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

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

        # Handle SVG files by converting to PNG then JPG
        if image_path.suffix.lower() == ".svg":
            try:
                # First convert to PNG
                png_path = self.temp_dir / f"{image_path.stem}.png"
                converter_cmd = _get_svg_converter()

                # Build command based on converter type
                if "rsvg-convert" in converter_cmd[0]:
                    cmd = [*converter_cmd, str(image_path), "--output", str(png_path)]
                else:  # inkscape
                    cmd = [
                        *converter_cmd,
                        str(image_path),
                        f"--export-filename={png_path}",
                    ]

                # Run conversion
                subprocess.run(cmd, check=True, capture_output=True)

                # Then convert PNG to JPG using PIL
                jpg_path = self.temp_dir / f"{image_path.stem}.jpg"
                with Image.open(png_path) as img:
                    # Convert to RGB mode if necessary
                    if img.mode in ("RGBA", "LA") or (
                        img.mode == "P" and "transparency" in img.info
                    ):
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        if img.mode == "P":
                            img = img.convert("RGBA")
                        background.paste(img, mask=img.split()[-1])
                        img = background
                    elif img.mode != "RGB":
                        img = img.convert("RGB")
                    img.save(jpg_path, "JPEG", quality=95)

                # Clean up temporary PNG
                png_path.unlink()

                return jpg_path, self._extract_metadata(jpg_path)
            except Exception as e:
                logger.warning(
                    f"SVG conversion failed for {image_path.name}, using basic copy: {str(e)}"
                )
                # Fall back to copying the original file
                shutil.copy2(image_path, temp_path)
                return temp_path, self._extract_metadata(temp_path)

        # Convert HEIC to JPG if needed
        if image_path.suffix.lower() == ".heic":
            jpg_path = self.temp_dir / f"{image_path.stem}.jpg"
            try:
                converter_cmd, converter_type = _get_heic_converter()
                if converter_type == "sips":
                    subprocess.run(
                        [*converter_cmd, str(image_path), "--out", str(jpg_path)],
                        check=True,
                        capture_output=True,
                    )
                elif converter_type == "libheif":
                    subprocess.run(
                        [*converter_cmd, str(image_path), str(jpg_path)],
                        check=True,
                        capture_output=True,
                    )
                elif converter_type == "imagemagick":
                    subprocess.run(
                        [*converter_cmd, str(image_path), str(jpg_path)],
                        check=True,
                        capture_output=True,
                    )
                return jpg_path, self._extract_metadata(jpg_path)
            except Exception as e:
                logger.warning(
                    f"HEIC conversion failed for {image_path.name}, using basic copy: {str(e)}"
                )
                # Fall back to copying the original file but keep .jpg extension
                temp_path = self.temp_dir / f"{image_path.stem}.jpg"
                shutil.copy2(image_path, temp_path)
                return temp_path, self._extract_metadata(temp_path)

        # Just copy the file for other formats
        shutil.copy2(image_path, temp_path)
        return temp_path, self._extract_metadata(temp_path)

    def _extract_metadata(self, image_path: Path) -> Dict:
        """Extract metadata from an image file."""
        try:
            # For unsupported formats, return basic metadata
            if image_path.suffix.lower() == ".heic":  # Removed .svg since we convert it
                return {
                    "size_bytes": image_path.stat().st_size,
                    "format": image_path.suffix.lower().lstrip("."),
                    "mode": "unknown",
                    "dimensions": (0, 0),
                }

            # For supported formats, use PIL
            with Image.open(image_path) as img:
                metadata = {
                    "size_bytes": image_path.stat().st_size,
                    "format": img.format.lower() if img.format else "unknown",
                    "mode": img.mode,
                    "dimensions": img.size,
                }
                return metadata
        except Exception:
            # Fallback metadata for any errors
            return {
                "size_bytes": image_path.stat().st_size if image_path.exists() else 0,
                "format": image_path.suffix.lower().lstrip("."),
                "mode": "unknown",
                "dimensions": (0, 0),
            }

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
