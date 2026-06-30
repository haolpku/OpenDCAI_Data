# 渲染增强：LaTeX 公式 + JSON 可视化

> 给 OpenDCAI_Data 展示站加的两个零成本前端增强。2026-06-30。

## 解决什么问题
原页面用 `<pre>`/纯文本直接显示样本值，导致：
1. **数学/推理类数据里的 LaTeX 公式**（`$z^2+...$`、`\frac{}{}`）显示成裸源码，对一个展示"数学推理数据"的橱窗很掉价。
2. **JSON/嵌套对象**只是灰底等宽字一坨，没有层级色、不易读。

## 怎么做的（关键：零成本、零维护、离线可用）
- **LaTeX**：引入 **KaTeX**（业界标准，比 MathJax 快），渲染发生在访问者浏览器里 → GitHub Pages 不增加任何服务器成本/并发压力/维护负担。
- **依赖方式：本地 vendored**（不是 CDN）。KaTeX 的 css/js + 20 个字体文件全部下载进 `assets/vendor/katex/`（共 600KB）→ **完全自包含、离线可用、不依赖任何外部 CDN**（避免国内网络卡 CDN 时公式渲染失败）。
- **JSON**：纯手写 ~15 行 JS 做语法高亮（key/string/number/bool/null 上色），无任何额外依赖。

## 改动范围（小、隔离、可回滚）
- `index.html`：+37 / -2 行
  - `<head>` 引入本地 KaTeX css/js
  - `<style>` 加 JSON 高亮 + KaTeX 深色微调样式
  - 加 `jsonHL()`（JSON 高亮）和 `typeset()`（触发 KaTeX）两个函数
  - `valInner`/`valHTML` 的 JSON 分支改用高亮版
  - 文本样本渲染到 DOM 后调用 `typeset()`
- 新增 `assets/vendor/katex/`（23 个文件，600KB）
- **未改动** `data.js` 和任何数据。

## 行为说明（诚实）
- 样本里用 `$...$` / `\(...\)` / `\[...\]` 包裹的 → KaTeX 渲染成公式。
- 样本里用 Unicode 符号（`z²`、`z₁`、`≤`）的 → 浏览器原生显示（本就正常，KaTeX 不碰）。
- KaTeX 设置了 `ignoredTags` 含 `pre`/`code`，所以 **JSON/代码块里的 `$` 不会被误当成公式**。
- 若 KaTeX 文件缺失/未加载，`typeset()` 静默跳过，页面退化成原样，不报错。

## 怎么验证
打开 `_preview_test.html`（临时验证页，合并时可删）能直接看到：①LaTeX公式 ②Unicode符号 ③JSON高亮 三种渲染效果。
或直接打开 `index.html` → 进"数学推理 CoT"类别看公式、进"Text2SQL"看 JSON。

## 没做 / 故意不做
- 没做"实时调模型给数据打分"——那需要后端、有并发/token/维护成本，违背静态站定位。
- 没改数据、没动其他类别的展示逻辑。
