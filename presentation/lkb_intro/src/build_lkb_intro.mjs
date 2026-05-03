import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const deckDir = path.resolve(__dirname, "..");
const repoDir = path.resolve(deckDir, "..", "..");
const scratchDir = path.join(deckDir, "scratch");
const outputDir = path.join(deckDir, "output");
const outputPptx = path.join(outputDir, "output.pptx");
const scriptPath = path.join(scratchDir, "lkb_video_script.md");
const comicPath = path.join(repoDir, "assets", "lkb-comic.jpg");

fs.mkdirSync(scratchDir, { recursive: true });
fs.mkdirSync(outputDir, { recursive: true });

const artifactToolPath = path.join(
  process.env.USERPROFILE || "C:\\Users\\kichi",
  ".cache",
  "codex-runtimes",
  "codex-primary-runtime",
  "dependencies",
  "node",
  "node_modules",
  "@oai",
  "artifact-tool",
  "dist",
  "artifact_tool.mjs",
);

const {
  Presentation,
  PresentationFile,
  FileBlob,
  row,
  column,
  grid,
  layers,
  panel,
  text,
  image,
  shape,
  rule,
  fill,
  hug,
  fixed,
  wrap,
  grow,
  fr,
  auto,
} = await import(pathToFileURL(artifactToolPath).href);

const W = 1920;
const H = 1080;
const fontCn = "Microsoft YaHei";
const fontMono = "Cascadia Mono";

const C = {
  ink: "#111827",
  mute: "#59606C",
  paper: "#F7F1E4",
  paper2: "#FFF8EA",
  cream: "#F4E7D1",
  teal: "#008B7A",
  blue: "#4B64D8",
  orange: "#E65D2F",
  yellow: "#D89B16",
  red: "#D94343",
  green: "#2D9B59",
  purple: "#7C4DCE",
  dark: "#101820",
  dark2: "#17212B",
  white: "#FFFFFF",
};

const script = [
  {
    title: "封面",
    text:
      "大家好，今天用两分钟介绍 Local Knowledge Bridge。它解决的问题很简单：AI 很聪明，但它不知道你电脑里那些 PDF、笔记、论文和项目文件在哪里。LKB 就像一座桥，把本地资料接到 Codex 前面，让 AI 先查你的本地数据库，再组织回答。",
  },
  {
    title: "主要功能",
    text:
      "日常使用时，你不用记一堆命令。提出问题时写 lkb，或者显式调用 Local Knowledge Bridge，就能启用本地检索。如果想更明确，可以写 lkbsearch、lkbreport、lkbask 来选择输出形式，也可以写 fast、balanced 或 deep 来指定搜索深度。",
  },
  {
    title: "底层原理与优点",
    text:
      "底层逻辑也不神秘。LKB 会把可读文件解析、分块，并建立本地索引；轻量模式用 SQLite FTS5 和混合排序，deep 模式再加入本地 embedding 和 reranker。优点很实际：本地、只读、可引用来源，而且 fast 和 balanced 不会加载大模型。",
  },
  {
    title: "部署和使用",
    text:
      "部署也尽量简单。第一步，下载项目并解压；第二步，在 local-knowledge-bridge 目录运行 lkb_setup.cmd，然后按向导添加数据源。之后就像聊天一样提问：想罗列材料用 lkbsearch，想整理证据脉络用 lkbreport，想得到带引用的分析回答用 lkbask。",
  },
];

const md = [
  "# LKB 两分钟视频讲稿",
  "",
  "总时长建议：约 2 分钟。语气可以轻松一点，像给朋友介绍一个实用小工具。",
  "",
  ...script.flatMap((item, idx) => [
    `## 第 ${idx + 1} 页：${item.title}`,
    "",
    item.text,
    "",
  ]),
].join("\n");
fs.writeFileSync(scriptPath, md, "utf8");

function titleStyle(size = 64, color = C.ink) {
  return {
    fontFamily: fontCn,
    fontSize: size,
    bold: true,
    color,
  };
}

function bodyStyle(size = 28, color = C.mute) {
  return {
    fontFamily: fontCn,
    fontSize: size,
    color,
  };
}

function monoStyle(size = 24, color = C.paper2) {
  return {
    fontFamily: fontMono,
    fontSize: size,
    color,
  };
}

