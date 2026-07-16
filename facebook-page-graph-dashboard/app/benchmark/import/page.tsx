"use client";

import Link from "next/link";
import BenchmarkImportBox from "@/components/BenchmarkImportBox";
import BenchmarkWarningBox from "@/components/BenchmarkWarningBox";

export default function BenchmarkImportPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Import benchmark từ CSV</h1>
        <p className="text-gray-500 text-sm">
          Paste CSV competitor metrics. Validate trước, import các dòng hợp lệ.
        </p>
      </div>

      <BenchmarkWarningBox variant="compact" />

      <BenchmarkImportBox onImported={() => {}} />

      <div className="flex gap-2">
        <Link href="/benchmark" className="btn-secondary">
          ← Quay lại Benchmark
        </Link>
      </div>
    </div>
  );
}
