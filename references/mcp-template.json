# lit-search-cite — MCP Server Configuration

Copy the relevant server blocks into your MCP config:

- **Claude Code (Codex)**: `%USERPROFILE%\.claude\mcp.json`
- **Claude Desktop**: `%APPDATA%\Claude\claude_desktop_config.json`
- **OpenCode / Cursor**: MCP settings panel
- **Hermes / other agents**: agent's MCP config file

## Recommended (full setup)

```json
{
  "mcpServers": {
    "ai4scholar": {
      "command": "npx",
      "args": ["-y", "@ai4scholar/mcp-server"],
      "env": {
        "AI4SCHOLAR_API_KEY": "sk-user-your-key-here"
      }
    },
    "scansci-pdf": {
      "command": "uvx",
      "args": ["scansci-pdf"]
    }
  }
}
```

## With Chrome DevTools MCP (paywall fallback)

Adds browser-based download for paywalled papers not covered by scansci-pdf.
Requires Chrome started with `--remote-debugging-port=9222`. See `references/chrome-devtools.md`.

```json
{
  "mcpServers": {
    "ai4scholar": {
      "command": "npx",
      "args": ["-y", "@ai4scholar/mcp-server"],
      "env": {
        "AI4SCHOLAR_API_KEY": "sk-user-your-key-here"
      }
    },
    "scansci-pdf": {
      "command": "uvx",
      "args": ["scansci-pdf"]
    },
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-chrome-devtools"],
      "env": {
        "CDP_URL": "http://localhost:9222"
      }
    }
  }
}
```

## Minimal (zero API key)

If you don't have an ai4scholar key, the skill automatically falls back to free APIs (OpenAlex, CrossRef, PubMed, arXiv). You only need:

```json
{
  "mcpServers": {
    "scansci-pdf": {
      "command": "uvx",
      "args": ["scansci-pdf"]
    }
  }
}
```

## API Key Registration

| Service | URL | Cost |
|---------|-----|------|
| ai4scholar | https://ai4scholar.net | Free tier (10 req/min) |
| Semantic Scholar | https://www.semanticscholar.org/product/api | Free |
| OneScholar | https://www.scigreat.com/s/app/?t=oneapi-info | Free (1000/day) |
| Elsevier Scopus | https://dev.elsevier.com/ | Institutional |
| Springer Nature | https://dev.springernature.com/ | Free |
