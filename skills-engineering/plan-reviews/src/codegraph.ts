/**
 * Code Structure Graph Generator
 *
 * Parses TypeScript source files in plan-reviews/src/ and generates
 * an interactive architecture graph showing:
 *   - File dependency graph (imports/exports)
 *   - Key functions/classes per file
 *   - Data flow direction
 *   - Architectural layers
 *
 * Usage:
 *   npx tsx src/cli.ts codegraph
 *   npx tsx src/cli.ts codegraph --output ./architecture.html
 */

import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Walk upward to find project root (has .plan-reviews/ or .codebuddy/)
function discoverProjectRoot(): string {
	let dir = process.cwd();
	for (let i = 0; i < 10; i++) {
		if (fs.existsSync(path.join(dir, ".plan-reviews")) || fs.existsSync(path.join(dir, ".codebuddy"))) {
			return dir;
		}
		const parent = path.dirname(dir);
		if (parent === dir) break;
		dir = parent;
	}
	return process.cwd();
}

// ─── TypeScript source analysis ────────────────────────────────────

interface FileNode {
	id: string;
	path: string;          // relative to src/
	name: string;          // file name
	layer: string;         // architectural layer
	description: string;   // what this file does
	exports: ExportItem[]; // what it exports
	imports: ImportItem[]; // what it imports (from project)
	externalImports: string[]; // external packages
}

interface ExportItem {
	name: string;
	kind: "class" | "function" | "interface" | "type" | "variable" | "enum";
}

interface ImportItem {
	name: string;
	from: string; // target file name (resolved)
	kind: "named" | "default" | "type";
}

interface GraphEdge {
	from: string;   // source file id
	to: string;     // target file id
	label: string;  // what's being imported
	color: string;
}

// ─── Manual architecture definition (more reliable than regex parsing) ──

