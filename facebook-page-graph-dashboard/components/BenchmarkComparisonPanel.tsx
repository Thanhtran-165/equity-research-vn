import React from "react";

interface Props {
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  loading?: boolean;
}

export default function BenchmarkComparisonPanel({
  strengths,
  weaknesses,
  recommendations,
  loading,
}: Props) {
  if (loading) {
    return (
      <div className="card p-5">
        <div className="h-5 bg-gray-100 animate-pulse rounded w-1/3 mb-3" />
        <div className="h-4 bg-gray-100 animate-pulse rounded w-2/3 mb-2" />
        <div className="h-4 bg-gray-100 animate-pulse rounded w-1/2" />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
      <Panel
        title="Điểm mạnh của Page bạn"
        items={strengths}
        tone="green"
        emptyText="Chưa phát hiện điểm mạnh nổi bật so với peer."
      />
      <Panel
        title="Điểm yếu tương đối"
        items={weaknesses}
        tone="red"
        emptyText="Không có điểm yếu rõ rệt so với peer."
      />
      <Panel
        title="Gợi ý chiến lược nội dung"
        items={recommendations}
        tone="brand"
        emptyText="Chưa có gợi ý — cần thêm dữ liệu peer."
      />
    </div>
  );
}

function Panel({
  title,
  items,
  tone,
  emptyText,
}: {
  title: string;
  items: string[];
  tone: "green" | "red" | "brand";
  emptyText: string;
}) {
  const tones: Record<string, { wrap: string; head: string; dot: string }> = {
    green: {
      wrap: "border-green-200 bg-green-50",
      head: "text-green-800",
      dot: "text-green-600",
    },
    red: {
      wrap: "border-red-200 bg-red-50",
      head: "text-red-800",
      dot: "text-red-600",
    },
    brand: {
      wrap: "border-brand-200 bg-brand-50",
      head: "text-brand-800",
      dot: "text-brand-600",
    },
  };
  const t = tones[tone];
  return (
    <div className={`card p-4 ${t.wrap}`}>
      <h3 className={`font-semibold ${t.head} mb-2`}>{title}</h3>
      {items.length === 0 ? (
        <p className="text-sm text-gray-600">{emptyText}</p>
      ) : (
        <ul className="space-y-2 text-sm text-gray-800">
          {items.map((s, i) => (
            <li key={i} className="flex gap-2">
              <span className={t.dot}>•</span>
              <span>{s}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
