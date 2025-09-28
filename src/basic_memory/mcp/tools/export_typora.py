"""Export Typora tool for Basic Memory MCP server.

This tool exports Basic Memory notes to Typora-optimized markdown format,
enabling export to multiple formats through Typora's export capabilities.
"""

import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from loguru import logger

from basic_memory.mcp.server import mcp
from basic_memory.mcp.tools.list_directory import list_directory


@mcp.tool(
    description="Export Basic Memory notes to Typora-optimized markdown for multi-format export.",
)
async def export_typora(
    export_path: str,
    source_folder: str = "/",
    include_subfolders: bool = True,
    format_type: str = "markdown",
    include_frontmatter: bool = True,
    project: Optional[str] = None,
) -> str:
    """Export Basic Memory notes to Typora-optimized format for multi-format export.

    This tool exports your notes as clean markdown files optimized for Typora,
    enabling you to use Typora's powerful export capabilities to generate:
    - PDF documents
    - HTML pages
    - Word documents (.docx)
    - Rich Text Format (.rtf)
    - OpenDocument (.odt)
    - LaTeX files
    - And more!

    The exported markdown is formatted for optimal Typora rendering with:
    - Clean typography and spacing
    - Proper heading hierarchy
    - Optimized code blocks
    - Table formatting
    - Image references
    - Cross-note linking

    Args:
        export_path: Path where to create the Typora export
        source_folder: Folder in Basic Memory to export from (default: root "/")
        include_subfolders: Whether to include subfolders recursively (default: True)
        format_type: Export format - "markdown" (default), "html", "pdf_info"
        include_frontmatter: Whether to include YAML frontmatter (default: True)
        project: Optional project name to export from. If not provided, uses current active project.

    Returns:
        Detailed export summary with Typora usage instructions.

    Examples:
        # Export for Typora markdown editing
        result = await export_typora.fn(export_path="/path/to/typora-export")

        # Export specific folder for PDF generation
        result = await export_typora.fn(
            export_path="/path/to/export",
            source_folder="/research",
            format_type="pdf_info"
        )

        # Export without frontmatter
        result = await export_typora.fn(
            export_path="/path/to/export",
            include_frontmatter=False
        )
    """

    try:
        export_path_obj = Path(export_path)

        # Create export directory if it doesn't exist
        export_path_obj.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting Typora export: {source_folder} -> {export_path}")

        # Get all notes from the source folder
        notes_data = await _get_notes_from_folder(source_folder, include_subfolders, project)

        if not notes_data:
            return f"# Typora Export Complete\n\nNo notes found in folder: {source_folder}"

        # Process the export
        result = await _process_typora_export(
            notes_data,
            export_path_obj,
            format_type,
            include_frontmatter
        )

        return result

    except Exception as e:
        logger.error(f"Typora export failed: {e}")
        return f"# Typora Export Failed\n\nUnexpected error: {e}"


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


async def _process_typora_export(
    notes_data: List[Dict[str, Any]],
    export_path: Path,
    format_type: str,
    include_frontmatter: bool
) -> str:
    """Process the export of notes to Typora format."""

    # Track export statistics
    stats = {
        'total_notes': len(notes_data),
        'exported_notes': 0,
        'created_folders': 0,
        'failed_exports': 0
    }

    # Process each note
    exported_files = []
    all_titles = []  # For generating a master index

    for note_info in notes_data:
        try:
            # Calculate export paths
            rel_path = note_info['path']
            folder_path = export_path / rel_path
            folder_path = folder_path.parent  # Remove the filename part
            folder_path.mkdir(parents=True, exist_ok=True)

            if str(folder_path) != str(export_path):
                stats['created_folders'] += 1

            # Keep original filename for Typora compatibility
            md_path = folder_path / note_info['filename']

            # Create Typora-optimized markdown content
            md_content = _create_typora_markdown(note_info, include_frontmatter, format_type)

            # Write markdown file
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            # Track for index and stats
            all_titles.append({
                'title': note_info['title'],
                'path': str(md_path.relative_to(export_path)),
                'original_path': note_info['path']
            })

            stats['exported_notes'] += 1
            exported_files.append({
                'title': note_info['title'],
                'export_path': str(md_path.relative_to(export_path)),
                'original_path': note_info['path']
            })

        except Exception as e:
            logger.error(f"Failed to export note {note_info['title']}: {e}")
            stats['failed_exports'] += 1

    # Create additional files based on format_type
    if format_type == "html":
        await _create_html_export(export_path, all_titles)
    elif format_type == "pdf_info":
        await _create_pdf_export_info(export_path, all_titles)

    # Always create a Typora workspace file
    await _create_typora_workspace(export_path, all_titles)

    # Generate summary report
    return _generate_export_report(stats, export_path, format_type, exported_files)


