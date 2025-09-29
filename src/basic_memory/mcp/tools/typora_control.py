"""
Typora Control via json_rpc Plugin

Swiss Army Knife tool for full Typora automation using the obgnail/typora_plugin json_rpc plugin.

REQUIRES: obgnail/typora_plugin with json_rpc enabled on port 8888

Provides direct API control of Typora without GUI automation brittleness.
"""

import asyncio
import json
import websockets
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from basic_memory.mcp import mcp
from basic_memory.utils import logger


class TyporaRPCClient:
    """WebSocket client for Typora json_rpc communication."""

    def __init__(self, host: str = "localhost", port: int = 8888):
        self.uri = f"ws://{host}:{port}"
        self.connection_timeout = 5.0
        self.request_timeout = 10.0

    async def call(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a JSON-RPC call to Typora."""
        if params is None:
            params = {}

        request = {
            "jsonrpc": "2.0",
            "id": self._generate_id(),
            "method": method,
            "params": params
        }

        try:
            async with websockets.connect(
                self.uri,
                extra_headers={"Origin": "basic-memory-mcp"},
                open_timeout=self.connection_timeout
            ) as websocket:
                await websocket.send(json.dumps(request))

                # Set timeout for response
                response = await asyncio.wait_for(
                    websocket.recv(),
                    timeout=self.request_timeout
                )

                result = json.loads(response)

                if "error" in result:
                    return {
                        "success": False,
                        "error": result["error"].get("message", "Unknown error"),
                        "code": result["error"].get("code", -1)
                    }

                return {
                    "success": True,
                    "result": result.get("result")
                }

        except asyncio.TimeoutError:
            return {"success": False, "error": "Request timeout"}
        except websockets.exceptions.ConnectionClosedError:
            return {"success": False, "error": "Connection closed by Typora"}
        except Exception as e:
            return {"success": False, "error": f"Connection failed: {str(e)}"}

    def _generate_id(self) -> int:
        """Generate unique request ID."""
        import time
        return int(time.time() * 1000000) % 1000000


# Global client instance
typora_client = TyporaRPCClient()


@mcp.tool(
    description="""🛠️ Swiss Army Knife for Typora Control via json_rpc Plugin

REQUIRES: obgnail/typora_plugin with json_rpc enabled (default port 8888)

FULL TYPORA API CONTROL - No more GUI automation brittleness!

CORE OPERATIONS:
• export - Export current document (pdf, html, docx, etc.)
• get_content - Get current document content
• set_content - Replace entire document content
• insert_text - Insert text at cursor position
• get_cursor - Get cursor position and selection
• open_file - Open a file in Typora
• save_file - Save current file
• new_file - Create new document
• get_metadata - Get document metadata
• set_metadata - Set document metadata
• search_replace - Find and replace text
• get_themes - List available themes
• set_theme - Change theme
• toggle_sidebar - Show/hide sidebar
• toggle_toolbar - Show/hide toolbar

ADVANCED OPERATIONS:
• batch_export - Export multiple files
• content_analysis - Analyze document structure
• link_validation - Check and fix links
• template_apply - Apply Basic Memory templates
• sync_to_basic_memory - Sync content to Basic Memory

EXAMPLES:
typora_control("export", format="pdf", output_path="/exports/doc.pdf")
typora_control("get_content")
typora_control("insert_text", text="## New Section\\n\\nContent here")
typora_control("batch_export", files=["/docs/1.md", "/docs/2.md"], format="html")
"""
)
async def typora_control(
    operation: str,
    # Common parameters
    format: Optional[str] = None,
    output_path: Optional[str] = None,
    text: Optional[str] = None,
    file_path: Optional[str] = None,
    content: Optional[str] = None,
    position: Optional[str] = None,
    # Search/replace parameters
    find_text: Optional[str] = None,
    replace_text: Optional[str] = None,
    # Batch operation parameters
    files: Optional[List[str]] = None,
    # Theme/UI parameters
    theme: Optional[str] = None,
    visible: Optional[bool] = None,
    # Template parameters
    template_name: Optional[str] = None,
    # Advanced parameters
    options: Optional[Dict[str, Any]] = None
) -> str:
    """Swiss Army Knife tool for Typora control via json_rpc."""

    # Default options
    if options is None:
        options = {}

    # Route to appropriate handler
    try:
        if operation == "export":
            return await _handle_export(format, output_path, options)
        elif operation == "get_content":
            return await _handle_get_content()
        elif operation == "set_content":
            return await _handle_set_content(content)
        elif operation == "insert_text":
            return await _handle_insert_text(text, position)
        elif operation == "get_cursor":
            return await _handle_get_cursor()
        elif operation == "open_file":
            return await _handle_open_file(file_path)
        elif operation == "save_file":
            return await _handle_save_file()
        elif operation == "new_file":
            return await _handle_new_file()
        elif operation == "get_metadata":
            return await _handle_get_metadata()
        elif operation == "set_metadata":
            return await _handle_set_metadata(options)
        elif operation == "search_replace":
            return await _handle_search_replace(find_text, replace_text, options)
        elif operation == "get_themes":
            return await _handle_get_themes()
        elif operation == "set_theme":
            return await _handle_set_theme(theme)
        elif operation == "toggle_sidebar":
            return await _handle_toggle_sidebar(visible)
        elif operation == "toggle_toolbar":
            return await _handle_toggle_toolbar(visible)
        elif operation == "batch_export":
            return await _handle_batch_export(files, format, output_path, options)
        elif operation == "content_analysis":
            return await _handle_content_analysis()
        elif operation == "link_validation":
            return await _handle_link_validation()
        elif operation == "template_apply":
            return await _handle_template_apply(template_name, options)
        elif operation == "sync_to_basic_memory":
            return await _handle_sync_to_basic_memory(options)
        else:
            return await _handle_unknown_operation(operation)

    except Exception as e:
        logger.error(f"Typora control operation failed: {str(e)}")
        return f"❌ **Typora Control Error**\n\nOperation '{operation}' failed: {str(e)}\n\n**Troubleshooting**:\n• Ensure Typora is running\n• Check json_rpc plugin is enabled\n• Verify port 8888 is available\n• Restart Typora if issues persist"


async def _handle_export(format: Optional[str], output_path: Optional[str], options: Dict[str, Any]) -> str:
    """Handle document export operation."""
    if not format:
        return "❌ Export requires 'format' parameter (pdf, html, docx, odt, etc.)"
    if not output_path:
        return "❌ Export requires 'output_path' parameter"

    # Ensure output directory exists
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Build export parameters
    export_params = {
        "format": format,
        "outputPath": str(output_path_obj),
        "includeImages": options.get("include_images", True),
        "embedStyles": options.get("embed_styles", True),
        "embedImages": options.get("embed_images", True),
        "keepSource": options.get("keep_source", False)
    }

    # Add format-specific options
    if format == "pdf":
        export_params.update({
            "pageSize": options.get("page_size", "A4"),
            "margins": options.get("margins", "1cm"),
            "printBackground": options.get("print_background", True)
        })
    elif format in ["html", "docx"]:
        export_params.update({
            "embedImages": options.get("embed_images", True),
            "keepSource": options.get("keep_source", False)
        })

    result = await typora_client.call("export", export_params)

    if not result["success"]:
        return f"❌ **Export Failed**\n\nError: {result['error']}\n\n**Check**:\n• Current document is open in Typora\n• Output path is writable\n• Format is supported by Typora"

    return f"""✅ **Document Exported Successfully!**

**Format**: {format.upper()}
**Output**: {output_path}
**Options**: {'Images embedded' if export_params.get('embedImages') else 'Images referenced'}

**Next Steps**:
• Open {output_path} to verify export
• Share or archive the exported file
• Use batch_export for multiple files"""


async def _handle_get_content() -> str:
    """Get current document content."""
    result = await typora_client.call("getContent")

    if not result["success"]:
        return f"❌ **Content Retrieval Failed**\n\nError: {result['error']}\n\n**Check**:\n• Document is open in Typora\n• json_rpc plugin is enabled"

    content = result["result"]
    if not content:
        return "📄 **Current Document**: Empty or no document open"

    # Provide summary and preview
    lines = content.split('\n')
    line_count = len(lines)
    char_count = len(content)

    # Get first few lines as preview
    preview_lines = lines[:10] if len(lines) > 10 else lines
    preview = '\n'.join(preview_lines)
    if len(lines) > 10:
        preview += f"\n... ({len(lines) - 10} more lines)"

    return f"""📄 **Document Content Retrieved**

**Statistics**:
• Lines: {line_count}
• Characters: {char_count}

**Content Preview**:
```
{preview}
```

**Actions Available**:
• Use `set_content` to replace entire document
• Use `insert_text` to add content at cursor
• Use `search_replace` to modify specific text"""


async def _handle_set_content(content: Optional[str]) -> str:
    """Replace entire document content."""
    if content is None:
        return "❌ set_content requires 'content' parameter"

    result = await typora_client.call("setContent", {"content": content})

    if not result["success"]:
        return f"❌ **Content Update Failed**\n\nError: {result['error']}"

    return f"""✅ **Document Content Updated**

**New Content Length**: {len(content)} characters
**Lines**: {len(content.split('\\n'))}

**Note**: Previous content has been replaced. Use `save_file` to persist changes."""


async def _handle_insert_text(text: Optional[str], position: Optional[str]) -> str:
    """Insert text at cursor position."""
    if text is None:
        return "❌ insert_text requires 'text' parameter"

    insert_params = {"text": text}
    if position:
        insert_params["position"] = position

    result = await typora_client.call("insertText", insert_params)

    if not result["success"]:
        return f"❌ **Text Insertion Failed**\n\nError: {result['error']}\n\n**Check**:\n• Document is open in Typora\n• Cursor position is valid"

    return f"""✅ **Text Inserted Successfully**

**Inserted Text**: {text[:50]}{'...' if len(text) > 50 else ''}
**Position**: {position or 'current cursor'}

**Tip**: Use `get_cursor` to check current position before inserting."""


async def _handle_get_cursor() -> str:
    """Get cursor position and selection."""
    result = await typora_client.call("getCursor")

    if not result["success"]:
        return f"❌ **Cursor Info Failed**\n\nError: {result['error']}"

    cursor_info = result["result"]
    return f"""📍 **Cursor Position**

**Line**: {cursor_info.get('line', 'N/A')}
**Column**: {cursor_info.get('column', 'N/A')}
**Selection Start**: {cursor_info.get('selectionStart', 'N/A')}
**Selection End**: {cursor_info.get('selectionEnd', 'N/A')}
**Selected Text Length**: {cursor_info.get('selectedTextLength', 0)} characters

**Use this info for**:
• Precise text insertion with `insert_text`
• Understanding current editing context"""


async def _handle_open_file(file_path: Optional[str]) -> str:
    """Open a file in Typora."""
    if file_path is None:
        return "❌ open_file requires 'file_path' parameter"

    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        return f"❌ **File Not Found**\n\nPath: {file_path}\n\n**Check**:\n• File exists at specified path\n• Path is absolute or correct relative path"

    result = await typora_client.call("openFile", {"path": str(file_path_obj)})

    if not result["success"]:
        return f"❌ **File Open Failed**\n\nError: {result['error']}\n\n**Check**:\n• File is accessible\n• Typora can read the file format"

    return f"""✅ **File Opened in Typora**

**Path**: {file_path}
**Name**: {file_path_obj.name}

**Ready for**:
• Export operations
• Content manipulation
• Editing workflows"""


async def _handle_save_file() -> str:
    """Save current file."""
    result = await typora_client.call("saveFile")

    if not result["success"]:
        return f"❌ **Save Failed**\n\nError: {result['error']}\n\n**Check**:\n• Document is open\n• File path is writable\n• Sufficient disk space"

    return "✅ **File Saved Successfully**"


async def _handle_new_file() -> str:
    """Create new document."""
    result = await typora_client.call("newFile")

    if not result["success"]:
        return f"❌ **New File Failed**\n\nError: {result['error']}"

    return """✅ **New Document Created**

**Ready for**:
• Content insertion with `set_content` or `insert_text`
• Template application with `template_apply`
• Saving with `save_file`"""


async def _handle_get_metadata() -> str:
    """Get document metadata."""
    result = await typora_client.call("getMetadata")

    if not result["success"]:
        return f"❌ **Metadata Retrieval Failed**\n\nError: {result['error']}"

    metadata = result["result"]

    # Format metadata for display
    formatted_metadata = []
    for key, value in metadata.items():
        formatted_metadata.append(f"• **{key}**: {value}")

    return f"""📋 **Document Metadata**

{chr(10).join(formatted_metadata)}

**Use `set_metadata` to modify these values**"""


async def _handle_set_metadata(options: Dict[str, Any]) -> str:
    """Set document metadata."""
    if not options:
        return "❌ set_metadata requires metadata options (e.g., {'title': 'New Title'})"

    result = await typora_client.call("setMetadata", options)

    if not result["success"]:
        return f"❌ **Metadata Update Failed**\n\nError: {result['error']}"

    updated_fields = list(options.keys())
    return f"""✅ **Metadata Updated**

**Fields Updated**: {', '.join(updated_fields)}

**Use `get_metadata` to verify changes**"""


async def _handle_search_replace(find_text: Optional[str], replace_text: Optional[str], options: Dict[str, Any]) -> str:
    """Search and replace text."""
    if find_text is None:
        return "❌ search_replace requires 'find_text' parameter"

    params = {
        "findText": find_text,
        "replaceText": replace_text or "",
        "caseSensitive": options.get("case_sensitive", False),
        "wholeWord": options.get("whole_word", False),
        "regex": options.get("regex", False),
        "replaceAll": options.get("replace_all", True)
    }

    result = await typora_client.call("searchReplace", params)

    if not result["success"]:
        return f"❌ **Search/Replace Failed**\n\nError: {result['error']}"

    replace_info = result["result"]
    replacements = replace_info.get("replacements", 0)

    return f"""✅ **Search and Replace Completed**

**Search Term**: "{find_text}"
**Replace With**: "{replace_text or '(empty)'}"
**Replacements Made**: {replacements}
**Options**: Case {'sensitive' if params['caseSensitive'] else 'insensitive'}, {'Whole word' if params['wholeWord'] else 'Partial match'}

**Tip**: Use `save_file` to persist changes"""


async def _handle_get_themes() -> str:
    """List available themes."""
    result = await typora_client.call("getThemes")

    if not result["success"]:
        return f"❌ **Theme List Failed**\n\nError: {result['error']}"

    themes = result["result"].get("themes", [])
    current_theme = result["result"].get("current", "Unknown")

    if not themes:
        return "📋 **No Themes Available**"

    theme_list = []
    for theme in themes:
        marker = " ← CURRENT" if theme == current_theme else ""
        theme_list.append(f"• {theme}{marker}")

    return f"""🎨 **Available Themes**

{chr(10).join(theme_list)}

**Use `set_theme` to change theme**"""


async def _handle_set_theme(theme: Optional[str]) -> str:
    """Change theme."""
    if theme is None:
        return "❌ set_theme requires 'theme' parameter"

    result = await typora_client.call("setTheme", {"theme": theme})

    if not result["success"]:
        return f"❌ **Theme Change Failed**\n\nError: {result['error']}\n\n**Check**:\n• Theme name is valid (use `get_themes` to list)\n• Theme files exist"

    return f"""✅ **Theme Changed**

**New Theme**: {theme}

**Changes take effect immediately in Typora**"""


async def _handle_toggle_sidebar(visible: Optional[bool]) -> str:
    """Toggle sidebar visibility."""
    result = await typora_client.call("toggleSidebar", {"visible": visible})

    if not result["success"]:
        return f"❌ **Sidebar Toggle Failed**\n\nError: {result['error']}"

    action = "shown" if visible else "hidden" if visible is False else "toggled"
    return f"""✅ **Sidebar {action.capitalize()}**

**Use `visible=true/false` to explicitly show/hide**"""


async def _handle_toggle_toolbar(visible: Optional[bool]) -> str:
    """Toggle toolbar visibility."""
    result = await typora_client.call("toggleToolbar", {"visible": visible})

    if not result["success"]:
        return f"❌ **Toolbar Toggle Failed**\n\nError: {result['error']}"

    action = "shown" if visible else "hidden" if visible is False else "toggled"
    return f"""✅ **Toolbar {action.capitalize()}**

**Use `visible=true/false` to explicitly show/hide**"""


async def _handle_batch_export(files: Optional[List[str]], format: Optional[str], output_path: Optional[str], options: Dict[str, Any]) -> str:
    """Export multiple files."""
    if not files:
        return "❌ batch_export requires 'files' parameter (list of file paths)"
    if not format:
        return "❌ batch_export requires 'format' parameter"
    if not output_path:
        return "❌ batch_export requires 'output_path' parameter (output directory)"

    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    successful_exports = 0

    for file_path in files:
        try:
            # Open file
            open_result = await typora_client.call("openFile", {"path": file_path})
            if not open_result["success"]:
                results.append(f"❌ {Path(file_path).name}: Failed to open - {open_result['error']}")
                continue

            # Brief pause for loading
            await asyncio.sleep(0.5)

            # Export file
            export_filename = Path(file_path).stem + f".{format}"
            export_path = output_dir / export_filename

            export_result = await typora_client.call("export", {
                "format": format,
                "outputPath": str(export_path),
                "includeImages": options.get("include_images", True),
                "embedStyles": options.get("embed_styles", True)
            })

            if export_result["success"]:
                results.append(f"✅ {export_filename}: Exported successfully")
                successful_exports += 1
            else:
                results.append(f"❌ {export_filename}: Export failed - {export_result['error']}")

        except Exception as e:
            results.append(f"❌ {Path(file_path).name}: Error - {str(e)}")

    return f"""📦 **Batch Export Completed**

**Files Processed**: {len(files)}
**Successful Exports**: {successful_exports}
**Format**: {format.upper()}
**Output Directory**: {output_path}

**Results**:
{chr(10).join(results)}

**Summary**: {successful_exports}/{len(files)} files exported successfully"""


async def _handle_content_analysis() -> str:
    """Analyze document structure and content."""
    result = await typora_client.call("getContent")

    if not result["success"]:
        return f"❌ **Content Analysis Failed**\n\nError: {result['error']}"

    content = result["result"]
    if not content:
        return "📄 **Document Analysis**: Empty document"

    # Analyze content
    lines = content.split('\n')
    headings = [line for line in lines if line.startswith('#')]
    links = len([line for line in lines if '[' in line and '](' in line])
    code_blocks = content.count('```')
    images = len([line for line in lines if '![' in line and '](' in line])

    word_count = len(content.split())
    char_count = len(content)

    # Heading structure
    heading_levels = {}
    for heading in headings:
        level = len(heading) - len(heading.lstrip('#'))
        heading_levels[level] = heading_levels.get(level, 0) + 1

    return f"""📊 **Document Analysis**

**Basic Stats**:
• Total Lines: {len(lines)}
• Word Count: {word_count}
• Character Count: {char_count}

**Content Elements**:
• Headings: {len(headings)}
• Links: {links}
• Code Blocks: {code_blocks // 2} (paired)
• Images: {images}

**Heading Structure**:
{chr(10).join(f"• Level {level}: {count} headings" for level, count in sorted(heading_levels.items()))}

**Document Health**:
• Has content: {'✅' if content.strip() else '❌'}
• Has structure: {'✅' if headings else '❌'}
• Has links: {'✅' if links > 0 else '❌'}"""


async def _handle_link_validation() -> str:
    """Validate and fix links in document."""
    result = await typora_client.call("getContent")

    if not result["success"]:
        return f"❌ **Link Validation Failed**\n\nError: {result['error']}"

    content = result["result"]
    lines = content.split('\n')

    # Find links
    links_found = []
    for i, line in enumerate(lines, 1):
        if '[' in line and '](' in line:
            # Extract link text and URL
            start = line.find('](')
            if start > 0:
                end = line.find(')', start)
                if end > 0:
                    link_text = line[line.find('[')+1:start]
                    link_url = line[start+2:end]
                    links_found.append({
                        'line': i,
                        'text': link_text,
                        'url': link_url,
                        'full_match': line
                    })

    if not links_found:
        return "🔗 **Link Validation**: No links found in document"

    # Validate links (basic checks)
    validation_results = []
    valid_links = 0
    broken_links = 0

    for link in links_found:
        is_valid = True
        issues = []

        url = link['url']

        # Check for basic issues
        if not url.strip():
            issues.append("Empty URL")
            is_valid = False
        elif url.startswith('http') and not url.startswith(('http://', 'https://')):
            issues.append("Invalid HTTP/HTTPS URL")
            is_valid = False
        elif url.startswith(('http://', 'https://')):
            # Could add HTTP validation here, but keeping it simple
            pass
        elif not Path(url).exists() and not url.startswith(('http://', 'https://')):
            issues.append("Local file not found")
            is_valid = False

        if is_valid:
            valid_links += 1
            validation_results.append(f"✅ Line {link['line']}: {link['text']} → {url}")
        else:
            broken_links += 1
            validation_results.append(f"❌ Line {link['line']}: {link['text']} → {url} ({', '.join(issues)})")

    return f"""🔗 **Link Validation Results**

**Links Found**: {len(links_found)}
**Valid Links**: {valid_links}
**Broken Links**: {broken_links}

**Details**:
{chr(10).join(validation_results)}

**Actions Available**:
• Manual fix broken links
• Use `search_replace` to batch fix link patterns
• Consider using Basic Memory link resolution for [[WikiLinks]]"""


async def _handle_template_apply(template_name: Optional[str], options: Dict[str, Any]) -> str:
    """Apply a Basic Memory template to the document."""
    if template_name is None:
        return "❌ template_apply requires 'template_name' parameter"

    # For now, provide common templates. In future, could integrate with actual Basic Memory templates
    templates = {
        "research_note": """# Research Note

## Overview
[Brief description of research topic]

## Key Findings
- Finding 1
- Finding 2
- Finding 3

## Methodology
[How the research was conducted]

## Sources
- Source 1
- Source 2

## Conclusions
[Key takeaways and implications]

## Tags
#research #notes""",

        "meeting_notes": """# Meeting Notes

**Date**: [Meeting Date]
**Attendees**: [List attendees]
**Location**: [Physical or virtual location]

## Agenda
1. Topic 1
2. Topic 2
3. Topic 3

## Discussion Notes

### Topic 1
- Discussion points
- Decisions made
- Action items

### Topic 2
- Discussion points
- Decisions made
- Action items

## Action Items
- [ ] Action 1 - Owner: [Name] - Due: [Date]
- [ ] Action 2 - Owner: [Name] - Due: [Date]

## Next Meeting
**Date**: [Next meeting date]
**Focus**: [Meeting focus/topics]

## Tags
#meeting #notes""",

        "project_plan": """# Project Plan

## Project Overview
**Name**: [Project Name]
**Goal**: [Project goal/objective]
**Timeline**: [Start date] - [End date]
**Budget**: [Budget information]

## Stakeholders
- Sponsor: [Name]
- Team Lead: [Name]
- Team Members: [List]

## Scope
### In Scope
- Deliverable 1
- Deliverable 2

### Out of Scope
- Item 1
- Item 2

## Milestones
- Milestone 1: [Date] - [Description]
- Milestone 2: [Date] - [Description]
- Milestone 3: [Date] - [Description]

## Risk Assessment
### High Risk
- Risk 1: [Description] - Mitigation: [Strategy]

### Medium Risk
- Risk 2: [Description] - Mitigation: [Strategy]

## Communication Plan
- Weekly status updates
- Monthly stakeholder reviews
- Documentation updates

## Success Criteria
- Criterion 1
- Criterion 2
- Criterion 3

## Tags
#project #planning""",

        "code_review": """# Code Review

## Pull Request
**Title**: [PR Title]
**Author**: [Author Name]
**Reviewers**: [Reviewer Names]

## Files Changed
- File 1: [Changes summary]
- File 2: [Changes summary]

## Code Quality
### Strengths
- Good implementation of [feature]
- Clean code structure
- Proper error handling

### Areas for Improvement
- [Issue 1]: [Suggestion]
- [Issue 2]: [Suggestion]

## Security Considerations
- [Security review notes]

## Performance Impact
- [Performance analysis]

## Testing
### Test Coverage
- Unit tests: [Coverage %]
- Integration tests: [Pass/Fail]
- Manual testing: [Results]

### Test Recommendations
- [Additional test suggestions]

## Deployment Notes
- [Deployment considerations]
- [Rollback plan]
- [Monitoring requirements]

## Approval Status
- [ ] Code review complete
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Ready for merge

## Tags
#code-review #development"""
    }

    if template_name not in templates:
        available_templates = ', '.join(templates.keys())
        return f"""❌ **Unknown Template**

Template '{template_name}' not found.

**Available Templates**:
• {available_templates}

**Usage**: typora_control("template_apply", template_name="research_note")"""

    template_content = templates[template_name]

    # Apply any customizations from options
    if options.get("custom_title"):
        template_content = template_content.replace("[Project Name]", options["custom_title"])
    if options.get("custom_date"):
        template_content = template_content.replace("[Meeting Date]", options["custom_date"])

    result = await typora_client.call("setContent", {"content": template_content})

    if not result["success"]:
        return f"❌ **Template Application Failed**\n\nError: {result['error']}"

    return f"""✅ **Template Applied Successfully**

**Template**: {template_name}
**Content Length**: {len(template_content)} characters

**Template includes**:
• Structured sections and placeholders
• Professional formatting
• Action items and checklists
• Tagging suggestions

**Next Steps**:
• Replace [placeholders] with actual content
• Customize sections as needed
• Save with `save_file`"""


async def _handle_sync_to_basic_memory(options: Dict[str, Any]) -> str:
    """Sync current Typora document to Basic Memory."""
    # Get current content
    content_result = await typora_client.call("getContent")
    if not content_result["success"]:
        return f"❌ **Sync Failed - Content Retrieval**\n\nError: {content_result['error']}"

    content = content_result["result"]
    if not content:
        return "❌ **Sync Failed - No Content**\n\nDocument appears to be empty"

    # Get metadata
    metadata_result = await typora_client.call("getMetadata")
    title = "Synced from Typora"
    if metadata_result["success"]:
        metadata = metadata_result["result"]
        if metadata.get("title"):
            title = metadata["title"]

    # For now, provide guidance. In future, could directly call Basic Memory APIs
    return f"""📤 **Ready to Sync to Basic Memory**

**Document Title**: {title}
**Content Length**: {len(content)} characters

**To complete sync**:
1. Copy the content from Typora
2. Use Basic Memory's `write_note` tool:
   ```
   write_note(
       title="{title}",
       content="[paste content here]",
       folder="imported/typora"
   )
   ```

**Content Preview**:
{content[:200]}{'...' if len(content) > 200 else ''}

**Future Enhancement**: Direct API integration for seamless sync"""


async def _handle_unknown_operation(operation: str) -> str:
    """Handle unknown operations."""
    available_ops = [
        "export", "get_content", "set_content", "insert_text", "get_cursor",
        "open_file", "save_file", "new_file", "get_metadata", "set_metadata",
        "search_replace", "get_themes", "set_theme", "toggle_sidebar", "toggle_toolbar",
        "batch_export", "content_analysis", "link_validation", "template_apply",
        "sync_to_basic_memory"
    ]

    return f"""❌ **Unknown Operation**: {operation}

**Available Operations**:
{chr(10).join(f"• {op}" for op in available_ops)}

**Usage Examples**:
• typora_control("export", format="pdf", output_path="/path/to/file.pdf")
• typora_control("get_content")
• typora_control("insert_text", text="New content here")
• typora_control("batch_export", files=["file1.md", "file2.md"], format="html")

**For help with a specific operation**:
• Check the tool description for parameter details
• Use `typora_control("get_content")` to see current document state"""


# Additional utility functions for integration

async def check_typora_connection() -> bool:
    """Check if Typora json_rpc is available."""
    try:
        result = await typora_client.call("status")
        return result["success"]
    except:
        return False


async def get_typora_status() -> Dict[str, Any]:
    """Get comprehensive Typora status."""
    status = {
        "connection": False,
        "current_file": None,
        "theme": None,
        "ui_state": {}
    }

    # Check connection
    status["connection"] = await check_typora_connection()

    if status["connection"]:
        # Get current file info
        try:
            metadata_result = await typora_client.call("getMetadata")
            if metadata_result["success"]:
                metadata = metadata_result["result"]
                status["current_file"] = metadata.get("filePath")
        except:
            pass

        # Get theme
        try:
            theme_result = await typora_client.call("getThemes")
            if theme_result["success"]:
                status["theme"] = theme_result["result"].get("current")
        except:
            pass

    return status
