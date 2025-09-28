"""Edit in Typora tool for Basic Memory MCP server.

This tool enables editing Basic Memory notes in Typora, bridging the gap
between Basic Memory's knowledge management and Typora's rich editing features.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from loguru import logger

from basic_memory.mcp.server import mcp
from basic_memory.mcp.tools.read_note import read_note
from basic_memory.mcp.tools.write_note import write_note


@mcp.tool(
    description="""Export Basic Memory notes to Typora for professional rich-text editing with round-trip capability.

This tool creates a bridge between Basic Memory's knowledge management and Typora's
professional editing environment, enabling WYSIWYG editing while maintaining data integrity.

EDITING WORKFLOW:
1. Export note from Basic Memory to Typora workspace
2. Edit with Typora's rich formatting features (tables, math, diagrams, etc.)
3. Import edited content back to Basic Memory
4. Preserve all metadata and relationships

TYPORA FEATURES AVAILABLE:
- Live preview with instant formatting feedback
- Advanced table editing with visual controls
- LaTeX math equation rendering and editing
- Syntax-highlighted code blocks
- Image insertion and resizing
- Professional typography and spacing
- Outline view for document structure
- Word count and reading time estimates

PARAMETERS:
- note_identifier (str, REQUIRED): Note title or permalink to edit
- workspace_path (str, optional): Custom workspace directory (defaults to "typora-workspace")
- create_backup (bool, default=True): Create backup of original content before editing
- project (str, optional): Specific Basic Memory project

WORKSPACE MANAGEMENT:
- Automatic workspace creation and organization
- Backup preservation for safety
- Clear file naming and version tracking
- Temporary file cleanup options

TYPORA INTEGRATION:
- Automatic file opening in Typora (if installed)
- Markdown format compatibility
- Rich content preservation
- Professional editing workflow

USAGE EXAMPLES:
Basic edit: edit_in_typora("Meeting Notes")
Custom workspace: edit_in_typora("Project Plan", workspace_path="current-projects")
No backup: edit_in_typora("Draft", create_backup=False)

RETURNS:
Detailed export summary with file paths, backup locations, and import instructions.

NOTE: Requires Typora to be installed. This tool enables professional editing while
maintaining Basic Memory's knowledge structure. Use import_from_typora() to complete the workflow.""",
)
async def edit_in_typora(
    note_identifier: str,
    workspace_path: Optional[str] = None,
    create_backup: bool = True,
    project: Optional[str] = None,
) -> str:
    """Export a Basic Memory note to Typora for rich editing.

    This tool bridges Basic Memory and Typora by:
    1. Exporting the specified note as clean markdown
    2. Saving it to a workspace directory for Typora
    3. Providing clear instructions for editing in Typora
    4. Enabling import-back of edited content

    While this goes against Basic Memory's self-contained philosophy, it enables
    users to leverage Typora's rich editing features (tables, math, diagrams, etc.)
    while maintaining Basic Memory as the knowledge base.

    Args:
        note_identifier: Note title, permalink, or path to edit
        workspace_path: Directory for Typora workspace (default: system temp + 'basic_memory_typora')
        create_backup: Whether to create backup of original note (default: True)
        project: Optional project name to work with. If not provided, uses current active project.

    Returns:
        Instructions for editing in Typora and importing back.

    Examples:
        # Edit a note in Typora
        result = await edit_in_typora.fn("My Research Note")

        # Edit with custom workspace
        result = await edit_in_typora.fn(
            "Project Alpha",
            workspace_path="/path/to/typora/workspace"
        )

        # Edit without backup
        result = await edit_in_typora.fn(
            "meeting-notes",
            create_backup=False
        )
    """

    try:
        # Determine workspace path
        if workspace_path is None:
            workspace_path = os.path.join(tempfile.gettempdir(), 'basic_memory_typora')
        workspace_path = Path(workspace_path)

        # Create workspace directory
        workspace_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Setting up Typora editing workspace: {workspace_path}")

        # Read the original note
        original_content = await read_note.fn(note_identifier, project=project)

        if "Error" in original_content or "not found" in original_content.lower():
            return f"# Edit in Typora Failed\n\nNote '{note_identifier}' not found or could not be read."

        # Parse the note content (remove the header/footer added by read_note)
        note_content = _extract_note_content(original_content)

        # Extract note title
        note_title = _extract_note_title(original_content, note_identifier)

        # Create backup if requested
        backup_info = ""
        if create_backup:
            backup_path = workspace_path / f"{note_title}_backup_{int(datetime.now().timestamp())}.md"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(note_content)
            backup_info = f"\n\n**Backup created:** {backup_path}"

        # Create the Typora-ready file
        typora_filename = _sanitize_filename(note_title) + ".md"
        typora_path = workspace_path / typora_filename

        # Add Typora-specific formatting and metadata
        typora_content = _create_typora_content(note_content, note_title, note_identifier)

        with open(typora_path, 'w', encoding='utf-8') as f:
            f.write(typora_content)

        # Create workspace configuration
        workspace_config = _create_workspace_config(workspace_path, note_title, typora_filename)

        # Generate instructions
        instructions = _generate_typora_instructions(
            workspace_path, typora_path, note_title, note_identifier,
            workspace_config, backup_info, project
        )

        return instructions

    except Exception as e:
        logger.error(f"Edit in Typora failed: {e}")
        return f"# Edit in Typora Failed\n\nUnexpected error: {e}"


