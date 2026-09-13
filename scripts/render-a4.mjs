#!/usr/bin/env node
// Render diagrams/src/*.mmd → diagrams/pdf/*.pdf, each guaranteed to be exactly ONE A4 page.
// Metadata lives in Mermaid comments at the top of the .mmd file:
//   %% @title  Trạng thái đơn hàng
//   %% @subtitle Nguồn: backend/order-service ... (cập nhật 2026-09-13)
//   %% @orientation portrait|landscape
//   %% @legend <span class="sw ok"></span> Đang chạy thật
//   %% @note Một dòng ghi chú (lặp lại nhiều lần)
//   %% @row T2 | IDLE → IN_FLIGHT | Kích hoạt | Ai | Điều kiện   (bảng chuyển trạng thái;
//        mã bắt đầu bằng "~" = CHƯA code, "!" = chỉ DEMO, "x" = lỗ hổng)
import { readFileSync, writeFileSync, readdirSync, mkdirSync, existsSync, rmSync } from 'node:fs';
import { join, resolve, basename, dirname } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const srcDir = join(root, 'diagrams', 'src');
const outDir = join(root, 'diagrams', 'pdf');
const tmpDir = join(root, 'diagrams', '.build');
const checkOnly = process.argv.includes('--check');
const only = process.argv.slice(2).filter((a) => !a.startsWith('--'));

const mermaidJs = createRequire(import.meta.url).resolve('mermaid/dist/mermaid.min.js');

function findChrome() {
  const candidates = [
    process.env.CHROME_PATH,
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  ].filter(Boolean);
  const hit = candidates.find((p) => existsSync(p));
  if (!hit) throw new Error('Không tìm thấy Chrome/Edge. Đặt biến CHROME_PATH.');
  return hit;
}

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function parse(file) {
  const text = readFileSync(file, 'utf8');
  const meta = { title: basename(file, '.mmd'), subtitle: '', orientation: 'portrait', legend: [], notes: [], rows: [] };
  for (const line of text.split(/\r?\n/)) {
    const m = line.match(/^%%\s*@(\w+)\s+(.*)$/);
    if (!m) continue;
    const [, key, value] = m;
    if (key === 'note') meta.notes.push(value);
    else if (key === 'legend') meta.legend.push(value);
    else if (key === 'row') meta.rows.push(value.split('|').map((c) => c.trim()));
    else meta[key] = value;
  }
  return { text, meta };
}

function page({ text, meta }) {
  const landscape = meta.orientation === 'landscape';
  const [w, h] = landscape ? [297, 210] : [210, 297];
  const margin = 10;
  // Inline HTML is allowed in @legend/@note (trusted repo content); the diagram source is escaped.
  return `<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>${esc(meta.title)}</title>
<style>
  @page { size: A4 ${landscape ? 'landscape' : 'portrait'}; margin: ${margin}mm; }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body { width: ${w - 2 * margin}mm; height: ${h - 2 * margin}mm; overflow: hidden;
         font-family: "Segoe UI", Arial, "Noto Sans", sans-serif; color: #1f2328;
         display: flex; flex-direction: column; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  header { border-bottom: 1.5pt solid #1f2328; padding-bottom: 2mm; margin-bottom: 3mm; }
  h1 { font-size: 16pt; margin: 0; }
  .sub { font-size: 8.5pt; color: #57606a; margin-top: 1mm; }
  .legend { font-size: 8pt; margin-top: 1.5mm; display: flex; flex-wrap: wrap; gap: 1mm 5mm; }
  .sw { display: inline-block; width: 3.2mm; height: 3.2mm; border: 0.6pt solid #333; border-radius: 0.8mm; vertical-align: -0.5mm; margin-right: 1mm; }
  .sw.ok { background: #d8f5dd; } .sw.demo { background: #fff1c2; } .sw.gap { background: #eceef1; border-style: dashed; }
  .sw.bad { background: #ffd8d3; } .sw.end { background: #dbe7ff; }
  #stage { flex: 1 1 auto; min-height: 0; display: flex; align-items: center; justify-content: center; }
  footer { border-top: 0.8pt solid #d0d7de; padding-top: 1.5mm; margin-top: 2mm; font-size: 7.6pt; line-height: 1.32; }
  footer ul { margin: 0; padding-left: 4mm; } footer li { margin: 0.3mm 0; }
  table.tx { width: 100%; border-collapse: collapse; font-size: 6.9pt; line-height: 1.22; margin-top: 2mm; }
  table.tx th { text-align: left; background: #1f2328; color: #fff; font-weight: 600; padding: 0.6mm 1.2mm; }
  table.tx td { border-bottom: 0.4pt solid #d0d7de; padding: 0.45mm 1.2mm; vertical-align: top; }
  table.tx td:first-child { font-weight: 700; white-space: nowrap; }
  table.tx td:nth-child(2) { max-width: 46mm; font-family: Consolas, "Courier New", monospace; }
  table.tx tr.gap td { color: #57606a; font-style: italic; background: #f6f8fa; }
  table.tx tr.demo td { background: #fff8e1; } table.tx tr.hole td { background: #fff0ee; }
  code { font-family: Consolas, "Courier New", monospace; font-size: 0.95em; }
</style></head><body>
<header><h1>${esc(meta.title)}</h1>${meta.subtitle ? `<div class="sub">${meta.subtitle}</div>` : ''}
${meta.legend.length ? `<div class="legend">${meta.legend.map((l) => `<span>${l}</span>`).join('')}</div>` : ''}</header>
<div id="stage"><pre class="mermaid">${esc(text)}</pre></div>
${meta.rows.length ? `<table class="tx"><thead><tr><th>#</th><th>Chuyển</th><th>Kích hoạt</th><th>Ai</th><th>Điều kiện · ghi chú</th></tr></thead><tbody>${meta.rows.map((r) => {
    const cls = r[0].startsWith('~') ? 'gap' : r[0].startsWith('!') ? 'demo' : r[0].startsWith('x') ? 'hole' : '';
    const id = r[0].replace(/^[~!x]/, '');
    return `<tr class="${cls}"><td>${id}</td>${r.slice(1).map((c) => `<td>${c}</td>`).join('')}</tr>`;
  }).join('')}</tbody></table>` : ''}
${meta.notes.length ? `<footer><ul>${meta.notes.map((n) => `<li>${n}</li>`).join('')}</ul></footer>` : ''}
<script src="${pathToFileURL(mermaidJs).href}"></script>
<script>
  mermaid.initialize({ startOnLoad: false, theme: 'base', securityLevel: 'strict', fontFamily: '"Segoe UI", Arial, sans-serif',
    themeVariables: { fontSize: '14px', primaryColor: '#f6f8fa', primaryBorderColor: '#57606a', lineColor: '#57606a', textColor: '#1f2328' },
    state: { padding: 6 }, flowchart: { htmlLabels: true } });
  mermaid.run({ querySelector: '.mermaid' }).then(() => {
    const stage = document.getElementById('stage');
    const svg = stage.querySelector('svg');
    const vb = svg.viewBox.baseVal;
    const scale = Math.min(stage.clientWidth / vb.width, stage.clientHeight / vb.height);
    svg.removeAttribute('style');
    svg.setAttribute('width', Math.floor(vb.width * scale));
    svg.setAttribute('height', Math.floor(vb.height * scale));
    document.body.dataset.scale = scale.toFixed(3);
    document.title = 'READY ' + scale.toFixed(3);
  }).catch((e) => { document.body.innerHTML = '<h1>MERMAID ERROR</h1><pre>' + String(e) + '</pre>'; document.title = 'ERROR'; });
</script></body></html>`;
}

