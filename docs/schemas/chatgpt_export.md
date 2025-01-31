# ChatGPT Export Schema

This document describes the schema for conversations exported from OpenAI's ChatGPT assistant. The conversations are stored in JSON format and represent interactions through the ChatGPT interface.

## Overview
Each conversation represents an interaction session between a user and ChatGPT through the ChatGPT interface. The conversation includes:
- Basic metadata (id, timestamps, etc.)
- Title and model information
- Messages in a tree structure
- Plugin and tool configurations
- Moderation results and status information

## Top Level Structure
Each conversation in the array has the following fields:

- `id`: Unique identifier for the conversation
- `title`: Title/name of the conversation
- `create_time`: Timestamp when conversation was created
- `update_time`: Timestamp when conversation was last updated
- `mapping`: Object containing message tree structure
- `current_node`: ID of the current/latest message node
- `conversation_id`: Another identifier for the conversation
- `conversation_origin`: Origin information
- `conversation_template_id`: Template identifier if used
- `default_model_slug`: Default model used (e.g., "gpt-4")
- `gizmo_id`: Identifier for custom GPT if used
- `gizmo_type`: Type of custom GPT if used
- `is_archived`: Whether conversation is archived
- `is_starred`: Whether conversation is starred
- `plugin_ids`: Array of enabled plugin IDs
- `disabled_tool_ids`: Array of disabled tool IDs
- `safe_urls`: Array of safe URLs
- `moderation_results`: Moderation check results
- `async_status`: Status of async operations
- `voice`: Voice settings

## Message Structure
Messages are stored in a tree structure within the `mapping` object. Each node has:

- `id`: Unique identifier for the node
- `message`: The message content object (if not a root node)
  - `id`: Same as node ID
  - `author`: Object containing role information
    - `role`: Role of the sender (e.g., "user", "assistant", "system")
    - `name`: Optional name
    - `metadata`: Additional metadata
  - `create_time`: When message was created
  - `update_time`: When message was last updated
  - `content`: Content object
    - `content_type`: Type of content (e.g., "text")
    - `parts`: Array of content parts
  - `status`: Message status (e.g., "finished_successfully")
  - `end_turn`: Whether this message ends the turn
  - `weight`: Message weight value
  - `metadata`: Additional message metadata
    - `is_visually_hidden_from_conversation`: Whether message is hidden
  - `recipient`: Message recipient (e.g., "all")
  - `channel`: Optional channel information
- `parent`: ID of parent node (null for root)
- `children`: Array of child node IDs

### Content Types
Message content can be in several formats:

1. Text Content
   ```json
   {
     "content_type": "text",
     "parts": [
       "Text content here"
     ]
   }
   ```

2. Code Content
   ```json
   {
     "content_type": "code",
     "parts": [
       "code content here"
     ],
     "language": "python"  // Optional language identifier
   }
   ```

3. Multi-modal Content
   ```json
   {
     "content_type": "multimodal",
     "parts": [
       {
         "type": "text",
         "text": "Text description"
       },
       {
         "type": "image_url",
         "image_url": {
           "url": "path/to/image"
         }
       }
     ]
   }
   ```

4. User Context Content
   ```json
   {
     "content_type": "user_editable_context",
     "user_profile": string,    // User-provided profile information
     "user_instructions": string // User-provided response preferences
   }
   ```

5. Document Content
   ```json
   {
     "content_type": "text",
     "parts": [
       "{\"name\": string, \"type\": \"document\", \"content\": string}"
     ]
   }
   ```

### File Handling

1. Images
   - Can be embedded as base64 data URLs
   - Format: `data:image/{format};base64,{data}`
   - Supported formats: determined by image header

2. File Attachments
   - Referenced by URL
   - Stored separately from conversation JSON
   - Processed into attachments directory

### Output Format
Conversations are converted to Markdown with the following structure:

```markdown
# {title}

Created: {formatted_create_time}
Updated: {formatted_update_time}
Model: {default_model_slug}

## {role.title()}

{content}
```

Where:
- Timestamps are formatted as "YYYY-MM-DD HH:MM:SS TZ"
- Content includes processed text, images, and file attachments
- Images are wrapped in details tags with size and dimension info
- File attachments are wrapped in details tags with size info
