import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const sourcePath = path.join(root, "docs", "product", "DONDOO_BRANDING_GUIDE.md");
const outputPath = path.join(root, "stakeholder-approval", "dondoo-branding-guide.html");
const markdown = fs.readFileSync(sourcePath, "utf8").replace(/\r/g, "");

const esc = (value) => value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const inline = (value) => esc(value)
  .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
  .replace(/`([^`]+)`/g, "<code>$1</code>")
  .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

const lines = markdown.split("\n");
const blocks = [];
let paragraph = [];
let list = [];
let table = [];
let inCode = false;
let code = [];

const flushParagraph = () => { if (paragraph.length) { blocks.push(`<p>${inline(paragraph.join(" "))}</p>`); paragraph = []; } };
const flushList = () => { if (list.length) { blocks.push(`<ul>${list.map((item) => `<li>${inline(item)}</li>`).join("")}</ul>`); list = []; } };
const flushTable = () => {
  if (!table.length) return;
  const rows = table.filter((row) => !/^\s*\|?\s*-{3,}/.test(row));
  const cells = (row) => row.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((cell) => cell.trim());
  const [head, ...body] = rows;
  blocks.push(`<table><thead><tr>${cells(head).map((cell) => `<th>${inline(cell)}</th>`).join("")}</tr></thead><tbody>${body.map((row) => `<tr>${cells(row).map((cell) => `<td>${inline(cell)}</td>`).join("")}</tr>`).join("")}</tbody></table>`);
  table = [];
};

for (const line of lines) {
  if (line.startsWith("```")) {
    flushParagraph(); flushList(); flushTable();
    if (inCode) { blocks.push(`<pre><code>${esc(code.join("\n"))}</code></pre>`); code = []; }
    inCode = !inCode; continue;
  }
  if (inCode) { code.push(line); continue; }
  if (/^\|/.test(line)) { flushParagraph(); flushList(); table.push(line); continue; }
  if (!line.trim()) { flushParagraph(); flushList(); flushTable(); continue; }
  const heading = line.match(/^(#{1,3})\s+(.+)/);
  if (heading) { flushParagraph(); flushList(); flushTable(); const level = heading[1].length; blocks.push(`<h${level}>${inline(heading[2])}</h${level}>`); continue; }
  if (/^[-*]\s+/.test(line)) { flushParagraph(); flushTable(); list.push(line.replace(/^[-*]\s+/, "")); continue; }
  if (/^>\s?/.test(line)) { flushParagraph(); flushList(); flushTable(); blocks.push(`<blockquote>${inline(line.replace(/^>\s?/, ""))}</blockquote>`); continue; }
  flushList(); flushTable(); paragraph.push(line.trim());
}
flushParagraph(); flushList(); flushTable();

const html = `<!doctype html><html><head><meta charset="utf-8"><title>Dondoo Branding Guide</title>
<style>
@page{size:A4;margin:18mm 16mm 18mm}*{box-sizing:border-box}body{margin:0;color:#213043;background:#fffdf8;font:11pt/1.55 Arial,"Segoe UI",sans-serif}.logo{width:180px;height:auto;margin:0 0 16pt}h1{font-size:30pt;line-height:1.1;color:#214f58;margin:0 0 8pt;border-bottom:4px solid #2f7b74;padding-bottom:10pt}h2{font-size:18pt;color:#214f58;margin:24pt 0 7pt;border-bottom:1px solid #deece8;padding-bottom:4pt}h3{font-size:13pt;color:#2f7b74;margin:16pt 0 5pt}p{margin:0 0 9pt}ul{margin:3pt 0 11pt;padding-left:20pt}li{margin:3pt 0}a{color:#2f7b74;text-decoration:none}blockquote{margin:10pt 0;padding:9pt 12pt;background:#deece8;border-left:4px solid #2f7b74}code{font-family:Consolas,monospace;background:#f3ede3;padding:1pt 3pt;border-radius:3pt}pre{background:#213043;color:#fffdf8;padding:10pt;border-radius:7pt;white-space:pre-wrap}table{width:100%;border-collapse:collapse;margin:7pt 0 13pt;font-size:9.5pt;break-inside:avoid}th{background:#214f58;color:#fffdf8;text-align:left}th,td{border:1px solid #d9ddd9;padding:5pt 6pt;vertical-align:top}tr:nth-child(even){background:#f3ede3}strong{font-weight:700}h1+p{color:#667384;font-size:12pt}
</style></head><body><img class="logo" src="../apps/pwa/public/brand/dondoo-logo.svg" alt="Dondoo logo">${blocks.join("\n")}</body></html>`;
fs.writeFileSync(outputPath, html);
console.log(outputPath);
