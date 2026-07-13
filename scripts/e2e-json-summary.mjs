#!/usr/bin/env node
/**
 * Summarize Playwright JSON report into:
 *   - test-results/e2e-failure-summary.json  (structured)
 *   - GitHub Actions job summary (markdown)
 *
 * Usage: node scripts/e2e-json-summary.mjs [path-to-e2e-results.json]
 */
import fs from "node:fs";
import path from "node:path";

const reportPath = process.argv[2] || "test-results/e2e-results.json";
const outPath = "test-results/e2e-failure-summary.json";

function walkSuites(suites, parentTitle = []) {
  const tests = [];
  for (const suite of suites || []) {
    const titles = [...parentTitle, suite.title].filter(Boolean);
    for (const spec of suite.specs || []) {
      for (const test of spec.tests || []) {
        const results = test.results || [];
        const last = results[results.length - 1] || {};
        const status = test.status || last.status || "unknown";
        const errors = (results || [])
          .flatMap((r) => r.errors || [])
          .map((e) => ({
            message: e.message || e.value || String(e),
            snippet: e.snippet || null,
            location: e.location || null,
          }));
        tests.push({
          title: [...titles, spec.title].filter(Boolean).join(" › "),
          file: spec.file || suite.file || null,
          line: spec.line ?? null,
          project: test.projectName || null,
          status,
          ok: status === "expected" || status === "flaky",
          durationMs: results.reduce((sum, r) => sum + (r.duration || 0), 0),
          retries: Math.max(0, results.length - 1),
          errors,
        });
      }
    }
    tests.push(...walkSuites(suite.suites, titles));
  }
  return tests;
}

function main() {
  if (!fs.existsSync(reportPath)) {
    const summary = {
      generatedAt: new Date().toISOString(),
      reportPath,
      available: false,
      error: `Report not found: ${reportPath}`,
      totals: { total: 0, passed: 0, failed: 0, flaky: 0, skipped: 0 },
      failed: [],
    };
    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    fs.writeFileSync(outPath, JSON.stringify(summary, null, 2));
    console.error(JSON.stringify(summary, null, 2));
    appendGithubSummary(summary);
    process.exit(0);
  }

  const report = JSON.parse(fs.readFileSync(reportPath, "utf8"));
  const all = walkSuites(report.suites || []);
  const failed = all.filter((t) => !t.ok && t.status !== "skipped");
  const passed = all.filter((t) => t.status === "expected");
  const flaky = all.filter((t) => t.status === "flaky");
  const skipped = all.filter((t) => t.status === "skipped");

  const summary = {
    generatedAt: new Date().toISOString(),
    reportPath,
    available: true,
    stats: report.stats || null,
    totals: {
      total: all.length,
      passed: passed.length,
      failed: failed.length,
      flaky: flaky.length,
      skipped: skipped.length,
    },
    failed: failed.map((t) => ({
      title: t.title,
      file: t.file,
      line: t.line,
      project: t.project,
      status: t.status,
      durationMs: t.durationMs,
      retries: t.retries,
      errors: t.errors,
    })),
  };

  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, JSON.stringify(summary, null, 2));

  // Always print JSON to CI logs for easy copy
  console.log("--- E2E failure summary (JSON) ---");
  console.log(JSON.stringify(summary, null, 2));
  console.log("--- end summary ---");

  appendGithubSummary(summary);
}

function appendGithubSummary(summary) {
  const stepSummary = process.env.GITHUB_STEP_SUMMARY;
  if (!stepSummary) return;

  const lines = [];
  lines.push("## E2E failure summary");
  lines.push("");
  if (!summary.available) {
    lines.push(`Report missing: \`${summary.reportPath}\``);
  } else {
    const { totals } = summary;
    lines.push(
      `| Total | Passed | Failed | Flaky | Skipped |`,
      `| ---: | ---: | ---: | ---: | ---: |`,
      `| ${totals.total} | ${totals.passed} | ${totals.failed} | ${totals.flaky} | ${totals.skipped} |`,
      "",
    );
    if (summary.failed.length === 0) {
      lines.push("_No failed tests in JSON report._");
    } else {
      lines.push("### Failed tests");
      lines.push("");
      for (const f of summary.failed) {
        lines.push(`#### ${f.title}`);
        lines.push("");
        lines.push(`- **File:** \`${f.file || "?"}${f.line != null ? `:${f.line}` : ""}\``);
        lines.push(`- **Status:** \`${f.status}\``);
        lines.push(`- **Retries:** ${f.retries}`);
        if (f.errors?.length) {
          lines.push("- **Errors:**");
          for (const e of f.errors) {
            const msg = (e.message || "").split("\n")[0].slice(0, 500);
            lines.push(`  - ${msg}`);
          }
        }
        lines.push("");
      }
    }
    lines.push("");
    lines.push(`Full JSON: \`test-results/e2e-failure-summary.json\``);
  }
  fs.appendFileSync(stepSummary, lines.join("\n") + "\n");
}

main();