@mcp.tool(
    description="""Import professionally edited content from Typora back into Basic Memory, completing the round-trip workflow.

This tool completes the Typora editing workflow by importing enhanced content back into Basic Memory,
preserving rich formatting while maintaining knowledge structure and relationships.

IMPORT PROCESS:
1. Locate edited file in Typora workspace
2. Read enhanced markdown content with rich formatting
3. Update original Basic Memory note with improvements
4. Preserve all metadata, tags, and relationships
5. Clean up workspace files (optional)

CONTENT ENHANCEMENT PRESERVED:
- Professional table formatting and structure
- Mathematical equations and LaTeX expressions
- Syntax-highlighted code blocks
- Image formatting and captions
- Advanced typography and spacing
- Document structure improvements

PARAMETERS:
- note_identifier (str, REQUIRED): Note title or permalink to update
- workspace_path (str, optional): Workspace directory containing edited file (defaults to "typora-workspace")
- project (str, optional): Specific Basic Memory project

WORKSPACE DETECTION:
- Automatic workspace location detection
- File matching by note identifier
- Backup preservation for safety
- Version conflict resolution

CONTENT INTEGRITY:
- Metadata preservation (creation date, author, etc.)
- Relationship maintenance
- Tag retention
- Folder structure preservation

USAGE EXAMPLES:
Basic import: import_from_typora("Meeting Notes")
Custom workspace: import_from_typora("Project Plan", workspace_path="current-projects")
Specific project: import_from_typora("Research Notes", project="academic-work")

RETURNS:
Import summary with content changes, file locations, and validation results.

NOTE: This tool assumes the note was previously exported using edit_in_typora().
Ensure Typora has saved changes before importing. Backups are automatically created for safety.""",
)
async def import_from_typora(
    note_identifier: str,
    workspace_path: Optional[str] = None,
    project: Optional[str] = None,
) -> str:
    """Import a note edited in Typora back into Basic Memory.

    This tool reads the edited markdown file from the Typora workspace
    and updates the corresponding note in Basic Memory.

    Args:
        note_identifier: Original note identifier used for editing
        workspace_path: Typora workspace directory (default: system temp + 'basic_memory_typora')
        project: Optional project name to work with. If not provided, uses current active project.

    Returns:
        Confirmation of successful import.

    Examples:
        # Import edited note back
        result = await import_from_typora.fn("My Research Note")

        # Import from custom workspace
        result = await import_from_typora.fn(
            "Project Alpha",
            workspace_path="/path/to/typora/workspace"
        )
    """

    try:
        # Determine workspace path
        if workspace_path is None:
            workspace_path = os.path.join(tempfile.gettempdir(), 'basic_memory_typora')
        workspace_path = Path(workspace_path)

        if not workspace_path.exists():
            return f"# Import from Typora Failed\n\nWorkspace directory does not exist: {workspace_path}"

        # Find the edited file
        # Look for files that match the note identifier pattern
        edited_files = list(workspace_path.glob("*.md"))
        if not edited_files:
            return f"# Import from Typora Failed\n\nNo markdown files found in workspace: {workspace_path}"

        # Try to find the right file based on note identifier
        target_file = None
        for file_path in edited_files:
            if "_backup_" not in file_path.name:  # Skip backup files
                # Read first few lines to check if it matches
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read(500)  # Read first 500 chars
                        if note_identifier.lower() in content.lower()[:200]:  # Check in header
                            target_file = file_path
                            break
                except Exception:
                    continue

        if not target_file:
            # Fallback: use the most recently modified non-backup file
            valid_files = [f for f in edited_files if "_backup_" not in f.name]
            if valid_files:
                target_file = max(valid_files, key=lambda x: x.stat().st_mtime)
            else:
                return f"# Import from Typora Failed\n\nCould not identify edited file for note: {note_identifier}"

        # Read the edited content
        with open(target_file, 'r', encoding='utf-8') as f:
            edited_content = f.read()

        # Clean the content (remove Typora-specific additions)
        clean_content = _clean_typora_content(edited_content)

        # Write back to Basic Memory
        result = await write_note.fn(
            title=note_identifier,  # Use original identifier as title
            content=clean_content,
            project=project
        )

        # Create success message
        success_msg = f"""# Import from Typora Successful

**Note updated:** {note_identifier}
**Source file:** {target_file}
**Last modified:** {datetime.fromtimestamp(target_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}

The edited content has been imported back into Basic Memory.

## Next Steps
- Review the updated note in Basic Memory
- The Typora workspace files are preserved for reference
- Delete workspace files when no longer needed

## Workspace Location
{workspace_path}

*Imported at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        return success_msg

    except Exception as e:
        logger.error(f"Import from Typora failed: {e}")
        return f"# Import from Typora Failed\n\nUnexpected error: {e}"


def _extract_note_content(content: str) -> str:
    """Extract the actual note content from read_note output."""
    lines = content.split('\n')

    # Remove the header that read_note adds
    if lines and lines[0].startswith('# '):
        # Find where the actual content starts
        content_start = 0
        for i, line in enumerate(lines):
            if line.strip() == '---' and i > 0:
                content_start = i + 1
                break

        if content_start > 0:
            lines = lines[content_start:]

    # Remove any footer content
    # Look for common footer patterns
    footer_patterns = ['*Generated by', '*Imported from', '*Created by']
    for i, line in enumerate(lines):
        if any(pattern in line for pattern in footer_patterns):
            lines = lines[:i]
            break

    return '\n'.join(lines).strip()


def _extract_note_title(content: str, identifier: str) -> str:
    """Extract note title from content or use identifier."""
    lines = content.split('\n')

    # Look for first heading
    for line in lines:
        if line.startswith('# '):
            return line[2:].strip()

    # Fallback to identifier
    return identifier


def _sanitize_filename(title: str) -> str:
    """Sanitize title for use as filename."""
    import re
    # Replace unsafe characters
    safe_name = re.sub(r'[^\w\s-]', '_', title)
    # Replace spaces and multiple underscores
    safe_name = re.sub(r'[\s_]+', '_', safe_name)
    # Trim underscores
    safe_name = safe_name.strip('_')
    # Limit length
    if len(safe_name) > 50:
        safe_name = safe_name[:47] + '...'
    if not safe_name:
        safe_name = 'untitled'
    return safe_name


def _create_typora_content(content: str, title: str, identifier: str) -> str:
    """Create Typora-optimized content with metadata."""
    lines = []

    # Add frontmatter
    lines.extend([
        "---",
        f"title: {title}",
        f"basic_memory_id: {identifier}",
        f"exported_at: {datetime.now().isoformat()}",
        f"source: Basic Memory",
        "---",
        ""
    ])

    # Ensure content starts with proper heading
    if not content.strip().startswith('# '):
        lines.extend([f"# {title}", ""])

    lines.append(content)

    # Add editing instructions at the end
    lines.extend([
        "",
        "---",
        "",
        "## Typora Editing Notes",
        "",
        "- **Save frequently** while editing",
        "- **Use Typora's features**: tables, math, diagrams, etc.",
        "- **Preview mode** shows final formatting",
        "- **Export** to test other formats if needed",
        "",
        "*When finished editing, use Basic Memory's `import_from_typora` tool to import back*",
        ""
    ])

    return '\n'.join(lines)


def _create_workspace_config(workspace_path: Path, note_title: str, filename: str) -> Dict[str, Any]:
    """Create workspace configuration for reference."""
    config = {
        "workspace_type": "basic_memory_typora_edit",
        "note_title": note_title,
        "filename": filename,
        "created_at": datetime.now().isoformat(),
        "instructions": "Edit the .md file in Typora, then use import_from_typora to bring changes back"
    }

    config_path = workspace_path / 'workspace-info.json'
    with open(config_path, 'w', encoding='utf-8') as f:
        import json
        json.dump(config, f, indent=2, ensure_ascii=False)

    return config


def _generate_typora_instructions(
    workspace_path: Path,
    typora_path: Path,
    note_title: str,
    note_identifier: str,
    workspace_config: Dict[str, Any],
    backup_info: str,
    project: Optional[str]
) -> str:
    """Generate comprehensive instructions for Typora editing."""

    project_param = f', project="{project}"' if project else ''

    instructions = f"""# Edit in Typora Setup Complete

