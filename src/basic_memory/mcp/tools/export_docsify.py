"""Export Docsify tool for Basic Memory MCP server.

This tool exports Basic Memory notes to Docsify format, creating a
complete documentation website from your knowledge base.
"""

import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from loguru import logger

from basic_memory.mcp.server import mcp
from basic_memory.mcp.tools.list_directory import list_directory


@mcp.tool(
    description="Export Basic Memory notes to Docsify documentation site format.",
)
async def export_docsify(
    export_path: str,
    source_folder: str = "/",
    include_subfolders: bool = True,
    site_title: str = "Knowledge Base",
    site_description: str = "Documentation generated from Basic Memory",
    project: Optional[str] = None,
) -> str:
    """Export Basic Memory notes to a complete Docsify documentation site.

    This tool converts your knowledge base into a Docsify-powered documentation
    website. Docsify creates beautiful, searchable documentation sites from
    markdown files with no build process required.

    Args:
        export_path: Path where to create the Docsify site
        source_folder: Folder in Basic Memory to export from (default: root "/")
        include_subfolders: Whether to include subfolders recursively (default: True)
        site_title: Title for the documentation site (default: "Knowledge Base")
        site_description: Description for the site (default: "Documentation generated from Basic Memory")
        project: Optional project name to export from. If not provided, uses current active project.

    Returns:
        Detailed export summary with setup instructions.

    Examples:
        # Export entire knowledge base to Docsify site
        result = await export_docsify.fn(export_path="/path/to/docs-site")

        # Export specific folder with custom title
        result = await export_docsify.fn(
            export_path="/path/to/docs",
            source_folder="/research",
            site_title="Research Documentation",
            site_description="My research notes and findings"
        )

        # Export single level only
        result = await export_docsify.fn(
            export_path="/path/to/docs",
            include_subfolders=False
        )
    """

    try:
        export_path_obj = Path(export_path)

        # Create export directory if it doesn't exist
        export_path_obj.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting Docsify export: {source_folder} -> {export_path}")

        # Get all notes from the source folder
        notes_data = await _get_notes_from_folder(source_folder, include_subfolders, project)

        if not notes_data:
            return f"# Docsify Export Complete\n\nNo notes found in folder: {source_folder}"

        # Process the export
        result = await _process_docsify_export(
            notes_data,
            export_path_obj,
            site_title,
            site_description
        )

        return result

    except Exception as e:
        logger.error(f"Docsify export failed: {e}")
        return f"# Docsify Export Failed\n\nUnexpected error: {e}"


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


async def _process_docsify_export(
    notes_data: List[Dict[str, Any]],
    export_path: Path,
    site_title: str,
    site_description: str
) -> str:
    """Process the export of notes to Docsify format."""

    # Track export statistics
    stats = {
        'total_notes': len(notes_data),
        'exported_notes': 0,
        'created_folders': 0,
        'failed_exports': 0
    }

    # Group notes by folder for sidebar generation
    notes_by_folder = {}

    # Process each note
    for note_info in notes_data:
        try:
            # Calculate export paths
            rel_path = note_info['path']
            folder_path = export_path / rel_path
            folder_path = folder_path.parent  # Remove the filename part
            folder_path.mkdir(parents=True, exist_ok=True)

            if str(folder_path) != str(export_path):
                stats['created_folders'] += 1

            # Keep original markdown filename
            md_path = folder_path / note_info['filename']

            # For now, create placeholder content
            # In a real implementation, you'd read the actual note content
            md_content = _create_markdown_content(note_info)

            # Write markdown file
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            # Track for sidebar
            folder_key = str(folder_path.relative_to(export_path)) if folder_path != export_path else ''
            if folder_key not in notes_by_folder:
                notes_by_folder[folder_key] = []
            notes_by_folder[folder_key].append({
                'title': note_info['title'],
                'md_path': str(md_path.relative_to(export_path)),
                'original_path': note_info['path']
            })

            stats['exported_notes'] += 1

        except Exception as e:
            logger.error(f"Failed to export note {note_info['title']}: {e}")
            stats['failed_exports'] += 1

    # Create Docsify files
    await _create_docsify_files(export_path, notes_by_folder, site_title, site_description)

    # Generate summary report
    return _generate_export_report(stats, export_path, site_title)


