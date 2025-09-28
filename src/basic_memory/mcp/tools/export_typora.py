"""Export Typora tool for Basic Memory MCP server.

This tool exports Basic Memory notes to Typora-optimized markdown format,
enabling export to multiple formats through Typora's export capabilities.
"""

import os
import re
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from loguru import logger

from basic_memory.mcp.server import mcp
from basic_memory.mcp.tools.list_directory import list_directory
from basic_memory.mcp.tools.search import search_notes
from basic_memory.mcp.tools.read_note import read_note


@mcp.tool(
    description="""Export Basic Memory notes with full Typora integration for professional multi-format publishing.

This comprehensive export tool bridges Basic Memory and Typora's powerful publishing capabilities,
enabling export to professional document formats with rich formatting and layout control.

TYPORA EXPORT FORMATS SUPPORTED:
- **PDF** - Professional documents with themes, headers, footers, and table of contents
- **Word (.docx)** - Microsoft Word compatible documents
- **HTML** - Web-ready pages with embedded styles
- **OpenDocument (.odt)** - LibreOffice compatible format
- **Rich Text (.rtf)** - Universal rich text format
- **LaTeX** - Academic and technical document preparation
- **Plain Text** - Clean text with preserved structure
- **And more formats supported by Typora!**

EXPORT CAPABILITIES:
- **Themes & Styling**: Professional document themes and custom CSS
- **Page Layout**: Custom margins, headers, footers, page breaks
- **Table of Contents**: Automatic TOC generation and numbering
- **Image Handling**: Automatic resizing and positioning
- **Math Support**: LaTeX equation rendering and formatting
- **Code Syntax**: Highlighted code blocks with language detection
- **Typography**: Professional fonts and spacing

PARAMETERS:
- export_path (str, REQUIRED): Directory where Typora export files will be created
- source_folder (str, default="/"): Basic Memory folder to export (use "/" for all notes)
- include_subfolders (bool, default=True): Include subfolders recursively
- format_type (str, default="markdown"): Preparation mode ("markdown", "html", "pdf_info")
- direct_export_format (str, optional): Direct export format ("pdf", "docx", "html", "rtf", "odt", "tex")
- include_frontmatter (bool, default=True): Include metadata in exported files
- project (str, optional): Specific Basic Memory project to export from

EXPORT WORKFLOW:
1. **Preparation**: Export notes as Typora-optimized markdown with proper formatting
2. **Typora Processing**: Open files in Typora for layout and styling adjustments
3. **Format Export**: Use Typora's export menu to generate final documents
4. **Batch Processing**: Export multiple notes to consistent formats

TYPORA FEATURES LEVERAGED:
- **Live Preview**: WYSIWYG editing with instant formatting feedback
- **Table Editor**: Visual table creation and formatting
- **Math Rendering**: Live LaTeX equation preview
- **Image Tools**: Drag-drop image insertion and resizing
- **Outline View**: Document structure management
- **Themes**: Multiple professional document themes

DIRECT EXPORT FORMATS:
- **pdf**: Professional PDF with themes and table of contents
- **docx**: Microsoft Word document format
- **html**: Standalone HTML with embedded styles
- **rtf**: Rich Text Format for universal compatibility
- **odt**: OpenDocument format for LibreOffice
- **tex**: LaTeX source for academic publishing

USAGE EXAMPLES:
Basic export: export_typora("typora-ready/")
Direct PDF: export_typora("exports/", direct_export_format="pdf")
Word docs: export_typora("docs/", direct_export_format="docx")
Project docs: export_typora("docs/", source_folder="projects/alpha")
Single folder: export_typora("export/", include_subfolders=False)
With metadata: export_typora("export/", include_frontmatter=True)

OUTPUT FILES:
- **Markdown files**: Typora-ready with proper formatting and structure
- **HTML preview**: index.html for web preview of export
- **PDF guide**: PDF_Export_Guide.md with detailed instructions
- **Workspace config**: workspace-config.json for Typora workspace setup

TYPORA EXPORT PROCESS:
1. Open exported .md files in Typora
2. Apply themes and adjust formatting as needed
3. Use File → Export menu to select format:
   - PDF (with theme selection)
   - Word (.docx)
   - HTML (with CSS)
   - LaTeX (for academic papers)
   - RTF (rich text)
   - And many more...

RETURNS:
Comprehensive export report with file statistics, Typora integration instructions,
and step-by-step guides for each supported export format.

NOTE: Use direct_export_format for automatic conversion if Typora is installed.
Otherwise, this tool prepares content for manual export through Typora's interface.
For direct API-based export without Typora, consider using export_html_notes() or export_docsify() tools.""",
)
async def export_typora(
    export_path: str,
    source_folder: str = "/",
    include_subfolders: bool = True,
    format_type: str = "markdown",
    direct_export_format: Optional[str] = None,
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
        direct_export_format: Direct export to format ("pdf", "docx", "html", "rtf", "odt", "tex")
                           Requires Typora to be installed and available in PATH
        include_frontmatter: Whether to include YAML frontmatter (default: True)
        project: Optional project name to export from. If not provided, uses current active project.

    Returns:
        Detailed export summary with Typora usage instructions and direct export results.

    Examples:
        # Export for Typora markdown editing
        result = await export_typora.fn(export_path="/path/to/typora-export")

        # Direct PDF export (requires Typora installed)
        result = await export_typora.fn(
            export_path="/path/to/export",
            direct_export_format="pdf"
        )

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

        # If direct export format is specified, attempt direct conversion
        if direct_export_format:
            direct_result = await _perform_direct_export(
                export_path_obj,
                notes_data,
                direct_export_format
            )
            result += "\n\n" + direct_result

        return result

    except Exception as e:
        logger.error(f"Typora export failed: {e}")
        return f"# Typora Export Failed\n\nUnexpected error: {e}"


async def _perform_direct_export(
    export_path: Path,
    notes_data: List[Dict[str, Any]],
    export_format: str
) -> str:
    """Attempt direct export using Typora command line if available."""
    lines = ["## Direct Export Results", ""]

    # Check if Typora is available
    typora_path = _find_typora_executable()
    if not typora_path:
        lines.extend([
            "❌ **Typora not found**",
            "Direct export requires Typora to be installed and available in PATH.",
            "Falling back to markdown preparation only.",
            "",
            "**To enable direct export:**",
            "1. Install Typora from https://typora.io",
            "2. Ensure Typora executable is in your system PATH",
            "3. Try the export again"
        ])
        return "\n".join(lines)

    # Supported formats mapping
    format_mapping = {
        'pdf': 'pdf',
        'docx': 'docx',
        'html': 'html',
        'rtf': 'rtf',
        'odt': 'odt',
        'tex': 'tex'
    }

    if export_format not in format_mapping:
        lines.append(f"❌ **Unsupported format:** {export_format}")
        lines.append(f"Supported formats: {', '.join(format_mapping.keys())}")
        return "\n".join(lines)

    lines.extend([
        f"✅ **Typora found:** {typora_path}",
        f"📄 **Export format:** {export_format.upper()}",
        ""
    ])

    # Create output directory for exported files
    output_dir = export_path / f"exported_{export_format}"
    output_dir.mkdir(exist_ok=True)

    success_count = 0
    fail_count = 0
    exported_files = []

    # Process each note
    for note_info in notes_data:
        try:
            # Get the markdown file path
            md_file = export_path / note_info['filename']
            if not md_file.exists():
                fail_count += 1
                continue

            # Determine output filename
            base_name = note_info['filename'][:-3]  # Remove .md extension
            output_file = output_dir / f"{base_name}.{format_mapping[export_format]}"

            # Run Typora export command
            cmd = [
                typora_path,
                "--export", export_format,
                str(md_file),
                "--output", str(output_file)
            ]

            logger.info(f"Running Typora export: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout per file
            )

            if result.returncode == 0:
                success_count += 1
                exported_files.append({
                    'title': note_info['title'],
                    'format': export_format.upper(),
                    'path': str(output_file.relative_to(export_path))
                })
                logger.info(f"Successfully exported {note_info['title']} to {export_format}")
            else:
                fail_count += 1
                logger.warning(f"Failed to export {note_info['title']}: {result.stderr}")

        except subprocess.TimeoutExpired:
            fail_count += 1
            logger.error(f"Timeout exporting {note_info['title']}")
        except Exception as e:
            fail_count += 1
            logger.error(f"Error exporting {note_info['title']}: {e}")

    # Generate results summary
    lines.extend([
        f"📊 **Export Summary:**",
        f"- **Successful exports:** {success_count}",
        f"- **Failed exports:** {fail_count}",
        f"- **Output directory:** {output_dir.relative_to(export_path)}",
        ""
    ])

    if exported_files:
        lines.append("📁 **Exported Files:**")
        for file_info in exported_files:
            lines.append(f"- **{file_info['title']}** → {file_info['path']}")
        lines.append("")

    if success_count > 0:
        lines.extend([
            "✅ **Direct export completed successfully!**",
            f"Files are ready in: `{output_dir}`"
        ])
    else:
        lines.extend([
            "❌ **All direct exports failed**",
            "Check Typora installation and try manual export through Typora interface."
        ])

    return "\n".join(lines)


def _find_typora_executable() -> Optional[str]:
    """Find Typora executable in system PATH."""
    # Common executable names for different platforms
    candidates = ['typora', 'Typora', 'typora.exe']

    for candidate in candidates:
        if shutil.which(candidate):
            return candidate

    # Check common installation paths (macOS example)
    common_paths = [
        '/Applications/Typora.app/Contents/MacOS/Typora',  # macOS
        'C:\\Program Files\\Typora\\Typora.exe',  # Windows
        '/usr/bin/typora',  # Linux
        '/usr/local/bin/typora'  # Linux alternative
    ]

    for path in common_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path

    return None


async def _get_notes_from_folder(
    source_folder: str,
    include_subfolders: bool,
    project: Optional[str]
) -> List[Dict[str, Any]]:
    """Get all notes from the specified folder with full content."""
    try:
        # Use search_notes to find all notes in the folder
        # We'll search for all notes and then filter by folder
        search_query = "*"  # Match all notes
        search_result = await search_notes.fn(
            query=search_query,
            page=1,
            page_size=1000,  # Large page to get all notes
            search_type="text",
            project=project
        )

        notes_data = []

        # Filter notes by folder and get their content
        for note in search_result.get('results', []):
            note_path = note.get('path', '')
            note_title = note.get('title', '')

            # Check if note is in the requested folder
            if include_subfolders:
                # Include notes in subfolders
                folder_matches = note_path.startswith(source_folder.lstrip('/'))
            else:
                # Only notes directly in the folder
                note_folder = '/'.join(note_path.split('/')[:-1])  # Remove filename
                folder_matches = note_folder == source_folder.lstrip('/')

            if folder_matches and note_path.endswith('.md'):
                # Read the actual note content
                try:
                    note_content = await read_note.fn(
                        identifier=note_title,
                        project=project
                    )

                    # Extract just the markdown content (remove any artifact formatting)
                    content = note_content
                    if content.startswith('# '):
                        # Remove any auto-generated headers from view_note
                        lines = content.split('\n')
                        # Skip lines that look like auto-generated metadata
                        filtered_lines = []
                        skip_until_content = False
                        for line in lines:
                            if line.startswith('*Original path:*') or line.startswith('*Exported:*'):
                                continue
                            if line.strip() == '---' and not skip_until_content:
                                continue
                            if line.startswith('## Content') or line.startswith('This note has been exported'):
                                skip_until_content = True
                                continue
                            if skip_until_content or not line.startswith('*Generated by'):
                                filtered_lines.append(line)

                        content = '\n'.join(filtered_lines).strip()

                    notes_data.append({
                        'filename': f"{note_title}.md",
                        'path': note_path,
                        'title': note_title,
                        'folder': source_folder,
                        'content': content
                    })

                except Exception as e:
                    logger.warning(f"Could not read content for note {note_title}: {e}")
                    # Still include the note but with empty content
                    notes_data.append({
                        'filename': f"{note_title}.md",
                        'path': note_path,
                        'title': note_title,
                        'folder': source_folder,
                        'content': f"# {note_title}\n\n*Content could not be read*"
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
    """Create Typora-optimized markdown content with actual note content."""
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

    # Add the actual note content
    content = note_info.get('content', f"# {note_info['title']}\n\n*Content could not be loaded*")

    # Ensure content starts with a proper title if it doesn't already
    if not content.strip().startswith('# '):
        lines.extend([
            f"# {note_info['title']}",
            "",
            f"*Original path: `{note_info['path']}`*",
            f"*Exported from Basic Memory: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "---",
            ""
        ])

    # Add the actual content
    lines.append(content)

    # Add export footer if the content doesn't already have it
    if not content.strip().endswith("*Generated by Basic Memory*"):
        lines.extend([
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
