# Consolidate Markdown Test Coverage Improvement Plan
Last Updated: 2025-02-10 12:27

## Phase 0: Project Initialization
Status: Complete

- [x] Task 0.1: Core Infrastructure Setup
    - [x] Python 3.12+ project structure
    - [x] UV package management
    - [x] Configuration system
    - [x] Logging framework
    - [x] Pre-commit hooks
    - [x] Base processors
    - Completed: 2025-02-10

- [x] Task 0.2: Dependencies Setup
    - [x] PDF processing (pymupdf)
    - [x] Office document conversion (markitdown)
    - [x] Image processing (pillow, cairosvg)
    - [x] Configuration (tomli)
    - [x] OpenAI integration
    - Completed: 2025-02-10

- [x] Task 0.3: Documentation Enhancement
    - [x] Update root README.md
        - Add `uv pip install .` as primary installation method
        - Update usage examples with `--processor` and `--limit` options
        - Add Model Performance section with link to docs/model_performance.md

    - [x] Enhance docs/README.md
        - Update Contents section for current structure
        - Add API Providers section (OpenAI/OpenRouter)
        - Add Processor Differences section with Claude attachment limitations
        - Add Quick Links to all schema documents
        - Add Getting Started with numbered steps
        - Add Additional Resources section

    - [x] Review Schema Documents (/docs/schemas/)
        - Update Available Schemas list in README.md
        - For each schema (bear_export.md, chatgpt_export.md, claude_export.md, xbookmarks_export.md):
            - Review/update Overview sections
            - Verify Structure sections
            - Update Media Handling sections
            - Check Processing Behavior sections
            - Update Example Structure sections
        - Specific updates:
            - claude_export.md: Update Attachment Handling section
            - chatgpt_export.md: Verify File Handling/Output Format
            - bear_export.md: Update Processing/Media Handling
            - xbookmarks_export.md: Update Processing/Media Handling

    - [x] Enhance configuration.md
        - Update Command Line Options section
        - Expand Global Configuration details
        - Update Environment Variables section
        - Enhance Testing Configuration section
        - Add detailed Model Configuration section:
            - Available Models
            - Model Selection
            - Model Capabilities
            - Model Usage Examples
        - Expand Source Configuration details
        - Add detailed Processor Types section with options tables
        - Add more example configurations

    - [x] Review and Update Core Documentation
        - architecture.md:
            - Update Components, Key Features, Data Flow
            - Review Directory Structure
            - Update Extension Points and Performance sections
        - caching.md:
            - Verify Cache Structure and Implementation
            - Update example structures
        - claude-attachments.md:
            - Review Export Format Limitations
            - Update Attachment Handling details
        - data_flow.md:
            - Update Processing Pipeline diagram
            - Review Component Interactions
        - document_conversion.md:
            - Update Supported Formats
            - Review PyMuPDF implementation details
        - enhanced-output.md:
            - Update Rich Console implementation
            - Review Sample Output
        - examples.md:
            - Add Error Handling Examples
            - Update Common Workflows
            - Add Best Practices
        - installation.md:
            - Update UV-specific instructions
            - Review Platform-Specific details
        - model_performance.md:
            - Update for current default model
            - Review performance analysis (as of 2024-02-01)
        - model-comparison.md:
            - Update Pricing (as of March 2024)
            - Review Use Case Recommendations
        - prd.md:
            - Review Product Scope & Features
            - Update Processing Logic
            - Verify example outputs
        - testing.md:
            - Update for UV usage
            - Enhance Live API Test Guidelines
        - troubleshooting.md:
            - Expand Common Error Messages
            - Add Model-Specific Issues section
            - Update Installation Verification

    - Explanation: Comprehensive documentation update to improve completeness, accuracy, and LLM understanding. Each file has specific changes needed to ensure documentation accurately reflects current implementation and provides clear guidance for both users and LLMs.
    - Note: Documentation updates completed, including README, schema documents, configuration, and core documentation.

## Phase 1: Low Coverage Modules
Status: In Progress

- [ ] Task 1.1: Improve test coverage for `src/consolidate_markdown/__main__.py` (Current coverage: 41%)
    - [ ] Add tests for command-line argument parsing
    - [ ] Add tests for main function execution with different scenarios
    - [ ] Add tests for error handling
    - Explanation: This module is the entry point of the application and needs comprehensive testing to ensure it works correctly.

- [ ] Task 1.2: Improve test coverage for `src/consolidate_markdown/attachments/document.py` (Current coverage: 31%)
    - [ ] Add tests for different document types
    - [ ] Add tests for attachment extraction
    - [ ] Add tests for error handling during document processing
    - Explanation: This module handles document processing and attachment extraction, which are critical for the application's functionality.

