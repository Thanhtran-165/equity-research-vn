import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import {
  isSafeToCleanupFile,
  verifyCopiedFile,
  hashFile,
  moveToArchive,
  cleanupProcessedFile,
} from "../imports/fileCleanup";

let tmpDir: string;

beforeEach(() => {
  tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "cleanup-test-"));
});

afterEach(() => {
  fs.rmSync(tmpDir, { recursive: true, force: true });
});

function createTestFile(dir: string, name: string, content = "test data"): string {
  const fp = path.join(dir, name);
  fs.writeFileSync(fp, content);
  return fp;
}

describe("isSafeToCleanupFile", () => {
  it("accepts CSV file inside watchDir", () => {
    const fp = createTestFile(tmpDir, "test.csv");
    expect(isSafeToCleanupFile(fp, tmpDir)).toBe(true);
  });

  it("accepts XLSX file inside watchDir", () => {
    const fp = createTestFile(tmpDir, "test.xlsx");
    expect(isSafeToCleanupFile(fp, tmpDir)).toBe(true);
  });

  it("rejects file outside watchDir", () => {
    const otherDir = fs.mkdtempSync(path.join(os.tmpdir(), "other-"));
    const fp = createTestFile(otherDir, "test.csv");
    expect(isSafeToCleanupFile(fp, tmpDir)).toBe(false);
    fs.rmSync(otherDir, { recursive: true, force: true });
  });

  it("rejects directory", () => {
    const dirPath = path.join(tmpDir, "subdir");
    fs.mkdirSync(dirPath);
    expect(isSafeToCleanupFile(dirPath, tmpDir)).toBe(false);
  });

  it("rejects .crdownload temp file", () => {
    const fp = createTestFile(tmpDir, "download.crdownload");
    expect(isSafeToCleanupFile(fp, tmpDir)).toBe(false);
  });

  it("rejects .tmp file", () => {
    const fp = createTestFile(tmpDir, "export.tmp");
    expect(isSafeToCleanupFile(fp, tmpDir)).toBe(false);
  });

  it("rejects Excel lock file ~$", () => {
    const fp = createTestFile(tmpDir, "~$export.xlsx");
    expect(isSafeToCleanupFile(fp, tmpDir)).toBe(false);
  });

  it("rejects unsupported extension", () => {
    const fp = createTestFile(tmpDir, "test.pdf");
    expect(isSafeToCleanupFile(fp, tmpDir)).toBe(false);
  });

  it("rejects non-existent file", () => {
    expect(isSafeToCleanupFile(path.join(tmpDir, "nope.csv"), tmpDir)).toBe(false);
  });
});

describe("hashFile", () => {
  it("produces consistent SHA-256", async () => {
    const fp = createTestFile(tmpDir, "test.csv", "hello world");
    const h = await hashFile(fp);
    expect(h).toHaveLength(64);
    expect(h).toMatch(/^[0-9a-f]+$/);
  });
});

describe("verifyCopiedFile", () => {
  it("returns true for identical copy", async () => {
    const orig = createTestFile(tmpDir, "orig.csv", "test data 123");
    const copy = path.join(tmpDir, "copy.csv");
    fs.copyFileSync(orig, copy);
    expect(await verifyCopiedFile(orig, copy)).toBe(true);
  });

  it("returns false for different content", async () => {
    const orig = createTestFile(tmpDir, "orig.csv", "original");
    const copy = createTestFile(tmpDir, "copy.csv", "different");
    expect(await verifyCopiedFile(orig, copy)).toBe(false);
  });

  it("returns false for non-existent copy", async () => {
    const orig = createTestFile(tmpDir, "orig.csv", "data");
    expect(await verifyCopiedFile(orig, path.join(tmpDir, "nope.csv"))).toBe(false);
  });
});

