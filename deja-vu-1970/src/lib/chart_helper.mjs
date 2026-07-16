// src/lib/chart_helper.mjs
// Bridge between Chart.mjs (returns HTML string) and React server components.
import { Chart } from "../components/Chart.mjs";

export function chartHtml(props) {
  return Chart(props);
}