const FILES: FileNode[] = [
	{
		id: "types",
		path: "src/types.ts",
		name: "types.ts",
		layer: "Foundation",
		description: "纯类型定义层——定义 PlanEntity、PlanRelation、SearchQuery 等所有接口/类型，零依赖",
		exports: [
			{ name: "PlanSections", kind: "interface" },
			{ name: "PlanArtifact", kind: "interface" },
			{ name: "PlanResolution", kind: "type" },
			{ name: "PlanEntity", kind: "interface" },
			{ name: "PlanEntityType", kind: "type" },
			{ name: "PlanRelation", kind: "interface" },
			{ name: "PlanRelationType", kind: "type" },
			{ name: "GraphSearchResult", kind: "interface" },
			{ name: "PlanChunk", kind: "interface" },
			{ name: "EmbeddedChunk", kind: "interface" },
			{ name: "SearchQuery", kind: "interface" },
			{ name: "SemanticHit", kind: "interface" },
			{ name: "SearchResponse", kind: "interface" },
			{ name: "SyncEvent", kind: "interface" },
			{ name: "SyncStats", kind: "interface" },
			{ name: "KbPlan", kind: "interface" },
			{ name: "KbSyncState", kind: "interface" },
			{ name: "KbStats", kind: "interface" },
			{ name: "KbIndexData", kind: "interface" },
		],
		imports: [],
		externalImports: [],
	},
	{
		id: "config",
		path: "src/config.ts",
		name: "config.ts",
		layer: "Config",
		description: "配置加载——从环境变量 + env/secrets.json 读取 Embedding API 配置，自动发现项目根目录",
		exports: [
			{ name: "PlanReviewsConfig", kind: "interface" },
			{ name: "loadConfig", kind: "function" },
		],
		imports: [],
		externalImports: ["node:fs", "node:path"],
	},
	{
		id: "store",
		path: "src/store.ts",
		name: "store.ts",
		layer: "Core Storage",
		description: "内存存储 + JSON 持久化——单文件 .kb-index.json 替代 SQLite，原子写入（tmp + rename）",
		exports: [
			{ name: "PlanStore", kind: "class" },
		],
		imports: [
			{ name: "KbIndexData, KbPlan, ...", from: "types", kind: "type" },
		],
		externalImports: ["node:fs", "node:path"],
	},
	{
		id: "embed",
		path: "src/embed.ts",
		name: "embed.ts",
		layer: "Core Service",
		description: "Embedding API 客户端——OpenAI 兼容接口，纯原生 fetch，无 SDK 依赖",
		exports: [
			{ name: "EmbeddingService", kind: "class" },
		],
		imports: [
			{ name: "PlanReviewsConfig", from: "config", kind: "type" },
		],
		externalImports: [],
	},
	{
		id: "vector",
		path: "src/vector.ts",
		name: "vector.ts",
		layer: "Core Service",
		description: "内存向量索引——余弦相似度搜索，替代 Qdrant，适合低数百条 chunks 的场景",
		exports: [
			{ name: "VectorIndex", kind: "class" },
			{ name: "cosineSimilarity", kind: "function" },
			{ name: "VectorSearchResult", kind: "interface" },
		],
		imports: [
			{ name: "EmbeddedChunk", from: "types", kind: "type" },
		],
		externalImports: [],
	},
	{
		id: "parser",
		path: "src/parser.ts",
		name: "parser.ts",
		layer: "Processing",
		description: "结构化解析——解析 PLAN.md 七段结构 + PLAN-REVIEW-LOG.md 审查结果，纯正则无 LLM",
		exports: [
			{ name: "parsePlan", kind: "function" },
			{ name: "parseReviewLog", kind: "function" },
			{ name: "scanPlansDir", kind: "function" },
			{ name: "getPlanMtime", kind: "function" },
			{ name: "ReviewMetadata", kind: "interface" },
		],
		imports: [
			{ name: "PlanSections, PlanArtifact, ...", from: "types", kind: "type" },
		],
		externalImports: ["node:fs", "node:path"],
	},
	{
		id: "extractor",
		path: "src/extractor.ts",
		name: "extractor.ts",
		layer: "Processing",
		description: "实体提取——76 种技术/服务正则匹配，决策/风险/约束提取，自动构建实体间关系",
		exports: [
			{ name: "extractFromArtifact", kind: "function" },
			{ name: "planToChunks", kind: "function" },
			{ name: "ExtractionOutput", kind: "interface" },
		],
		imports: [
			{ name: "PlanArtifact, PlanEntity, ...", from: "types", kind: "type" },
		],
		externalImports: ["node:crypto"],
	},
	{
		id: "sync",
		path: "src/sync.ts",
		name: "sync.ts",
		layer: "Engine",
		description: "增量同步引擎——扫描 .plan-reviews/ 目录，diff mtime，只重建变化的 plan",
		exports: [
			{ name: "SyncEngine", kind: "class" },
		],
		imports: [
			{ name: "PlanReviewsConfig", from: "config", kind: "type" },
			{ name: "PlanArtifact, SyncStats, ...", from: "types", kind: "type" },
			{ name: "scanPlansDir, getPlanMtime", from: "parser", kind: "named" },
			{ name: "extractFromArtifact, planToChunks", from: "extractor", kind: "named" },
			{ name: "PlanStore", from: "store", kind: "type" },
			{ name: "EmbeddingService", from: "embed", kind: "type" },
			{ name: "VectorIndex", from: "vector", kind: "type" },
		],
		externalImports: ["node:path", "node:crypto"],
	},
	{
		id: "search",
		path: "src/search.ts",
		name: "search.ts",
		layer: "Engine",
		description: "统一搜索入口——语义搜索（向量相似度）+ 图谱搜索（实体关系遍历），双路并行",
		exports: [
			{ name: "SearchEngine", kind: "class" },
		],
		imports: [
			{ name: "PlanStore", from: "store", kind: "type" },
			{ name: "EmbeddingService", from: "embed", kind: "type" },
			{ name: "VectorIndex", from: "vector", kind: "type" },
			{ name: "SearchQuery, SearchResponse, ...", from: "types", kind: "type" },
		],
		externalImports: [],
	},
	{
		id: "index",
		path: "src/index.ts",
		name: "index.ts",
		layer: "Entry Point",
		description: "主入口——PlanReviewsKB 门面类，聚合所有引擎，提供 init/sync/search/reset/stats API",
		exports: [
			{ name: "PlanReviewsKB", kind: "class" },
			{ name: "PlanReviewsConfig", kind: "type" },
			{ name: "SearchQuery, SearchResponse, ...", kind: "type" },
		],
		imports: [
			{ name: "loadConfig, PlanReviewsConfig", from: "config", kind: "named" },
			{ name: "PlanStore", from: "store", kind: "named" },
			{ name: "EmbeddingService", from: "embed", kind: "named" },
			{ name: "VectorIndex", from: "vector", kind: "named" },
			{ name: "SearchEngine", from: "search", kind: "named" },
			{ name: "SyncEngine", from: "sync", kind: "named" },
			{ name: "SearchQuery, ...", from: "types", kind: "type" },
		],
		externalImports: [],
	},
	{
		id: "cli",
		path: "src/cli.ts",
		name: "cli.ts",
		layer: "Entry Point",
		description: "CLI 入口——sync/search/stats/reset/visualize 命令分发",
		exports: [],
		imports: [
			{ name: "PlanReviewsKB", from: "index", kind: "named" },
			{ name: "generateKnowledgeGraph", from: "visualize", kind: "named" },
		],
		externalImports: [],
	},
	{
		id: "visualize",
		path: "src/visualize.ts",
		name: "visualize.ts",
		layer: "Visualization",
		description: "知识图谱可视化——读取 .kb-index.json，生成交互式 D3.js 力导向图 HTML",
		exports: [
			{ name: "generateKnowledgeGraph", kind: "function" },
			{ name: "VisualizeOptions", kind: "interface" },
		],
		imports: [
			{ name: "KbIndexData, PlanEntity, ...", from: "types", kind: "type" },
			{ name: "loadConfig", from: "config", kind: "named" },
		],
		externalImports: ["node:fs", "node:path"],
	},
];

