/**
 * Knowledge Graph Visualizer for .plan-reviews
 *
 * Reads .kb-index.json and generates an interactive D3.js force-directed
 * graph as a self-contained HTML file.
 *
 * Usage:
 *   npx tsx src/cli.ts visualize
 *   npx tsx src/cli.ts visualize --output ./my-graph.html
 */

import * as fs from "node:fs";
import * as path from "node:path";
import type { KbIndexData, PlanEntity, PlanRelation } from "./types.js";
import { loadConfig } from "./config.js";

// ─── Color palette for entity types ─────────────────────────────────

const ENTITY_COLORS: Record<string, string> = {
	goal:          "#e74c3c",  // red
	constraint:    "#f39c12",  // orange
	decision:      "#2ecc71",  // green
	risk:          "#e91e63",  // pink
	technology:    "#3498db",  // blue
	service:       "#9b59b6",  // purple
	out_of_scope:  "#95a5a6",  // grey
	pattern:       "#1abc9c",  // teal
	flaw:          "#c0392b",  // dark red
	reviewer:      "#8e44ad",  // dark purple
};

const RELATION_COLORS: Record<string, string> = {
	uses:        "#3498db",
	addresses:   "#2ecc71",
	mitigates:   "#27ae60",
	constrains:  "#e67e22",
	depends_on:  "#9b59b6",
	found:       "#e74c3c",
	accepted:    "#27ae60",
	rejected:    "#c0392b",
	references:  "#7f8c8d",
};

const ENTITY_LABELS: Record<string, string> = {
	goal:          "目标",
	constraint:    "约束",
	decision:      "决策",
	risk:          "风险",
	technology:    "技术",
	service:       "服务",
	out_of_scope:  "范围外",
	pattern:       "模式",
	flaw:          "缺陷",
	reviewer:      "审查者",
};

const RELATION_LABELS: Record<string, string> = {
	uses:        "使用",
	addresses:   "应对",
	mitigates:   "缓解",
	constrains:  "约束",
	depends_on:  "依赖",
	found:       "发现",
	accepted:    "接受",
	rejected:    "拒绝",
	references:  "引用",
};

// ─── Main generator ─────────────────────────────────────────────────

export interface VisualizeOptions {
	/** Output HTML file path. Default: .plan-reviews/knowledge-graph.html */
	output?: string;
	/** Project root. Default: cwd */
	projectRoot?: string;
}

export function generateKnowledgeGraph(options: VisualizeOptions = {}): string {
	const config = loadConfig({ projectRoot: options.projectRoot });
	const indexPath = config.indexPath;

	if (!fs.existsSync(indexPath)) {
		throw new Error(
			`No .kb-index.json found at ${indexPath}. Run "npm run sync" first.`,
		);
	}

	const raw = fs.readFileSync(indexPath, "utf-8");
	const data: KbIndexData = JSON.parse(raw);

	if (data.entities.length === 0) {
		throw new Error("No entities found in .kb-index.json. Run sync first.");
	}

	const outputPath = options.output ?? path.join(config.projectRoot, ".plan-reviews", "knowledge-graph.html");
	const html = buildHtml(data, config.projectRoot);

	fs.writeFileSync(outputPath, html, "utf-8");
	return outputPath;
}

// ─── HTML builder ────────────────────────────────────────────────────