function addSlide(presentation, node, note) {
  const slide = presentation.slides.add();
  slide.compose(node, {
    frame: { left: 0, top: 0, width: W, height: H },
    baseUnit: 8,
  });
  slide.speakerNotes.setText(note);
  return slide;
}

function fileIcon(ext, label, color) {
  return panel(
    {
      name: `file-icon-${ext.toLowerCase()}`,
      width: fixed(162),
      height: fixed(136),
      fill: C.paper2,
      borderRadius: 18,
      padding: { x: 16, y: 14 },
    },
    column(
      { width: fill, height: fill, gap: 10, justify: "center", align: "center" },
      [
        shape({
          name: `file-icon-${ext.toLowerCase()}-bar`,
          width: fixed(96),
          height: fixed(8),
          fill: color,
          borderRadius: 4,
        }),
        text(ext, {
          name: `file-icon-${ext.toLowerCase()}-ext`,
          width: fill,
          height: hug,
          style: { ...titleStyle(34, C.ink), fontFamily: fontMono },
        }),
        text(label, {
          name: `file-icon-${ext.toLowerCase()}-label`,
          width: fill,
          height: hug,
          style: bodyStyle(16, C.mute),
        }),
      ],
    ),
  );
}

function featureStep(num, title, detail, color) {
  return column(
    {
      name: `feature-step-${num}`,
      width: fixed(380),
      height: hug,
      gap: 16,
      align: "start",
    },
    [
      text(String(num).padStart(2, "0"), {
        name: `feature-step-${num}-number`,
        width: fill,
        height: hug,
        style: { ...titleStyle(52, color), fontFamily: fontMono },
      }),
      text(title, {
        name: `feature-step-${num}-title`,
        width: fill,
        height: hug,
        style: titleStyle(34, C.ink),
      }),
      text(detail, {
        name: `feature-step-${num}-detail`,
        width: fill,
        height: hug,
        style: bodyStyle(23, C.mute),
      }),
    ],
  );
}

function pipelineNode(title, detail, color) {
  return panel(
    {
      name: `pipeline-${title}`,
      width: fill,
      height: hug,
      fill: C.paper2,
      borderRadius: 18,
      padding: { x: 24, y: 18 },
    },
    row(
      { width: fill, height: hug, gap: 18, align: "center" },
      [
        shape({
          name: `pipeline-dot-${title}`,
          width: fixed(18),
          height: fixed(18),
          geometry: "ellipse",
          fill: color,
        }),
        column({ name: `pipeline-text-${title}`, width: fill, height: hug, gap: 2 }, [
          text(title, {
            name: `pipeline-title-${title}`,
            width: fill,
            height: hug,
            style: titleStyle(24, C.ink),
          }),
          text(detail, {
            name: `pipeline-detail-${title}`,
            width: fill,
            height: hug,
            style: bodyStyle(16, C.mute),
          }),
        ]),
      ],
    ),
  );
}

async function saveBlobLike(blob, filePath) {
  if (blob && typeof blob.save === "function") {
    await blob.save(filePath);
    return;
  }
  if (blob && typeof blob.arrayBuffer === "function") {
    await fs.promises.writeFile(filePath, Buffer.from(await blob.arrayBuffer()));
    return;
  }
  throw new Error(`Unsupported export type for ${filePath}`);
}

function exampleLine(copy, color) {
  return row(
    { width: fill, height: hug, gap: 14, align: "start" },
    [
      shape({
        name: `example-mark-${copy.slice(0, 6)}`,
        width: fixed(10),
        height: fixed(28),
        fill: color,
        borderRadius: 5,
      }),
      text(copy, {
        name: `example-${copy.slice(0, 8)}`,
        width: fill,
        height: hug,
        style: bodyStyle(23, C.ink),
      }),
    ],
  );
}

const presentation = Presentation.create({
  slideSize: { width: W, height: H },
});

