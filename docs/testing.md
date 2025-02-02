# Testing Guide

This document describes how to run and write tests for the consolidate-markdown tool.

## Test Types

### Unit Tests

Unit tests cover individual components and functions. Run them with:

```bash
uv run pytest tests/unit/
```

### Integration Tests

Integration tests verify component interactions and end-to-end functionality. Run them with:

```bash
uv run pytest tests/integration/
```

### Live API Tests

Live API tests verify integration with OpenAI and OpenRouter APIs. These tests are skipped by default and require API keys to run.

To run live API tests:

1. Configure API keys in `config.toml`:
   ```toml
   [global]
   openai_key = "your-openai-key"
   openrouter_key = "your-openrouter-key"
   ```

2. Run tests with the `--run-live-api` flag:
   ```bash
   uv run pytest tests/integration/test_live_api.py --run-live-api
   ```

## Test Configuration

### API Provider Testing

The test suite supports both OpenAI and OpenRouter APIs:

1. OpenAI Tests:
   - Uses GPT-4 Vision API
   - Requires valid OpenAI API key in `config.toml`
   - Tests image description functionality
   - Verifies response caching

2. OpenRouter Tests:
   - Uses OpenRouter API endpoint
   - Requires valid OpenRouter API key in `config.toml`
   - Tests multiple model providers (GPT-4, Gemini, Yi, BLIP, Llama)
   - Verifies model switching and caching
   - Tests various content types (code, UI, text)

### Test Fixtures

Common test fixtures include:

1. `test_image`: Creates a small test image (100x100) with simple shapes
2. `openai_live_config`: OpenAI-specific configuration from root config
3. `openrouter_live_config`: OpenRouter-specific configuration from root config
4. `code_screenshot`: Test image of code content
5. `ui_screenshot`: Test image of UI elements
6. `text_editor_screenshot`: Test image of text editor content

### Test Data

Test data is managed through fixtures in `tests/conftest.py`:

- Sample Bear notes with attachments
- X bookmarks with media
- Test images and documents
- Configuration templates

## Running Tests

### Basic Test Run

Run all tests (excluding live API tests):

```bash
uv run pytest
```

### Test Selection

Run specific test types:

```bash
# Run only unit tests
uv run pytest tests/unit/

# Run only integration tests
uv run pytest tests/integration/

# Run specific test file
uv run pytest tests/unit/test_config.py

# Run live API tests
uv run pytest tests/integration/test_live_api.py --run-live-api
```

### Test Options

Common pytest options:

- `-v`: Verbose output
- `-s`: Show print statements
- `-k "test_name"`: Run tests matching pattern
- `--pdb`: Debug on failure

## Writing Tests

### Test Structure

Follow the Arrange-Act-Assert pattern:

```python
def test_example():
    # Arrange
    config = create_test_config()

    # Act
    result = process_config(config)

    # Assert
    assert result.is_valid
```

### Live API Test Guidelines

When writing live API tests:

1. Use the `@pytest.mark.live_api` decorator
2. Use the root config for API keys
3. Use minimal test data to reduce costs
4. Implement proper cleanup
5. Handle rate limiting gracefully
6. Use unique test names for caching tests
7. Verify response content appropriately:
   ```python
   # Example assertions for image analysis
   assert len(description) > 50, "Description should be detailed"
   assert "python" in description.lower(), "Should identify Python code"
   assert result.gpt_new_analyses == 1, "Should count as new analysis"
   ```

### Best Practices

1. Keep tests focused and isolated
2. Use appropriate fixtures
3. Clean up test data
4. Document test requirements
5. Handle edge cases
6. Write clear failure messages
7. Use unique test names for caching
8. Increment counters manually when reusing result objects

## Troubleshooting

Common testing issues and solutions:

1. Missing API keys:
   - Check API keys in `config.toml`
   - Verify API key validity
   - Ensure proper provider configuration

2. Skipped tests:
   - Check if `--run-live-api` flag is needed
   - Verify test dependencies
   - Check for missing fixtures

3. Failed assertions:
   - Review test data setup
   - Check API response format
   - Verify configuration settings
   - Ensure unique test names for caching

4. Performance issues:
   - Use appropriate test selection
   - Implement proper cleanup
   - Monitor API rate limits
   - Cache test results appropriately
