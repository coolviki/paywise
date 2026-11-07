// Builds each view into ONE self-contained HTML file (inline CSS + JS, no CDN),
// so the MCP Apps sandbox needs no CSP exceptions. Output: dist/<view>.html
// Run: npm install && npm run build   (commit dist/ - Railway only runs Python)
import { build } from "esbuild";
import { readFile, writeFile, mkdir } from "node:fs/promises";

const VIEWS = {
  "restaurant-offers": "PayWise dine-out offers",
  "card-ranking": "PayWise card ranking",
};

const css = await readFile(new URL("./src/styles.css", import.meta.url), "utf8");
await mkdir(new URL("./dist/", import.meta.url), { recursive: true });

for (const [view, title] of Object.entries(VIEWS)) {
  const out = await build({
    entryPoints: [new URL(`./src/${view}.js`, import.meta.url).pathname],
    bundle: true,
    minify: true,
    format: "iife",
    target: "es2020",
    write: false,
  });
  const js = out.outputFiles[0].text.replace(/<\/script/gi, "<\\/script");
  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>${title}</title>
<style>${css}</style>
</head>
<body>
<div id="root"></div>
<script>${js}</script>
</body>
</html>
`;
  await writeFile(new URL(`./dist/${view}.html`, import.meta.url), html);
  console.log(`dist/${view}.html  ${(html.length / 1024).toFixed(1)} KB`);
}
