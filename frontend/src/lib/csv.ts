export function toCSV(rows: Record<string, unknown>[]): string {
  if (!rows.length) return "";
  const headers = [...new Set(rows.flatMap(Object.keys))];
  const cell = (value: unknown) => {
    let text = value == null ? "" : typeof value === "object" ? JSON.stringify(value) : String(value);
    if (typeof value === "string" && /^[=+@-]/.test(text)) text = "'" + text;
    return `"${text.replace(/"/g, '\"\"')}"`;
  };
  return [headers.map(cell).join(","), ...rows.map(row => headers.map(h => cell(row[h])).join(","))].join("\r\n");
}
