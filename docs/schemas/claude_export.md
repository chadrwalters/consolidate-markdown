# Claude Export Schema

This document describes the schema for conversations exported from Anthropic's Claude AI assistant. The conversations are stored in JSON format and represent interactions through the Claude interface.

## Overview
Each conversation represents an interaction session between a user and Claude through the Claude interface. The conversation includes:
- Basic metadata (uuid, timestamps, etc.)
- Messages exchanged between user and assistant
- Tools used by Claude during the conversation
- Files and artifacts referenced or generated
- Special content like embedded images or code artifacts

## Top Level Structure
Each conversation in the array has the following fields:

- `uuid`: Unique identifier for the conversation
- `name`: Title/name of the conversation
- `created_at`: Timestamp when conversation was created
- `updated_at`: Timestamp when conversation was last updated
- `account`: Account information
  - `uuid`: Unique identifier for the account
- `chat_messages`: Array of messages in the conversation

## Chat Messages Structure

Each message in the `chat_messages` array has the following fields:

- `uuid`: Unique identifier for the message
- `sender`: Who sent the message (e.g., "assistant" or "user")
- `text`: The raw text content of the message
- `content`: Array of content blocks
- `attachments`: Array of attachments (appears to be unused/empty)
- `files`: Array of files
- `created_at`: Timestamp when message was created
- `updated_at`: Timestamp when message was last updated

### Content Structure
Each content block in the `content` array has base fields:

- `type`: Type of content (one of: "text", "tool_use", "tool_result")
- `start_timestamp`: When this content block started
- `stop_timestamp`: When this content block ended

#### Content Types

1. Text Content (`type: "text"`)
   - Adds `text`: The actual content text

2. Tool Use (`type: "tool_use"`)
   - Adds `name`: Name of the tool being used (see Tools section)
   - Adds `input`: Arguments/input for the tool (structure varies by tool)

3. Tool Result (`type: "tool_result"`)
   - Adds `name`: Name of the tool that was used
   - Adds `content`: The result content from the tool
   - Adds `is_error`: Boolean indicating if the tool execution failed

### Tools Available
The following tools appear in the conversations:

1. `search`: Tool for searching
   - Input structure:
     ```json
     {
       "limit": number,    // Maximum number of results
       "query": string     // Search query text
     }
     ```
   - Result structure:
     ```json
     {
       "results": [
         {
           "rank": number,          // Result ranking
           "score": number,         // Relevance score
           "heading": string,       // Section heading (if any)
           "tags": string,          // JSON array of tags as string
           "content": string,       // Matched content snippet
           "attachments": string,   // JSON array of attachments as string
           "heading_level": number, // Heading level (0 if none)
           "heading_text": string,  // Heading text (if any)
           "source": string        // Source file path
         }
       ],
       "count": number,            // Number of results
       "query": string,            // Original search query
       "query_time": number        // Time taken to execute query
     }
     ```

2. `artifacts`: Tool for managing artifacts
   - Input structure:
     ```json
     {
       "id": string,           // Unique identifier for the artifact
       "type": string,         // MIME type of the content
       "title": string,        // Human readable title
       "command": string,      // Action to perform (e.g., "create")
       "content": string,      // The actual artifact content
       "version_uuid": string  // Version identifier
     }
     ```

3. `echo`: Tool for echoing input
   - Input structure:
     ```json
     {
       "message": string    // Message to echo back
     }
     ```

4. `monitor`: Tool for monitoring something
   - Input structure:
     ```json
     {
       "command": string   // Command to execute (e.g., "health", "stats")
     }
     ```

5. `process_notes`: Tool for processing notes
   - Input structure:
     ```json
     {}    // Takes no parameters
     ```

6. `repl`: Tool for REPL interactions
   - Input structure:
     ```json
     {
       "code": string    // JavaScript code to execute
     }
     ```

## Tool Result Structures

Each tool returns results in a specific format:

1. `search`: Returns search results with ranking, relevance scores, and content snippets (see above)
2. `artifacts`: Returns a simple confirmation
   ```json
   {
     "type": "text",
     "text": "OK"    // Confirmation of successful execution
   }
   ```
3. `echo`: Returns the input message with a prefix
   ```json
   {
     "type": "text",
     "text": {
       "message": string    // Format: "Echo: {original_message}"
     }
   }
   ```
4. `monitor`: Returns health status or error information
   ```json
   {
     "type": "text",
     "text": {
       // Success case
       "status": "healthy",
       "vector_store": {
         "path": string,
         "exists": boolean,
         "is_dir": boolean,
         "permissions": string
       }
       // Error case
       "status": "error",
       "error": string     // Error message
     }
   }
   ```
5. `process_notes`: Returns processing status and counts
   ```json
   {
     "type": "text",
     "text": {
       "status": string,      // e.g., "success"
       "processed": number,   // Number of notes processed
       "errors": number,      // Number of errors encountered
       "input_path": string   // Path to input directory
     }
   }
   ```
6. `repl`: Returns execution results
   ```json
   {
     "type": "text",
     "text": {
       "status": string,    // e.g., "success"
       "logs": string[]     // Array of output lines from code execution
     }
   }
   ```

### Files Structure
Each file in the `files` array has:
- `file_name`: Name of the file (this is the only field)

Supported file types include:
- Documents: .txt, .md, .doc, .docx, .pdf
- Images: .png, .jpeg
- Code: .py, .js, .ts, .tsx
- Data: .json, .yaml, .csv
- Shell: .zsh, .zshrc, .zshenv
- Other: .diff, .prompt

File contents appear to be stored separately from the conversation JSON and are referenced by filename.

## Special Content

1. XML Tags
   The following XML tags appear in message text:
   - `<antThinking>`: Contains assistant's thought process about code artifacts
   - `<antArtifact>`: Defines a code artifact with attributes:
     - `identifier`: Unique ID for the artifact
     - `type`: Content type (e.g., "application/vnd.ant.code")
     - `language`: Programming language
     - `title`: Human readable title

2. Base64 Images
   Images can be embedded in text content using data URLs:
   ```
   data:image/svg+xml;base64,...
   ```
   or as SVG directly:
   ```
   data:image/svg+xml;utf8,...
   ```

3. Tool Usage/Results
   Tool usage and results are stored in the content array as separate blocks with their own types and structures (see Content Types and Tool Result Structures sections above).

## Additional Investigation Needed

1. Content Type Details
   - [x] What are all possible values for content.type?
   - [x] What is the specific structure for tool_use content?
   - [x] What is the specific structure for tool_result content?
   - [x] What tools are available (unique tool names)?
   - [x] What is the structure of tool inputs for each tool?
   - [x] What is the structure of tool result content for each tool?

2. File Details
   - [x] Are there additional file fields beyond file_name?
   - [x] How are file contents stored/referenced?
   - [x] What file types are supported?

3. Account Structure
   - [x] What fields are in the account object?

4. Special Content
   - [x] How are XML tags like antThinking and antArtifact stored?
   - [x] How are base64 encoded images handled?
   - [x] How are tool usage/results formatted?

Let's examine the input structure for the process_notes tool next:

## Investigation Status
All schema investigation items have been completed:

1. Content Type Details ✓
   - Identified all content types
   - Documented tool_use and tool_result structures
   - Mapped available tools and their I/O formats

2. File Details ✓
   - Confirmed file_name is only field
   - Documented file storage approach
   - Listed supported file types

3. Account Structure ✓
   - Documented uuid field

4. Special Content ✓
   - Documented XML tags
   - Documented base64 image handling
   - Documented tool usage formatting
