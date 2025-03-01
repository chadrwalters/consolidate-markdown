import subprocess
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from consolidate_markdown.attachments.image import (
    ImageProcessingError,
    ImageProcessor,
    _get_heic_converter,
)


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path


@pytest.fixture
def cm_dir(temp_dir):
    """Create a temporary CM directory for testing."""
    cm_dir = temp_dir / ".cm"
    cm_dir.mkdir(parents=True, exist_ok=True)
    return cm_dir


@pytest.fixture
def image_processor(cm_dir):
    """Create an ImageProcessor instance for testing."""
    return ImageProcessor(cm_dir)


@pytest.fixture
def jpg_image(temp_dir):
    """Create a sample JPG image file."""
    jpg_path = temp_dir / "test.jpg"

    # Create a small test image
    img = Image.new("RGB", (100, 100), color="red")
    img.save(jpg_path)

    return jpg_path


@pytest.fixture
def png_image(temp_dir):
    """Create a sample PNG image file."""
    png_path = temp_dir / "test.png"

    # Create a small test image
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(png_path)

    return png_path


@pytest.fixture
def svg_image(temp_dir):
    """Create a sample SVG image file."""
    svg_path = temp_dir / "test.svg"

    # Create a simple SVG file
    svg_content = """<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
        <rect width="100" height="100" fill="green" />
    </svg>"""

    svg_path.write_text(svg_content)

    return svg_path


@pytest.fixture
def webp_image(temp_dir):
    """Create a sample WebP image file."""
    webp_path = temp_dir / "test.webp"

    # Create a small test image
    img = Image.new("RGB", (100, 100), color="yellow")
    img.save(webp_path, format="WEBP")

    return webp_path


@pytest.fixture
def heic_image(temp_dir):
    """Create a mock HEIC image file."""
    heic_path = temp_dir / "test.heic"

    # Just create a dummy file since we'll mock the conversion
    heic_path.write_bytes(b"fake heic data")

    return heic_path