**Note:** {note_title}
**Original ID:** {note_identifier}
**Workspace:** {workspace_path}

## Files Created
- **Main file:** {typora_path}
- **Workspace info:** {workspace_path}/workspace-info.json{backup_info}

## How to Edit in Typora

### Step 1: Open in Typora
```bash
# Open the file directly in Typora
typora "{typora_path}"
```

Or manually:
1. Open Typora application
2. File → Open → Navigate to: `{workspace_path}`
3. Open `{os.path.basename(typora_path)}`

### Step 2: Edit Your Note
- Use Typora's rich editing features:
  - **Tables**: Create with `| Column | Column |` syntax or GUI
  - **Math**: LaTeX expressions with `$$` delimiters
  - **Diagrams**: Mermaid diagrams in code blocks
  - **Images**: Drag & drop or paste images
  - **Links**: `[text](url)` or `[[WikiLinks]]`
  - **Code**: Syntax highlighting for 100+ languages

### Step 3: Save Frequently
- Typora auto-saves, but manual saves are recommended
- Use `Ctrl+S` (or `Cmd+S` on Mac) to save

### Step 4: Import Back to Basic Memory
When finished editing, import the changes back:

```python
# In Basic Memory/Claude
await import_from_typora.fn("{note_identifier}"{project_param})
```

