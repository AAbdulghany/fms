#!/usr/bin/env node
/**
 * CLEAN-002 — fail if any src/ file imports legacy @/components or @/pages.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "src");
const PATTERN =
  /from\s+['"]@\/(components|pages)\/[^'"]+['"]|import\s*\(\s*['"]@\/(components|pages)\/[^'"]+['"]\s*\)/g;

const hits = [];

function walk(dir) {
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, ent.name);
    if (ent.isDirectory()) {
      if (ent.name === "node_modules" || ent.name === "dist") continue;
      walk(full);
      continue;
    }
    if (!/\.(ts|tsx)$/.test(ent.name)) continue;
    const text = fs.readFileSync(full, "utf8");
    let m;
    const re = new RegExp(PATTERN.source, "g");
    while ((m = re.exec(text)) !== null) {
      const line = text.slice(0, m.index).split(/\r?\n/).length;
      hits.push(`${path.relative(process.cwd(), full)}:${line}  ${m[0]}`);
    }
  }
}

if (!fs.existsSync(ROOT)) {
  console.error("src/ missing");
  process.exit(1);
}

walk(ROOT);

if (hits.length) {
  console.error("Legacy imports found (use @/shared or @/features):\n");
  for (const h of hits) console.error(`  ${h}`);
  process.exit(1);
}

console.log("check:imports OK — no @/components or @/pages imports");
