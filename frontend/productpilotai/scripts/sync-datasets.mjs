import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join, resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(__dirname, "..");
const backendRoot = resolve(frontendRoot, "../../backend/productpilotai");
const datasetDir = join(backendRoot, "datasets");
const generatedFile = join(frontendRoot, "src/generated/backendData.js");

const sourceFiles = [
  "jira_sprint_board.json",
  "servicenow_defects.json",
  "github_work.json",
  "outlook_emails.json",
  "slack_mentions.json",
  "meeting_notes.json"
];

// Embed logo as base64 data URL so it works in Electron (file://) and browser
const logoPath = join(frontendRoot, "logo.jpg");
let logoDataUrl = "";
try {
  const logoBytes = readFileSync(logoPath);
  logoDataUrl = `data:image/jpeg;base64,${logoBytes.toString("base64")}`;
} catch {
  console.warn("logo.jpg not found, logo will not display");
}

function syncDatasets() {
  if (!existsSync(datasetDir) && existsSync(generatedFile)) {
    console.log("Backend dataset directory not accessible in build context. Using pre-generated src/generated/backendData.js.");
    return;
  }
  try {
    let industrialCatalog = [];
    let industrialSources = [];
    let industrialStats = {};
    if (existsSync(join(datasetDir, "industrial_catalog.json"))) {
      industrialCatalog = readJson(join(datasetDir, "industrial_catalog.json"));
    }
    if (existsSync(join(datasetDir, "industrial_sources.json"))) {
      industrialSources = readJson(join(datasetDir, "industrial_sources.json"));
    }
    if (existsSync(join(datasetDir, "industrial_stats.json"))) {
      industrialStats = readJson(join(datasetDir, "industrial_stats.json"));
    }

    const data = {
      industrialCatalog,
      industrialSources,
      industrialStats,
      logoDataUrl
    };

    writeFileSync(
      generatedFile,
      `export const backendData = ${JSON.stringify(data, null, 2)};\n`
    );
    console.log(`Synced ${industrialCatalog.length} industrial products and sources into frontend generated data.`);
  } catch (e) {
    console.warn("Could not sync datasets, using existing backendData.js:", e.message);
  }
}

function readJson(file) {
  return JSON.parse(readFileSync(file, "utf8"));
}

syncDatasets();
