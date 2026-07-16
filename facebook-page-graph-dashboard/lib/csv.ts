/**
 * CSV helper. Không dùng dependency ngoài.
 */

function escapeCell(value: unknown): string {
  if (value === null || value === undefined) return "";
  const s = String(value);
  // RFC4180: nếu chứa ", , \n hoặc \r → bọc bằng "" và escape " thành ""
  if (/[",\n\r]/.test(s)) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

export function toCsv(rows: Record<string, any>[], headers?: string[]): string {
  if (!rows || rows.length === 0) {
    return headers ? headers.join(",") : "";
  }
  const cols = headers ?? Object.keys(rows[0]);
  const head = cols.join(",");
  const body = rows
    .map((row) => cols.map((c) => escapeCell(row[c])).join(","))
    .join("\n");
  return `${head}\n${body}`;
}

export function csvFilename(prefix: string): string {
  const ts = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
  return `${prefix}-${ts}.csv`;
}

/**
 * Minimal RFC4180 CSV parser (no external dep).
 * Hỗ trợ quote ", escaped quote "", comma delimiter, newline trong ô có quote.
 */
export function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let inQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        field += c;
      }
    } else {
      if (c === '"') {
        inQuotes = true;
      } else if (c === ",") {
        row.push(field);
        field = "";
      } else if (c === "\n") {
        row.push(field);
        rows.push(row);
        row = [];
        field = "";
      } else if (c === "\r") {
        // bỏ qua, xử lý \n ở ký tự tiếp theo
      } else {
        field += c;
      }
    }
  }
  // flush
  if (field.length > 0 || row.length > 0) {
    row.push(field);
    rows.push(row);
  }
  // bỏ row rỗng hoàn toàn
  return rows.filter((r) => r.length > 1 || (r.length === 1 && r[0].trim() !== ""));
}