// ─── Build graph edges from imports ───────────────────────────────

function buildEdges(): GraphEdge[] {
	const edges: GraphEdge[] = [];
	const seen = new Set<string>();

	for (const file of FILES) {
		for (const imp of file.imports) {
			const key = `${file.id}→${imp.from}`;
			if (seen.has(key)) continue;
			seen.add(key);

			edges.push({
				from: file.id,
				to: imp.from,
				label: imp.name,
				color: imp.kind === "type" ? "#f39c12" : "#3498db",
			});
		}
	}

	return edges;
}

// ─── Layer colors ─────────────────────────────────────────────────

const LAYER_COLORS: Record<string, string> = {
	"Foundation":     "#7f8c8d",
	"Config":         "#e67e22",
	"Core Storage":   "#9b59b6",
	"Core Service":   "#3498db",
	"Processing":     "#1abc9c",
	"Engine":         "#2ecc71",
	"Entry Point":    "#e74c3c",
	"Visualization":  "#e91e63",
};

// Pre-computed darker versions for node backgrounds (avoid d3.color().darker() runtime risk)
const LAYER_DARK_COLORS: Record<string, string> = {
	"Foundation":     "#1a1d1d",
	"Config":         "#1f1407",
	"Core Storage":   "#1b1122",
	"Core Service":   "#0a1d2d",
	"Processing":     "#05211c",
	"Engine":         "#082314",
	"Entry Point":    "#2d0c08",
	"Visualization":  "#2d0714",
};

// Pre-computed rgba versions for layer backgrounds (avoid 8-digit hex issues)
const LAYER_BG_RGBA: Record<string, string> = {
	"Foundation":     "rgba(127,140,141,0.05)",
	"Config":         "rgba(230,126,34,0.05)",
	"Core Storage":   "rgba(155,89,182,0.05)",
	"Core Service":   "rgba(52,152,219,0.05)",
	"Processing":     "rgba(26,188,156,0.05)",
	"Engine":         "rgba(46,204,113,0.05)",
	"Entry Point":    "rgba(231,76,60,0.05)",
	"Visualization":  "rgba(233,30,99,0.05)",
};

// Pre-computed rgba for layer label backgrounds
const LAYER_LABEL_BG: Record<string, string> = {
	"Foundation":     "rgba(127,140,141,0.20)",
	"Config":         "rgba(230,126,34,0.20)",
	"Core Storage":   "rgba(155,89,182,0.20)",
	"Core Service":   "rgba(52,152,219,0.20)",
	"Processing":     "rgba(26,188,156,0.20)",
	"Engine":         "rgba(46,204,113,0.20)",
	"Entry Point":    "rgba(231,76,60,0.20)",
	"Visualization":  "rgba(233,30,99,0.20)",
};

