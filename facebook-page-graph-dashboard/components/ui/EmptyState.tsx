import React from "react";
import { Inbox } from "lucide-react";

interface Props {
  title?: string;
  description?: React.ReactNode;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}

export default function EmptyState({
  title = "Chưa có dữ liệu",
  description,
  icon,
  action,
}: Props) {
  return (
    <div className="card p-8 text-center flex flex-col items-center gap-2">
      <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-muted">
        {icon ?? <Inbox className="w-6 h-6" />}
      </div>
      <div className="font-medium text-slate-700 dark:text-slate-200">{title}</div>
      {description && <div className="text-sm text-muted max-w-sm">{description}</div>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
