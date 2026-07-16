/**
 * XLSX parser cho Meta Business Suite export.
 *
 * Dùng thư viện `xlsx` (SheetJS).
 * - Default: lấy sheet đầu tiên.
 * - Tự detect header row (scan 5 dòng đầu).
 */
import * as XLSX from "xlsx";

export interface ParsedXlsx {
  headers: string[];
  rows: string[][];
  sheetName: string;
  headerRowIndex: number;
  warnings: string[];
}

export function parseXlsxBuffer(buf: Buffer): ParsedXlsx {
  const warnings: string[] = [];
  const wb = XLSX.read(buf, { type: "buffer" });
  const sheetName = wb.SheetNames[0];
  if (!sheetName) {
    return { headers: [], rows: [], sheetName: "", headerRowIndex: 0, warnings: ["no-sheet"] };
  }
  const sheet = wb.Sheets[sheetName];
  // cellDates để parse date cell thành string ISO
  const json: any[][] = XLSX.utils.sheet_to_json(sheet, {
    header: 1,
    raw: false,
    defval: "",
    blankrows: false,
  });

  if (!json.length) {
    return { headers: [], rows: [], sheetName, headerRowIndex: 0, warnings: ["empty-sheet"] };
  }

  // Detect header row — scan 5 dòng đầu, chọn row có nhiều cell khác rỗng + không phải số-only
  let headerRowIndex = 0;
  let bestScore = -1;
  for (let i = 0; i < Math.min(5, json.length); i++) {
    const row = json[i] ?? [];
    const nonEmpty = row.filter((c) => String(c).trim().length > 0).length;
    const nonNumeric = row.filter(
      (c) => isNaN(Number(String(c).replace(/[,.]/g, ""))) && String(c).trim().length > 0,
    ).length;
    const score = nonEmpty * 2 + nonNumeric;
    if (score > bestScore) {
      bestScore = score;
      headerRowIndex = i;
    }
  }

  const headers = (json[headerRowIndex] ?? []).map((c) => String(c).trim());
  const rows = json.slice(headerRowIndex + 1).map((r) => (r as any[]).map((c) => String(c ?? "")));

  return { headers, rows, sheetName, headerRowIndex, warnings };
}