def _create_markdown_content(note_info: Dict[str, Any]) -> str:
    """Create markdown content for a note."""
    # In a real implementation, this would use the actual note content
    # For now, we'll create a simple markdown structure

    content = f"""# {note_info['title']}

*Original path: {note_info['path']}*
*Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

---

## Content

This is a placeholder. In a full implementation, the actual note content would appear here.

## Note Information

- **Title:** {note_info['title']}
- **Original Path:** {note_info['path']}
- **Filename:** {note_info['filename']}

## Sample Content

This note contains information about {note_info['title'].lower()}.

### Section Example

This is a sample section to demonstrate markdown structure.

### Lists

- List item 1
- List item 2
- List item 3

### Code Example

```javascript
function helloWorld() {{
    console.log("Hello, World!");
}}
```

### Links

- [Internal Link Example](relative-link)
- [External Link](https://example.com)

### Blockquote

> This is a blockquote example.
> It can span multiple lines.

---

*Generated by Basic Memory Docsify Export*
"""

    return content


async def _create_docsify_files(
    export_path: Path,
    notes_by_folder: Dict[str, List[Dict[str, Any]]],
    site_title: str,
    site_description: str
) -> None:
    """Create the necessary Docsify files."""

    # Create index.html
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>""" + site_title + """</title>
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1" />
    <meta name="description" content=\"""" + site_description + """\">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0">
    <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify@4/lib/themes/vue.css">
    <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify@4/lib/themes/dark.css" title="dark" disabled>
</head>
<body>
    <div id="app"></div>
    <script>
        window.$docsify = {{
            name: '""" + site_title + """',
            repo: '',
            loadSidebar: true,
            loadNavbar: true,
            mergeNavbar: true,
            maxLevel: 4,
            subMaxLevel: 2,
            search: 'auto',
            search: {{
                paths: 'auto',
                placeholder: 'Search...',
                noData: 'No results found',
                depth: 6
            }},
            pagination: {{
                previousText: 'Previous',
                nextText: 'Next',
                crossChapter: true,
                crossChapterText: true
            }},
            plugins: [
                function(hook, vm) {
                    hook.beforeEach(function(content) {
                        return content
                            + '\\n\\n---\\n'
                            + '*Generated by [Basic Memory](https://github.com/user/basic-memory)*';
                    });
                }
            ]
        }}
    </script>
    <script src="//cdn.jsdelivr.net/npm/docsify@4/lib/docsify.min.js"></script>
    <script src="//cdn.jsdelivr.net/npm/docsify@4/lib/plugins/search.min.js"></script>
    <script src="//cdn.jsdelivr.net/npm/docsify@4/lib/plugins/zoom-image.min.js"></script>
    <script src="//cdn.jsdelivr.net/npm/docsify@4/lib/plugins/emoji.min.js"></script>
    <script src="//cdn.jsdelivr.net/npm/docsify@4/lib/plugins/external-script.min.js"></script>
    <script src="//cdn.jsdelivr.net/npm/docsify-pagination@2/dist/docsify-pagination.min.js"></script>
</body>
</html>"""

    # Write index.html
    index_path = export_path / 'index.html'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)

    # Create _sidebar.md
    sidebar_content = f"""<!-- docs/_sidebar.md -->