addSlide(
  presentation,
  layers({ name: "slide-1-root", width: fill, height: fill }, [
    shape({ name: "cover-bg", width: fill, height: fill, fill: C.dark }),
    grid(
      {
        name: "cover-grid",
        width: fill,
        height: fill,
        rows: [auto, fr(1), auto],
        columns: [fr(1)],
        padding: { x: 96, y: 72 },
        rowGap: 44,
      },
      [
        row({ name: "cover-top", width: fill, height: hug, justify: "between", align: "center" }, [
          text("Local Knowledge Bridge", {
            name: "cover-brand",
            width: hug,
            height: hug,
            style: { ...titleStyle(32, C.paper2), letterSpacing: 0 },
          }),
          text("让 Codex 先查本地资料", {
            name: "cover-promise",
            width: hug,
            height: hug,
            style: bodyStyle(24, "#C8D2D8"),
          }),
        ]),
        column(
          {
            name: "cover-center",
            width: fill,
            height: fill,
            justify: "center",
            align: "start",
            gap: 30,
          },
          [
            text("AI+本地数据库", {
              name: "cover-phrase",
              width: wrap(1500),
              height: hug,
              style: titleStyle(118, C.paper2),
            }),
            rule({ name: "cover-rule", width: fixed(360), stroke: C.teal, weight: 8 }),
            text("把散落在电脑里的笔记、论文和项目文件，变成 AI 能先检索、再引用的知识入口。", {
              name: "cover-subtitle",
              width: wrap(1160),
              height: hug,
              style: bodyStyle(32, "#DCE5E7"),
            }),
          ],
        ),
        row(
          {
            name: "cover-file-icons",
            width: fill,
            height: hug,
            gap: 26,
            justify: "center",
            align: "center",
          },
          [
            fileIcon("PDF", "论文 / 报告", C.red),
            fileIcon("MD", "Obsidian", C.teal),
            fileIcon("TXT", "文本资料", C.yellow),
            fileIcon("PPTX", "演示文稿", C.orange),
            fileIcon("DOCX", "文档", C.blue),
            fileIcon("XLSX", "表格", C.green),
          ],
        ),
      ],
    ),
  ]),
  script[0].text,
);

addSlide(
  presentation,
  layers({ name: "slide-2-root", width: fill, height: fill }, [
    shape({ name: "slide-2-bg", width: fill, height: fill, fill: C.paper }),
    grid(
      {
        name: "feature-grid",
        width: fill,
        height: fill,
        rows: [auto, fr(1), auto],
        columns: [fr(1)],
        padding: { x: 88, y: 72 },
        rowGap: 54,
      },
      [
        column({ name: "feature-title-stack", width: fill, height: hug, gap: 14 }, [
          text("使用方式：先选输出，再选深度", {
            name: "slide-2-title",
            width: fill,
            height: hug,
            style: titleStyle(62, C.ink),
          }),
          text("最简单：直接写 lkb 让 Codex 自动判断。想更明确：用 lkbsearch / lkbreport / lkbask 指定输出，用 fast / balanced / deep 指定搜索深度。", {
            name: "slide-2-subtitle",
            width: wrap(1260),
            height: hug,
            style: bodyStyle(28, C.mute),
          }),
        ]),
        row(
          {
            name: "feature-steps",
            width: fill,
            height: hug,
            gap: 38,
            align: "start",
            justify: "center",
          },
          [
            featureStep(
              1,
              "自动模式",
              "不确定怎么选时，写 lkb 加问题，让 Codex 自动选择输出和深度。",
              C.teal,
            ),
            featureStep(
              2,
              "lkbsearch",
              "想罗列候选材料，例如“二战期间有哪些主流思潮”。",
              C.orange,
            ),
            featureStep(
              3,
              "lkbreport",
              "想整理证据脉络，例如“按热烈讨论的时间排先后”。",
              C.blue,
            ),
            featureStep(
              4,
              "lkbask",
              "想得到分析结论，例如“这些思潮有什么共性”。",
              C.green,
            ),
          ],
        ),
        row({ name: "feature-bottom", width: fill, height: hug, gap: 26, align: "center" }, [
          shape({
            name: "feature-bottom-mark",
            width: fixed(14),
            height: fixed(58),
            fill: C.teal,
            borderRadius: 7,
          }),
          text("搜索深度也能自动；需要时再显式写 fast、balanced / balance 或 deep。", {
            name: "feature-bottom-copy",
            width: fill,
            height: hug,
            style: titleStyle(34, C.ink),
          }),
        ]),
      ],
    ),
  ]),
  script[1].text,
);

