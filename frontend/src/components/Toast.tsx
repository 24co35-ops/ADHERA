import React, { useEffect } from 'react';
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from 'lucide-react';
import clsx from 'clsx';

export type ToastType = 'success' | 'warning' | 'error' | 'info';

export interface ToastMessage {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

interface ToastProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

export const ToastContainer: React.FC<ToastProps> = ({ toasts, onDismiss }) => {
  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col space-y-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  );
};

const ToastItem: React.FC<{ toast: ToastMessage; onDismiss: (id: string) => void }> = ({
  toast,
  onDismiss,
}) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss(toast.id);
    }, toast.duration || 4000);
    return () => clearTimeout(timer);
  }, [toast, onDismiss]);

  const icons = {
    success: <CheckCircle2 className="w-5 h-5 text-status-success shrink-0" />,
    warning: <AlertTriangle className="w-5 h-5 text-status-warning shrink-0" />,
    error: <AlertCircle className="w-5 h-5 text-status-error shrink-0" />,
    info: <Info className="w-5 h-5 text-primary shrink-0" />,
  };

  const borders = {
    success: 'border-status-success/30',
    warning: 'border-status-warning/30',
    error: 'border-status-error/30',
    info: 'border-primary/30',
  };

  return (
    <div
      className={clsx(
        'pointer-events-auto flex items-center justify-between p-4 rounded-2xl glass-panel shadow-2xl border transition-all duration-200 animate-in slide-in-from-bottom-5',
        borders[toast.type]
      )}
    >
      <div className="flex items-center space-x-3 mr-2">
        {icons[toast.type]}
        <p className="text-sm font-medium text-white">{toast.message}</p>
      </div>
      <button
        onClick={() => onDismiss(toast.id)}
        aria-label="Dismiss notification"
        className="text-on-surface-variant hover:text-white p-1 rounded-lg"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};