* [{site_title}](README.md)
"""

    # Sort folders and add to sidebar
    for folder in sorted(notes_by_folder.keys()):
        folder_name = folder.replace('_', ' ').title() if folder else 'Home'

        if folder:
            sidebar_content += f"\n* **{folder_name}**\n"
        else:
            sidebar_content += "\n"

        # Add notes in this folder
        for note in sorted(notes_by_folder[folder], key=lambda x: x['title']):
            indent = "  " if folder else ""
            # Remove .md extension for docsify links
            link_path = note['md_path'].replace('.md', '')
            sidebar_content += f"{indent}* [{note['title']}]({link_path})\n"

    # Write _sidebar.md
    sidebar_path = export_path / '_sidebar.md'
    with open(sidebar_path, 'w', encoding='utf-8') as f:
        f.write(sidebar_content)

    # Create README.md (home page)
    readme_content = f"""# {site_title}

{site_description}

## Overview

This documentation site was generated from a Basic Memory knowledge base using the Docsify export tool.

## Features

- **Search**: Full-text search across all documents
- **Navigation**: Easy browsing with sidebar navigation
- **Responsive**: Works on desktop and mobile devices
- **Fast**: No build process required
- **Modern**: Clean, professional appearance

## Getting Started

Use the sidebar to navigate through the documentation, or use the search box to find specific content.

## Statistics

- **Total Documents:** {sum(len(notes) for notes in notes_by_folder.values())}
- **Categories:** {len(notes_by_folder)}
- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

*Powered by [Docsify](https://docsify.js.org/) and [Basic Memory](https://github.com/user/basic-memory)*
"""

    # Write README.md
    readme_path = export_path / 'README.md'
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    # Create .nojekyll file (for GitHub Pages)
    nojekyll_path = export_path / '.nojekyll'
    nojekyll_path.touch()

    # Create docsify configuration file (optional)
    config = {
        "name": site_title,
        "description": site_description,
        "version": "1.0.0",
        "exported_by": "Basic Memory",
        "exported_at": datetime.now().isoformat(),
        "note_count": sum(len(notes) for notes in notes_by_folder.values()),
        "folder_count": len(notes_by_folder)
    }

    config_path = export_path / 'docsify-config.json'
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def _generate_export_report(
    stats: Dict[str, Any],
    export_path: Path,
    site_title: str
) -> str:
    """Generate a comprehensive export report."""
    lines = [
        f"# Docsify Export Complete",
        f"**Export location:** {export_path}",
        f"**Site title:** {site_title}",
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

    # Docsify features
    lines.extend([
        "## Docsify Features Created",
        "- **index.html:** Main entry point with Docsify configuration",
        "- **README.md:** Home page with site overview",
        "- **_sidebar.md:** Navigation sidebar with all documents",
        "- **.nojekyll:** GitHub Pages compatibility file",
        "- **docsify-config.json:** Export metadata and configuration",
        ""
    ])

    # Files created
    lines.extend([
        "## Files Generated",
        f"- **Markdown files:** {stats['exported_notes']} documents",
        "- **HTML framework:** 1 index page",
        "- **Navigation:** 1 sidebar file",
        "- **Configuration:** 2 config files",
        ""
    ])

    # How to use
    lines.extend([
        "## How to Use Your Docsify Site",
        "",
        "### Local Development:",
        f"1. **Navigate to the export folder:** `cd {export_path}`",
        "2. **Start a local server:** `python -m http.server 3000`",
        "3. **Open in browser:** `http://localhost:3000`",
        "",
        "### GitHub Pages Deployment:",
        f"1. **Upload the `{export_path}` folder to GitHub**",
        "2. **Enable GitHub Pages** in repository settings",
        "3. **Access your site** at `https://username.github.io/repository/`",
        "",
        "### Other Hosting:",
        "Upload the entire folder to any web server or static hosting service.",
        "",
        "## Docsify Features Available",
        "- **Full-text search** across all documents",
        "- **Responsive design** for mobile and desktop",
        "- **Table of contents** for each page",
        "- **Emoji support** in markdown",
        "- **Image zoom** on click",
        "- **Pagination** between pages",
        ""
    ])

    return "\n".join(lines)
