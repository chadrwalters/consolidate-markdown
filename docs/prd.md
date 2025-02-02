# Product Requirements Document

## 1. Product Overview

Consolidate Markdown is a unified command-line tool that processes Markdown files from multiple sources—currently Bear.app exports and X Bookmarks—and consolidates those files, along with their attachments, into a single Markdown output per note/bookmark. The tool also supports AI-powered image analysis (via GPT-4o) to generate text-based descriptions of visual content, enhancing long-term archival, searchability, and portability.

For detailed format specifications, see:
- [Bear Export Schema](schemas/bear_export.md)
- [ChatGPT Export Schema](schemas/chatgpt_export.md)
- [Claude Export Schema](schemas/claude_export.md)
- [XBookmarks Export Schema](schemas/xbookmarks_export.md)

### Key Goals
1. **Central Repository**
   - Provide a single command-line process that gathers content from various sources into a consistent Markdown format.
2. **AI-Enhanced Attachments**
   - For image attachments, generate textual descriptions or placeholders so that visual content is more searchable and accessible.
3. **Versatile Processing**
   - Accommodate future expansions of input source types by configuring them in a single tool.
4. **Easy Maintenance & Organization**
   - Minimize manual copying or complex setups: run one command to transform all relevant files into well-structured, consolidated Markdown.
5. **Ephemeral Environment Execution**
   - All Python commands (installation, running, testing) must be executed through uv (or an equivalent ephemeral environment manager) to ensure consistency and isolation.

## 2. Problem Statement & Rationale

### Current Challenges
1. **Fragmented Content**
   - Users store notes in Bear.app and collect bookmarks (X Bookmarks) separately, leading to fragmented text, images, and documents scattered across folder structures.
2. **Inefficient Workflows**
   - Without a single aggregator, manual merges or ad hoc scripts are necessary. This is error-prone and time-consuming.
3. **Attachment Blind Spots**
   - Rich attachments (images, .docx, .pdf, etc.) often remain outside a cohesive text-based system. They may require separate conversions or be overlooked entirely.

### Why We Need This
1. **Unified Knowledge Base**
   - Converting and merging everything into Markdown (with integrated attachment data) provides consistency and clarity.
2. **Improved Access & Searchability**
   - GPT-4o image analysis creates textual descriptors, making even visual content searchable and accessible over the long term.
3. **Time & Cost Efficiency**
   - A single tool to read, convert, and output all content saves substantial effort compared to manually unifying or reprocessing files.

## 3. Product Scope & Features

### 3.1 Multi-Source Support
- **Bear Notes**: Finds .md files along with matching attachment folders.
- **X Bookmarks**: Identifies subdirectories that contain an index.md, then processes them similarly.

### 3.2 Attachment Conversion
- **MarkItDown**: A universal library/tool for converting .docx, .pdf, .csv, .xlsx, etc. into Markdown text for inlining.
- **GPT-4o Image Analysis**: For image attachments, generate text describing the visuals. If no_image=true, skip GPT calls and insert a placeholder instead.

### 3.3 Single CLI with Config-Driven Approach
- Users specify sources and their properties in a TOML config file (e.g., consolidate_config.toml).
- One command reads this config, processes all sources, and outputs consolidated Markdown files.

### 3.4 Summary & Logging
- Display end-of-run summaries to show processed, skipped, and error items per source.
- Write detailed logs to a .cm/logs directory for troubleshooting.

### 3.5 No Redundant Data
- Temporary conversions and partial artifacts live in .cm.
- Only final .md files appear in the user's destination directory (destDir).

### 3.6 Force / Clean Flags
- `--force`: Reconvert everything regardless of timestamps or existing processed files.
- `--delete`: Remove old outputs (in each destDir) and the entire .cm directory before processing.

## 4. Technical Requirements

### 4.1 Execution Through UV
All Python commands must be performed via uv:

```bash
# Install dependencies
uv pip install -r requirements.txt

# Run the tool
uv run python -m consolidate_markdown --config ./consolidate_config.toml --delete
```

### 4.2 Handling Paths with Spaces
- Must gracefully handle source and destination paths with spaces or special characters.
- Example path: "/Users/chadwalters/Library/Mobile Documents/com~apple~CloudDocs/My Notes/"
- Internally use Python's pathlib.Path.

### 4.3 Directories & File Outputs
1. **Temporary Directory**
   - .cm is the default location for all intermediate/working files
   - Can be overridden in the [global] section of the config as cm_dir
2. **Delete Option**
   - `--delete` removes all existing destination directories and .cm directory
3. **Final Markdown**
   - Each discovered note/bookmark becomes exactly one .md file in destDir
   - No subfolders or partial files in destDir

### 4.4 Config-Driven Sources
Example consolidate_config.toml:

```toml
[global]
cm_dir = ".cm"
log_level = "INFO"
force_generation = false
no_image = false
openai_key = "<YOUR_OPENAI_KEY_HERE>"

[[sources]]
type = "bear"
srcDir = "/Users/chadwalters/Library/Mobile Documents/com~apple~CloudDocs/_BearNotes"
destDir = "/Users/chadwalters/Library/Mobile Documents/com~apple~CloudDocs/BearOutput"

[[sources]]
type = "xbookmarks"
srcDir = "/Users/chadwalters/Library/Mobile Documents/com~apple~CloudDocs/_XBookmarks"
destDir = "/Users/chadwalters/Library/Mobile Documents/com~apple~CloudDocs/XOutput"
index_filename = "index.md"
```

## 5. Processing Logic

### 5.1 Bear Source Processing
1. Discover all *.md files in srcDir
2. For each file (e.g., Foo.md), look for matching attachment folder (Foo/)
3. Replace references in Foo.md:
   - Non-image attachments: Use MarkItDown to convert to Markdown text
   - Image attachments: Pass to GPT-4o for textual analysis unless no_image=true
   - Format conversions (e.g., .heic → .jpg) occur inside .cm
4. Merge into one final .md in destDir

### 5.2 X Bookmarks Processing
1. For each subdirectory in srcDir:
   - Check for index.md (or configured index_filename)
   - Process if found
2. Handle attachments:
   - Non-image: Use MarkItDown for .docx, .pdf, etc.
   - Images: GPT-4o for text descriptions (if no_image=false)
3. Output single .md in destDir matching subdirectory name

## 6. User Experience

### 6.1 Typical Usage
1. Edit consolidate_config.toml
2. Run command:
```bash
uv run python -m consolidate_markdown --config ./consolidate_config.toml --delete
```
3. Review output files in destDir

### 6.2 Output Examples

#### Bear Note Example
```markdown
# 20241218 - Format Test

Some text from the original note.

<!-- EMBEDDED DOCUMENT: Some.xlsx -->
<details>
<summary>📄 Some.xlsx</summary>

Converted markdown table/content via MarkItDown...

</details>

<!-- EMBEDDED IMAGE: sample.png -->
<details>
<summary>🖼️ sample.png (1200x800, 350KB)</summary>

GPT-4o textual description about the image...

</details>
```

#### X Bookmark Example
```markdown
**[UserName](https://x.com/username)**

[Timestamp or other metadata from index.md]

Some text describing the bookmark.

<!-- EMBEDDED IMAGE: photo.jpg -->
<details>
<summary>🖼️ photo.jpg (1024x768, 300KB)</summary>

GPT-4o analysis text here...

</details>
```

## 7. Assumptions & Constraints

### 7.1 OS Compatibility
- Primarily tested on macOS. Conversions for certain formats (e.g., .heic) rely on OS-specific tools.
- Other OSes should work with fallback logic but may have limited support.

### 7.2 Image Analysis API Support
- Support for multiple API providers:
  1. OpenAI GPT-4 Vision (default)
     - Requires valid OpenAI API key
     - Uses GPT-4 Vision model
     - Configurable base URL
  2. OpenRouter
     - Alternative provider support
     - Requires valid OpenRouter API key
     - Configurable base URL
- Provider selection through configuration
- Environment variable support for all API settings
- Graceful fallback for missing API keys
- Skip image analysis with no_image=true

### 7.3 API Configuration
Example configuration with OpenAI:
```toml
[global]
api_provider = "openai"
openai_key = "${OPENAI_API_KEY}"
openai_base_url = "https://api.openai.com/v1"
```

Example configuration with OpenRouter:
```toml
[global]
api_provider = "openrouter"
openrouter_key = "${OPENROUTER_API_KEY}"
openrouter_base_url = "https://openrouter.ai/api/v1"
```

### 7.4 No GPT Caching in v1
- GPT is called every time a new image is processed, or when --force is used.
- Timestamp-based skipping may apply to final .md checks, but no separate GPT result cache is stored.

### 7.5 Spaces & Special Characters
- All directory handling must accommodate spaces or special characters through robust path handling.

## 8. End-of-Run Summary

At the end of the process, the CLI prints a consolidated summary. For example:

```
───────────────────────────────────────────────
Summary for Bear Source (./_BearNotes):
  - 5 notes discovered
  - 5 processed
  - 0 skipped
  - 0 errors

Summary for X Bookmarks Source (./_XBookmarks):
  - 3 subdirectories with index.md
  - 3 processed
  - 0 skipped
  - 1 error:
    -> 2025_01_21_1881890021667725515 (GPT analysis error)

───────────────────────────────────────────────
Overall: 8 processed, 0 skipped, 1 error
───────────────────────────────────────────────
```

## 9. Future Enhancements

### 9.1 v1 Scope
- Bear & X Bookmarks source support
- MarkItDown usage for non-image attachments
- GPT-4o for image-to-text conversion (optional)
- Summaries, logs, skip/reprocess logic

### 9.2 Future Features
- Caching of GPT results to avoid re-analysis
- Additional Source Types (e.g., Evernote exports, Obsidian vaults)
- Richer Error Handling for partial merges
- GUI or Web-Based Interface for non-technical users
```
