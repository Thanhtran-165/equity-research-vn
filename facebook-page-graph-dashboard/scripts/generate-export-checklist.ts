/**
 * CLI: Generate export checklist cho Chim Cút.
 *
 * Usage:
 *   npx tsx scripts/generate-export-checklist.ts --period monthly --month 2026-07
 *   npx tsx scripts/generate-export-checklist.ts --period quarterly --quarter 2026-Q2
 *   npx tsx scripts/generate-export-checklist.ts --period yearly --year 2026
 */
import { writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import { generateExportPlan, formatChecklistMarkdown, parsePeriod, type ExportPeriod } from "../lib/imports/exportPlan";

function parseArgs(): { period: ExportPeriod; input: string; includeVideo: boolean; includeAudience: boolean; includeUnverified: boolean } {
  const args = process.argv.slice(2);
  const opts = {
    period: "monthly" as ExportPeriod,
    input: "",
    includeVideo: true,
    includeAudience: false,
    includeUnverified: false,
  };
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case "--period":
        opts.period = (args[++i] as ExportPeriod) ?? "monthly";
        break;
      case "--month":
        opts.input = args[++i] ?? "";
        opts.period = "monthly";
        break;
      case "--quarter":
        opts.input = args[++i] ?? "";
        opts.period = "quarterly";
        break;
      case "--year":
        opts.input = args[++i] ?? "";
        opts.period = "yearly";
        break;
      case "--no-video":
        opts.includeVideo = false;
        break;
      case "--audience":
        opts.includeAudience = true;
        break;
      case "--include-unverified-page-performance":
        opts.includeUnverified = true;
        break;
      case "--help":
        console.log(`Usage: npx tsx scripts/generate-export-checklist.ts [options]

Options:
  --period <monthly|quarterly|yearly>  Period type (default: monthly)
  --month <YYYY-MM>                     Export for specific month
  --quarter <YYYY-QX>                   Export for specific quarter
  --year <YYYY>                         Export for full year
  --no-video                            Exclude video/reels exports
  --audience                            Include audience preset (if available)
  --include-unverified-page-performance  Include G01 (unverified Page/Daily/Performance)
`);
        process.exit(0);
    }
  }
  if (!opts.input) {
    const now = new Date();
    opts.input = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
  }
  return opts;
}

function main() {
  const opts = parseArgs();
  const { label } = parsePeriod(opts.input);

  console.log(`→ Generating export checklist for ${label}...`);

  const tasks = generateExportPlan({
    period: opts.period,
    startDate: opts.input,
    includeVideo: opts.includeVideo,
    includeAudience: opts.includeAudience,
    includeUnverifiedPagePerformance: opts.includeUnverified,
  });

  const markdown = formatChecklistMarkdown(tasks, label);

  const outputDir = join(process.cwd(), "docs", "export-checklists");
  mkdirSync(outputDir, { recursive: true });

  const filename = `chimcut-${label.replace(/[^0-9A-Za-z]/g, "-")}.md`;
  const outputPath = join(outputDir, filename);
  writeFileSync(outputPath, markdown);

  console.log(`✓ Export checklist saved: ${outputPath}`);
  console.log(`  ${tasks.length} tasks (${tasks.filter((t) => t.priority === "P0").length} P0, ${tasks.filter((t) => t.priority === "P1").length} P1, ${tasks.filter((t) => t.priority === "P2").length} P2)`);
  console.log();
  console.log("Tasks:");
  for (const t of tasks) {
    console.log(`  ${t.priority} ${t.id}: ${t.contentLevel} / ${t.preset} → ${t.filename}`);
  }
}

main();
