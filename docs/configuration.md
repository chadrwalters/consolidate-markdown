# Configuration Guide

This document describes how to configure the consolidate-markdown tool.

## Command Line Options

The following command line options are available:

- `--config PATH`: Path to configuration file (required)
- `--force`: Force regeneration of all files
- `--delete`: Delete existing output and cache before processing
- `--debug`: Enable debug logging
- `--log-level LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `--no-image`: Skip image analysis
- `--processor TYPE`: Run only the specified processor type (claude, bear, xbookmarks, chatgptexport)
- `--limit N`: Process only the N most recent items from each source

## Configuration File

The configuration file uses TOML format and consists of a global section and one or more source sections.

### Global Configuration

The global section defines settings that apply to all processors:

```toml
[global]
# Directory for cache files (required)
cm_dir = ".cm"

# Skip image analysis (optional, default: false)
no_image = false

# Log level (optional, default: INFO)
log_level = "INFO"

# API Provider Configuration
api_provider = "openai"  # Can be "openai" or "openrouter"

# OpenAI Configuration
openai_key = "sk-..."  # OpenAI API key
openai_base_url = "https://api.openai.com/v1"  # OpenAI API base URL (optional)

# OpenRouter Configuration (when api_provider = "openrouter")
openrouter_key = "sk-..."  # OpenRouter API key
openrouter_base_url = "https://openrouter.ai/api/v1"  # OpenRouter API base URL (optional)
```

### Environment Variables

The following environment variables can be used to override configuration settings:

- `CM_LOG_LEVEL`: Override log level
- `CM_NO_IMAGE`: Set to "true" to skip image analysis
- `CM_API_PROVIDER`: Set the API provider ("openai" or "openrouter")
- `OPENAI_API_KEY`: OpenAI API key
- `OPENAI_API_BASE_URL`: OpenAI API base URL
- `OPENROUTER_API_KEY`: OpenRouter API key
- `OPENROUTER_API_BASE_URL`: OpenRouter API base URL

### Testing Configuration

For testing purposes, you can use environment variables to configure API providers:

1. For OpenAI testing:
   ```bash
   export OPENAI_API_KEY="your-openai-key"
   pytest tests/integration/test_live_api.py --run-live-api
   ```

2. For OpenRouter testing:
   ```bash
   export OPENROUTER_API_KEY="your-openrouter-key"
   pytest tests/integration/test_live_api.py --run-live-api
   ```

3. For testing both providers:
   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export OPENROUTER_API_KEY="your-openrouter-key"
   pytest tests/integration/test_live_api.py --run-live-api
   ```

See the [Testing Guide](testing.md) for more details on running tests.

### API Provider Configuration

The tool supports two API providers for image analysis:

1. OpenAI (default)
   - Uses the OpenAI GPT-4 Vision API
   - Requires `openai_key`
   - Optional custom `openai_base_url`

2. OpenRouter
   - Uses the OpenRouter API
   - Requires `openrouter_key`
   - Optional custom `openrouter_base_url`

Example OpenAI configuration:
```toml
[global]
api_provider = "openai"
openai_key = "sk-..."
```

Example OpenRouter configuration:
```toml
[global]
api_provider = "openrouter"
openrouter_key = "sk-..."
```

### Model Configuration

The tool supports configuring different models for image analysis through the `models` section:

```toml
[models]
# Default model (as of February 2024)
default_model = "google/gemini-pro-vision-1.0"

# Alternate models (optional)
alternate_model_gpt4 = "gpt-4o"
alternate_model_yi = "yi/yi-vision-01"
alternate_model_blip = "deepinfra/blip"
alternate_model_llama = "meta/llama-3.2-90b-vision-instruct"
```

#### Available Models

When using OpenRouter as the API provider, the following models are available:

1. Google Gemini Pro Vision (Default)
   - Our current default model
   - Excellent balance of performance and cost
   - Strong technical understanding
   - Model: `google/gemini-pro-vision-1.0`

2. GPT-4 Vision
   - Highest performance for complex tasks
   - Most expensive option
   - Model: `gpt-4o`

3. Yi Vision
   - Fast and efficient vision model
   - Good at general image description
   - Model: `yi/yi-vision-01`

4. DeepInfra BLIP
   - Specialized in image understanding
   - Good at concise descriptions
   - Model: `deepinfra/blip`

5. Llama 3.2 Vision
   - Open source vision model
   - Good general performance
   - Model: `meta/llama-3.2-90b-vision-instruct`

See our [Model Performance Analysis](model_performance.md) for detailed comparisons and recommendations.

#### Model Selection

Models can be selected in several ways:

1. Default Model:
   ```toml
   [models]
   default_model = "google/gemini-pro-vision-1.0"
   ```

2. Environment Variable:
   ```bash
   export CM_DEFAULT_MODEL="google/gemini-pro-vision-1.0"
   ```