- [ ] Task 1.3: Improve test coverage for `src/consolidate_markdown/attachments/gpt.py` (Current coverage: 46%)
    - [ ] Add tests for different GPT models
    - [ ] Add tests for generating text descriptions for attachments
    - [ ] Add tests for error handling during GPT communication
    - Explanation: This module integrates with GPT models for attachment processing, which requires thorough testing to ensure proper functionality and error handling.
    - [ ] Add tests to verify correct client initialization for OpenAI and OpenRouter providers
    - [ ] Add tests to verify correct model selection based on alias
    - [ ] Add tests to verify image encoding and API request formation
    - [ ] Add tests to mock API responses and verify parsing
    - [ ] Add tests to verify error handling for invalid API keys, API errors, and invalid image formats

## Phase 2: Medium Coverage Modules
Status: Pending

- [ ] Task 2.1: Improve test coverage for `src/consolidate_markdown/attachments/image.py` (Current coverage: 66%)
    - [ ] Add tests for image processing functions
    - [ ] Add tests for different image formats
    - Explanation: This module handles image processing, which requires testing to ensure proper functionality for different image formats.
    - [ ] Add tests to verify correct HEIC converter selection for different platforms
    - [ ] Add tests to verify successful SVG conversion using rsvg-convert and inkscape
    - [ ] Add tests for WebP conversion, including different color modes
    - [ ] Add tests to verify correct metadata extraction for different image formats
    - [ ] Add tests to verify error handling for missing converter tools, conversion errors, and unsupported image formats

- [ ] Task 2.2: Improve test coverage for `src/consolidate_markdown/output.py` (Current coverage: 67%)
    - [ ] Add tests for output formatting
    - [ ] Add tests for different output destinations
    - Explanation: This module handles output formatting, which requires testing to ensure proper functionality for different output destinations.
    - [ ] Add tests to verify correct file writing, backup creation, and error handling in `write_output`
    - [ ] Add tests to verify correct formatting of documents, embedded documents, and embedded images
    - [ ] Add tests to verify correct printing of processing summary

- [ ] Task 2.3: Improve test coverage for `src/consolidate_markdown/processors/base.py` (Current coverage: 77%)
    - [ ] Add tests for base processor functions
    - Explanation: This module provides base functionality for processors, which requires testing to ensure proper functionality.
    - [ ] Add tests for AttachmentHandlerMixin methods (_format_image, _format_document, _process_attachment)
    - [ ] Add tests for SourceProcessor methods (validate, _create_temp_dir, _cleanup_temp_dir, _apply_limit)
    - [ ] Add tests for abstract methods in base classes
    - [ ] Add tests for processor registration and deregistration
    - [ ] Add tests for processor initialization and cleanup

## Phase 3: High Coverage Modules
Status: Pending

- [ ] Task 3.1: Review and improve test coverage for modules with coverage between 80% and 90%
    - Explanation: These modules have relatively high coverage, but a review can identify areas for improvement and ensure comprehensive testing.
    - [ ] Review `src/consolidate_markdown/attachments/processor.py` (87%) and add tests for edge cases and error handling
    - [ ] Review `src/consolidate_markdown/config.py` (91%) and add tests for different configuration scenarios
    - [ ] Review `src/consolidate_markdown/log_setup.py` (88%) and add tests for different logging configurations
    - [ ] Review `src/consolidate_markdown/processors/bear.py` (84%) and add tests for specific Bear processor functionality
    - [ ] Review `src/consolidate_markdown/runner.py` (84%) and add tests for different runner scenarios
    - [ ] Review `src/consolidate_markdown/processors/markdown.py` (89%) and add tests for Markdown processor functionality
    - [ ] Review `src/consolidate_markdown/processors/html.py` (85%) and add tests for HTML processor functionality

## Phase 4: Version File
Status: Pending

- [ ] Task 4.1: Add or remove version file
    - Explanation: The version file has 0% coverage, so we need to decide if it's necessary and add tests or remove it.
    - [ ] Add a test to verify that the version information is defined correctly in `src/consolidate_markdown/version.py`
    - [ ] Alternatively, remove the `src/consolidate_markdown/version.py` file if it's not being used
    - [ ] Consider using a dynamic versioning approach, such as using the `__version__` attribute from the `setup.py` file
    - [ ] Consider using a versioning library, such as `setuptools-scm`, to manage versioning

---
## Notes
- [2025-02-10] Prioritized test creation based on current code coverage report.
- [2025-02-10] Focused on modules with coverage below 80% in Phase 1 and Phase 2.