const LAYER_ORDER = [
	"Foundation",
	"Config",
	"Core Storage",
	"Core Service",
	"Processing",
	"Engine",
	"Entry Point",
	"Visualization",
];

// ─── Generate HTML ────────────────────────────────────────────────

export interface CodeGraphOptions {
	output?: string;
	projectRoot?: string;
}

export function generateCodeGraph(options: CodeGraphOptions = {}): string {
	const projectRoot = options.projectRoot ?? discoverProjectRoot();
	const outputPath = options.output ?? path.join(
		projectRoot,
		".plan-reviews",
		"code-graph.html",
	);

	// Ensure output directory exists
	const outDir = path.dirname(outputPath);
	if (!fs.existsSync(outDir)) {
		fs.mkdirSync(outDir, { recursive: true });
	}

	const edges = buildEdges();
	const html = buildHtml(FILES, edges);
	fs.writeFileSync(outputPath, html, "utf-8");
	return outputPath;
}

function buildHtml(files: FileNode[], edges: GraphEdge[]): string {
	const filesJson = JSON.stringify(files);
	const edgesJson = JSON.stringify(edges);
	const layerColorsJson = JSON.stringify(LAYER_COLORS);
	const layerDarkColorsJson = JSON.stringify(LAYER_DARK_COLORS);
	const layerBgRgbaJson = JSON.stringify(LAYER_BG_RGBA);
	const layerLabelBgJson = JSON.stringify(LAYER_LABEL_BG);
	const layerOrderJson = JSON.stringify(LAYER_ORDER);

	return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>plan-reviews — Code Architecture Graph</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }

  :root {
    --bg: #0d1117;
    --panel-bg: #161b22;
    --text: #c9d1d9;
    --text-dim: #8b949e;
    --border: #30363d;
    --accent: #58a6ff;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    height: 100vh;
    display: flex;
    overflow: hidden;
  }

  /* ── Sidebar ──────────────────────────────── */
  aside {
    width: 320px;
    min-width: 320px;
    background: var(--panel-bg);
    display: flex;
    flex-direction: column;
    border-right: 1px solid var(--border);
    z-index: 10;
  }

  aside header {
    padding: 20px 18px 16px;
    border-bottom: 1px solid var(--border);
  }

  aside header h1 {
    font-size: 18px;
    font-weight: 600;
    letter-spacing: 0.3px;
    margin-bottom: 4px;
  }

  aside header .subtitle {
    font-size: 12px;
    color: var(--text-dim);
  }

  /* File detail panel */
  .file-detail {
    flex: 1;
    overflow-y: auto;
    padding: 16px 18px;
  }

  .file-detail .placeholder {
    color: var(--text-dim);
    font-size: 13px;
    font-style: italic;
    padding: 20px 0;
    text-align: center;
  }

  .fd-header {
    margin-bottom: 14px;
  }

  .fd-name {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }

  .fd-layer {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: 600;
    margin-bottom: 8px;
  }

  .fd-desc {
    font-size: 12px;
    color: var(--text-dim);
    line-height: 1.5;
  }

  .fd-section {
    margin-top: 16px;
  }

  .fd-section h4 {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--text-dim);
    margin-bottom: 8px;
  }

  .fd-item {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 3px 0;
    font-size: 12px;
    font-family: "SF Mono", "Fira Code", monospace;
  }

  .fd-tag {
    display: inline-block;
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    background: rgba(255,255,255,0.08);
    color: var(--text-dim);
  }

  .fd-tag.class { background: rgba(88,166,255,0.15); color: #58a6ff; }
  .fd-tag.function { background: rgba(63,185,80,0.15); color: #3fb950; }
  .fd-tag.interface { background: rgba(210,168,0,0.15); color: #d2a800; }
  .fd-tag.type { background: rgba(188,140,255,0.15); color: #bc8cff; }

  /* Deps list */
  .fd-dep {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 0;
    font-size: 11px;
    font-family: "SF Mono", "Fira Code", monospace;
  }

  .fd-dep .arrow { color: var(--text-dim); }
  .fd-dep .dep-file { color: #58a6ff; cursor: pointer; }
  .fd-dep .dep-file:hover { text-decoration: underline; }
  .fd-dep .dep-items { color: var(--text-dim); font-size: 10px; }

  /* Stats */
  .sidebar-stats {
    padding: 12px 18px;
    border-top: 1px solid var(--border);
    font-size: 11px;
    color: var(--text-dim);
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }

  .sidebar-stats strong { color: var(--text); }

  /* ── Main graph area ───────────────────────── */
  main {
    flex: 1;
    position: relative;
    background: var(--bg);
    overflow: hidden;
    cursor: grab;
  }

  main:active { cursor: grabbing; }

  svg { width: 100%; height: 100%; }

  .layer-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    opacity: 0.5;
  }

  .node-group { cursor: pointer; }

  .node-group rect {
    rx: 6px;
    transition: fill 0.15s, stroke 0.15s;
    stroke-width: 1.5px;
  }

  .node-group:hover rect {
    stroke-width: 2.5px;
    filter: brightness(1.2);
  }

  .node-group text {
    font-family: "SF Mono", "Fira Code", monospace;
    font-size: 11px;
    fill: #c9d1d9;
    pointer-events: none;
  }

  .node-group text.fn {
    font-size: 9px;
    fill: #8b949e;
  }

  .edge-group line {
    stroke-width: 1.5px;
    stroke-opacity: 0.4;
  }

  .edge-group text {
    font-family: "SF Mono", "Fira Code", monospace;
    font-size: 8px;
    fill: #8b949e;
    paint-order: stroke;
    stroke: #0d1117;
    stroke-width: 3px;
  }

  .tooltip {
    position: absolute;
    max-width: 300px;
    padding: 10px 12px;
    background: rgba(22,27,34,0.97);
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 12px;
    line-height: 1.5;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.12s;
    z-index: 100;
  }

  .tooltip.visible { opacity: 1; }

  .controls-hint {
    position: absolute;
    bottom: 16px;
    right: 20px;
    font-size: 11px;
    color: var(--text-dim);
    pointer-events: none;
  }
</style>
</head>
<body>

<aside>
  <header>
    <h1>📐 plan-reviews 代码架构</h1>
    <div class="subtitle">文件依赖 · 导出函数 · 数据流向</div>
  </header>
  <div class="file-detail" id="file-detail">
    <div class="placeholder">👆 点击左侧节点查看详情</div>
  </div>
  <div class="sidebar-stats" id="stats"></div>
</aside>

<main id="graph-container">
  <div class="tooltip" id="tooltip"></div>
  <div class="controls-hint">🖱 点击查看 | 拖拽平移 | 滚轮缩放 | 悬停看类型</div>
</main>

<script>
(function() { "use strict";
try {

const FILES = ${filesJson};
const EDGES = ${edgesJson};
const LAYER_COLORS = ${layerColorsJson};
const LAYER_DARK  = ${layerDarkColorsJson};
const LAYER_BG    = ${layerBgRgbaJson};
const LAYER_TAG   = ${layerLabelBgJson};
const LAYER_ORDER = ${layerOrderJson};

const NS = "http://www.w3.org/2000/svg";

const container = document.getElementById("graph-container");
const W = Math.max(container.clientWidth, 100);
const H = Math.max(container.clientHeight, 100);

// ─── Helper: create SVG element ────────────────────────────────────

function el(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  if (attrs) Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, v));
  if (parent) parent.appendChild(e);
  return e;
}

// ─── Layout: layers stacked top→bottom, files in rows ─────────────

const layerHeight = 240;
const layers = {};
LAYER_ORDER.forEach(name => { layers[name] = []; });
FILES.forEach(f => { if (layers[f.layer]) layers[f.layer].push(f); });
const activeLayers = LAYER_ORDER.filter(l => layers[l].length > 0);

const nodePositions = {};
let layerY = 60;
const gap = 30;

activeLayers.forEach(layerName => {
  const group = layers[layerName];
  const count = group.length;
  const totalWidth = count * 180 + (count - 1) * 30;
  const startX = (W - totalWidth) / 2;
  group.forEach((f, i) => {
    nodePositions[f.id] = { x: startX + i * 210, y: layerY, w: 180, h: 180, layer: layerName };
  });
  layerY += layerHeight + gap;
});

const totalH = layerY + 40;
const viewH = Math.max(H, totalH);

// ─── SVG setup ─────────────────────────────────────────────────────

const svg = el("svg", { viewBox: [0, 0, W, viewH].join(" "), width: "100%", height: "100%" }, container);

const gMain = el("g", {}, svg);
let gTransform = { x: 0, y: 0, k: 1 };
function applyTransform() {
  gMain.setAttribute("transform", "translate(" + gTransform.x + "," + gTransform.y + ") scale(" + gTransform.k + ")");
}

// ─── Zoom (mouse wheel) ───────────────────────────────────────────

container.addEventListener("wheel", function(e) {
  e.preventDefault();
  const rect = container.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  const factor = e.deltaY < 0 ? 1.08 : 1 / 1.08;
  const newK = Math.min(3, Math.max(0.2, gTransform.k * factor));
  gTransform.x = mx - (mx - gTransform.x) * (newK / gTransform.k);
  gTransform.y = my - (my - gTransform.y) * (newK / gTransform.k);
  gTransform.k = newK;
  applyTransform();
}, { passive: false });

// ─── Pan (mouse drag) ─────────────────────────────────────────────

let dragging = false, dragStart = { x: 0, y: 0 }, dragOrig = { x: 0, y: 0 };
container.addEventListener("mousedown", function(e) {
  if (e.target === container || e.target === svg || e.target.tagName === "rect" && e.target.closest(".layers")) {
    dragging = true;
    dragStart = { x: e.clientX, y: e.clientY };
    dragOrig = { x: gTransform.x, y: gTransform.y };
    container.style.cursor = "grabbing";
  }
});
window.addEventListener("mousemove", function(e) {
  if (!dragging) return;
  gTransform.x = dragOrig.x + (e.clientX - dragStart.x);
  gTransform.y = dragOrig.y + (e.clientY - dragStart.y);
  applyTransform();
});
window.addEventListener("mouseup", function() {
  dragging = false;
  container.style.cursor = "grab";
});

// ─── Arrow markers ─────────────────────────────────────────────────

const defs = el("defs", {}, svg);
["#3498db", "#f39c12"].forEach(color => {
  const id = "arrow-" + color.replace("#", "");
  const m = el("marker", { id: id, viewBox: "0 0 8 8", refX: "8", refY: "4", markerWidth: "5", markerHeight: "5", orient: "auto" }, defs);
  el("path", { d: "M0,0 L8,4 L0,8 z", fill: color, opacity: "0.5" }, m);
});

// ─── Layer backgrounds + labels ────────────────────────────────────

const layerGroup = el("g", { class: "layers" }, gMain);
activeLayers.forEach(layerName => {
  const group = layers[layerName];
  const first = nodePositions[group[0].id];
  const last = nodePositions[group[group.length - 1].id];
  const x1 = first.x - 40, x2 = last.x + last.w + 40;
  const y1 = first.y - 50, y2 = first.y + first.h + 20;

  el("rect", {
    x: x1, y: y1, width: x2 - x1, height: y2 - y1, rx: "8",
    fill: LAYER_BG[layerName] || "rgba(255,255,255,0.03)",
    stroke: LAYER_COLORS[layerName] || "#444", "stroke-opacity": "0.15", "stroke-width": "1"
  }, layerGroup);

  el("text", {
    x: x1 + 12, y: y1 + 20, fill: LAYER_COLORS[layerName],
    "font-size": "13", "font-weight": "700", class: "layer-label"
  }, layerGroup).textContent = layerName;
});

// ─── Render edges ─────────────────────────────────────────────────

function getNodeCenter(id) {
  const p = nodePositions[id];
  return { x: p.x + p.w / 2, y: p.y + p.h / 2 };
}

const edgeGroup = el("g", { class: "edge-group" }, gMain);

EDGES.forEach(edge => {
  const fC = getNodeCenter(edge.from);
  const tC = getNodeCenter(edge.to);
  const fP = nodePositions[edge.from];
  const tP = nodePositions[edge.to];
  let fx, fy, tx, ty;

  if (fC.y < tC.y)      { fx = fC.x; fy = fP.y + fP.h; tx = tC.x; ty = tP.y; }
  else if (fC.y > tC.y) { fx = fC.x; fy = fP.y;        tx = tC.x; ty = tP.y + tP.h; }
  else                   { fx = fP.x + fP.w; fy = fC.y;  tx = tP.x; ty = tC.y; }

  const midY = (fy + ty) / 2;
  const midX = (fx + tx) / 2;
  const d = "M" + fx + "," + fy + " Q" + fx + "," + midY + " " + midX + "," + midY + " Q" + tx + "," + midY + " " + tx + "," + ty;

  el("path", {
    d: d, fill: "none", stroke: edge.color, "stroke-width": "1.5",
    "stroke-opacity": "0.35", "marker-end": "url(#arrow-" + edge.color.replace("#", "") + ")"
  }, edgeGroup);

  const lbl = edge.label.length > 24 ? edge.label.slice(0, 22) + "…" : edge.label;
  const t = el("text", {
    x: (fC.x + tC.x) / 2, y: midY - 4, "text-anchor": "middle",
    "font-family": "SF Mono,Fira Code,monospace", "font-size": "8", fill: "#8b949e"
  }, edgeGroup);
  t.textContent = lbl;
});

// ─── Render nodes ──────────────────────────────────────────────────

const nodeGroup = el("g", { class: "node-group" }, gMain);

FILES.forEach(d => {
  const pos = nodePositions[d.id];
  const gFile = el("g", { class: "file", cursor: "pointer" }, nodeGroup);

  // Background
  el("rect", {
    x: pos.x, y: pos.y, width: pos.w, height: pos.h,
    fill: LAYER_DARK[d.layer] || "#1a1a2e",
    stroke: LAYER_COLORS[d.layer] || "#555", "stroke-opacity": "0.5", "stroke-width": "1.5"
  }, gFile);

  // File name
  const tName = el("text", {
    x: pos.x + 10, y: pos.y + 22, "font-family": "SF Mono,Fira Code,monospace",
    "font-size": "13", "font-weight": "700", fill: "#e6edf3"
  }, gFile);
  tName.textContent = d.name;

  // Layer tag bg
  el("rect", {
    x: pos.x + 10, y: pos.y + 30, width: d.layer.length * 9 + 12, height: "16", rx: "3",
    fill: LAYER_TAG[d.layer] || "rgba(255,255,255,0.1)"
  }, gFile);

  // Layer tag text
  const tLayer = el("text", {
    x: pos.x + 16, y: pos.y + 42, "font-size": "9", "font-weight": "600", fill: LAYER_COLORS[d.layer]
  }, gFile);
  tLayer.textContent = d.layer;

  // Exports preview (top 4)
  d.exports.slice(0, 4).forEach((exp, i) => {
    const tExp = el("text", {
      x: pos.x + 10, y: pos.y + 62 + i * 16,
      "font-family": "SF Mono,Fira Code,monospace", "font-size": "9",
      fill: exp.kind === "class" ? "#58a6ff" : exp.kind === "function" ? "#3fb950" : "#bc8cff",
      class: "fn"
    }, gFile);
    tExp.textContent = exp.name.length > 22 ? exp.name.slice(0, 20) + "…" : exp.name;
  });

  if (d.exports.length > 4) {
    const tMore = el("text", {
      x: pos.x + 10, y: pos.y + 62 + 4 * 16,
      "font-family": "SF Mono,Fira Code,monospace", "font-size": "8", fill: "#484f58", class: "fn"
    }, gFile);
    tMore.textContent = "+" + (d.exports.length - 4) + " more…";
  }

  // Dependency count
  if (d.imports.length > 0) {
    const tDeps = el("text", {
      x: pos.x + pos.w - 10, y: pos.y + pos.h - 10, "text-anchor": "end",
      "font-size": "9", fill: "#8b949e"
    }, gFile);
    tDeps.textContent = "← " + d.imports.length + " deps";
  }

  // Events
  gFile.addEventListener("click", function() { showFileDetail(d); });
  gFile.addEventListener("mouseenter", function(e) { showTooltip(e, d); });
  gFile.addEventListener("mousemove", function(e) {
    var tt = document.getElementById("tooltip");
    tt.style.left = (e.offsetX + 14) + "px";
    tt.style.top = (e.offsetY - 10) + "px";
  });
  gFile.addEventListener("mouseleave", function() {
    document.getElementById("tooltip").classList.remove("visible");
  });
});

// ─── Sidebar detail panel ──────────────────────────────────────────

const detailEl = document.getElementById("file-detail");
const filesById = {};
FILES.forEach(f => { filesById[f.id] = f; });

function showFileDetail(d) {
  var color = LAYER_COLORS[d.layer] || "#888";
  var h = '<div class="fd-header">';
  h += '<div class="fd-name" style="font-family:monospace">' + d.name + '</div>';
  h += '<span class="fd-layer" style="background:' + color + '22;color:' + color + '">' + d.layer + '</span>';
  h += '<div class="fd-desc">' + d.description + '</div></div>';

  if (d.exports.length > 0) {
    h += '<div class="fd-section"><h4>📤 导出 (' + d.exports.length + ')</h4>';
    d.exports.forEach(function(exp) {
      h += '<div class="fd-item"><span class="fd-tag ' + exp.kind + '">' + exp.kind + '</span>' + exp.name + '</div>';
    });
    h += '</div>';
  }

  if (d.imports.length > 0) {
    h += '<div class="fd-section"><h4>📥 项目依赖 (' + d.imports.length + ')</h4>';
    d.imports.forEach(function(imp) {
      h += '<div class="fd-dep"><span class="arrow">↓</span>' +
        '<span class="dep-file" onclick="jumpToFile(\\'' + imp.from + '\\')">' + imp.from + '.ts</span>' +
        '<span class="dep-items">(' + imp.name + ')</span></div>';
    });
    h += '</div>';
  }

  if (d.externalImports.length > 0) {
    h += '<div class="fd-section"><h4>📦 外部依赖</h4>';
    d.externalImports.forEach(function(ext) {
      h += '<div class="fd-dep" style="color:#8b949e">' + ext + '</div>';
    });
    h += '</div>';
  }

  detailEl.innerHTML = h;
}

window.jumpToFile = function(fileId) {
  var f = filesById[fileId];
  if (f) showFileDetail(f);
};

// ─── Tooltip ───────────────────────────────────────────────────────

function showTooltip(event, d) {
  var color = LAYER_COLORS[d.layer] || "#888";
  var tt = document.getElementById("tooltip");
  tt.innerHTML =
    '<span style="display:inline-block;padding:1px 6px;border-radius:3px;font-size:10px;font-weight:600;background:' + color + '22;color:' + color + ';margin-bottom:4px;">' + d.layer + '</span>' +
    '<div style="font-weight:600;font-size:13px;margin-bottom:2px;font-family:monospace">' + d.name + '</div>' +
    '<div style="color:#8b949e;font-size:11px;">' + d.description.slice(0, 120) + '</div>' +
    '<div style="margin-top:4px;font-size:10px;color:#8b949e;">📤 ' + d.exports.length + ' exports  📥 ' + d.imports.length + ' deps</div>';
  tt.style.left = (event.offsetX + 14) + "px";
  tt.style.top = (event.offsetY - 10) + "px";
  tt.classList.add("visible");
}

// ─── Stats ─────────────────────────────────────────────────────────

document.getElementById("stats").innerHTML =
  '<span>📁 <strong>' + FILES.length + '</strong> 文件</span>' +
  '<span>📐 <strong>' + activeLayers.length + '</strong> 层</span>' +
  '<span>🔗 <strong>' + EDGES.length + '</strong> 依赖边</span>';

if (FILES.length > 0) showFileDetail(FILES[0]);

} catch (err) {
  document.getElementById("file-detail").innerHTML =
    '<div style="color:#f44;padding:16px;"><strong>渲染错误</strong><pre style="margin-top:8px;font-size:11px;white-space:pre-wrap;">' + err.message + '\\n\\n打开浏览器控制台查看详细信息。</pre></div>';
  console.error("[code-graph] render error:", err);
}
})();
</script>
</body>
</html>`;
}