3. Alternate Models:
   ```toml
   [models]
   default_model = "google/gemini-pro-vision-1.0"
   alternate_model_gpt4 = "gpt-4o"
   ```

#### Model Capabilities

Different models have different strengths:

1. Text Recognition
   - GPT-4 Vision: Excellent
   - Gemini Pro Vision: Excellent
   - Yi Vision: Good
   - DeepInfra BLIP: Good
   - Llama Vision: Good

2. Code Understanding
   - GPT-4 Vision: Excellent
   - Gemini Pro Vision: Excellent
   - Yi Vision: Good
   - DeepInfra BLIP: Fair
   - Llama Vision: Good

3. UI Element Recognition
   - GPT-4 Vision: Excellent
   - Gemini Pro Vision: Excellent
   - Yi Vision: Good
   - DeepInfra BLIP: Fair
   - Llama Vision: Good

4. Technical Context
   - GPT-4 Vision: Excellent
   - Gemini Pro Vision: Excellent
   - Yi Vision: Good
   - DeepInfra BLIP: Fair
   - Llama Vision: Good

#### Model Usage Examples

1. Basic Configuration (Google Gemini Pro Vision):
   ```toml
   [models]
   default_model = "google/gemini-pro-vision-1.0"
   ```

2. Multiple Models Configuration:
   ```toml
   [models]
   default_model = "google/gemini-pro-vision-1.0"
   alternate_model_gpt4 = "gpt-4o"
   ```

3. Technical Documentation Configuration:
   ```toml
   [models]
   default_model = "google/gemini-pro-vision-1.0"  # Better for technical content
   alternate_model_backup = "gpt-4o"               # Fallback option
   ```

### Source Configuration

Each source section defines a specific content source to process:

```toml
[[sources]]
# Source type (required)
# Valid values: "claude", "bear", "xbookmarks", "chatgptexport"
type = "claude"

# Source directory (required)
# Path to input files
src_dir = "~/Documents/Claude Exports"

# Destination directory (required)
# Path where processed files will be written
dest_dir = "./output/claude"

# Source-specific options (optional)
# These vary by processor type
options = { key = "value" }
```

## Processor Types

### Claude Exports

Processes Claude conversation exports:

```toml
[[sources]]
type = "claude"
src_dir = "~/Downloads/claude_exports"
dest_dir = "output/claude"
options = {
    # Optional: Custom date format for conversation filenames
    date_format = "%Y%m%d",
    # Optional: Custom title format for conversation files
    title_format = "{date}-{name}",
    # Optional: Preserve original XML tags in output
    preserve_tags = false,
    # Optional: Extract artifacts from conversations
    extract_artifacts = true,
    # Optional: Track artifact versions
    track_versions = true,
    # Optional: Process attachments
    process_attachments = true,
    # Optional: Directory for processed attachments
    attachments_dir = "attachments"
}
```

### Bear Notes

Processes Bear note files:

```toml
[[sources]]
type = "bear"
src_dir = "~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/Local Files/Note Files"
dest_dir = "output/bear"
```

### X Bookmarks

Processes X (Twitter) bookmarks:

```toml
[[sources]]
type = "xbookmarks"
src_dir = "~/Library/Containers/com.apple.Safari/Data/Library/Safari/Bookmarks.plist"
dest_dir = "output/bookmarks"
```

### ChatGPT Export

Processes ChatGPT conversation exports:

```toml
[[sources]]
type = "chatgptexport"
src_dir = "~/Downloads/chatgpt_exports"
dest_dir = "output/chatgpt"
```

## Example Configurations

### Basic Claude Configuration

```toml
[global]
cm_dir = ".cm"
no_image = true

[[sources]]
type = "claude"
src_dir = "~/Documents/Claude Exports"
dest_dir = "./output/claude"
```

### Advanced Claude Configuration

```toml
[global]
cm_dir = ".cm"
openai_key = "sk-..."  # For image analysis in attachments

[[sources]]
type = "claude"
src_dir = "~/Documents/Claude Exports"
dest_dir = "./output/claude"
options = {
    date_format = "%Y%m%d",
    title_format = "{date}-{name}",
    preserve_tags = false,
    extract_artifacts = true,
    track_versions = true,
    process_attachments = true,
    attachments_dir = "attachments"
}
```

### Multiple Sources Including Claude

```toml
[global]
cm_dir = ".cm"
openai_key = "sk-..."

[[sources]]
type = "claude"
src_dir = "~/Documents/Claude Exports"
dest_dir = "./output/claude"

[[sources]]
type = "bear"
src_dir = "~/Documents/Notes"
dest_dir = "./output/notes"

[[sources]]
type = "chatgptexport"
src_dir = "~/Downloads/chatgpt"
dest_dir = "./output/chatgpt"
```
