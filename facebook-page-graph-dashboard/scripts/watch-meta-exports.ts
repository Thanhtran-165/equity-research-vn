/**
 * Watched folder semi-automation — tự phát hiện file CSV/XLSX do user tự tải về
 * từ Meta Business Suite, copy vào /imports/incoming, optionally cleanup file gốc.
 *
 * ⚠️ SEMI-AUTOMATION ONLY:
 * - KHÔNG mở browser.
 * - KHÔNG login Meta.
 * - KHÔNG tải file thay user.
 * - Chỉ xử lý file mà user đã tự tải về.
 * - Cleanup chỉ move to Trash/Archive, KHÔNG delete vĩnh viễn.
 *
 * Usage:
 *   npx tsx scripts/watch-meta-exports.ts
 *
 * Env:
 *   META_EXPORTS_WATCH_DIR=           (default: ~/Downloads)
 *   META_EXPORTS_INCOMING_DIR=        (default: imports/incoming)
 *   META_EXPORTS_AUTO_IMPORT=         (default: false)
 *   META_EXPORTS_CLEANUP_MODE=        none|trash|archive (default: none)
 *   META_EXPORTS_CLEANUP_DRY_RUN=     true|false (default: true)
 *   META_EXPORTS_CLEANUP_AFTER=       copy|upload_dry_run|apply (default: copy)
 *   META_EXPORTS_CLEANUP_DUPLICATES=  true|false (default: false)
 */
import * as fs from "fs";
import * as path from "path";
import { createHash } from "crypto";
import { cleanupProcessedFile, isSafeToCleanupFile, hashFile } from "../lib/imports/fileCleanup";

const WATCH_DIR = process.env.META_EXPORTS_WATCH_DIR || path.join(process.env.HOME || "/tmp", "Downloads");
const INCOMING_DIR = process.env.META_EXPORTS_INCOMING_DIR || path.join(process.cwd(), "imports", "incoming");
const ARCHIVE_DIR = process.env.META_EXPORTS_ARCHIVE_DIR || path.join(process.cwd(), "imports", "archive");
const AUTO_IMPORT = process.env.META_EXPORTS_AUTO_IMPORT === "true";
const CLEANUP_MODE = (process.env.META_EXPORTS_CLEANUP_MODE || "none") as "none" | "trash" | "archive";
const CLEANUP_DRY_RUN = process.env.META_EXPORTS_CLEANUP_DRY_RUN !== "false"; // default true
const CLEANUP_AFTER = (process.env.META_EXPORTS_CLEANUP_AFTER || "copy") as "copy" | "upload_dry_run" | "apply";
const CLEANUP_DUPLICATES = process.env.META_EXPORTS_CLEANUP_DUPLICATES === "true";
const PORT = process.env.PORT || "3123";

const PATTERNS = /\.(csv|xlsx|xls)$/i;
const NAME_HINTS = /(insights?|facebook|meta|business.?suite|export|chimcut|posts?|page|video)/i;

const STABILIZE_MS = 10000;
const processed = new Set<string>();
const processedHashes = new Set<string>();

function ensureDirs() {
  for (const dir of [INCOMING_DIR, ARCHIVE_DIR]) {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }
}

function isInterestingFile(filename: string): boolean {
  if (!PATTERNS.test(filename)) return false;
  // Reject temp files
  const lower = filename.toLowerCase();
  if (lower.endsWith(".crdownload") || lower.endsWith(".tmp") || lower.endsWith(".part")) return false;
  if (filename.startsWith("~$")) return false; // Excel lock
  return NAME_HINTS.test(filename);
}

async function waitForStable(filepath: string): Promise<boolean> {
  return new Promise((resolve) => {
    let lastSize = -1;
    let stableCount = 0;
    const interval = setInterval(() => {
      try {
        const stat = fs.statSync(filepath);
        if (stat.size === lastSize && stat.size > 0) {
          stableCount++;
          if (stableCount >= STABILIZE_MS / 1000) {
            clearInterval(interval);
            resolve(true);
          }
        } else {
          stableCount = 0;
          lastSize = stat.size;
        }
      } catch {
        clearInterval(interval);
        resolve(false);
      }
    }, 1000);
  });
}

function log(msg: string) {
  const ts = new Date().toISOString();
  console.log(`[${ts}] ${msg}`);
}

async function uploadToServer(filepath: string): Promise<{ ok: boolean; batchId?: number; duplicate?: boolean }> {
  try {
    const buf = fs.readFileSync(filepath);
    const blob = new Blob([buf]);
    const fd = new FormData();
    fd.append("file", blob, path.basename(filepath));
    const resp = await fetch(`http://localhost:${PORT}/api/imports/upload`, {
      method: "POST",
      body: fd,
    });
    const r = await resp.json();
    if (r.ok) {
      return { ok: true, batchId: r.data.batchId, duplicate: r.data.duplicate };
    }
    log(`  ✗ Upload failed: ${r.error?.message ?? "?"}`);
    return { ok: false };
  } catch (e: any) {
    log(`  ✗ Upload error: ${e?.message ?? e}`);
    return { ok: false };
  }
}

