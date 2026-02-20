# Gemini CLI Commands Reference

## Slash Commands (`/`)

### Session Management
- `/chat save <tag>` - Save conversation checkpoint
- `/chat resume <tag>` - Resume saved conversation
- `/chat list` - List saved chats
- `/chat share [file]` - Export to Markdown/JSON
- `/resume` - Browse previous sessions
- `/clear` - Clear screen
- `/compress` - Compress context to summary

### Configuration
- `/settings` - Open settings editor
- `/model` - Change Gemini model
- `/theme` - Change visual theme
- `/editor` - Select editor
- `/vim` - Toggle vim mode

### Tools & Extensions
- `/tools` - List available tools
- `/tools desc` - Show tool descriptions
- `/extensions` - List active extensions
- `/mcp list` - List MCP servers
- `/mcp auth <server>` - Authenticate with MCP server
- `/skills list` - List discovered skills

### Memory & Context
- `/memory add <text>` - Add to memory
- `/memory show` - Display current memory
- `/memory list` - List GEMINI.md files
- `/memory refresh` - Reload memory
- `/init` - Generate GEMINI.md for project

### Debugging
- `/stats` - Session statistics
- `/about` - Version info
- `/introspect` - Debug session state
- `/bug` - File an issue
- `/restore [id]` - Restore file checkpoints

## At Commands (`@`)

Include files or directories in prompts:
```
@path/to/file.txt Explain this
@src/my_project/ Summarize the code
```

Git-aware: ignores `node_modules/`, `.git/`, etc.

## Shell Commands (`!`)

Execute shell commands:
```
!ls -la
!git status
```

Toggle shell mode with lone `!`:
```
!                    # Enter shell mode
... shell commands ...
!                    # Exit shell mode
```