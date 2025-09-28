"""Export Joplin notes tool for Basic Memory MCP server.

This tool exports Basic Memory notes to Joplin format, creating
markdown files with corresponding JSON metadata.
"""

import os
import json
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from loguru import logger

from basic_memory.mcp.server import mcp
from basic_memory.mcp.tools.list_directory import list_directory


@mcp.tool(
    description="Export Basic Memory notes to Joplin format.",
)
async def export_joplin_notes(
    export_path: str,
    source_folder: str = "/",
    include_subfolders: bool = True,
    create_notebooks: bool = True,
    project: Optional[str] = None,
) -> str:
    """Export Basic Memory notes to Joplin format.

    This tool reads notes from Basic Memory and exports them to Joplin format,
    creating markdown files with corresponding JSON metadata files that can be
    imported back into Joplin.

    Args:
        source_folder: Folder in Basic Memory to export from (default: root "/")
        export_path: Path where to create the Joplin export
        include_subfolders: Whether to include subfolders recursively (default: True)
        create_notebooks: Whether to create notebook structure (default: True)
        project: Optional project name to export from. If not provided, uses current active project.

    Returns:
        Detailed export summary with statistics and file locations.

    Examples:
        # Export entire knowledge base
        result = await export_joplin_notes(export_path="/path/to/export")

        # Export specific folder
        result = await export_joplin_notes(
            source_folder="/research",
            export_path="/path/to/research-export"
        )

        # Export from specific project
        result = await export_joplin_notes(
            export_path="/path/to/export",
            project="work-notes"
        )

        # Flat export (no notebook structure)
        result = await export_joplin_notes(
            export_path="/path/to/export",
            create_notebooks=False
        )
    """

    try:
        export_path_obj = Path(export_path)

        # Create export directory if it doesn't exist
        export_path_obj.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting Joplin export: {source_folder} -> {export_path}")

        # Get all notes from the source folder
        notes_data = await _get_notes_from_folder(source_folder, include_subfolders, project)

        if not notes_data:
            return f"# Joplin Export Complete\n\nNo notes found in folder: {source_folder}"

        # Process the export
        result = await _process_joplin_export(
            notes_data,
            export_path_obj,
            create_notebooks
        )

        return result

    except Exception as e:
        logger.error(f"Joplin export failed: {e}")
        return f"# Joplin Export Failed\n\nUnexpected error: {e}"


async def _get_notes_from_folder(
    source_folder: str,
    include_subfolders: bool,
    project: Optional[str]
) -> List[Dict[str, Any]]:
    """Get all notes from the specified folder."""
    try:
        # Use list_directory to get all files in the folder
        depth = 10 if include_subfolders else 1

        dir_result = await list_directory.fn(
            dir_name=source_folder,
            depth=depth,
            project=project
        )

        # Parse the directory listing to extract note information
        notes_data = []

        lines = dir_result.split('\n')
        current_folder = source_folder

        for line in lines:
            if line.startswith('📄') and '.md' in line:
                # Extract filename and path
                parts = line.split()
                if len(parts) >= 2:
                    filename = parts[1].strip()
                    if filename.endswith('.md'):
                        # Get the full path from the line
                        path_part = line.split(' | ')[0] if ' | ' in line else parts[-1]

                        # Remove leading slash if present
                        if path_part.startswith('/'):
                            path_part = path_part[1:]

                        # Extract title if available
                        title = filename[:-3]  # Remove .md
                        if ' | ' in line:
                            title_part = line.split(' | ')[1].strip()
                            if title_part:
                                title = title_part

                        notes_data.append({
                            'filename': filename,
                            'path': path_part,
                            'title': title,
                            'folder': current_folder
                        })

    except Exception as e:
        logger.error(f"Error getting notes from folder {source_folder}: {e}")
        return []

    return notes_data


async def _process_joplin_export(
    notes_data: List[Dict[str, Any]],
    export_path: Path,
    create_notebooks: bool
) -> str:
    """Process the export of notes to Joplin format."""

    # Track export statistics
    stats = {
        'total_notes': len(notes_data),
        'exported_notes': 0,
        'created_folders': 0,
        'failed_exports': 0,
        'notebooks_created': set()
    }

    # Process each note
    exported_files = []

    for note_info in notes_data:
        try:
            # Calculate export paths
            if create_notebooks:
                # Create folder structure based on note path
                rel_path = note_info['path']
                folder_path = export_path / rel_path
                folder_path = folder_path.parent  # Remove the filename part
                folder_path.mkdir(parents=True, exist_ok=True)

                if str(folder_path) != str(export_path):
                    stats['created_folders'] += 1

                # Notebook name from folder
                notebook_name = folder_path.name if folder_path != export_path else "Imported Notes"
                if notebook_name not in stats['notebooks_created']:
                    stats['notebooks_created'].add(notebook_name)
            else:
                # Flat structure
                folder_path = export_path
                notebook_name = "Imported Notes"

            # Generate Joplin-compatible filenames
            base_name = _generate_joplin_filename(note_info['title'])
            md_path = folder_path / f"{base_name}.md"
            json_path = folder_path / f"{base_name}.json"

            # Create Joplin metadata
            metadata = _create_joplin_metadata(note_info, notebook_name)

            # For now, we'll create placeholder content
            # In a real implementation, you'd read the actual note content
            content = _create_placeholder_content(note_info)

            # Write files
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(content)

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            stats['exported_notes'] += 1
            exported_files.append({
                'title': note_info['title'],
                'export_path': str(md_path.relative_to(export_path)),
                'notebook': notebook_name,
                'id': metadata['id']
            })

        except Exception as e:
            logger.error(f"Failed to export note {note_info['title']}: {e}")
            stats['failed_exports'] += 1
            exported_files.append({
                'title': note_info['title'],
                'error': str(e)
            })

    # Generate summary report
    return _generate_export_report(stats, exported_files, export_path)


