import React from "react";

interface Props {
  /** compact = gọn ở header, full = box nổi bật */
  variant?: "compact" | "full";
}

export default function BenchmarkWarningBox({ variant = "full" }: Props) {
  if (variant === "compact") {
    return (
      <p className="text-xs text-amber-700">
        ⚠️ Benchmark bằng chỉ số công khai, không phải Facebook Page Insights chính thức của đối thủ.
      </p>
    );
  }
  return (
    <div className="card p-4 border-amber-200 bg-amber-50">
      <div className="flex items-start gap-3">
        <span className="text-amber-600 text-lg">⚠️</span>
        <div className="text-sm text-amber-900">
          <p className="font-semibold mb-1">Lưu ý về dữ liệu benchmark</p>
          <p>
            Đây là benchmark bằng <strong>chỉ số công khai</strong> (followers, reactions,
            comments, shares, video views, tần suất đăng bài), <strong>không phải Facebook
            Page Insights chính thức</strong> của đối thủ. Các chỉ số private như reach,
            impressions, clicks, engaged users <em>không thể</em> lấy được cho Page khác.
          </p>
          <p className="mt-2">
            Không so sánh trực tiếp public engagement với internal reach-based engagement rate.
          </p>
        </div>
      </div>
    </div>
  );
}
