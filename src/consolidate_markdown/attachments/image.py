"""Image processing utilities."""

import logging  # Standard library
import platform  # Standard library
import shutil  # Standard library
import subprocess  # Standard library
from pathlib import Path  # Standard library
from typing import Any, Dict, List, Tuple  # Standard library

from PIL import Image  # External dependency: pillow

from ..log_setup import logger

# Suppress PIL debug logging
pil_logger = logging.getLogger("PIL")
pil_logger.setLevel(logging.WARNING)


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


class ImageProcessor:
    """Handle image format conversions and metadata extraction."""

    SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".svg", ".heic", ".webp"}

    def __init__(self, cm_dir: Path):
        self.cm_dir = cm_dir
        self.temp_dir = cm_dir / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def _convert_svg_to_png(self, svg_path: Path, png_path: Path) -> None:
        """Convert SVG to PNG for GPT analysis."""
        try:
            # Try rsvg-convert first
            subprocess.run(
                ["rsvg-convert", "--version"], capture_output=True, check=True
            )
            cmd = ["rsvg-convert", "-f", "png", str(svg_path), "-o", str(png_path)]
        except (subprocess.SubprocessError, FileNotFoundError):
            try:
                # Try inkscape as fallback
                subprocess.run(
                    ["inkscape", "--version"], capture_output=True, check=True
                )
                cmd = [
                    "inkscape",
                    "--export-type=png",
                    "--export-filename=" + str(png_path),
                    str(svg_path),
                ]
            except (subprocess.SubprocessError, FileNotFoundError):
                raise ImageProcessingError(
                    "SVG converter not found. Please install librsvg (rsvg-convert) or inkscape."
                )

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise ImageProcessingError(f"SVG conversion failed: {e.stderr.decode()}")

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
            # Handle SVG files - convert to PNG for GPT analysis
            if suffix == ".svg":
                with open(image_path, "r", encoding="utf-8") as f:
                    svg_content = f.read()

                # Extract dimensions from SVG content
                dimensions = self._extract_svg_dimensions(svg_content)

                # Convert SVG to PNG for GPT analysis
                png_path = temp_path.with_suffix(".png")
                self._convert_svg_to_png(image_path, png_path)

                # Create metadata with both SVG content and PNG path
                metadata = {
                    "size_bytes": image_path.stat().st_size,
                    "dimensions": dimensions,
                    "inlined_content": svg_content,
                    "png_path": png_path,
                    "is_image": True,
                }

                # Copy original SVG for reference
                shutil.copy2(image_path, temp_path)
                return temp_path, metadata

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

            # Handle WebP files - convert to JPEG using Pillow
            elif suffix == ".webp":
                temp_path = temp_path.with_suffix(".jpg")
                try:
                    with Image.open(image_path) as img:
                        # Convert to RGB mode if necessary (in case of RGBA WebP)
                        if img.mode in ("RGBA", "LA"):
                            background = Image.new("RGB", img.size, (255, 255, 255))
                            background.paste(img, mask=img.split()[-1])
                            img = background
                        img.save(temp_path, "JPEG", quality=95)
                except Exception as e:
                    raise ImageProcessingError(f"WebP conversion failed: {str(e)}")

            # Handle other image formats - copy with metadata
            else:
                shutil.copy2(image_path, temp_path)

            return temp_path, self._extract_metadata(temp_path)

        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise ImageProcessingError(f"Image processing failed: {str(e)}")

    def _extract_svg_dimensions(self, svg_content: str) -> Tuple[int, int]:
        """Extract width and height from SVG content."""
        try:
            import re

            # Try to find width and height in SVG tag
            width = height = None
            svg_tag = re.search(r"<svg[^>]*>", svg_content)
            if svg_tag:
                tag = svg_tag.group(0)
                # Try explicit width/height attributes
                width_match = re.search(r'width="([0-9.]+)(?:px)?"', tag)
                height_match = re.search(r'height="([0-9.]+)(?:px)?"', tag)
                if width_match and height_match:
                    width = int(float(width_match.group(1)))
                    height = int(float(height_match.group(1)))
                else:
                    # Try viewBox attribute
                    viewbox_match = re.search(
                        r'viewBox="[0-9.]+ [0-9.]+ ([0-9.]+) ([0-9.]+)"', tag
                    )
                    if viewbox_match:
                        width = int(float(viewbox_match.group(1)))
                        height = int(float(viewbox_match.group(2)))
            return (width or 0, height or 0)
        except Exception as e:
            logger.warning(f"Failed to extract SVG dimensions: {str(e)}")
            return (0, 0)

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
