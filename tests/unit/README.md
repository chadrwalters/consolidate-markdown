# Unit Tests for Consolidate Markdown Issues

This directory contains unit tests that reproduce and verify fixes for issues found in the Consolidate Markdown tool.

## Issues Being Tested

1. **ChatGPT Processor Issues** (`test_chatgpt_processor_issues.py`)
   - `NoneType` object has no attribute `replace` error when title is None
   - Missing content in message
   - None content in message

2. **Claude Processor Issues** (`test_claude_processor_issues.py`)
   - Invalid text attachment with missing type
   - Invalid text attachment with missing name
   - Empty conversation with no messages

3. **XBookmarks Processor Issues** (`test_xbookmarks_processor_issues.py`)
   - Missing index file in bookmark directory
   - Special directories like "temp" and "markitdown"
   - Empty bookmark directory

4. **Image Processor Issues** (`test_image_processor_issues.py`)
   - GIF image format handling
   - Missing attachment
   - Unsupported image format

## Running the Tests

You can run all the issue tests using the provided script:

```bash
./tests/run_issue_tests.py
```

Or run individual test files with pytest:

```bash
# Run all issue tests
pytest -xvs tests/unit/test_*_issues.py

# Run a specific test file
pytest -xvs tests/unit/test_chatgpt_processor_issues.py
```

## Expected Results

Before implementing fixes, these tests are expected to fail. After implementing fixes, all tests should pass, indicating that the issues have been resolved.

## Test Strategy

These tests follow a pattern:

1. Set up test data that reproduces the issue
2. Run the processor on the test data
3. Verify that the issue is handled correctly (no exceptions, appropriate warnings, etc.)
4. Check that the output is as expected

This approach ensures that the fixes address the specific issues encountered in real-world usage.
