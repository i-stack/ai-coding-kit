import { _ as _export_sfc, C as resolveComponent, o as openBlock, c as createElementBlock, j as createBaseVNode, a as createTextVNode, E as createVNode, a2 as createStaticVNode } from "./chunks/framework.BcMzFyCJ.js";
const __pageData = JSON.parse('{"title":"iOS Engineer","description":"","frontmatter":{},"headers":[],"relativePath":"ios-engineer/index.md","filePath":"ios-engineer/index.md","lastUpdated":1783251060000}');
const _sfc_main = { name: "ios-engineer/index.md" };
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_Badge = resolveComponent("Badge");
  return openBlock(), createElementBlock("div", null, [
    _cache[0] || (_cache[0] = createBaseVNode("h1", {
      id: "ios-engineer",
      tabindex: "-1"
    }, [
      createTextVNode("iOS Engineer "),
      createBaseVNode("a", {
        class: "header-anchor",
        href: "#ios-engineer",
        "aria-label": 'Permalink to "iOS Engineer"'
      }, "​")
    ], -1)),
    createVNode(_component_Badge, {
      type: "tip",
      text: "v3.0.0"
    }),
    _cache[1] || (_cache[1] = createStaticVNode("", 21))
  ]);
}
const index = /* @__PURE__ */ _export_sfc(_sfc_main, [["render", _sfc_render]]);
export {
  __pageData,
  index as default
};