addSlide(
  presentation,
  layers({ name: "slide-3-root", width: fill, height: fill }, [
    shape({ name: "slide-3-bg", width: fill, height: fill, fill: C.dark2 }),
    grid(
      {
        name: "principle-grid",
        width: fill,
        height: fill,
        columns: [fr(0.92), fr(1.08)],
        rows: [auto, fr(1), auto],
        columnGap: 64,
        rowGap: 40,
        padding: { x: 88, y: 72 },
      },
      [
        column({ name: "principle-title-stack", width: fill, height: hug, gap: 14, columnSpan: 2 }, [
          text("底层原理：先建本地索引，再把证据交给 AI", {
            name: "slide-3-title",
            width: fill,
            height: hug,
            style: titleStyle(58, C.paper2),
          }),
          text("轻量检索和 deep 检索分开运行，速度、成本和效果可以按场景选择。", {
            name: "slide-3-subtitle",
            width: wrap(1180),
            height: hug,
            style: bodyStyle(28, "#CBD5DB"),
          }),
        ]),
        column({ name: "principle-left", width: fill, height: fill, gap: 28, justify: "center" }, [
          text("它不是把资料上传到远端，而是在本机建立一条可检索通道。", {
            name: "principle-main-claim",
            width: wrap(690),
            height: hug,
            style: titleStyle(46, C.paper2),
          }),
          rule({ name: "principle-rule", width: fixed(260), stroke: C.orange, weight: 6 }),
          text("默认只读：索引、配置、日志、模型都留在本机。轻量模式不加载 deep 模型；需要更深语义检索时，再启用 deep。", {
            name: "principle-detail",
            width: wrap(710),
            height: hug,
            style: bodyStyle(29, "#D8E1E4"),
          }),
        ]),
        column({ name: "principle-pipeline", width: fill, height: fill, gap: 18, justify: "center" }, [
          pipelineNode("解析与分块", "把笔记、论文附件和 Office 文件整理成可索引文本", C.teal),
          pipelineNode("SQLite FTS5", "fast / balanced 使用轻量本地词法检索", C.yellow),
          pipelineNode("混合评分与 RRF", "按来源路线、权重和排名融合证据", C.orange),
          pipelineNode("deep 可选", "本地 bge-m3 embedding + reranker 做语义增强", C.blue),
          pipelineNode("带来源回答", "回答里保留引用编号，方便回到原文件核对", C.green),
        ]),
        row({ name: "principle-footer", width: fill, height: hug, gap: 44, columnSpan: 2, align: "center" }, [
          text("优点", {
            name: "principle-footer-label",
            width: hug,
            height: hug,
            style: titleStyle(28, C.orange),
          }),
          text("本地优先", {
            name: "adv-local",
            width: hug,
            height: hug,
            style: titleStyle(28, C.paper2),
          }),
          text("默认只读", {
            name: "adv-readonly",
            width: hug,
            height: hug,
            style: titleStyle(28, C.paper2),
          }),
          text("快慢可选", {
            name: "adv-modes",
            width: hug,
            height: hug,
            style: titleStyle(28, C.paper2),
          }),
          text("证据可回查", {
            name: "adv-source",
            width: hug,
            height: hug,
            style: titleStyle(28, C.paper2),
          }),
        ]),
      ],
    ),
  ]),
  script[2].text,
);

