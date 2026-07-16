/**
 * Helper chung — parse uploaded file (CSV hoặc XLSX) → headers + rows.
 */
import { parseCsvBuffer, type ParsedCsv } from "./parseCsv";
import { parseXlsxBuffer, type ParsedXlsx } from "./parseXlsx";

export type FileFormat = "csv" | "xlsx" | "xls";

export interface ParsedFile {
  format: FileFormat;
  headers: string[];
  rows: string[][];
  warnings: string[];
  meta: {
    delimiter?: string;
    sheetName?: string;
    headerRowIndex: number;
  };
}

export function detectFormat(filename: string): FileFormat | null {
  const lower = filename.toLowerCase();
  if (lower.endsWith(".csv")) return "csv";
  if (lower.endsWith(".xlsx")) return "xlsx";
  if (lower.endsWith(".xls")) return "xls";
  return null;
}

export function parseFileBuffer(buf: Buffer, filename: string): ParsedFile {
  const format = detectFormat(filename);
  if (!format) {
    throw new Error(`Unsupported file type: ${filename}`);
  }

  if (format === "csv") {
    const r: ParsedCsv = parseCsvBuffer(buf);
    return {
      format,
      headers: r.headers,
      rows: r.rows,
      warnings: r.warnings,
      meta: { delimiter: r.delimiter, headerRowIndex: r.headerRowIndex },
    };
  }

  // xlsx hoặc xls
  const r: ParsedXlsx = parseXlsxBuffer(buf);
  return {
    format,
    headers: r.headers,
    rows: r.rows,
    warnings: r.warnings,
    meta: { sheetName: r.sheetName, headerRowIndex: r.headerRowIndex },
  };
}

/**
 * SHA-256 hash của file content — để dedupe.
 */
export async function hashFileBuffer(buf: Buffer): Promise<string> {
  const { createHash } = await import("crypto");
  return createHash("sha256").update(buf).digest("hex");
}