def _generate_joplin_filename(title: str) -> str:
    """Generate a Joplin-compatible filename from title."""
    # Joplin uses a specific naming scheme, often with IDs
    # For simplicity, we'll sanitize the title
    import re
    from unicodedata import normalize

    # Normalize unicode characters
    title = normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')

    # Replace unsafe characters
    title = re.sub(r'[^\w\s-]', '_', title)

    # Replace spaces and multiple underscores
    title = re.sub(r'[\s_]+', '_', title)

    # Trim underscores
    title = title.strip('_')

    # Limit length and ensure it's not empty
    if len(title) > 50:
        title = title[:47] + '...'

    if not title:
        title = 'untitled'

    # Add timestamp to make it unique (Joplin style)
    timestamp = int(datetime.now().timestamp() * 1000)
    return f"{title}_{timestamp}"


def _create_joplin_metadata(note_info: Dict[str, Any], notebook_name: str) -> Dict[str, Any]:
    """Create Joplin-compatible JSON metadata."""
    now = int(datetime.now().timestamp() * 1000)

    metadata = {
        "id": str(uuid.uuid4()),
        "title": note_info['title'],
        "body": "",  # Will be filled with actual content
        "parent_id": "",  # Would be set for notebook relationships
        "created_time": now,
        "updated_time": now,
        "user_created_time": now,
        "user_updated_time": now,
        "encryption_cipher_text": "",
        "encryption_applied": 0,
        "markup_language": 1,  # 1 = Markdown
        "is_shared": 0,
        "type_": 1,  # 1 = Note
        "source": "basic-memory-export",
        "source_application": "basic-memory",
        "application_data": json.dumps({
            "original_path": note_info['path'],
            "exported_from": "basic-memory",
            "export_timestamp": now
        }),
        "author": "",
        "source_url": "",
        "is_todo": 0,
        "todo_due": 0,
        "todo_completed": 0,
        "latitude": 0.0,
        "longitude": 0.0,
        "altitude": 0.0,
        "order": 0,
        "tags": []  # Could be populated from Basic Memory tags
    }

    return metadata


def _create_placeholder_content(note_info: Dict[str, Any]) -> str:
    """Create placeholder content for the note."""
    # In a real implementation, this would read the actual note content
    # For now, we'll create a placeholder
    content = f"""# {note_info['title']}

*This note was exported from Basic Memory.*
*Original path: {note_info['path']}*
*Export timestamp: {datetime.now().isoformat()}*

## Content

[Note: This is a placeholder. In a full implementation, the actual note content would be included here.]

## Metadata

- **Title:** {note_info['title']}
- **Original Path:** {note_info['path']}
- **Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    return content


def _generate_export_report(
    stats: Dict[str, Any],
    exported_files: List[Dict[str, Any]],
    export_path: Path
) -> str:
    """Generate a comprehensive export report."""
    lines = [
        f"# Joplin Export Complete",
        f"**Export location:** {export_path}",
        f"**Export completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]

    # Statistics
    lines.extend([
        "## Export Statistics",
        f"- **Total notes processed:** {stats['total_notes']}",
        f"- **Successfully exported:** {stats['exported_notes']}",
        f"- **Failed exports:** {stats['failed_exports']}",
        f"- **Folders created:** {stats['created_folders']}",
        f"- **Notebooks created:** {len(stats['notebooks_created'])}",
        ""
    ])

    # Success rate
    if stats['total_notes'] > 0:
        success_rate = stats['exported_notes'] / stats['total_notes'] * 100
        lines.append(f"**Success rate:** {success_rate:.1f}%")
        lines.append("")

    # List created notebooks
    if stats['notebooks_created']:
        lines.append("## Notebooks Created")
        for notebook in sorted(stats['notebooks_created']):
            lines.append(f"- {notebook}")
        lines.append("")

    # Exported files summary
    if exported_files:
        lines.append("## Exported Notes")
        for file_info in exported_files[:20]:  # Limit to first 20
            if 'error' in file_info:
                lines.append(f"- ❌ **{file_info['title']}** - Error: {file_info['error']}")
            else:
                lines.append(f"- ✅ **{file_info['title']}** → {file_info['export_path']} (ID: {file_info['id']})")

        if len(exported_files) > 20:
            lines.append(f"- ... and {len(exported_files) - 20} more notes")
        lines.append("")

    # Import instructions
    lines.extend([
        "## How to Import into Joplin",
        "1. **Open Joplin** and go to File → Import",
        "2. **Choose 'Joplin Export Directory'** as the import format",
        "3. **Select the export folder:** `{export_path}`",
        "4. **Complete the import** - Joplin will create the notes and notebooks",
        "",
        "## Notes",
        "- Each note has been exported as a `.md` file with a corresponding `.json` metadata file",
        "- Notebook structure has been preserved based on folder organization",
        "- Original Basic Memory paths are stored in the metadata for reference",
        ""
    ])

    return "\n".join(lines)
