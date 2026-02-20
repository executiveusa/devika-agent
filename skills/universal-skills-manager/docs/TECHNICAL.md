# Technical Reference

Detailed technical documentation for the Universal Skills Manager. For a quick overview, see the [README](../README.md).

## Table of Contents

- [Security Scanning](#security-scanning)
- [Install Script Usage](#install-script-usage)
- [API Key Setup (All Options)](#api-key-setup)
- [API Reference](#api-reference)
- [claude.ai / Claude Desktop](#claudeai--claude-desktop)
- [Frontmatter Compatibility](#frontmatter-compatibility)

---

## Security Scanning

Skills are automatically scanned for security threats at install time. The scanner (`scan_skill.py`) checks 20+ threat categories:

**Critical:**
- Symlink traversal and path escape attempts
- Invisible/zero-width Unicode characters hiding instructions
- Data exfiltration via markdown images with variable interpolation
- Remote code piped into shell interpreters (`curl | bash`)
- Unclosed HTML comments suppressing subsequent content

**Warning:**
- Credential file references (`~/.ssh/`, `~/.aws/`, etc.) and 30+ sensitive env var patterns
- Hardcoded secrets (AWS keys, GitHub PATs, Slack tokens, JWTs, private key blocks)
- Dangerous command execution (`eval()`, `os.system()`, `subprocess.run()`)
- Prompt injection (instruction overrides, role hijacking, safety bypasses)
- Homoglyph characters (Cyrillic look-alikes that bypass text-based checks)
- Data URIs, JavaScript URIs, and protocol-relative URLs

**Info:**
- Encoded content (base64, hex, URL-encoded payloads)
- LLM delimiter tokens, cross-skill escalation attempts
- Binary files and unreadable files

**Scanner defenses:** Triple-layer symlink protection, fd-based TOCTOU mitigation, 10MB file size limit, ANSI escape stripping, Unicode NFC normalization, continuation line joining for multi-line payloads.

Findings are displayed with severity levels and you choose whether to proceed. See also [Security Scanning Reference](SECURITY_SCANNING.md) and [SECURITY.md](../SECURITY.md).

---

## Install Script Usage

The skill includes a Python helper script (`install_skill.py`) for downloading skills from GitHub:

```bash
# Preview what would be downloaded (dry-run)
python3 path/to/install_skill.py \
  --url "https://github.com/user/repo/tree/main/skill-folder" \
  --dest "~/.codex/skills/my-skill" \
  --dry-run

# Actually install to your preferred tool
python3 path/to/install_skill.py \
  --url "https://github.com/user/repo/tree/main/skill-folder" \
  --dest "~/.gemini/skills/my-skill" \
  --force
```

**Script features:**
- Zero dependencies (Python 3 stdlib only)
- Atomic install (downloads to temp, validates, then copies to destination)
- Safety check prevents accidental targeting of root skills directories
- Compares new vs existing skills before update (shows diff)
- Validates `.py`, `.sh`, `.json`, `.yaml` files
- Supports subdirectories and nested files
- Skip security scan with `--skip-scan` (not recommended)

---

## API Key Setup

The Universal Skills Manager uses a SkillsMP API key for curated search with AI semantic matching. **The API key is optional** -- without it, you can still search SkillHub and ClawHub.

### Option 1: Shell Profile (Recommended)

```bash
# For Zsh users (macOS default)
echo 'export SKILLSMP_API_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc

# For Bash users
echo 'export SKILLSMP_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

### Option 2: .env File in Home Directory

```bash
# Create ~/.env
cat > ~/.env << 'EOF'
SKILLSMP_API_KEY=your_api_key_here
EOF

# Add to your shell profile to auto-load
echo 'source ~/.env' >> ~/.zshrc
```

### Option 3: Session-based (Temporary)

```bash
export SKILLSMP_API_KEY="your_api_key_here"
```

This only persists for the current terminal session.

### Windows Users

PowerShell:
```powershell
[System.Environment]::SetEnvironmentVariable('SKILLSMP_API_KEY', 'your_api_key_here', 'User')
```

Command Prompt:
```cmd
setx SKILLSMP_API_KEY "your_api_key_here"
```

Restart your terminal for changes to take effect.

### Getting Your API Key

1. Visit [SkillsMP.com](https://skillsmp.com)
2. Navigate to the API section
3. Generate or copy your API key

### Verify API Key Setup

```bash
echo $SKILLSMP_API_KEY

curl -X GET "https://skillsmp.com/api/v1/skills/search?q=test&limit=1" \
  -H "Authorization: Bearer $SKILLSMP_API_KEY" \
  -H "User-Agent: Universal-Skills-Manager"
```

If configured correctly, you should see a JSON response with skill data.

---

## API Reference

> **Note:** Always include a `User-Agent` header in all API requests. SkillsMP is behind Cloudflare and returns 403 Forbidden for bare curl requests.

### SkillsMP (Curated, API Key Required)

**Keyword Search**
```bash
curl -X GET "https://skillsmp.com/api/v1/skills/search?q=debugging&limit=20&sortBy=recent" \
  -H "Authorization: Bearer $SKILLSMP_API_KEY" \
  -H "User-Agent: Universal-Skills-Manager"
```

**AI Semantic Search**
```bash
curl -X GET "https://skillsmp.com/api/v1/skills/ai-search?q=help+me+debug+code" \
  -H "Authorization: Bearer $SKILLSMP_API_KEY" \
  -H "User-Agent: Universal-Skills-Manager"
```

**Wildcard / Top Skills** (use `q=*` with `sortBy=stars` when no specific query):
```bash
curl -X GET "https://skillsmp.com/api/v1/skills/search?q=*&limit=20&sortBy=stars" \
  -H "Authorization: Bearer $SKILLSMP_API_KEY" \
  -H "User-Agent: Universal-Skills-Manager"
```

**Response Format:**
```json
{
  "success": true,
  "data": {
    "skills": [
      {
        "id": "skill-id",
        "name": "code-debugging",
        "author": "AuthorName",
        "description": "Systematic debugging methodology...",
        "githubUrl": "https://github.com/user/repo/tree/main/skills/code-debugging",
        "stars": 15,
        "updatedAt": 1768838561
      }
    ]
  }
}
```

### SkillHub (Community, No API Key Required)

**Search Skills**
```bash
curl -X GET "https://skills.palebluedot.live/api/skills?q=debugging&limit=20" \
  -H "User-Agent: Universal-Skills-Manager"
```

**Get Skill Details (required before install)**
```bash
curl -X GET "https://skills.palebluedot.live/api/skills/{id}" \
  -H "User-Agent: Universal-Skills-Manager"
```

**Response Format (Search):**
```json
{
  "skills": [
    {
      "id": "wshobson/agents/debugging-strategies",
      "name": "debugging-strategies",
      "description": "Master systematic debugging...",
      "githubOwner": "wshobson",
      "githubRepo": "agents",
      "githubStars": 27021,
      "securityScore": 100
    }
  ],
  "pagination": { "page": 1, "limit": 20, "total": 1000 }
}
```

### ClawHub (Versioned, Semantic Search, No API Key Required)

**Semantic Search**
```bash
curl -X GET "https://clawhub.ai/api/v1/search?q=debugging&limit=20" \
  -H "User-Agent: Universal-Skills-Manager"
```

**Browse by Stars** (also supports `sort=downloads`, `sort=trending`, `sort=updated`)
```bash
curl -X GET "https://clawhub.ai/api/v1/skills?limit=20&sort=stars" \
  -H "User-Agent: Universal-Skills-Manager"
```

**Get Skill Details**
```bash
curl -X GET "https://clawhub.ai/api/v1/skills/{slug}" \
  -H "User-Agent: Universal-Skills-Manager"
```

**Get Skill File (raw text, NOT JSON)**
```bash
curl -X GET "https://clawhub.ai/api/v1/skills/{slug}/file?path=SKILL.md" \
  -H "User-Agent: Universal-Skills-Manager"
```

**Response Format (Search):**
```json
{
  "results": [
    {
      "score": 0.82,
      "slug": "self-improving-agent",
      "displayName": "Self-Improving Agent",
      "summary": "An agent that iteratively improves itself...",
      "version": "1.0.0",
      "updatedAt": "2026-01-15T10:30:00Z"
    }
  ]
}
```

**Key Differences:** ClawHub hosts skill files directly (not on GitHub), uses slug-based identifiers, supports semantic/vector search, and includes explicit version numbers. Rate limit: 120 reads/min per IP.

---

## claude.ai / Claude Desktop

### Known Limitation

Claude Desktop has a [known bug](https://github.com/anthropics/claude-code/issues) where custom domains added to the network egress whitelist are not included in the JWT token. This means the Universal Skills Manager cannot reach SkillsMP, SkillHub, or ClawHub APIs even when the domains are whitelisted. Until this is fixed, **Claude Code CLI is the recommended way to use this skill**.

### Manual Packaging

If you want to manually package the skill for claude.ai or Claude Desktop:

1. Copy the skill folder and create `config.json`:
   ```bash
   cp -r universal-skills-manager /tmp/
   echo '{"skillsmp_api_key": "YOUR_KEY_HERE"}' > /tmp/universal-skills-manager/config.json
   ```

2. Create ZIP:
   ```bash
   cd /tmp && zip -r universal-skills-manager.zip universal-skills-manager/
   ```

3. Upload to claude.ai:
   - Go to Settings -> Capabilities
   - Click "Upload skill" in the Skills section
   - Select your ZIP file

**Security Note:** If the packaged ZIP contains your API key, do not share it publicly or commit it to version control.

---

## Frontmatter Compatibility

Claude Desktop uses [`strictyaml`](https://hitchdev.com/strictyaml/) to parse SKILL.md frontmatter, which is stricter than standard YAML. Many third-party skills fail to upload with "malformed YAML frontmatter" or "unexpected key" errors.

### Allowed Frontmatter Fields (Agent Skills Spec)

| Field | Required | Constraints |
|-------|----------|-------------|
| `name` | Yes | Max 64 chars, lowercase letters/numbers/hyphens only, must match directory name |
| `description` | Yes | Max 1024 chars. No angle brackets (`<` `>`). Literal block scalars (`\|`) with blank lines fail. Folded scalars (`>`) work but inline strings are safest |
| `license` | No | License name or reference to bundled file |
| `compatibility` | No | Max 500 chars, environment requirements |
| `metadata` | No | Flat string key-value pairs only (no nested objects, no arrays) |
| `allowed-tools` | No | Space-delimited string of pre-approved tools (not a YAML list) |

### Validation Script

The `validate_frontmatter.py` script checks and auto-fixes skills for Claude Desktop compatibility:

```bash
# Check a skill for issues
python3 scripts/validate_frontmatter.py /path/to/SKILL.md

# Auto-fix and overwrite
python3 scripts/validate_frontmatter.py /path/to/SKILL.md --fix

# Fix a skill inside a ZIP file
python3 scripts/validate_frontmatter.py /path/to/skill.zip --fix
```

**What `--fix` does:**
- Moves unsupported top-level keys (e.g., `version`, `author`) into `metadata` as string values
- Collapses literal block scalar (`|`) descriptions to inline quoted strings (error if blank lines present). Folded scalars (`>`) trigger a warning but are not auto-fixed since they work in current Claude Desktop
- Converts YAML list-format `allowed-tools` to space-delimited string
- Strips angle brackets from description
- Flattens nested `metadata` objects to flat string key-value pairs
- Truncates fields exceeding length limits

The skill's functionality is preserved. When using the Universal Skills Manager to install skills for Claude Desktop, this check runs automatically -- you'll be notified of any issues and asked before any fixes are applied.

### Sources

- [Agent Skills Specification](https://agentskills.io/specification)
- [agentskills/agentskills reference SDK](https://github.com/agentskills/agentskills/tree/main/skills-ref) (uses `strictyaml`)
- [anthropics/skills quick_validate.py](https://github.com/anthropics/skills/blob/main/skills/skill-creator/scripts/quick_validate.py)
