import React from "react";

interface Props {
  className?: string;
  /** dạng block/h/text-line */
  variant?: "block" | "text";
  width?: string;
  height?: string;
  count?: number;
}

export default function Skeleton({
  className = "",
  variant = "block",
  width,
  height,
  count = 1,
}: Props) {
  const items = Array.from({ length: count });
  if (variant === "text") {
    return (
      <>
        {items.map((_, i) => (
          <div
            key={i}
            className={`skeleton h-3 ${className}`}
            style={{ width: width ?? "100%" }}
          />
        ))}
      </>
    );
  }
  return (
    <>
      {items.map((_, i) => (
        <div
          key={i}
          className={`skeleton ${className}`}
          style={{ width: width ?? "100%", height: height ?? "1rem" }}
        />
      ))}
    </>
  );
}

export function CardSkeleton() {
  return (
    <div className="card p-4 space-y-3">
      <Skeleton variant="text" width="40%" />
      <Skeleton height="2rem" width="60%" />
      <Skeleton variant="text" width="50%" />
    </div>
  );
}
