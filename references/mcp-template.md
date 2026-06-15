# lit-search-cite — MCP 服务器配置模板

将所需的服务器配置块复制到你的 MCP 配置文件中：

- **Claude Code / Codex**：`%USERPROFILE%\.claude\mcp.json`
- **Claude Desktop**：`%APPDATA%\Claude\claude_desktop_config.json`
- **OpenCode / Cursor**：MCP 设置面板
- **Hermes / 其他 Agent**：各 Agent 的 MCP 配置文件

## 推荐配置（完整功能）

```json
{
  "mcpServers": {
    "ai4scholar": {
      "command": "npx",
      "args": ["-y", "@ai4scholar/mcp-server"],
      "env": {
        "AI4SCHOLAR_API_KEY": "sk-user-你的密钥"
      }
    },
    "scansci-pdf": {
      "command": "uvx",
      "args": ["scansci-pdf"]
    }
  }
}
```

## 完整配置（推荐，全功能）

```json
{
  "mcpServers": {
    "ai4scholar": {
      "command": "npx",
      "args": ["-y", "@ai4scholar/mcp-server"],
      "env": {
        "AI4SCHOLAR_API_KEY": "sk-user-你的密钥"
      }
    },
    "scansci-pdf": {
      "command": "uvx",
      "args": ["scansci-pdf"]
    }
  }
}
```

> **付费墙兜底（Wiley / CNKI）** 现在由 **OpenCLI** 提供，通过浏览器扩展连接，无需加入 MCP 配置。  
> 安装方式：`npm install -g @jackwener/opencli` + 安装 Chrome 扩展。  
> 详见 `references/opencli.md`。

## 最小配置（无需 API Key）

无 ai4scholar Key 时，Skill 自动回退到免费 API（OpenAlex、CrossRef、PubMed、arXiv）：

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

## API Key 注册

| 服务 | 注册地址 | 费用 |
|------|---------|------|
| ai4scholar | https://ai4scholar.net | 免费（10 次/分钟） |
| Semantic Scholar | https://www.semanticscholar.org/product/api | 免费 |
| OneScholar | https://www.scigreat.com/s/app/?t=oneapi-info | 免费（1000 次/天） |
| Elsevier Scopus | https://dev.elsevier.com/ | 机构授权 |
| Springer Nature | https://dev.springernature.com/ | 免费 |
