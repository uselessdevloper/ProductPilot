import { readFileSync } from "node:fs";
import { join, resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const defaultRoot = resolve(__dirname, "..");

// Strip only top-level ES import statements (lines starting with "import ")
// The greedy regex /import .*?;\n/g incorrectly matches @import url() inside CSS strings
function stripModuleSyntax(src) {
  return src
    .split("\n")
    .filter(line => !line.match(/^import\s+/))
    .map(line => {
      return line
        .replace(/^export\s+default\s+/, "")
        .replace(/^export\s+async\s+function\s+/, "async function ")
        .replace(/^export\s+function\s+/, "function ")
        .replace(/^export\s+const\s+/, "const ")
        .replace(/^export\s+let\s+/, "let ")
        .replace(/^export\s+var\s+/, "var ")
        .replace(/^export\s+\{[^}]*\};?/, "");
    })
    .join("\n");
}

export function renderHtml(root = defaultRoot) {
  const css = readFileSync(join(root, "src/styles.css"), "utf8");
  const generated = stripModuleSyntax(readFileSync(join(root, "src/generated/backendData.js"), "utf8"));
  const data = stripModuleSyntax(readFileSync(join(root, "src/data.js"), "utf8"));
  const client = stripModuleSyntax(readFileSync(join(root, "src/geminiClient.js"), "utf8"));
  const main = stripModuleSyntax(readFileSync(join(root, "src/main.js"), "utf8"));

  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="color-scheme" content="light dark" />
    <meta name="theme-color" content="#8cbac9" />
    <title>ProductPilot AI — Autonomous Agentic Commerce for Razorpay</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@200;300;400;500;600;700;800&family=Outfit:wght@200;300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
    <script>
      (function() {
        const theme = localStorage.getItem("productpilot:theme") || "light";
        document.documentElement.setAttribute("data-theme", theme);
      })();
    </script>
    <style>${css}</style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
  </head>
  <body>
    <div id="app"></div>
    <script>
      window.jsPDF = window.jspdf?.jsPDF || window.jsPDF;
${[generated, data, client, main]
  .join("\n")
  .replace(/<\/script>/gi, "<\\/script>")}
    </script>
  </body>
</html>`;
}