/**
 * CSV parser cho Meta Business Suite export.
 *
 * Dùng thư viện `csv-parse` (RFC 4180 chuẩn) để xử lý quoted fields có newline
 * (thường gặp trong export Meta Business Suite khi header có multiline cell).
 *
 * Hỗ trợ:
 * - UTF-8 BOM stripping
 * - Auto-detect delimiter (comma vs semicolon vs tab)
 * - Quoted fields có newline bên trong
 * - Vietnamese text
 */
import { parse } from "csv-parse/sync";

export interface ParsedCsv {
  headers: string[];
  rows: string[][];
  delimiter: string;
  headerRowIndex: number;
  warnings: string[];
}

/**
 * Strip UTF-8 BOM (\uFEFF) nếu có.
 */
function stripBom(text: string): string {
  return text.charCodeAt(0) === 0xfeff ? text.slice(1) : text;
}

/**
 * Detect delimiter (comma vs semicolon vs tab) bằng cách đếm trong header row.
 */
function detectDelimiter(firstLine: string): string {
  const candidates = [",", ";", "\t", "|"];
  let best = ",";
  let bestCount = -1;
  for (const c of candidates) {
    const count = firstLine.split(c).length;
    if (count > bestCount) {
      bestCount = count;
      best = c;
    }
  }
  return best;
}

/**
 * Parse 1 line có xử lý quoted fields + escape "" trong quote.
 * Hỗ trợ newline trong ô có quote.
 */
function parseLine(text: string, delimiter: string, startIdx: number): { cells: string[]; nextIdx: number } {
  const cells: string[] = [];
  let i = startIdx;
  let current = "";
  let inQuotes = false;

  while (i < text.length) {
    const c = text[i];

    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') {
          current += '"';
          i += 2;
          continue;
        }
        inQuotes = false;
        i++;
        continue;
      }
      current += c;
      i++;
      continue;
    }

    // Not in quotes
    if (c === '"') {
      inQuotes = true;
      i++;
      continue;
    }
    if (c === delimiter) {
      cells.push(current);
      current = "";
      i++;
      continue;
    }
    if (c === "\r") {
      // Treat as line terminator cùng \n
      if (text[i + 1] === "\n") i++;
      break;
    }
    if (c === "\n") {
      break;
    }
    current += c;
    i++;
  }

  cells.push(current);
  return { cells, nextIdx: i + 1 };
}

/**
 * Parse toàn bộ CSV text → headers + rows.
 * Dùng csv-parse (RFC 4180) để xử lý quoted fields có newline (thường gặp Meta export).
 * Auto-skip các dòng rỗng ở đầu (nếu Meta có dòng title).
 * Auto-detect header row bằng cách tìm row có nhiều field non-numeric nhất.
 */
export function parseCsv(text: string): ParsedCsv {
  const cleaned = stripBom(text.replace(/^\uFEFF/, ""));
  const warnings: string[] = [];

  if (!cleaned.trim()) {
    return { headers: [], rows: [], delimiter: ",", headerRowIndex: 0, warnings: ["empty-file"] };
  }

  // Detect delimiter từ dòng đầu không rỗng
  const firstNonEmpty = cleaned.split(/\r?\n/).find((l) => l.trim().length > 0) ?? "";
  const delimiter = detectDelimiter(firstNonEmpty);

  // Parse synchronous (csv-parse/sync)
  const allRows: string[][] = [];
  try {
    const records = parse(cleaned, {
      delimiter,
      trim: true,
      skip_empty_lines: true,
      relax_quotes: true,
      relax_column_count: true,
    });
    allRows.push(...records);
  } catch (e: any) {
    // Fallback to legacy line-by-line parse if csv-parse fails
    return legacyParse(cleaned, delimiter);
  }

  if (allRows.length === 0) {
    return { headers: [], rows: [], delimiter, headerRowIndex: 0, warnings: ["no-rows"] };
  }

  // Detect header row — scan 5 dòng đầu, chọn row có nhiều field non-numeric nhất
  let headerRowIndex = 0;
  let bestScore = -1;
  for (let i = 0; i < Math.min(5, allRows.length); i++) {
    const row = allRows[i];
    const nonEmpty = row.filter((c) => c.trim().length > 0).length;
    const nonNumeric = row.filter(
      (c) => isNaN(Number(c.replace(/[,.]/g, ""))) && c.trim().length > 0,
    ).length;
    const score = nonEmpty * 2 + nonNumeric;
    if (score > bestScore) {
      bestScore = score;
      headerRowIndex = i;
    }
  }

  const headers = allRows[headerRowIndex].map((h) => h.trim());
  const rows = allRows.slice(headerRowIndex + 1);

  return { headers, rows, delimiter, headerRowIndex, warnings };
}

/**
 * Fallback parser (legacy line-by-line) nếu csv-parse throw.
 */
function legacyParse(cleaned: string, delimiter: string): ParsedCsv {
  const allRows: string[][] = [];
  let idx = 0;
  while (idx < cleaned.length) {
    if (cleaned[idx] === "\n" || cleaned[idx] === "\r") {
      idx++;
      continue;
    }
    const { cells, nextIdx } = parseLine(cleaned, delimiter, idx);
    if (cells.length > 1 || (cells.length === 1 && cells[0].trim().length > 0)) {
      allRows.push(cells);
    }
    idx = nextIdx;
  }
  if (allRows.length === 0) {
    return { headers: [], rows: [], delimiter, headerRowIndex: 0, warnings: ["no-rows"] };
  }
  let headerRowIndex = 0;
  let bestScore = -1;
  for (let i = 0; i < Math.min(5, allRows.length); i++) {
    const row = allRows[i];
    const nonEmpty = row.filter((c) => c.trim().length > 0).length;
    const nonNumeric = row.filter(
      (c) => isNaN(Number(c.replace(/[,.]/g, ""))) && c.trim().length > 0,
    ).length;
    const score = nonEmpty * 2 + nonNumeric;
    if (score > bestScore) {
      bestScore = score;
      headerRowIndex = i;
    }
  }
  const headers = allRows[headerRowIndex].map((h) => h.trim());
  const rows = allRows.slice(headerRowIndex + 1);
  return { headers, rows, delimiter, headerRowIndex, warnings: ["fallback-parser"] };
}

/**
 * Parse CSV từ Buffer (hỗ trợ upload file).
 */
export function parseCsvBuffer(buf: Buffer): ParsedCsv {
  return parseCsv(buf.toString("utf8"));
}