describe("moveToArchive", () => {
  it("moves file to archive dir", async () => {
    const fp = createTestFile(tmpDir, "test.csv", "data");
    const archiveDir = path.join(tmpDir, "archive");
    const result = await moveToArchive(fp, archiveDir);
    expect(result.ok).toBe(true);
    expect(fs.existsSync(result.destination)).toBe(true);
    expect(fs.existsSync(fp)).toBe(false);
  });

  it("creates suffix for duplicate filename", async () => {
    const fp = createTestFile(tmpDir, "test.csv", "data1");
    const archiveDir = path.join(tmpDir, "archive");
    fs.mkdirSync(archiveDir, { recursive: true });
    fs.writeFileSync(path.join(archiveDir, "test.csv"), "existing");

    const result = await moveToArchive(fp, archiveDir);
    expect(result.ok).toBe(true);
    expect(result.destination).toContain("test_");
    expect(result.destination).toContain(".csv");
    expect(path.basename(result.destination)).not.toBe("test.csv");
  });
});

describe("cleanupProcessedFile", () => {
  it("mode none returns ok with no action", async () => {
    const orig = createTestFile(tmpDir, "test.csv", "data");
    const copy = path.join(tmpDir, "copy.csv");
    fs.copyFileSync(orig, copy);
    const result = await cleanupProcessedFile({
      originalPath: orig,
      copiedPath: copy,
      watchDir: tmpDir,
      mode: "none",
      dryRun: false,
      reason: "test",
    });
    expect(result.ok).toBe(true);
    expect(fs.existsSync(orig)).toBe(true); // file still there
  });

  it("dry-run does not move file", async () => {
    const orig = createTestFile(tmpDir, "test.csv", "data");
    const copy = path.join(tmpDir, "copy.csv");
    fs.copyFileSync(orig, copy);
    const result = await cleanupProcessedFile({
      originalPath: orig,
      copiedPath: copy,
      watchDir: tmpDir,
      mode: "trash",
      dryRun: true,
      reason: "test",
    });
    expect(result.ok).toBe(true);
    expect(result.dryRun).toBe(true);
    expect(fs.existsSync(orig)).toBe(true); // file still there
  });

  it("archive mode moves file", async () => {
    const orig = createTestFile(tmpDir, "test.csv", "data");
    const copy = path.join(tmpDir, "copy.csv");
    fs.copyFileSync(orig, copy);
    const archiveDir = path.join(tmpDir, "archive");
    const result = await cleanupProcessedFile({
      originalPath: orig,
      copiedPath: copy,
      watchDir: tmpDir,
      mode: "archive",
      archiveDir,
      dryRun: false,
      reason: "test",
    });
    expect(result.ok).toBe(true);
    expect(fs.existsSync(orig)).toBe(false); // moved
    expect(fs.existsSync(result.destination!)).toBe(true);
  });

  it("fails when copy hash mismatch", async () => {
    const orig = createTestFile(tmpDir, "test.csv", "original");
    const copy = createTestFile(tmpDir, "copy.csv", "different");
    const result = await cleanupProcessedFile({
      originalPath: orig,
      copiedPath: copy,
      watchDir: tmpDir,
      mode: "archive",
      archiveDir: path.join(tmpDir, "archive"),
      dryRun: false,
      reason: "test",
    });
    expect(result.ok).toBe(false);
    expect(fs.existsSync(orig)).toBe(true); // not moved
  });

  it("fails for file outside watchDir", async () => {
    const otherDir = fs.mkdtempSync(path.join(os.tmpdir(), "other-"));
    const orig = createTestFile(otherDir, "test.csv", "data");
    const copy = createTestFile(tmpDir, "copy.csv", "data");
    const result = await cleanupProcessedFile({
      originalPath: orig,
      copiedPath: copy,
      watchDir: tmpDir,
      mode: "archive",
      archiveDir: path.join(tmpDir, "archive"),
      dryRun: false,
      reason: "test",
    });
    expect(result.ok).toBe(false);
    fs.rmSync(otherDir, { recursive: true, force: true });
  });
});
