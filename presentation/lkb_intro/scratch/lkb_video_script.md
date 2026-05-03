# LKB 两分钟视频讲稿

总时长建议：约 2 分钟。语气可以轻松一点，像给朋友介绍一个实用小工具。

## 第 1 页：封面

大家好，今天用两分钟介绍 Local Knowledge Bridge。它解决的问题很简单：AI 很聪明，但它不知道你电脑里那些 PDF、笔记、论文和项目文件在哪里。LKB 就像一座桥，把本地资料接到 Codex 前面，让 AI 先查你的本地数据库，再组织回答。

## 第 2 页：主要功能

日常使用时，你不用记一堆命令。提出问题时写 lkb，或者显式调用 Local Knowledge Bridge，就能启用本地检索。如果想更明确，可以写 lkbsearch、lkbreport、lkbask 来选择输出形式，也可以写 fast、balanced 或 deep 来指定搜索深度。

## 第 3 页：底层原理与优点

底层逻辑也不神秘。LKB 会把可读文件解析、分块，并建立本地索引；轻量模式用 SQLite FTS5 和混合排序，deep 模式再加入本地 embedding 和 reranker。优点很实际：本地、只读、可引用来源，而且 fast 和 balanced 不会加载大模型。

## 第 4 页：部署和使用

部署也尽量简单。第一步，下载项目并解压；第二步，在 local-knowledge-bridge 目录运行 lkb_setup.cmd，然后按向导添加数据源。之后就像聊天一样提问：想罗列材料用 lkbsearch，想整理证据脉络用 lkbreport，想得到带引用的分析回答用 lkbask。
