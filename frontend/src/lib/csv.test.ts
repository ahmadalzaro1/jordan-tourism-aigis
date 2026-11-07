import { describe, it, expect } from "vitest";
import { toCSV } from "./csv";
describe("CSV exports", () => {
  it("escapes commas, quotes, and newlines", () => {
    expect(toCSV([{name: 'Petra, \"Jordan\"\nsite'}])).toBe('"name"\r\n"Petra, ""Jordan""\nsite"');
  });
  it("retains fields from later records and handles empty lists", () => {
    expect(toCSV([{a:1},{b:2}])).toBe('"a","b"\r\n"1",""\r\n"","2"');
    expect(toCSV([])).toBe("");
  });
  it("neutralizes spreadsheet formulas from uploaded text", () => {
    expect(toCSV([{name: '=HYPERLINK("https://example.org")'}])).toContain("'=HYPERLINK");
  });
});