function countPages(pdfFile) {
  const buf = readFileSync(pdfFile).toString('latin1');
  return (buf.match(/\/Type\s*\/Page(?![s\w])/g) || []).length;
}

const chrome = findChrome();
mkdirSync(outDir, { recursive: true });
mkdirSync(tmpDir, { recursive: true });

const files = readdirSync(srcDir).filter((f) => f.endsWith('.mmd')).filter((f) => !only.length || only.some((o) => f.includes(o)));
if (!files.length) { console.error('Không có file .mmd nào trong diagrams/src'); process.exit(1); }

let failed = 0;
for (const f of files) {
  const name = basename(f, '.mmd');
  const parsed = parse(join(srcDir, f));
  const html = join(tmpDir, `${name}.html`);
  writeFileSync(html, page(parsed), 'utf8');
  const pdf = checkOnly ? join(tmpDir, `${name}.pdf`) : join(outDir, `${name}.pdf`);
  const dom = execFileSync(chrome, ['--headless=new', '--disable-gpu', '--no-sandbox', '--allow-file-access-from-files',
    '--virtual-time-budget=20000', '--dump-dom', pathToFileURL(html).href], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  if (!/<title>READY /.test(dom)) {
    const body = (dom.match(/<body[^>]*>([\s\S]*?)<script/) || [])[1] || dom;
    console.error(`✗ ${name}: lỗi cú pháp Mermaid\n${body.replace(/<[^>]+>/g, ' ').trim().slice(0, 800)}`);
    failed++; continue;
  }
  const scale = Number((dom.match(/<title>READY ([\d.]+)<\/title>/) || [])[1] || 0);
  execFileSync(chrome, ['--headless=new', '--disable-gpu', '--no-sandbox', '--allow-file-access-from-files', '--no-pdf-header-footer',
    '--virtual-time-budget=20000', `--print-to-pdf=${pdf}`, pathToFileURL(html).href], { stdio: 'ignore' });
  const pages = countPages(pdf);
  const tooSmall = scale > 0 && scale < 0.4;
  const status = pages === 1 && !tooSmall ? '✓' : '✗';
  if (status === '✗') failed++;
  console.log(`${status} ${name}.pdf  pages=${pages}  scale=${scale}${tooSmall ? '  (chữ quá nhỏ khi in — tách sơ đồ hoặc đổi orientation)' : ''}`);
}
if (checkOnly) rmSync(tmpDir, { recursive: true, force: true });
process.exit(failed ? 1 : 0);