addSlide(
  presentation,
  layers({ name: "slide-4-root", width: fill, height: fill }, [
    shape({ name: "slide-4-bg", width: fill, height: fill, fill: C.paper2 }),
    grid(
      {
        name: "deploy-grid",
        width: fill,
        height: fill,
        rows: [auto, fr(1), auto],
        columns: [fr(0.9), fr(1.1)],
        columnGap: 62,
        rowGap: 40,
        padding: { x: 88, y: 72 },
      },
      [
        column({ name: "deploy-title-stack", width: fill, height: hug, gap: 12, columnSpan: 2 }, [
          text("部署和使用：装好后，用自然语言触发", {
            name: "slide-4-title",
            width: fill,
            height: hug,
            style: titleStyle(60, C.ink),
          }),
          text("包含 lkb 或调用 skill 即可自动检索；也可以显式写搜索模式和搜索深度。", {
            name: "slide-4-subtitle",
            width: wrap(1040),
            height: hug,
            style: bodyStyle(28, C.mute),
          }),
        ]),
        column({ name: "deploy-left", width: fill, height: fill, gap: 30, justify: "center" }, [
          row({ name: "deploy-step-1", width: fill, height: hug, gap: 24, align: "start" }, [
            text("01", {
              name: "deploy-step-1-num",
              width: fixed(92),
              height: hug,
              style: { ...titleStyle(48, C.teal), fontFamily: fontMono },
            }),
            column({ width: fill, height: hug, gap: 8 }, [
              text("下载并解压", {
                name: "deploy-step-1-title",
                width: fill,
                height: hug,
                style: titleStyle(34, C.ink),
              }),
              text("进入项目里的 local-knowledge-bridge 目录。", {
                name: "deploy-step-1-copy",
                width: fill,
                height: hug,
                style: bodyStyle(24, C.mute),
              }),
            ]),
          ]),
          row({ name: "deploy-step-2", width: fill, height: hug, gap: 24, align: "start" }, [
            text("02", {
              name: "deploy-step-2-num",
              width: fixed(92),
              height: hug,
              style: { ...titleStyle(48, C.orange), fontFamily: fontMono },
            }),
            column({ width: fill, height: hug, gap: 8 }, [
              text("运行安装程序", {
                name: "deploy-step-2-title",
                width: fill,
                height: hug,
                style: titleStyle(34, C.ink),
              }),
              text("按向导配置已有部署或安装 / 重新部署，并添加数据源。", {
                name: "deploy-step-2-copy",
                width: fill,
                height: hug,
                style: bodyStyle(24, C.mute),
              }),
            ]),
          ]),
          panel(
            {
              name: "deploy-code-panel",
              width: fill,
              height: hug,
              fill: C.dark,
              borderRadius: 18,
              padding: { x: 26, y: 22 },
            },
            column({ width: fill, height: hug, gap: 12 }, [
              text("cd <repo>\\local-knowledge-bridge", {
                name: "deploy-code-1",
                width: fill,
                height: hug,
                style: monoStyle(24, C.paper2),
              }),
              text(".\\lkb_setup.cmd", {
                name: "deploy-code-2",
                width: fill,
                height: hug,
                style: monoStyle(26, "#9FF2DF"),
              }),
            ]),
          ),
        ]),
        column({ name: "deploy-right", width: fill, height: fill, gap: 22, justify: "center" }, [
          text("像这样在 Codex 里问", {
            name: "examples-title",
            width: fill,
            height: hug,
            style: titleStyle(36, C.ink),
          }),
          exampleLine("lkbsearch，罗列二战期间被讨论过的主流思潮。", C.teal),
          exampleLine("lkbreport deep，把这些思潮被热烈讨论的时间排成先后顺序。", C.orange),
          exampleLine("lkbask deep，分析这些思潮之间有什么共性，并引用来源。", C.blue),
        ]),
        text("使用示例依据 local-knowledge-bridge/README.zh-CN.md。", {
          name: "slide-4-footer",
          width: fill,
          height: hug,
          columnSpan: 2,
          style: bodyStyle(16, "#77705F"),
        }),
      ],
    ),
  ]),
  script[3].text,
);

const pptxBlob = await PresentationFile.exportPptx(presentation);
await saveBlobLike(pptxBlob, outputPptx);

for (let i = 0; i < presentation.slides.count; i += 1) {
  const slide = presentation.slides.getItem(i);
  const png = await slide.export({ format: "png" });
  await saveBlobLike(png, path.join(scratchDir, `slide-${i + 1}.png`));
  const layout = await slide.export({ format: "layout" });
  fs.writeFileSync(
    path.join(scratchDir, `slide-${i + 1}.layout.json`),
    JSON.stringify(layout, null, 2),
    "utf8",
  );
}

const loaded = await PresentationFile.importPptx(await FileBlob.load(outputPptx));
for (let i = 0; i < loaded.slides.count; i += 1) {
  const slide = loaded.slides.getItem(i);
  const png = await slide.export({ format: "png" });
  await saveBlobLike(png, path.join(scratchDir, `pptx-slide-${i + 1}.png`));
}

console.log(JSON.stringify({ outputPptx, scriptPath, scratchDir }, null, 2));
