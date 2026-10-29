# 使用说明

## 1. 安装

```bash
git clone https://github.com/<你的用户名>/repomind.git
cd repomind

python -m venv .venv
source .venv/bin/activate
pip install -e .
```

安装完成后会注册 `repomind` 命令，也可以用 `python -m repomind.cli` 的方式调用。

## 2. 配置项全表

所有配置都以 `REPOMIND_` 为前缀，可通过环境变量或 `.env` 文件设置。

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `LLM_PROVIDER` | `online` | 聊天模型后端，`online` / `offline` |
| `ONLINE_MODEL` | `deepseek-chat` | 在线模型名 |
| `ONLINE_API_KEY` | 空 | 在线接口密钥 |
| `ONLINE_BASE_URL` | DeepSeek 地址 | OpenAI 兼容接口地址 |
| `OFFLINE_MODEL` | `qwen2.5:7b` | Ollama 模型名 |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama 服务地址 |
| `EMBEDDING_PROVIDER` | `online` | 嵌入模型后端 |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | 在线嵌入模型名 |
| `OFFLINE_EMBEDDING_MODEL` | `nomic-embed-text` | 离线嵌入模型名 |
| `CHUNK_SIZE` | `1200` | 分块最大字符数 |
| `CHUNK_OVERLAP` | `150` | 相邻块重叠字符数 |
| `TOP_K` | `6` | 检索返回块数 |

### 接入其他兼容接口

只要服务兼容 OpenAI 协议，改两个字段即可。以智谱 GLM 为例：

```ini
REPOMIND_ONLINE_MODEL=glm-4-flash
REPOMIND_ONLINE_BASE_URL=https://open.bigmodel.cn/api/paas/v4
```

### 混合部署

嵌入模型走在线、生成模型走本地，可以兼顾检索质量和代码隐私：

```ini
REPOMIND_LLM_PROVIDER=offline
REPOMIND_EMBEDDING_PROVIDER=online
```

## 3. 命令详解

### 3.1 构建索引

```bash
repomind index /path/to/repo -c my-repo
```

`-c` 可选，不传时使用仓库目录名作为集合名。重复执行会先清空旧集合再重建。

### 3.2 单次问答

```bash
repomind ask /path/to/repo "认证中间件在哪个文件？"
```

### 3.3 多轮对话

```bash
repomind chat /path/to/repo
```

支持的斜杠命令：

| 命令 | 作用 |
| --- | --- |
| `/clear` | 清空对话历史，重新开始 |
| `/exit`、`/quit` | 退出 |

### 3.4 Agent 模式

```bash
repomind agent /path/to/repo
```

Agent 可调用的工具：

- `directory_tree`：查看目录结构；
- `code_search`：正则搜索代码；
- `read_file`：读取指定文件；
- `git_log`：查看提交历史。

### 3.5 查看已有索引

```bash
repomind collections
```

## 4. Web 界面

```bash
streamlit run repomind/app.py
```

使用流程：

1. 侧边栏填写仓库路径（可选填自定义集合名）；
2. 点击「构建索引」，等待完成提示；
3. 点击「加载仓库」，初始化问答链；
4. 在底部输入框提问，回答下方「引用来源」可展开查看命中的文件与行号。

## 5. Docker 部署

```bash
docker compose up -d --build
```

容器内 Streamlit 监听 8501 端口。离线模式下，容器需要访问宿主机的 Ollama：

- Linux：把 `OLLAMA_BASE_URL` 改为 `http://host.docker.internal:11434`，并确保 Ollama 启动时带 `OLLAMA_HOST=0.0.0.0`；
- macOS / Windows：Docker Desktop 自带 `host.docker.internal` 解析，直接可用。

## 6. 常见问题

**Q：提示"未配置在线模型 API Key"？**
A：`.env` 中的密钥没有生效。检查文件是否位于项目根目录、变量名前缀是否为 `REPOMIND_`，或者改用离线模式。

**Q：离线模式下 Agent 不调用工具？**
A：工具调用需要模型本身支持 function calling。请使用 Qwen2.5、Llama3.1 等支持该能力的模型，纯问答可以改用 `chat` 命令。

**Q：检索结果不相关？**
A：尝试调大 `TOP_K`，或减小 `CHUNK_SIZE` 让单个块语义更聚焦；同时确认嵌入模型与问题语言匹配。

**Q：索引时某个文件被跳过？**
A：超过 300KB 的文件、二进制文件和无法按 UTF-8 解码的文件会被跳过，忽略目录清单见 `indexing/loader.py` 的 `IGNORE_DIRS`。
