import { redirect } from "next/navigation";

// Redirect old /benchmark → /public-benchmark (v3.2 module)
export default function BenchmarkRedirect() {
  redirect("/public-benchmark");
}
