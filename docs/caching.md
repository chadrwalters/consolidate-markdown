# Caching System

The consolidate-markdown tool uses a simple but effective caching system to avoid unnecessary reprocessing of files and expensive GPT API calls.

## Cache Structure

All cache data is stored in the `.cm/cache/` directory:
```
.cm/
  └── cache/
      ├── notes.json      # Note/bookmark content hashes and timestamps
      └── gpt.json        # Image analysis cache
```

## How Caching Works

### Note/Bookmark Caching
- Each source file (Bear note or X bookmark) is cached with:
  - Content hash (MD5)
  - Last modified timestamp
- A file is regenerated if:
  - Content hash doesn't match cached version
  - Any attachments are newer than cached timestamp
  - `--force` flag is used

### GPT Image Analysis Caching
- Each image analysis is cached using:
  - Image content hash (MD5) as key
  - Analysis text as value
- GPT analysis is regenerated if:
  - Image hash isn't in cache
  - `--force` flag is used
- When `--no-image` is set:
  - Uses cached analysis if available
  - Uses placeholder if no cache exists
  - Never generates new analyses

## Cache Control

### Force Flag
The `--force` flag clears all caches and forces complete regeneration:
```bash
consolidate_markdown --config config.toml --force
```

### Cache Files
Cache files are simple JSON for easy inspection:

```json
// notes.json example
{
  "/path/to/note.md": {
    "hash": "abc123...",
    "timestamp": 1234567890.0
  }
}

// gpt.json example
{
  "def456...": "A detailed description of the image showing..."
}
```

## Statistics
The tool tracks and reports cache performance:
```
Summary for Bear Source:
  - 5 notes processed [3 from cache, 2 regenerated]
  - 10 images [7 from cache, 3 new analyses]
  - 2 skipped
  - 3 documents processed

Summary for X Bookmarks Source:
  - 3 bookmarks processed [2 from cache, 1 regenerated]
  - 5 images [4 from cache, 1 new analysis]
  - 1 skipped
  - 2 documents processed
```

## Implementation Details

### Content Hashing
- Uses fast MD5 hashing for quick cache lookups
- Hashes full content for notes/bookmarks
- Hashes binary data for images

### Timestamp Checking
- Notes/bookmarks check:
  - Source file timestamp
  - All attachment timestamps
- Only regenerates if any dependency is newer than cache

### Error Handling
- Cache read/write errors fail gracefully
- Missing cache files are automatically created
