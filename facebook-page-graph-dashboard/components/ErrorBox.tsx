"use client";

import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  title?: string;
  error: { code?: string; message: string; details?: any } | string;
  onRetry?: () => void;
}

export default function ErrorBox({ title = "Có lỗi", error, onRetry }: Props) {
  const errObj =
    typeof error === "string"
      ? { message: error }
      : error;

  return (
    <div className="card p-4 border-danger-200 dark:border-danger-500/30 bg-danger-50/50 dark:bg-danger-500/5 animate-fade-in">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <AlertTriangle className="w-4 h-4 text-danger-600 dark:text-danger-500 shrink-0" />
            <h3 className="font-semibold text-danger-700 dark:text-danger-400 text-sm">
              {title}
            </h3>
            {errObj.code && (
              <span className="badge bg-danger-200 text-danger-800 dark:bg-danger-500/20 dark:text-danger-400 font-mono text-[10px]">
                {errObj.code}
              </span>
            )}
          </div>
          <p className="text-sm text-danger-700/90 dark:text-danger-300/90 mt-1.5 break-words">
            {errObj.message}
          </p>
          {errObj.details?.tokenHint && (
            <p className="text-xs text-danger-600/80 dark:text-danger-400/80 mt-1.5">
              {errObj.details.tokenHint}
            </p>
          )}
          {errObj.details?.fbErrorCode != null && (
            <p className="text-xs text-muted font-mono mt-1">
              fb_code={errObj.details.fbErrorCode}
              {errObj.details.fbSubcode != null && ` · subcode=${errObj.details.fbSubcode}`}
            </p>
          )}
        </div>
        {onRetry && (
          <button onClick={onRetry} className="btn-secondary !py-1.5 shrink-0">
            <RefreshCw className="w-3.5 h-3.5" />
            <span className="text-xs">Thử lại</span>
          </button>
        )}
      </div>
    </div>
  );
}