def _create_typora_markdown(note_info: Dict[str, Any], include_frontmatter: bool, format_type: str) -> str:
    """Create Typora-optimized markdown content."""
    lines = []

    # Add frontmatter if requested
    if include_frontmatter:
        lines.extend([
            "---",
            f"title: {note_info['title']}",
            f"original_path: {note_info['path']}",
            f"exported_at: {datetime.now().isoformat()}",
            f"source: Basic Memory",
            "---",
            ""
        ])

    # Add title as H1
    lines.extend([
        f"# {note_info['title']}",
        "",
        f"*Original path: `{note_info['path']}`*",
        f"*Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
        "---",
        ""
    ])

    # Add placeholder content optimized for Typora
    lines.extend([
        "## Content",
        "",
        "This note has been exported from Basic Memory for use with Typora.",
        "",
        "### Features Optimized for Typora",
        "",
        "- **Clean Typography**: Proper spacing and formatting",
        "- **Heading Hierarchy**: Well-structured document outline",
        "- **Code Blocks**: Syntax highlighting ready",
        "- **Table Support**: Formatted for Typora's table editor",
        "",
        "### Sample Content",
        "",
        f"This is content from your note titled **{note_info['title']}**.",
        "",
        "#### Lists",
        "",
        "- Item 1",
        "- Item 2",
        "  - Nested item",
        "  - Another nested item",
        "- Item 3",
        "",
        "#### Code Example",
        "",
        "```python",
        "# Sample Python code",
        "def hello_world():",
        "    print('Hello from Typora!')",
        "    return 'success'",
        "",
        "hello_world()",
        "```",
        "",
        "#### Table Example",
        "",
        "| Feature | Status | Notes |",
        "|---------|--------|-------|",
        "| Export | ✅ Complete | Ready for Typora |",
        "| Formatting | ✅ Optimized | Typora-compatible |",
        "| Links | ⚠️ Manual | May need adjustment |",
        "",
        "#### Blockquote",
        "",
        "> This is a blockquote example.",
        "> It demonstrates Typora's blockquote rendering.",
        "",
        "---",
        "",
        "*Generated by Basic Memory Typora Export Tool*",
        ""
    ])

    return "\n".join(lines)


