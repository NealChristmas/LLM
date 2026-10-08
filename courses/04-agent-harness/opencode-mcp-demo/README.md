# OpenCode MCP Demo

这是一个供 OpenCode 启动的本地 stdio MCP Server。它使用官方 MCP TypeScript SDK v2，提供两个无外部副作用的工具：

- `explain_mcp_concept`：解释 `host`、`client`、`server`、`tools/list` 或 `tools/call`。
- `sum_numbers`：计算 1～20 个数字的总和。

## 安装与检查

在本目录运行：

```powershell
npm install
npm run check
npm run smoke
```

不要把 `npm run start` 后终端中“没有输出”误判为失败：stdio Server 会等待 MCP Client 从标准输入发送协议消息。诊断信息写入 stderr，stdout 专供协议使用。

## 使用 MCP Inspector 测试

```powershell
npx @modelcontextprotocol/inspector npm run start --silent
```

连接后打开 Tools，可直接调用 `explain_mcp_concept` 和 `sum_numbers`。

## 接入 OpenCode 1.x

仓库根目录的 `opencode.jsonc` 已配置此 Server。重新启动 OpenCode后运行：

```powershell
opencode mcp list
```

可用下面的提示验证：

```text
请务必使用 opencode_mcp_demo 的 explain_mcp_concept 工具解释 tools/list。
```

```text
请使用 opencode_mcp_demo 的 sum_numbers 工具计算 12、30.5 和 7.5 的总和。
```

OpenCode先按配置启动本进程，再通过 MCP取得工具列表，并把工具交给模型。模型看到的是工具名称、说明和输入 Schema，不会直接看到 `McpServer` 对象。

## 配置兼容性

本机 OpenCode `1.18.32` 使用 `mcp.<name>` 配置结构。OpenCode v2文档使用 `mcp.servers.<name>`；升级到 v2后需要把同一个 Server配置移动到 `mcp.servers` 下，启动命令和 `cwd` 不变。

## 验证状态

提交时应完成 TypeScript类型检查、自动化 Client冒烟测试，以及 OpenCode的 Server连接状态检查。模型是否主动选择工具仍取决于提示词和所用模型，因此验证提示明确要求使用指定工具。
