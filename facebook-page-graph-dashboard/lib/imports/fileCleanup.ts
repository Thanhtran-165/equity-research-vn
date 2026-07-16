/**
 * File Cleanup — đưa file gốc trong Downloads vào Trash/Archive
 * sau khi đã copy + hash + import thành công.
 *
 * Safety guards:
 * - KHÔNG bao giờ dùng fs.unlink (delete vĩnh viễn).
 * - Chỉ move to Trash (macOS/Windows) hoặc Recycle Bin hoặc archive folder.
 * - Chỉ cleanup sau khi verify copy hash khớp.
 * - Dry-run mode mặc định ON.
 */
import * as fs from "fs";
import * as path from "path";
import { createHash } from "crypto";
import { execFileSync } from "child_process";

const UNSUPPORTED_EXTENSIONS = [".crdownload", ".tmp", ".part", ".download"];
const UNSUPPORTED_PREFIXES = ["~$"]; // Excel lock files

/**
 * Kiểm tra file có an toàn để cleanup không.
 */
export function isSafeToCleanupFile(filePath: string, watchDir: string): boolean {
  const abs = path.resolve(filePath);
  const absWatch = path.resolve(watchDir);

  // Phải nằm trong watchDir
  if (!abs.startsWith(absWatch + path.sep) && abs !== absWatch) {
    return false;
  }

  // Phải là file, không phải directory
  try {
    const stat = fs.statSync(abs);
    if (!stat.isFile()) return false;
  } catch {
    return false;
  }

  // Extension check
  const ext = path.extname(abs).toLowerCase();
  if (![".csv", ".xlsx", ".xls"].includes(ext)) {
    return false;
  }

  // Reject temp/download-in-progress files
  if (UNSUPPORTED_EXTENSIONS.some((e) => abs.toLowerCase().endsWith(e))) {
    return false;
  }

  // Reject Excel lock files
  const basename = path.basename(abs);
  if (UNSUPPORTED_PREFIXES.some((p) => basename.startsWith(p))) {
    return false;
  }

  return true;
}

/**
 * Tính SHA-256 hash của file.
 */
export async function hashFile(filePath: string): Promise<string> {
  const buf = fs.readFileSync(filePath);
  return createHash("sha256").update(buf).digest("hex");
}

/**
 * Verify file copy: tồn tại + cùng size + cùng hash.
 */
export async function verifyCopiedFile(
  originalPath: string,
  copiedPath: string,
): Promise<boolean> {
  try {
    if (!fs.existsSync(copiedPath)) return false;

    const origStat = fs.statSync(originalPath);
    const copyStat = fs.statSync(copiedPath);
    if (origStat.size !== copyStat.size) return false;

    const origHash = await hashFile(originalPath);
    const copyHash = await hashFile(copiedPath);
    return origHash === copyHash;
  } catch {
    return false;
  }
}

export interface CleanupResult {
  ok: boolean;
  mode: "none" | "trash" | "archive";
  dryRun: boolean;
  originalPath: string;
  destination?: string;
  method?: string;
  error?: string;
  reason: string;
}

/**
 * Move file to Trash (macOS Finder Trash, not permanent delete).
 */
export async function moveToTrash(filePath: string): Promise<{ ok: boolean; method: string; error?: string }> {
  const platform = process.platform;
  const abs = path.resolve(filePath);

  try {
    if (platform === "darwin") {
      // macOS: dùng AppleScript qua osascript để move vào Trash của Finder
      const script = `tell application "Finder" to delete POSIX file "${abs}"`;
      execFileSync("osascript", ["-e", script], { timeout: 10000 });
      return { ok: true, method: "macos-finder-trash" };
    }
    if (platform === "win32") {
      // Windows: dùng PowerShell Recycle Bin
      const ps = `Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile('${abs.replace(/'/g, "''")}','OnlyErrorDialogs','SendToRecycleBin')`;
      execFileSync("powershell", ["-Command", ps], { timeout: 10000 });
      return { ok: true, method: "windows-recycle-bin" };
    }
    // Linux: move vào ~/.local/share/Trash/files
    const trashDir = path.join(process.env.HOME ?? "/tmp", ".local/share/Trash/files");
    fs.mkdirSync(trashDir, { recursive: true });
    const dest = path.join(trashDir, path.basename(abs));
    fs.renameSync(abs, dest);
    return { ok: true, method: "linux-trash-dir" };
  } catch (e: any) {
    return { ok: false, method: platform, error: e?.message ?? String(e) };
  }
}

/**
 * Move file vào archive directory.
 */
export async function moveToArchive(
  filePath: string,
  archiveDir: string,
): Promise<{ ok: boolean; destination: string; error?: string }> {
  try {
    fs.mkdirSync(archiveDir, { recursive: true });
    const basename = path.basename(filePath);
    let dest = path.join(archiveDir, basename);

    // Nếu trùng tên, thêm suffix timestamp
    if (fs.existsSync(dest)) {
      const ext = path.extname(basename);
      const name = path.basename(basename, ext);
      const ts = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
      dest = path.join(archiveDir, `${name}_${ts}${ext}`);
    }

    fs.renameSync(filePath, dest);
    return { ok: true, destination: dest };
  } catch (e: any) {
    return { ok: false, destination: "", error: e?.message ?? String(e) };
  }
}

/**
 * Cleanup wrapper — orchestrates the full cleanup flow.
 */
export async function cleanupProcessedFile(options: {
  originalPath: string;
  copiedPath: string;
  watchDir: string;
  mode: "none" | "trash" | "archive";
  archiveDir?: string;
  dryRun: boolean;
  reason: string;
  batchId?: number;
  hash?: string;
}): Promise<CleanupResult> {
  const { originalPath, copiedPath, watchDir, mode, dryRun, reason } = options;

  // Validate safe path
  if (!isSafeToCleanupFile(originalPath, watchDir)) {
    return {
      ok: false,
      mode,
      dryRun,
      originalPath,
      error: "File không an toàn để cleanup (ngoài watchDir, là directory, hoặc extension không hỗ trợ).",
      reason,
    };
  }

  // Verify copy
  const verified = await verifyCopiedFile(originalPath, copiedPath);
  if (!verified) {
    return {
      ok: false,
      mode,
      dryRun,
      originalPath,
      error: "Copy hash không khớp hoặc copy không tồn tại.",
      reason,
    };
  }

  // Dry run — chỉ log
  if (dryRun) {
    return {
      ok: true,
      mode,
      dryRun: true,
      originalPath,
      reason,
      method: "dry-run (no action taken)",
    };
  }

  // Mode none — no-op
  if (mode === "none") {
    return {
      ok: true,
      mode: "none",
      dryRun: false,
      originalPath,
      reason,
      method: "none (disabled)",
    };
  }

  // Mode trash
  if (mode === "trash") {
    const result = await moveToTrash(originalPath);
    return {
      ok: result.ok,
      mode: "trash",
      dryRun: false,
      originalPath,
      method: result.method,
      error: result.error,
      reason,
    };
  }

  // Mode archive
  if (mode === "archive") {
    const result = await moveToArchive(originalPath, options.archiveDir ?? "imports/archive");
    return {
      ok: result.ok,
      mode: "archive",
      dryRun: false,
      originalPath,
      destination: result.destination,
      error: result.error,
      reason,
    };
  }

  return {
    ok: false,
    mode,
    dryRun,
    originalPath,
    error: "Unknown mode",
    reason,
  };
}
