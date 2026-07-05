import { resolveComponent, useSSRContext } from "vue";
import { ssrRenderAttrs, ssrRenderComponent } from "vue/server-renderer";
import { _ as _export_sfc } from "./plugin-vue_export-helper.1tPrXgE0.js";
const __pageData = JSON.parse('{"title":"iOS Engineer","description":"","frontmatter":{},"headers":[],"relativePath":"ios-engineer/index.md","filePath":"ios-engineer/index.md","lastUpdated":1783251060000}');
const _sfc_main = { name: "ios-engineer/index.md" };
function _sfc_ssrRender(_ctx, _push, _parent, _attrs, $props, $setup, $data, $options) {
  const _component_Badge = resolveComponent("Badge");
  _push(`<div${ssrRenderAttrs(_attrs)}><h1 id="ios-engineer" tabindex="-1">iOS Engineer <a class="header-anchor" href="#ios-engineer" aria-label="Permalink to &quot;iOS Engineer&quot;">​</a></h1>`);
  _push(ssrRenderComponent(_component_Badge, {
    type: "tip",
    text: "v3.0.0"
  }, null, _parent));
  _push(`<p>iOS / Swift / SwiftUI / UIKit / Xcode / CocoaPods / SPM engineering — architecture, concurrency, networking, performance, crash debugging, code review, refactoring, migration, testing.</p><p>This is the primary Agent Skill in ai-coding-kit, providing <strong>production-grade AI coding rules</strong> for iOS development.</p><div class="info custom-block"><p class="custom-block-title">Supported Locales</p><p>English (en-US) · 简体中文 (zh-CN). The skill auto-matches your language.</p></div><h2 id="architecture" tabindex="-1">Architecture <a class="header-anchor" href="#architecture" aria-label="Permalink to &quot;Architecture&quot;">​</a></h2><p>The skill is organized as a layered system:</p><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>ios-engineer/</span></span>
<span class="line"><span>├── SKILL.md              # Entry point: routing, triggers, output templates</span></span>
<span class="line"><span>├── references/           # 34 domain reference files (zh-CN)</span></span>
<span class="line"><span>│   ├── rule_index.md     # Canonical Rule ID registry</span></span>
<span class="line"><span>│   ├── self_evolution.md # Auto-evolution governance</span></span>
<span class="line"><span>│   └── ...               # 31 domain-specific references</span></span>
<span class="line"><span>├── i18n/en-US/           # English governance-layer mirrors</span></span>
<span class="line"><span>│   └── references/</span></span>
<span class="line"><span>├── scripts/              # 27 validation &amp; evolution scripts</span></span>
<span class="line"><span>├── evolution/            # Proposal-driven evolution pipeline</span></span>
<span class="line"><span>│   ├── proposals/        # Active/in-review proposals</span></span>
<span class="line"><span>│   ├── archive/          # Archived/implemented proposals</span></span>
<span class="line"><span>│   └── hooks/            # Evolution guard scripts</span></span>
<span class="line"><span>└── snapshots/            # Evolution snapshots for consistency checks</span></span></code></pre></div><h2 id="rule-system" tabindex="-1">Rule System <a class="header-anchor" href="#rule-system" aria-label="Permalink to &quot;Rule System&quot;">​</a></h2><p>The skill enforces <strong>40+ rule IDs</strong> across 5 categories:</p><table tabindex="0"><thead><tr><th>Category</th><th>Prefix</th><th>Count</th><th>Scope</th></tr></thead><tbody><tr><td>Iron Rules</td><td><code>IR-NNN</code></td><td>3</td><td>Always enforced</td></tr><tr><td>Global Rules</td><td><code>GR-NNN</code></td><td>9</td><td>Cross-platform (epistemic, logic, discipline)</td></tr><tr><td>Symptom Routing</td><td><code>SYM-NNN</code></td><td>7</td><td>Auto-route symptoms → references</td></tr><tr><td>Task Routing</td><td><code>ROUTE-NNN</code></td><td>10</td><td>Auto-route task types → references</td></tr><tr><td>Output Templates</td><td><code>OUT-NNN</code></td><td>6</td><td>Structured output formats</td></tr></tbody></table><p>See the <a href="./rule-index">Rule Index</a> for the complete registry.</p><h2 id="key-rules" tabindex="-1">Key Rules <a class="header-anchor" href="#key-rules" aria-label="Permalink to &quot;Key Rules&quot;">​</a></h2><h3 id="ir-001-—-language-anchoring" tabindex="-1">IR-001 — Language Anchoring <a class="header-anchor" href="#ir-001-—-language-anchoring" aria-label="Permalink to &quot;IR-001 — Language Anchoring&quot;">​</a></h3><p>Output language matches the user&#39;s input language. No forced Chinese output.</p><h3 id="ir-006-—-version-context-block" tabindex="-1">IR-006 — Version Context Block <a class="header-anchor" href="#ir-006-—-version-context-block" aria-label="Permalink to &quot;IR-006 — Version Context Block&quot;">​</a></h3><p>All concurrency / availability / SwiftUI behavior / network cancellation answers require a version context block before conclusions.</p><h3 id="ir-011-—-cognitive-adversary-mode" tabindex="-1">IR-011 — Cognitive Adversary Mode <a class="header-anchor" href="#ir-011-—-cognitive-adversary-mode" aria-label="Permalink to &quot;IR-011 — Cognitive Adversary Mode&quot;">​</a></h3><p>When triggered: output restatement, strongest counter-argument, hidden assumptions, failure conditions, falsifiable conditions, position flip, conformity self-check, confidence level, conclusion.</p><h2 id="evolution-governance" tabindex="-1">Evolution Governance <a class="header-anchor" href="#evolution-governance" aria-label="Permalink to &quot;Evolution Governance&quot;">​</a></h2><p>The skill evolves through a <strong>proposal-driven pipeline</strong>:</p><ol><li><strong>Propose</strong> — Create a proposal in <code>evolution/proposals/</code></li><li><strong>Validate</strong> — Run <code>scripts/validate_skill_evolution.sh</code> (14-step check)</li><li><strong>Implement</strong> — Add/modify references; update <code>rule_index.md</code></li><li><strong>Promote</strong> — Archive proposal; snapshot the skill state</li></ol><p>All changes to <code>SKILL.md</code> or <code>references/</code> are gated by the pre-commit hook, which requires a staged evolution proposal in the same commit.</p></div>`);
}
const _sfc_setup = _sfc_main.setup;
_sfc_main.setup = (props, ctx) => {
  const ssrContext = useSSRContext();
  (ssrContext.modules || (ssrContext.modules = /* @__PURE__ */ new Set())).add("ios-engineer/index.md");
  return _sfc_setup ? _sfc_setup(props, ctx) : void 0;
};
const index = /* @__PURE__ */ _export_sfc(_sfc_main, [["ssrRender", _sfc_ssrRender]]);
export {
  __pageData,
  index as default
};
