import React, { useEffect } from 'react';
import { CheckCircle2, XCircle, Info, X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info';

interface ToastProps {
    id: number;
    message: string;
    type: ToastType;
    onClose: (id: number) => void;
}

export default function Toast({ id, message, type, onClose }: ToastProps) {
    useEffect(() => {
        const timer = setTimeout(() => {
            onClose(id);
        }, 4000); // Auto close after 4s
        return () => clearTimeout(timer);
    }, [id, onClose]);

    const bgColors = {
        success: 'bg-emerald-600/10 border-emerald-600/20 text-emerald-600 dark:text-emerald-400',
        error: 'bg-red-600/10 border-red-600/20 text-red-600 dark:text-red-400',
        info: 'bg-blue-600/10 border-blue-600/20 text-blue-600 dark:text-blue-400'
    };

    const icons = {
        success: <CheckCircle2 size={18} className="shrink-0" />,
        error: <XCircle size={18} className="shrink-0" />,
        info: <Info size={18} className="shrink-0" />
    };

    return (
        <div className={`flex items-start gap-3 p-4 rounded-xl border backdrop-blur-md shadow-lg animate-in slide-in-from-top-2 fade-in duration-300 w-full max-w-sm pointer-events-auto bg-background/95 ${bgColors[type]}`}>
            <div className="mt-0.5">{icons[type]}</div>
            <div className="flex-1 text-sm font-medium leading-relaxed dark:text-white text-foreground">
                {message}
            </div>
            <button
                onClick={() => onClose(id)}
                className="opacity-50 hover:opacity-100 transition-opacity p-0.5 -mt-1 -mr-1"
            >
                <X size={16} />
            </button>
        </div>
    );
}

// Container for managing multiple toasts
export function ToastContainer({ toasts, removeToast }: { toasts: any[], removeToast: (id: number) => void }) {
    return (
        <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 w-full max-w-sm pointer-events-none">
            {toasts.map(toast => (
                <Toast
                    key={toast.id}
                    id={toast.id}
                    message={toast.message}
                    type={toast.type}
                    onClose={removeToast}
                />
            ))}
        </div>
    );
}