class TestImageProcessor:
    """Tests for the ImageProcessor class."""

    def test_initialization(self, cm_dir):
        """Test initialization of ImageProcessor."""
        processor = ImageProcessor(cm_dir)

        # Check that the directories are set correctly
        assert processor.cm_dir == cm_dir
        assert processor.temp_dir == cm_dir / "temp"

        # Check that the temp directory was created
        assert processor.temp_dir.exists()
        assert processor.temp_dir.is_dir()

    @patch("consolidate_markdown.attachments.image.subprocess.run")
    def test_convert_svg_to_png_with_rsvg(
        self, mock_run, image_processor, svg_image, temp_dir
    ):
        """Test converting SVG to PNG using rsvg-convert."""
        # Set up mock subprocess.run to succeed with rsvg-convert
        mock_run.return_value = MagicMock(returncode=0)

        # Create output path
        png_path = temp_dir / "output.png"

        # Convert SVG to PNG
        image_processor._convert_svg_to_png(svg_image, png_path)

        # Check that rsvg-convert was called with the correct arguments
        assert mock_run.call_count == 2
        # First call should check if rsvg-convert is available
        assert mock_run.call_args_list[0][0][0][0] == "rsvg-convert"
        # Second call should convert the SVG
        assert mock_run.call_args_list[1][0][0][0] == "rsvg-convert"
        assert mock_run.call_args_list[1][0][0][2] == "png"

    @patch("consolidate_markdown.attachments.image.subprocess.run")
    def test_convert_svg_to_png_with_inkscape(
        self, mock_run, image_processor, svg_image, temp_dir
    ):
        """Test converting SVG to PNG using Inkscape as fallback."""

        # Set up mock subprocess.run to fail for rsvg-convert but succeed for inkscape
        def side_effect(*args, **kwargs):
            if args[0][0] == "rsvg-convert":
                raise subprocess.SubprocessError("rsvg-convert not found")
            return MagicMock(returncode=0)

        mock_run.side_effect = side_effect

        # Create output path
        png_path = temp_dir / "output.png"

        # Convert SVG to PNG
        image_processor._convert_svg_to_png(svg_image, png_path)

        # Check that inkscape was called after rsvg-convert failed
        assert (
            mock_run.call_count == 3
        )  # Version check, rsvg-convert failure, inkscape success
        assert mock_run.call_args_list[0][0][0][0] == "rsvg-convert"  # Version check
        assert mock_run.call_args_list[2][0][0][0] == "inkscape"  # Inkscape call

    @patch("consolidate_markdown.attachments.image.subprocess.run")
    def test_convert_svg_to_png_no_converter(
        self, mock_run, image_processor, svg_image, temp_dir
    ):
        """Test error handling when no SVG converter is available."""
        # Set up mock subprocess.run to fail for both converters
        mock_run.side_effect = subprocess.SubprocessError("No converter found")

        # Create output path
        png_path = temp_dir / "output.png"

        # Try to convert SVG to PNG
        with pytest.raises(ImageProcessingError, match="SVG converter not found"):
            image_processor._convert_svg_to_png(svg_image, png_path)

    @patch("consolidate_markdown.attachments.image.subprocess.run")
    def test_convert_svg_to_png_conversion_error(
        self, mock_run, image_processor, svg_image, temp_dir
    ):
        """Test error handling when SVG conversion fails."""
        # Set up mock subprocess.run to succeed for rsvg-convert check but fail for conversion
        mock_run.side_effect = [
            MagicMock(returncode=0),  # rsvg-convert --version
            subprocess.CalledProcessError(
                1, "rsvg-convert", stderr=b"Conversion error"
            ),
        ]

        # Create output path
        png_path = temp_dir / "output.png"

        # Try to convert SVG to PNG
        with pytest.raises(ImageProcessingError, match="SVG conversion failed"):
            image_processor._convert_svg_to_png(svg_image, png_path)

    def test_process_image_jpg(self, image_processor, jpg_image):
        """Test processing a JPG image."""
        # Process the image
        temp_path, metadata = image_processor.process_image(jpg_image)

        # Check the result
        assert temp_path.exists()
        assert temp_path.suffix == ".jpg"
        assert temp_path.name == jpg_image.name

        # Check the metadata
        assert "size_bytes" in metadata
        assert metadata["size_bytes"] > 0
        assert "dimensions" in metadata
        assert metadata["dimensions"] == (100, 100)

    def test_process_image_png(self, image_processor, png_image):
        """Test processing a PNG image."""
        # Process the image
        temp_path, metadata = image_processor.process_image(png_image)

        # Check the result
        assert temp_path.exists()
        assert temp_path.suffix == ".png"
        assert temp_path.name == png_image.name

        # Check the metadata
        assert "size_bytes" in metadata
        assert metadata["size_bytes"] > 0
        assert "dimensions" in metadata
        assert metadata["dimensions"] == (100, 100)

    @patch("consolidate_markdown.attachments.image.ImageProcessor._convert_svg_to_png")
    def test_process_image_svg(self, mock_convert, image_processor, svg_image):
        """Test processing an SVG image."""
        # Set up mock for PNG conversion
        png_path = svg_image.with_suffix(".png")
        mock_convert.return_value = None  # Just for the side effect

        # Create a dummy PNG file
        with open(png_path, "wb") as f:
            f.write(b"fake png data")

        # Process the image
        temp_path, metadata = image_processor.process_image(svg_image)

        # Check the result
        assert temp_path.exists()
        assert temp_path.suffix == ".svg"
        assert temp_path.name == svg_image.name

        # Check the metadata
        assert "size_bytes" in metadata
        assert metadata["size_bytes"] > 0
        assert "dimensions" in metadata
        assert metadata["dimensions"] == (100, 100)  # From the SVG width/height
        assert "inlined_content" in metadata
        assert "<svg" in metadata["inlined_content"]
        assert "png_path" in metadata
        assert metadata["png_path"].suffix == ".png"

        # Check that the conversion was called
        mock_convert.assert_called_once()

    @patch("consolidate_markdown.attachments.image._get_heic_converter")
    @patch("consolidate_markdown.attachments.image.subprocess.run")
    def test_process_image_heic(
        self, mock_run, mock_get_converter, image_processor, heic_image
    ):
        """Test processing a HEIC image."""
        # Set up mocks
        mock_get_converter.return_value = (["sips", "-s", "format", "jpeg"], "sips")
        mock_run.return_value = MagicMock(returncode=0)

        # Mock the _extract_metadata method to avoid file not found errors
        with patch.object(image_processor, "_extract_metadata") as mock_extract:
            mock_extract.return_value = {
                "dimensions": (100, 100),
                "size_bytes": 1024,
                "is_image": True,
            }

            # Process the image
            temp_path, metadata = image_processor.process_image(heic_image)

            # Check that the image was processed correctly
            assert temp_path.suffix == ".jpg"
            assert metadata["dimensions"] == (100, 100)
            assert metadata["is_image"] is True

            # Check that the converter was called with the correct arguments
            mock_run.assert_called_once()

    @patch("consolidate_markdown.attachments.image._get_heic_converter")
    @patch("consolidate_markdown.attachments.image.subprocess.run")
    def test_process_image_heic_error(
        self, mock_run, mock_get_converter, image_processor, heic_image
    ):
        """Test error handling when HEIC conversion fails."""
        # Set up mocks
        mock_get_converter.return_value = (["sips", "-s", "format", "jpeg"], "sips")
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "sips", stderr=b"Conversion error"
        )

        # Try to process the image
        with pytest.raises(ImageProcessingError, match="HEIC conversion failed"):
            image_processor.process_image(heic_image)

    def test_process_image_webp(self, image_processor, webp_image):
        """Test processing a WebP image."""
        # Process the image
        temp_path, metadata = image_processor.process_image(webp_image)

        # Check the result
        assert temp_path.exists()
        assert temp_path.suffix == ".jpg"  # WebP is converted to JPG

        # Check the metadata
        assert "size_bytes" in metadata
        assert metadata["size_bytes"] > 0
        assert "dimensions" in metadata
        assert metadata["dimensions"] == (100, 100)

    def test_process_image_webp_with_alpha(self, temp_dir, image_processor):
        """Test processing a WebP image with alpha channel."""
        # Create a WebP image with alpha channel
        webp_path = temp_dir / "alpha.webp"
        img = Image.new(
            "RGBA", (100, 100), color=(255, 0, 0, 128)
        )  # Semi-transparent red
        img.save(webp_path, format="WEBP")

        # Process the image
        temp_path, metadata = image_processor.process_image(webp_path)

        # Check the result
        assert temp_path.exists()
        assert temp_path.suffix == ".jpg"  # WebP is converted to JPG

        # Check the metadata
        assert "dimensions" in metadata
        assert metadata["dimensions"] == (100, 100)

        # Check that the image was converted to RGB
        with Image.open(temp_path) as img:
            assert img.mode == "RGB"  # Alpha channel should be removed

    def test_process_image_nonexistent(self, image_processor, temp_dir):
        """Test error handling for nonexistent image files."""
        # Create a path to a nonexistent file
        nonexistent_path = temp_dir / "nonexistent.jpg"

        # Try to process the nonexistent image
        with pytest.raises(FileNotFoundError):
            image_processor.process_image(nonexistent_path)

    def test_process_image_unsupported_format(self, image_processor, temp_dir):
        """Test error handling for unsupported image formats."""
        # Create a file with unsupported extension
        unsupported_path = temp_dir / "test.xyz"
        unsupported_path.write_bytes(b"unsupported format")

        # Try to process the unsupported image
        with pytest.raises(ImageProcessingError, match="Unsupported image format"):
            image_processor.process_image(unsupported_path)

    def test_process_image_caching(self, image_processor, jpg_image):
        """Test that processed images are cached."""
        # Mock the _extract_metadata method to return consistent results
        with patch.object(image_processor, "_extract_metadata") as mock_extract:
            # Set up mock to return different values on each call
            mock_extract.side_effect = [
                # First call - original metadata
                {
                    "dimensions": (100, 100),
                    "size_bytes": 1024,
                    "is_image": True,
                },
                # Second call - same as first (for cached version)
                {
                    "dimensions": (100, 100),
                    "size_bytes": 1024,
                    "is_image": True,
                },
                # Third call - updated metadata for forced processing
                {
                    "dimensions": (100, 100),
                    "size_bytes": 2048,  # Different size
                    "is_image": True,
                },
            ]

            # Process the image first time
            temp_path1, metadata1 = image_processor.process_image(jpg_image)

            # Modify the source file to be newer
            jpg_image.write_bytes(b"updated image data")

            # Process the image second time without force
            temp_path2, metadata2 = image_processor.process_image(jpg_image)

            # Check that the cached version was used
            assert temp_path1 == temp_path2
            assert metadata1 == metadata2

            # Process the image third time with force
            temp_path3, metadata3 = image_processor.process_image(jpg_image, force=True)

            # Check that a new version was created
            assert temp_path3 == temp_path1  # Same path
            assert (
                metadata3["size_bytes"] != metadata1["size_bytes"]
            )  # Different content

    def test_extract_svg_dimensions_with_attributes(self, image_processor):
        """Test extracting dimensions from SVG with width/height attributes."""
        svg_content = """<svg width="200" height="300" xmlns="http://www.w3.org/2000/svg">
            <rect width="200" height="300" fill="blue" />
        </svg>"""

        dimensions = image_processor._extract_svg_dimensions(svg_content)

        assert dimensions == (200, 300)

    def test_extract_svg_dimensions_with_viewbox(self, image_processor):
        """Test extracting dimensions from SVG with viewBox attribute."""
        svg_content = """<svg viewBox="0 0 400 500" xmlns="http://www.w3.org/2000/svg">
            <rect width="400" height="500" fill="blue" />
        </svg>"""

        dimensions = image_processor._extract_svg_dimensions(svg_content)

        assert dimensions == (400, 500)

    def test_extract_svg_dimensions_with_decimal_values(self, image_processor):
        """Test extracting dimensions from SVG with decimal values."""
        svg_content = """<svg width="200.5" height="300.75" xmlns="http://www.w3.org/2000/svg">
            <rect width="200.5" height="300.75" fill="blue" />
        </svg>"""

        dimensions = image_processor._extract_svg_dimensions(svg_content)

        assert dimensions == (200, 300)  # Should be converted to integers

    def test_extract_svg_dimensions_missing(self, image_processor):
        """Test extracting dimensions from SVG with missing dimensions."""
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <rect fill="blue" />
        </svg>"""

        dimensions = image_processor._extract_svg_dimensions(svg_content)

        assert dimensions == (0, 0)  # Default when dimensions are missing

    def test_extract_svg_dimensions_error(self, image_processor):
        """Test error handling when extracting SVG dimensions."""
        # Invalid SVG content
        svg_content = "Not an SVG file"

        dimensions = image_processor._extract_svg_dimensions(svg_content)

        assert dimensions == (0, 0)  # Default on error

    def test_extract_metadata_jpg(self, image_processor, jpg_image):
        """Test extracting metadata from a JPG image."""
        metadata = image_processor._extract_metadata(jpg_image)

        assert "size_bytes" in metadata
        assert metadata["size_bytes"] > 0
        assert "dimensions" in metadata
        assert metadata["dimensions"] == (100, 100)

    def test_extract_metadata_svg(self, image_processor, svg_image):
        """Test extracting metadata from an SVG image."""
        metadata = image_processor._extract_metadata(svg_image)

        assert "size_bytes" in metadata
        assert metadata["size_bytes"] > 0
        assert "dimensions" in metadata
        assert (
            metadata["dimensions"] is None
        )  # SVG dimensions are not extracted with PIL

    def test_extract_metadata_error(self, image_processor, temp_dir):
        """Test error handling when extracting metadata."""
        # Create a corrupt image file
        corrupt_path = temp_dir / "corrupt.jpg"
        corrupt_path.write_bytes(b"not a valid image")

        # Extract metadata should not raise an exception
        metadata = image_processor._extract_metadata(corrupt_path)

        assert "size_bytes" in metadata
        assert metadata["size_bytes"] > 0
        assert "dimensions" in metadata
        assert metadata["dimensions"] is None  # Failed to extract dimensions

    def test_cleanup(self, image_processor):
        """Test cleaning up temporary files."""
        # Create some test files in the temp directory
        test_file = image_processor.temp_dir / "test.txt"
        test_file.write_text("test")

        # Verify the file exists
        assert test_file.exists()

        # Clean up
        image_processor.cleanup()

        # Verify the temp directory was removed
        assert not image_processor.temp_dir.exists()


class TestHelperFunctions:
    """Tests for helper functions in the image module."""

    @patch("consolidate_markdown.attachments.image.subprocess.run")
    @patch("consolidate_markdown.attachments.image.platform.system")
    def test_get_heic_converter_imagemagick(self, mock_system, mock_run):
        """Test getting HEIC converter with ImageMagick available."""
        # Set up mocks
        mock_system.return_value = "Linux"
        mock_run.return_value = MagicMock(returncode=0)

        # Get the converter
        converter, converter_type = _get_heic_converter()

        # Check the result
        assert converter == ["magick", "convert"]
        assert converter_type == "imagemagick"

        # Check that subprocess.run was called to check for ImageMagick
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0][0] == "magick"

    @patch("consolidate_markdown.attachments.image.subprocess.run")
    @patch("consolidate_markdown.attachments.image.platform.system")
    def test_get_heic_converter_macos(self, mock_system, mock_run):
        """Test getting HEIC converter on macOS."""
        # Set up mocks
        mock_system.return_value = "Darwin"
        mock_run.side_effect = FileNotFoundError("magick not found")

        # Get the converter
        converter, converter_type = _get_heic_converter()

        # Check the result
        assert converter == ["sips", "-s", "format", "jpeg"]
        assert converter_type == "sips"

    @patch("consolidate_markdown.attachments.image.subprocess.run")
    @patch("consolidate_markdown.attachments.image.platform.system")
    def test_get_heic_converter_linux_libheif(self, mock_system, mock_run):
        """Test getting HEIC converter on Linux with libheif."""
        # Set up mocks
        mock_system.return_value = "Linux"
        mock_run.side_effect = [
            FileNotFoundError("magick not found"),
            MagicMock(returncode=0),
        ]

        # Get the converter
        converter, converter_type = _get_heic_converter()

        # Check the result
        assert converter == ["heif-convert"]
        assert converter_type == "libheif"

        # Check that subprocess.run was called to check for both converters
        assert mock_run.call_count == 2
        assert mock_run.call_args_list[0][0][0][0] == "magick"
        assert mock_run.call_args_list[1][0][0][0] == "heif-convert"

    @patch("consolidate_markdown.attachments.image.subprocess.run")
    @patch("consolidate_markdown.attachments.image.platform.system")
    def test_get_heic_converter_no_converter(self, mock_system, mock_run):
        """Test error handling when no HEIC converter is available."""
        # Set up mocks
        mock_system.return_value = "Linux"
        mock_run.side_effect = FileNotFoundError("No converter found")

        # Try to get the converter
        with pytest.raises(ImageProcessingError, match="No HEIC converter found"):
            _get_heic_converter()