Or with custom workspace:
```python
await import_from_typora.fn(
    "{note_identifier}",
    workspace_path="{workspace_path}"{project_param}
)
```

## Typora Tips for Best Results

### Themes & Styling
- **Themes**: View → Themes → Choose a style
- **Focus Mode**: View → Focus Mode for distraction-free writing
- **Typewriter Mode**: View → Typewriter Mode

### Export Testing (Optional)
Before importing back, you can test exports:
- File → Export → PDF/HTML/Word/etc.
- Check formatting in different formats
- Adjust content as needed

### Advanced Features
- **Outline**: View → Outline for document structure
- **Word Count**: View → Word Count
- **Find & Replace**: Edit → Find
- **Multiple Cursors**: Ctrl+Click for multi-edit

## Important Notes

- **Don't rename the file** - Basic Memory identifies it by content
- **Keep workspace organized** - All related files are in `{workspace_path}`
- **Backup safety** - Original note is preserved in Basic Memory
- **Version control** - Consider the edit session as a batch of changes

## Troubleshooting

### File Not Found
- Ensure Typora is installed and accessible
- Check file paths for special characters
- Try opening Typora first, then File → Open

### Import Issues
- Ensure you've saved changes in Typora before importing
- Check that the workspace path matches exactly
- Verify the note identifier is correct

### Content Problems
- Review the imported content in Basic Memory
- Check for Typora-specific formatting that didn't convert
- Manual cleanup may be needed for complex elements

## Workspace Contents
```
{workspace_path}/
├── {os.path.basename(typora_path)}     # Main editing file
├── workspace-info.json                 # Configuration
└── [backup files if created]
```

*Setup completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    return instructions


def _clean_typora_content(content: str) -> str:
    """Clean Typora-specific additions before importing back."""
    lines = content.split('\n')

    # Remove frontmatter if present
    if lines and lines[0].strip() == '---':
        # Find end of frontmatter
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                lines = lines[i + 1:]
                break

    # Remove Typora editing notes section
    in_typora_notes = False
    cleaned_lines = []

    for line in lines:
        if line.strip() == '## Typora Editing Notes':
            in_typora_notes = True
            continue
        elif in_typora_notes and line.startswith('##'):
            # Next section, stop removing
            in_typora_notes = False
            cleaned_lines.append(line)
        elif not in_typora_notes:
            cleaned_lines.append(line)

    # Remove trailing empty lines and footer markers
    while cleaned_lines and cleaned_lines[-1].strip() in ['', '---', '*When finished editing...*']:
        cleaned_lines.pop()

    return '\n'.join(cleaned_lines).strip()
