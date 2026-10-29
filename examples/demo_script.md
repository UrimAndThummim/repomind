# 课堂演示脚本

以仓库自身（repomind）为索引对象，约 5 分钟完整演示。

## 准备

```bash
source .venv/bin/activate
```

## 第一步：构建索引（约 30 秒）

```bash
repomind index .
```

预期输出：`索引完成，共写入 N 个代码块。`

讲解点：加载器跳过了 `.venv`、`.git` 等目录，分块器按 Python 语法边界切分并记录行号。

## 第二步：单轮 RAG 问答

```bash
repomind ask . "在线模型和离线模型是怎么切换的？"
```

预期：回答指向 `core/llm_factory.py`，引用具体行号，下方出现「引用来源」面板。

讲解点：MMR 检索 + 提示词约束带来源引用，模型无法引用检索不到的内容。

## 第三步：多轮对话

```bash
repomind chat .
```

依次输入：

```
检索器为什么用 MMR 而不是普通 top-k？
那它的参数在哪里配置？
/clear
/exit
```

讲解点：第二个问题里的"它"依赖上文，历史改写链先把问题补全再检索；`/clear` 后历史归零。

## 第四步：Agent 自主工具调用

```bash
repomind agent .
```

输入：

```
帮我看看这个项目的目录结构，然后找出所有用 @tool 装饰的函数
```

预期：Agent 先调用 `directory_tree`，再调用 `code_search`（正则 `@tool`），最后汇总回答。

讲解点：调用顺序由模型决定，工具全只读，路径穿越会被拦截。

## 第五步：Web 界面（可选）

```bash
streamlit run repomind/app.py
```

浏览器中展示对话式交互与来源展开。
