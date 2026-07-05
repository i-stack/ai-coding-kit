import { _ as _export_sfc, C as resolveComponent, o as openBlock, c as createElementBlock, j as createBaseVNode, a as createTextVNode, E as createVNode, a2 as createStaticVNode } from "./chunks/framework.BcMzFyCJ.js";
const __pageData = JSON.parse('{"title":"Rule Index","description":"","frontmatter":{},"headers":[],"relativePath":"ios-engineer/rule-index.md","filePath":"ios-engineer/rule-index.md","lastUpdated":1783251060000}');
const _sfc_main = { name: "ios-engineer/rule-index.md" };
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_Badge = resolveComponent("Badge");
  return openBlock(), createElementBlock("div", null, [
    _cache[0] || (_cache[0] = createBaseVNode("h1", {
      id: "rule-index",
      tabindex: "-1"
    }, [
      createTextVNode("Rule Index "),
      createBaseVNode("a", {
        class: "header-anchor",
        href: "#rule-index",
        "aria-label": 'Permalink to "Rule Index"'
      }, "​")
    ], -1)),
    createVNode(_component_Badge, {
      type: "tip",
      text: "49 IDs registered"
    }),
    _cache[1] || (_cache[1] = createStaticVNode("", 14))
  ]);
}
const ruleIndex = /* @__PURE__ */ _export_sfc(_sfc_main, [["render", _sfc_render]]);
export {
  __pageData,
  ruleIndex as default
};
