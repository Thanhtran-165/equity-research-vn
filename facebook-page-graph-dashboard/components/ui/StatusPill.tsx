import React from "react";
import { Check, X, AlertCircle } from "lucide-react";

type Tone = "success" | "warning" | "danger" | "neutral" | "info" | "proxy";

const TONES: Record<Tone, string> = {
  success: "bg-success-100 text-success-700 dark:bg-success-500/15 dark:text-success-500",
  warning: "bg-warning-100 text-warning-700 dark:bg-warning-500/15 dark:text-warning-500",
  danger: "bg-danger-100 text-danger-700 dark:bg-danger-500/15 dark:text-danger-500",
  neutral: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  info: "bg-brand-100 text-brand-800 dark:bg-brand-500/15 dark:text-brand-300",
  proxy: "bg-purple-100 text-purple-700 dark:bg-purple-500/15 dark:text-purple-400",
};

interface Props {
  tone?: Tone;
  children: React.ReactNode;
  icon?: React.ReactNode;
}

export default function StatusPill({ tone = "neutral", children, icon }: Props) {
  return (
    <span className={`badge ${TONES[tone]} gap-1`}>
      {icon}
      {children}
    </span>
  );
}

export function SuccessPill({ children = "Live" }: { children?: React.ReactNode }) {
  return <StatusPill tone="success" icon={<Check className="w-3 h-3" />}>{children}</StatusPill>;
}
export function DangerPill({ children = "Lỗi" }: { children?: React.ReactNode }) {
  return <StatusPill tone="danger" icon={<X className="w-3 h-3" />}>{children}</StatusPill>;
}
export function WarningPill({ children = "Cảnh báo" }: { children?: React.ReactNode }) {
  return <StatusPill tone="warning" icon={<AlertCircle className="w-3 h-3" />}>{children}</StatusPill>;
}
export function ProxyPill({ children = "proxy" }: { children?: React.ReactNode }) {
  return <StatusPill tone="proxy" icon={<AlertCircle className="w-3 h-3" />}>{children}</StatusPill>;
}
