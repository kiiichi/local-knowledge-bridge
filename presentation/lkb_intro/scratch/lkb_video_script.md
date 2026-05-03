# LKB 两分钟视频讲稿

总时长建议：约 2 分钟。语气可以轻松一点，像给朋友介绍一个实用小工具。

## 第 1 页：封面

大家好，今天用两分钟介绍 Local Knowledge Bridge。它解决的问题很简单：AI 很聪明，但它不知道你电脑里那些 PDF、笔记、论文和项目文件在哪里。LKB 就像一座桥，把本地资料接到 Codex 前面，让 AI 先查你的本地数据库，再组织回答。

## 第 2 页：主要功能

日常使用时，你不用记一堆命令。在 Codex 里写 Local Knowledge Bridge，或者直接写 lkb，它就会去 Obsidian、Zotero、EndNote 和本地文件夹里找证据。它支持 fast、balanced 和可选 deep 三种方式，既能快速查找，也能做更深入的本地语义检索。

## 第 3 页：底层原理与优点

底层逻辑也不神秘。LKB 会把可读文件解析、分块，并建立本地索引；轻量模式用 SQLite FTS5 和混合排序，deep 模式再加入本地 embedding 和 reranker。优点很实际：本地、只读、可引用来源，而且 fast 和 balanced 不会加载大模型。

## 第 4 页：部署和使用

部署也尽量简单。第一步，下载项目并解压；第二步，在 local-knowledge-bridge 目录运行 lkb_setup.cmd，然后按向导添加数据源。之后就像聊天一样提问，例如查 Transformer 压缩笔记，或让 lkb 基于本地论文整理报告。资料仍在本机，AI 终于能用上它们。