async function handleFile(filepath: string) {
  if (processed.has(filepath)) return;
  const filename = path.basename(filepath);
  log(`detected: ${filepath}`);

  // Wait stable
  const stable = await waitForStable(filepath);
  if (!stable) {
    log(`  ✗ File không ổn định, skip`);
    return;
  }

  // Hash
  const fileHash = await hashFile(filepath);
  log(`  hash: ${fileHash.slice(0, 16)}...`);

  // Check duplicate
  if (processedHashes.has(fileHash)) {
    if (!CLEANUP_DUPLICATES) {
      log(`  ⚠️ Duplicate hash (đã xử lý trước đó). Giữ file.`);
      processed.add(filepath);
      return;
    }
    log(`  ⚠️ Duplicate hash nhưng CLEANUP_DUPLICATES=true → tiếp tục cleanup`);
  }
  processedHashes.add(fileHash);

  // Copy vào incoming
  const dest = path.join(INCOMING_DIR, filename);
  try {
    fs.copyFileSync(filepath, dest);
    log(`  copied: ${dest}`);
  } catch (e: any) {
    log(`  ✗ Copy failed: ${e.message}`);
    return;
  }
  processed.add(filepath);

  let uploadOk = false;
  if (AUTO_IMPORT) {
    log(`  → Auto upload...`);
    const result = await uploadToServer(dest);
    uploadOk = result.ok;
    if (uploadOk) {
      log(`  import dry-run: success${result.duplicate ? " (duplicate)" : ""}`);
    }
  } else {
    log(`  → File ready for manual import (AUTO_IMPORT=false)`);
  }

  // Cleanup logic
  const shouldCleanup =
    (CLEANUP_AFTER === "copy") ||
    (CLEANUP_AFTER === "upload_dry_run" && uploadOk);

  if (shouldCleanup && CLEANUP_MODE !== "none") {
    log(`  → Cleanup mode: ${CLEANUP_MODE} (dryRun=${CLEANUP_DRY_RUN}, after=${CLEANUP_AFTER})`);
    const result = await cleanupProcessedFile({
      originalPath: filepath,
      copiedPath: dest,
      watchDir: WATCH_DIR,
      mode: CLEANUP_MODE,
      archiveDir: ARCHIVE_DIR,
      dryRun: CLEANUP_DRY_RUN,
      reason: `after=${CLEANUP_AFTER}`,
      hash: fileHash,
    });
    if (result.ok) {
      if (result.dryRun) {
        log(`  ✓ cleanup dry-run: would ${CLEANUP_MODE} ${filepath}`);
      } else {
        log(`  ✓ moved original to ${CLEANUP_MODE}: ${result.destination ?? result.method ?? "ok"}`);
      }
    } else {
      log(`  ✗ cleanup failed: ${result.error}`);
    }
  } else if (CLEANUP_MODE !== "none") {
    log(`  → Cleanup deferred (after=${CLEANUP_AFTER}, uploadOk=${uploadOk})`);
  }
}

function scanExisting() {
  try {
    const files = fs.readdirSync(WATCH_DIR);
    for (const f of files) {
      const fp = path.join(WATCH_DIR, f);
      try {
        const stat = fs.statSync(fp);
        if (stat.isFile() && isInterestingFile(f)) {
          processed.add(fp);
        }
      } catch {}
    }
  } catch (e: any) {
    console.error(`Không đọc được ${WATCH_DIR}: ${e.message}`);
    process.exit(1);
  }
}

function main() {
  ensureDirs();
  console.log(`═══════════════════════════════════════════════════════════`);
  console.log(`  Meta Business Suite Exports Watcher (semi-automation)`);
  console.log(`═══════════════════════════════════════════════════════════`);
  console.log(`Watch dir:      ${WATCH_DIR}`);
  console.log(`Incoming:       ${INCOMING_DIR}`);
  console.log(`Auto upload:    ${AUTO_IMPORT}`);
  console.log(`Cleanup mode:   ${CLEANUP_MODE}`);
  console.log(`Cleanup dryRun: ${CLEANUP_DRY_RUN}`);
  console.log(`Cleanup after:  ${CLEANUP_AFTER}`);
  console.log(`Server port:    ${PORT}`);
  console.log();

  scanExisting();
  console.log(`→ Bỏ qua ${processed.size} file đã có sẵn từ trước.`);

  setInterval(() => {
    try {
      const files = fs.readdirSync(WATCH_DIR);
      for (const f of files) {
        if (!isInterestingFile(f)) continue;
        const fp = path.join(WATCH_DIR, f);
        if (processed.has(fp)) continue;
        try {
          const stat = fs.statSync(fp);
          if (stat.isFile()) handleFile(fp);
        } catch {}
      }
    } catch (e: any) {
      console.error(`Scan error: ${e.message}`);
    }
  }, 5000);

  console.log(`→ Watching... (Ctrl+C để thoát)`);
}

main();