function buildHtml(data: KbIndexData, _projectRoot: string): string {
	const entitiesJson = JSON.stringify(data.entities);
	const relationsJson = JSON.stringify(data.relations);
	const plansJson = JSON.stringify(data.plans);

	return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Plan Reviews — Knowledge Graph</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }

  :root {
    --bg: #1a1a2e;
    --panel-bg: #16213e;
    --text: #e0e0e0;
    --text-dim: #888;
    --accent: #3498db;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    overflow: hidden;
    height: 100vh;
    display: flex;
  }

  /* ── Sidebar ──────────────────────────────── */
  aside {
    width: 280px;
    min-width: 280px;
    background: var(--panel-bg);
    display: flex;
    flex-direction: column;
    border-right: 1px solid rgba(255,255,255,0.08);
    z-index: 10;
  }

  aside header {
    padding: 20px 18px 12px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }

  aside header h1 {
    font-size: 18px;
    font-weight: 600;
    letter-spacing: 0.3px;
  }

  aside header .subtitle {
    font-size: 12px;
    color: var(--text-dim);
    margin-top: 4px;
  }

  /* Search */
  .search-box {
    padding: 12px 18px;
  }

  .search-box input {
    width: 100%;
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid rgba(255,255,255,0.1);
    background: rgba(255,255,255,0.05);
    color: var(--text);
    font-size: 13px;
    outline: none;
    transition: border-color 0.2s;
  }

  .search-box input:focus {
    border-color: var(--accent);
  }

  /* Legend */
  .legend {
    flex: 1;
    overflow-y: auto;
    padding: 8px 18px 18px;
  }

  .legend h3 {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--text-dim);
    margin-bottom: 10px;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 0;
    font-size: 12px;
    cursor: pointer;
    opacity: 0.7;
    transition: opacity 0.15s;
  }

  .legend-item:hover { opacity: 1; }
  .legend-item.active { opacity: 1; font-weight: 600; }

  .legend-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .legend-count {
    margin-left: auto;
    color: var(--text-dim);
    font-size: 11px;
  }

  /* Stats footer */
  .stats {
    padding: 12px 18px;
    border-top: 1px solid rgba(255,255,255,0.06);
    font-size: 11px;
    color: var(--text-dim);
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }

  .stats span { white-space: nowrap; }
  .stats strong { color: var(--text); }

  /* ── Main graph area ───────────────────────── */
  main {
    flex: 1;
    position: relative;
    cursor: grab;
  }

  main:active { cursor: grabbing; }

  svg { width: 100%; height: 100%; }

  /* Node styles */
  .node circle {
    stroke-width: 2px;
    stroke-opacity: 0.8;
    transition: r 0.2s, stroke-width 0.2s;
  }

  .node text {
    font-size: 10px;
    fill: #ccc;
    pointer-events: none;
    text-shadow: 0 1px 3px rgba(0,0,0,0.7);
    transition: font-size 0.2s, fill 0.2s;
  }

  .node:hover circle { stroke-width: 3px; }
  .node:hover text { font-size: 12px; fill: #fff; font-weight: 600; }

  .node.dimmed { opacity: 0.15; }
  .node.dimmed circle { stroke-width: 1px; }

  /* Edge styles */
  .edge line {
    stroke-opacity: 0.35;
    transition: stroke-opacity 0.25s;
  }

  .edge text {
    font-size: 10px;
    fill: #aaa;
    font-weight: 500;
    pointer-events: none;
    transition: fill 0.25s, font-size 0.25s;
    paint-order: stroke;
    stroke: rgba(26,26,46,0.85);
    stroke-width: 3px;
  }

  .edge.dimmed line { stroke-opacity: 0.06; }
  .edge.dimmed text { opacity: 0.08; }

  .edge.highlighted line { stroke-opacity: 0.8; stroke-width: 2.5px; }
  .edge.highlighted text { font-size: 12px; fill: #fff; font-weight: 700; }

  .edge.clickable line { cursor: pointer; stroke-width: 8px; stroke: transparent; }

  /* Tooltip */
  .tooltip {
    position: absolute;
    max-width: 320px;
    padding: 12px 14px;
    background: rgba(22,33,62,0.96);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 8px;
    font-size: 12px;
    line-height: 1.5;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.15s;
    z-index: 100;
    backdrop-filter: blur(8px);
  }

  .tooltip.visible { opacity: 1; }

  .tooltip .tt-type {
    display: inline-block;
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    margin-bottom: 6px;
  }

  .tooltip .tt-name {
    font-weight: 600;
    font-size: 13px;
    margin-bottom: 4px;
    color: #fff;
  }

  .tooltip .tt-desc {
    color: #aaa;
    font-size: 11px;
  }

  .tooltip .tt-meta {
    margin-top: 6px;
    color: var(--text-dim);
    font-size: 10px;
  }

  /* Controls hint */
  .controls-hint {
    position: absolute;
    bottom: 16px;
    right: 20px;
    font-size: 11px;
    color: var(--text-dim);
    pointer-events: none;
  }

  /* ── Relation detail panel (in sidebar) ───── */
  .relation-panel {
    flex: 1;
    overflow-y: auto;
    padding: 12px 18px;
    border-top: 1px solid rgba(255,255,255,0.08);
    min-height: 0;
  }

  .rp-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .rp-header h3 {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--text-dim);
    margin: 0;
  }

  #rp-close {
    background: none;
    border: none;
    color: var(--text-dim);
    cursor: pointer;
    font-size: 16px;
    line-height: 1;
    padding: 0 4px;
  }

  #rp-close:hover { color: #fff; }

  .rp-relation {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    padding: 6px 8px;
    margin: 2px 0;
    border-radius: 4px;
    font-size: 11px;
    line-height: 1.45;
    cursor: pointer;
    transition: background 0.15s;
  }

  .rp-relation:hover { background: rgba(255,255,255,0.06); }

  .rp-relation .rp-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    margin-top: 5px;
    flex-shrink: 0;
  }

  .rp-relation .rp-text { color: #ccc; }

  .rp-relation .rp-target {
    font-weight: 600;
  }

  .rp-empty {
    color: var(--text-dim);
    font-size: 11px;
    font-style: italic;
    padding: 8px;
  }
</style>
</head>
<body>

<aside>
  <header>
    <h1>Plan Reviews — 知识图谱</h1>
    <div class="subtitle" id="plan-title">加载中…</div>
  </header>

  <div class="search-box">
    <input type="text" id="search-input" placeholder="搜索实体…" autocomplete="off" />
  </div>

  <div class="legend" id="legend-entities">
    <h3>实体类型</h3>
  </div>

  <div class="legend" id="legend-relations" style="flex:0 0 auto; max-height:200px;">
    <h3>关系类型</h3>
  </div>

  <div class="relation-panel" id="relation-panel" style="display:none;">
    <div class="rp-header">
      <h3 id="rp-title"></h3>
      <button id="rp-close">&times;</button>
    </div>
    <div class="rp-list" id="rp-list"></div>
  </div>

  <div class="stats" id="stats"></div>
</aside>

<main id="graph-container">
  <div class="tooltip" id="tooltip"></div>
  <div class="controls-hint">🖱 拖拽节点 | 滚轮缩放 | 右键平移 | 点击高亮邻域</div>
</main>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
// ─── Embedded data ────────────────────────────────────────────────
const ENTITIES = ${entitiesJson};
const RELATIONS = ${relationsJson};
const PLANS = ${plansJson};

const ENTITY_COLORS = ${JSON.stringify(ENTITY_COLORS)};
const RELATION_COLORS = ${JSON.stringify(RELATION_COLORS)};
const ENTITY_LABELS = ${JSON.stringify(ENTITY_LABELS)};
const RELATION_LABELS = ${JSON.stringify(RELATION_LABELS)};

// ─── Build graph data ─────────────────────────────────────────────

// Entity ID → index map
const entityMap = new Map(ENTITIES.map((e, i) => [e.id, i]));

// Nodes
const nodes = ENTITIES.map((e, i) => ({
  id: e.id,
  index: i,
  type: e.type,
  name: e.name,
  description: e.description,
  planId: e.planId,
  color: ENTITY_COLORS[e.type] || "#666",
}));

// Links (edges)
const links = RELATIONS.map(r => ({
  source: entityMap.get(r.fromEntityId),
  target: entityMap.get(r.toEntityId),
  relation: r.relation,
  relationLabel: RELATION_LABELS[r.relation] || r.relation,
  color: RELATION_COLORS[r.relation] || "#666",
})).filter(l => l.source !== undefined && l.target !== undefined);

// ─── Static layered layout ───────────────────────────────────────

const container = document.getElementById("graph-container");
const W = container.clientWidth;
const H = container.clientHeight;

// Column layout (left → right): constraints | decisions | goal | risks | tech/service | out_of_scope
const LAYOUT = {
  constraint:    { cx: W * 0.08, w: W * 0.14 },
  decision:      { cx: W * 0.26, w: W * 0.16 },
  goal:          { cx: W * 0.46, w: W * 0.10 },
  risk:          { cx: W * 0.60, w: W * 0.14 },
  technology:    { cx: W * 0.78, w: W * 0.10 },
  service:       { cx: W * 0.90, w: W * 0.08 },
  out_of_scope:  { cx: W * 0.78, w: W * 0.16 },
};

// Group nodes by type
const grouped = {};
nodes.forEach(n => {
  if (!grouped[n.type]) grouped[n.type] = [];
  grouped[n.type].push(n);
});

// Assign static (x, y) positions within each column
Object.entries(grouped).forEach(([type, group]) => {
  const col = LAYOUT[type] || { cx: W * 0.5, w: W * 0.3 };
  const topPad = type === "goal" ? H * 0.35 : H * 0.12;
  const spacing = Math.min(70, (H * 0.76) / Math.max(group.length, 1));
  group.forEach((n, i) => {
    const jitterX = (Math.random() - 0.5) * col.w * 0.4;
    n.x = col.cx + jitterX;
    n.y = topPad + i * spacing;
  });
});

// If tech + service + out_of_scope share right region, stagger vertical
const rightTypes = ["technology", "service", "out_of_scope"];
let rightOffset = 0;
rightTypes.forEach(type => {
  const group = grouped[type];
  if (!group) return;
  group.forEach((n, i) => {
    n.x = (type === "service" ? W * 0.90 : W * 0.78) + (Math.random() - 0.5) * 40;
    n.y = H * 0.08 + (rightOffset + i) * 58;
  });
  rightOffset += group.length;
});

// ─── SVG setup ────────────────────────────────────────────────────

const svg = d3.select("#graph-container")
  .append("svg")
  .attr("viewBox", [0, 0, W, H]);

const g = svg.append("g");

svg.call(d3.zoom()
  .scaleExtent([0.2, 4])
  .on("zoom", (event) => {
    g.attr("transform", event.transform);
  }));

// ─── Column headers ──────────────────────────────────────────────

const colGroup = g.append("g").attr("class", "columns");
Object.entries(LAYOUT).forEach(([type, col]) => {
  const count = (grouped[type] || []).length;
  if (count === 0) return;
  colGroup.append("text")
    .attr("x", col.cx)
    .attr("y", 20)
    .attr("text-anchor", "middle")
    .attr("fill", ENTITY_COLORS[type] || "#888")
    .attr("font-size", 13)
    .attr("font-weight", "600")
    .text((ENTITY_LABELS[type] || type) + " (" + count + ")");
  // Subtle column divider
  colGroup.append("line")
    .attr("x1", col.cx - col.w * 0.3)
    .attr("y1", 30)
    .attr("x2", col.cx - col.w * 0.3)
    .attr("y2", H - 10)
    .attr("stroke", "rgba(255,255,255,0.04)")
    .attr("stroke-width", 1);
});

// ─── Arrow markers ──────────────────────────────────────────────

const defs = svg.append("defs");
Object.entries(RELATION_COLORS).forEach(([rel, color]) => {
  defs.append("marker")
    .attr("id", "arrow-" + rel)
    .attr("viewBox", "0 0 8 8")
    .attr("refX", 24)
    .attr("refY", 4)
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("orient", "auto")
    .append("path")
    .attr("d", "M0,0 L0,8 L8,4 z")
    .attr("fill", color)
    .attr("opacity", 0.55);
});

// ─── Render links ────────────────────────────────────────────────

const linkGroup = g.append("g").attr("class", "links");

const link = linkGroup.selectAll("g")
  .data(links)
  .join("g")
  .attr("class", "edge");

link.append("line")
  .attr("class", "edge-hit")
  .attr("stroke", "transparent")
  .attr("stroke-width", 12)
  .attr("x1", d => d.source.x)
  .attr("y1", d => d.source.y)
  .attr("x2", d => d.target.x)
  .attr("y2", d => d.target.y)
  .style("pointer-events", "stroke");

link.append("line")
  .attr("class", "edge-visual")
  .attr("stroke", d => d.color)
  .attr("stroke-width", 1.2)
  .attr("stroke-opacity", 0.4)
  .attr("marker-end", d => "url(#arrow-" + d.relation + ")")
  .attr("x1", d => d.source.x)
  .attr("y1", d => d.source.y)
  .attr("x2", d => d.target.x)
  .attr("y2", d => d.target.y);

link.append("text")
  .attr("class", "edge-label")
  .text(d => d.relationLabel)
  .attr("dy", -5)
  .attr("text-anchor", "middle")
  .attr("fill", d => d.color)
  .attr("x", d => (d.source.x + d.target.x) / 2)
  .attr("y", d => (d.source.y + d.target.y) / 2);

// ─── Render nodes ────────────────────────────────────────────────

const nodeGroup = g.append("g").attr("class", "nodes");

const node = nodeGroup.selectAll("g")
  .data(nodes)
  .join("g")
  .attr("class", "node")
  .attr("transform", d => "translate(" + d.x + "," + d.y + ")")
  .call(d3.drag()
    .on("start", dragStarted)
    .on("drag", dragged)
    .on("end", dragEnded));

node.append("circle")
  .attr("r", d => d.type === "goal" ? 10 : d.type === "decision" ? 9 : d.type === "risk" ? 7 : 6)
  .attr("fill", d => d.color)
  .attr("fill-opacity", 0.85)
  .attr("stroke", d => d.color);

node.append("text")
  .text(d => truncate(d.name, 28))
  .attr("dx", d => d.type === "goal" ? 14 : 12)
  .attr("dy", 4);

// ─── Drag (manual reposition, no simulation) ─────────────────────

function dragStarted(event, d) {
  d3.select(this).raise();
}

function dragged(event, d) {
  d.x = event.x;
  d.y = event.y;
  d3.select(this).attr("transform", "translate(" + d.x + "," + d.y + ")");
  // Update connected edges—both hit and visual lines
  link.each(function(ld) {
    if (ld.source === d || ld.target === d) {
      d3.select(this).selectAll("line")
        .attr("x1", ld.source.x).attr("y1", ld.source.y)
        .attr("x2", ld.target.x).attr("y2", ld.target.y);
      d3.select(this).select("text")
        .attr("x", (ld.source.x + ld.target.x) / 2)
        .attr("y", (ld.source.y + ld.target.y) / 2);
    }
  });
}

function dragEnded(event, d) {
  // Keep position; no simulation to restart
}

// ─── Interaction state ─────────────────────────────────────────────

let pinnedNode = null;

// ─── Tooltip ──────────────────────────────────────────────────────

const tooltip = document.getElementById("tooltip");

node.on("mouseenter", (event, d) => {
  _showNodeTooltip(event, d);
  if (!pinnedNode) _highlightRelations(d);
}).on("mousemove", (event) => {
  tooltip.style.left = (event.offsetX + 14) + "px";
  tooltip.style.top  = (event.offsetY - 10) + "px";
}).on("mouseleave", (event, d) => {
  tooltip.classList.remove("visible");
  if (!pinnedNode) _clearHighlight();
});

// Edge hover: show readable relation + highlight the two connected nodes
link.on("mouseenter", (event, d) => {
  const src = ENTITIES[entityMap.get(d.source.id)];
  const tgt = ENTITIES[entityMap.get(d.target.id)];
  const label = RELATION_LABELS[d.relation] || d.relation;
  const srcLabel = ENTITY_LABELS[src.type] || src.type;
  const tgtLabel = ENTITY_LABELS[tgt.type] || tgt.type;

  tooltip.innerHTML = [
    '<span class="tt-type" style="background:' + d.color + '33;color:' + d.color + '">' + label + '</span>',
    '<div class="tt-name">' + escapeHtml(src.name) + ' <span style="color:#888;font-weight:400">→</span> ' + escapeHtml(tgt.name) + '</div>',
    '<div class="tt-desc">' + srcLabel + ' <b style="color:' + d.color + '">' + label + '</b> ' + tgtLabel + '</div>',
  ].join('');
  tooltip.classList.add("visible");

  d3.select(this).classed("highlighted", true);
}).on("mousemove", (event) => {
  tooltip.style.left = (event.offsetX + 14) + "px";
  tooltip.style.top  = (event.offsetY - 10) + "px";
}).on("mouseleave", (event, d) => {
  tooltip.classList.remove("visible");
  d3.select(this).classed("highlighted", false);
});

// ─── Click: pin node + show relationship panel ────────────────────

node.on("click", (event, d) => {
  event.stopPropagation();

  if (pinnedNode === d) {
    // Deselect
    pinnedNode = null;
    _clearAll();
    return;
  }

  pinnedNode = d;
  _pinRelations(d);
});

// Click background to deselect
svg.on("click", () => {
  pinnedNode = null;
  _clearAll();
});

// ─── Highlight helpers ─────────────────────────────────────────────

function _highlightRelations(d) {
  const connectedIds = new Set([d.id]);
  RELATIONS.forEach(r => {
    if (r.fromEntityId === d.id) connectedIds.add(r.toEntityId);
    if (r.toEntityId === d.id) connectedIds.add(r.fromEntityId);
  });

  node.classed("dimmed", n => !connectedIds.has(n.id));
  link.classed("dimmed", l => l.source.id !== d.id && l.target.id !== d.id);
}

function _clearHighlight() {
  if (pinnedNode) {
    // Restore pinned state
    _pinRelations(pinnedNode);
  } else {
    node.classed("dimmed", false);
    link.classed("dimmed", false);
  }
  hideRelationPanel();
}

function _clearAll() {
  node.classed("dimmed", false);
  link.classed("dimmed", false);
  hideRelationPanel();
}

function _pinRelations(d) {
  const connectedIds = new Set([d.id]);
  RELATIONS.forEach(r => {
    if (r.fromEntityId === d.id) connectedIds.add(r.toEntityId);
    if (r.toEntityId === d.id) connectedIds.add(r.fromEntityId);
  });

  node.classed("dimmed", n => !connectedIds.has(n.id));
  link.classed("dimmed", l => l.source.id !== d.id && l.target.id !== d.id);
  showRelationPanel(d);
}

// ─── Relation panel in sidebar ────────────────────────────────────

const rpTitle = document.getElementById("rp-title");
const rpList = document.getElementById("rp-list");
const rpPanel = document.getElementById("relation-panel");
const rpClose = document.getElementById("rp-close");

rpClose.addEventListener("click", () => {
  pinnedNode = null;
  _clearAll();
});

function showRelationPanel(d) {
  const ownLabel = ENTITY_LABELS[d.type] || d.type;

  rpTitle.innerHTML = '<span class="tt-type" style="background:' + d.color + '33;color:' + d.color + ';display:inline-block;padding:1px 6px;border-radius:3px;font-size:10px;margin-right:6px;">' + ownLabel + '</span>' + escapeHtml(truncate(d.name, 36));

  // Collect all relations involving this entity
  const outgoing = RELATIONS.filter(r => r.fromEntityId === d.id);
  const incoming = RELATIONS.filter(r => r.toEntityId === d.id);

  if (outgoing.length === 0 && incoming.length === 0) {
    rpList.innerHTML = '<div class="rp-empty">该实体没有关联关系</div>';
    rpPanel.style.display = "flex";
    rpPanel.style.flexDirection = "column";
    return;
  }

  let html = "";
  const seen = new Set();

  // Outgoing relations
  outgoing.forEach(r => {
    const tgt = ENTITIES.find(e => e.id === r.toEntityId);
    if (!tgt) return;
    const key = r.relation + "|" + r.toEntityId;
    if (seen.has(key)) return;
    seen.add(key);
    const relLabel = RELATION_LABELS[r.relation] || r.relation;
    html += _buildRelationRow(d, tgt, r, relLabel, "out");
  });

  // Incoming relations
  incoming.forEach(r => {
    const src = ENTITIES.find(e => e.id === r.fromEntityId);
    if (!src) return;
    const key = r.relation + "|" + r.fromEntityId;
    if (seen.has(key)) return;
    seen.add(key);
    const relLabel = RELATION_LABELS[r.relation] || r.relation;
    html += _buildRelationRow(src, d, r, relLabel, "in");
  });

  rpList.innerHTML = html || '<div class="rp-empty">该实体没有关联关系</div>';
  rpPanel.style.display = "flex";
  rpPanel.style.flexDirection = "column";
}

function _buildRelationRow(fromEntity, toEntity, r, relLabel, direction) {
  const color = RELATION_COLORS[r.relation] || "#666";
  const fromLabel = ENTITY_LABELS[fromEntity.type] || fromEntity.type;
  const toLabel = ENTITY_LABELS[toEntity.type] || toEntity.type;
  const prefix = direction === "in" ? "← " : "";

  return '<div class="rp-relation" style="border-left: 2px solid ' + color + '">' +
    '<span class="rp-dot" style="background:' + color + '"></span>' +
    '<span class="rp-text">' + prefix +
    '<span class="rp-target" style="color:' + ENTITY_COLORS[fromEntity.type] + '">' + escapeHtml(truncate(fromEntity.name, 24)) + '</span>' +
    '  <b style="color:' + color + '">' + relLabel + '</b>  ' +
    '<span class="rp-target" style="color:' + ENTITY_COLORS[toEntity.type] + '">' + escapeHtml(truncate(toEntity.name, 24)) + '</span>' +
    '</span></div>';
}

function hideRelationPanel() {
  rpPanel.style.display = "none";
}

// ─── Node tooltip helper ──────────────────────────────────────────

function _showNodeTooltip(event, d) {
  const label = ENTITY_LABELS[d.type] || d.type;
  const plan = PLANS.find(p => p.id === d.planId);
  tooltip.innerHTML = [
    '<span class="tt-type" style="background:' + d.color + '33;color:' + d.color + '">' + label + '</span>',
    '<div class="tt-name">' + escapeHtml(d.name) + '</div>',
    d.description ? '<div class="tt-desc">' + escapeHtml(truncate(d.description, 180)) + '</div>' : '',
    '<div class="tt-meta">📋 ' + (plan ? plan.title : d.planId) + '</div>',
  ].join('');
  tooltip.classList.add("visible");
}

// ─── Search ───────────────────────────────────────────────────────

const searchInput = document.getElementById("search-input");
searchInput.addEventListener("input", () => {
  const q = searchInput.value.toLowerCase().trim();
  if (!q) {
    if (pinnedNode) { _pinRelations(pinnedNode); }
    else { _clearAll(); }
    return;
  }

  const matched = new Set();
  ENTITIES.forEach(e => {
    if (e.name.toLowerCase().includes(q) || e.description.toLowerCase().includes(q)) {
      matched.add(e.id);
    }
  });

  if (matched.size === 0) {
    node.classed("dimmed", true);
    link.classed("dimmed", true);
  } else {
    node.classed("dimmed", n => !matched.has(n.id));
    link.classed("dimmed", l => !matched.has(l.source.id) && !matched.has(l.target.id));
  }
});

// ─── Sidebar: Legend ──────────────────────────────────────────────

// Entity type legend
const legendEl = document.getElementById("legend-entities");
const typeCounts = {};
ENTITIES.forEach(e => { typeCounts[e.type] = (typeCounts[e.type] || 0) + 1; });

Object.entries(ENTITY_COLORS).forEach(([type, color]) => {
  const count = typeCounts[type];
  if (!count) return;
  const item = document.createElement("div");
  item.className = "legend-item";
  item.innerHTML = '<span class="legend-dot" style="background:' + color + '"></span>' +
    (ENTITY_LABELS[type] || type) +
    '<span class="legend-count">' + count + '</span>';
  item.addEventListener("click", () => {
    item.classList.toggle("active");
    const active = item.classList.contains("active");
    if (active) {
      // Dim nodes not of this type
      node.classed("dimmed", n => n.type !== type);
      link.classed("dimmed", l => l.source.type !== type && l.target.type !== type);
    } else {
      node.classed("dimmed", false);
      link.classed("dimmed", false);
    }
  });
  legendEl.appendChild(item);
});

// Relation type legend
const relLegendEl = document.getElementById("legend-relations");
const relCounts = {};
RELATIONS.forEach(r => { relCounts[r.relation] = (relCounts[r.relation] || 0) + 1; });

Object.entries(RELATION_COLORS).forEach(([rel, color]) => {
  const count = relCounts[rel];
  if (!count) return;
  const item = document.createElement("div");
  item.className = "legend-item";
  item.innerHTML = '<span class="legend-dot" style="background:' + color + '"></span>' +
    (RELATION_LABELS[rel] || rel) +
    '<span class="legend-count">' + count + '</span>';
  relLegendEl.appendChild(item);
});

// ─── Stats ────────────────────────────────────────────────────────

document.getElementById("stats").innerHTML =
  '<span>📋 <strong>' + PLANS.length + '</strong> 计划</span>' +
  '<span>🔷 <strong>' + ENTITIES.length + '</strong> 实体</span>' +
  '<span>🔗 <strong>' + RELATIONS.length + '</strong> 关系</span>';

document.getElementById("plan-title").textContent =
  PLANS.map(p => p.title.replace("Plan: ", "")).join(" | ") || "暂无计划";

// ─── Helpers ──────────────────────────────────────────────────────

function truncate(str, maxLen) {
  return str && str.length > maxLen ? str.slice(0, maxLen) + "…" : str || "";
}

function escapeHtml(str) {
  const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  return (str || "").replace(/[&<>"']/g, c => map[c]);
}

// ─── Resize handler ───────────────────────────────────────────────

window.addEventListener("resize", () => {
  const w = container.clientWidth;
  const h = container.clientHeight;
  svg.attr("viewBox", [0, 0, w, h]);
});
</script>
</body>
</html>`;
}