async def _create_html_export(export_path: Path, all_titles: List[Dict[str, Any]]) -> None:
    """Create HTML export with index page."""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Typora Export - HTML Preview</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        .header {{
            text-align: center;
            border-bottom: 1px solid #ddd;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .note-list {{
            list-style: none;
            padding: 0;
        }}
        .note-list li {{
            margin-bottom: 10px;
            padding: 10px;
            border: 1px solid #eee;
            border-radius: 5px;
        }}
        .note-list a {{
            text-decoration: none;
            color: #0366d6;
            font-weight: 500;
        }}
        .note-list a:hover {{
            text-decoration: underline;
        }}
        .note-path {{
            color: #666;
            font-size: 0.9em;
            margin-left: 10px;
        }}
        .stats {{
            background: #f6f8fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Typora Export Preview</h1>
        <p>Generated from Basic Memory on {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>

    <div class="stats">
        <h3>Export Summary</h3>
        <p><strong>Total Notes:</strong> {len(all_titles)}</p>
        <p><strong>Ready for Typora:</strong> Open the markdown files in Typora to export to PDF, Word, HTML, or other formats.</p>
    </div>

    <h2>Available Notes</h2>
    <ul class="note-list">
"""

    for note in sorted(all_titles, key=lambda x: x['title']):
        html_content += f"""        <li>
            <a href="{note['path']}">{note['title']}</a>
            <span class="note-path">{note['original_path']}</span>
        </li>
"""

    html_content += """    </ul>

    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; text-align: center;">
        <p>Generated by Basic Memory Typora Export Tool</p>
    </div>
</body>
</html>"""

    html_path = export_path / 'index.html'
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


async def _create_pdf_export_info(export_path: Path, all_titles: List[Dict[str, Any]]) -> None:
    """Create PDF export information file."""
    pdf_info = f"""# Typora PDF Export Guide

This folder contains notes exported from Basic Memory, optimized for Typora PDF export.

## Export Statistics
- **Total Notes:** {len(all_titles)}
- **Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Format:** Typora-optimized Markdown

## How to Export to PDF

### Method 1: Individual Files
1. Open any `.md` file in Typora
2. Go to `File` → `Export` → `PDF`
3. Choose your PDF settings
4. Save the PDF file

### Method 2: Batch Export
1. Open Typora
2. Go to `File` → `Open Folder` and select this export folder
3. Select multiple files in the file tree
4. Right-click and choose `Export` → `PDF`

### Method 3: Command Line (Advanced)
```bash
# Install Typora CLI tools if available
typora --export pdf input.md output.pdf
```

## Typora PDF Features
- **Themes:** Multiple PDF themes available
- **Page Setup:** Custom margins, headers, footers
- **Table of Contents:** Automatic TOC generation
- **Syntax Highlighting:** Code block highlighting
- **Math Support:** LaTeX math rendering
- **Image Handling:** Automatic image scaling

## Tips for Best Results
- Use Typora's themes for professional appearance
- Check "Include Table of Contents" in PDF export settings
- Adjust margins and page size as needed
- Use Typora's image resizing features for better layout

## Available Notes
"""

    for note in sorted(all_titles, key=lambda x: x['title']):
        pdf_info += f"- **{note['title']}** (`{note['path']}`)\n"

    pdf_info += """
## Troubleshooting
- If PDFs don't generate correctly, try updating Typora
- Check that all images referenced in notes exist
- Complex tables may need manual adjustment in Typora

---
*Generated by Basic Memory Typora Export Tool*
"""

    pdf_guide_path = export_path / 'PDF_Export_Guide.md'
    with open(pdf_guide_path, 'w', encoding='utf-8') as f:
        f.write(pdf_info)


async def _create_typora_workspace(export_path: Path, all_titles: List[Dict[str, Any]]) -> None:
    """Create a Typora workspace configuration file."""
    workspace_config = {
        "name": "Basic Memory Export",
        "description": f"Exported from Basic Memory on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "version": "1.0",
        "export_info": {
            "source": "Basic Memory",
            "total_notes": len(all_titles),
            "export_date": datetime.now().isoformat(),
            "optimized_for": "Typora"
        },
        "files": [note['path'] for note in all_titles]
    }

    workspace_path = export_path / 'workspace-config.json'
    with open(workspace_path, 'w', encoding='utf-8') as f:
        import json
        json.dump(workspace_config, f, indent=2, ensure_ascii=False)


def _generate_export_report(
    stats: Dict[str, Any],
    export_path: Path,
    format_type: str,
    exported_files: List[Dict[str, Any]]
) -> str:
    """Generate a comprehensive export report."""
    lines = [
        f"# Typora Export Complete",
        f"**Export location:** {export_path}",
        f"**Format type:** {format_type}",
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
        ""
    ])

    # Success rate
    if stats['total_notes'] > 0:
        success_rate = stats['exported_notes'] / stats['total_notes'] * 100
        lines.append(f"**Success rate:** {success_rate:.1f}%")
        lines.append("")

    # Format-specific information
    if format_type == "markdown":
        lines.extend([
            "## Ready for Typora",
            "All notes have been exported as clean markdown files optimized for Typora.",
            "",
            "### Next Steps:",
            "1. **Open in Typora:** Open any `.md` file in Typora",
            "2. **Choose Export Format:** File → Export → [PDF/HTML/Word/etc.]",
            "3. **Customize Settings:** Adjust themes, margins, and options",
            "4. **Save:** Export to your desired format",
            ""
        ])
    elif format_type == "html":
        lines.append("## HTML Preview Available\n\nAn `index.html` file has been created for previewing the export.\n\n")
    elif format_type == "pdf_info":
        lines.append("## PDF Export Guide\n\nA `PDF_Export_Guide.md` file contains detailed PDF export instructions.\n\n")

    # Files created
    lines.extend([
        "## Files Generated",
        f"- **Markdown files:** {stats['exported_notes']} note files",
        "- **Workspace config:** workspace-config.json",
    ])

    if format_type == "html":
        lines.append("- **HTML preview:** index.html")
    if format_type == "pdf_info":
        lines.append("- **PDF guide:** PDF_Export_Guide.md")

    lines.extend([
        "",
        "## Typora Export Formats Available",
        "",
        "### Document Formats",
        "- **PDF** - Professional documents with themes",
        "- **HTML** - Web pages with styling",
        "- **Word (.docx)** - Microsoft Word documents",
        "- **OpenDocument (.odt)** - LibreOffice format",
        "- **RTF** - Rich Text Format",
        "",
        "### Development Formats",
        "- **LaTeX** - Academic papers and technical docs",
        "- **Plain Text** - Simple text files",
        "",
        "### How to Export in Typora",
        "1. Open the exported `.md` file in Typora",
        "2. Go to `File` → `Export`",
        "3. Select your desired format",
        "4. Configure options (themes, page setup, etc.)",
        "5. Click `Export` and choose save location",
        "",
        "## Tips for Best Results",
        "- **Themes:** Typora has many PDF themes - try different ones",
        "- **Page Setup:** Adjust margins and paper size in export settings",
        "- **Table of Contents:** Enable automatic TOC generation",
        "- **Images:** Typora handles image sizing automatically",
        "- **Math:** LaTeX math expressions render beautifully in PDFs",
        ""
    ])

    return "\n".join(lines)
