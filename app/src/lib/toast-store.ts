export type ToastKind = "success" | "error" | "info";

export type ToastAction = {
  label: string;
  onClick: () => void;
};

export type Toast = {
  id: string;
  kind: ToastKind;
  title: string;
  description?: string;
  durationMs: number;
  action?: ToastAction;
};

type Listener = (toasts: Toast[]) => void;

type PushOptions = {
  description?: string;
  durationMs?: number;
  action?: ToastAction;
};

class ToastStore {
  private toasts: Toast[] = [];
  private listeners = new Set<Listener>();

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    listener(this.toasts);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private emit() {
    for (const l of this.listeners) l(this.toasts);
  }

  push(kind: ToastKind, title: string, options: PushOptions = {}) {
    const id =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `t_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    const durationMs = options.durationMs ?? 2800;
    const toast: Toast = {
      id,
      kind,
      title,
      description: options.description,
      durationMs,
      action: options.action,
    };
    this.toasts = [toast, ...this.toasts].slice(0, 5);
    this.emit();
    if (durationMs > 0) {
      window.setTimeout(() => this.dismiss(id), durationMs);
    }
    return id;
  }

  dismiss(id: string) {
    this.toasts = this.toasts.filter((t) => t.id !== id);
    this.emit();
  }

  clear() {
    this.toasts = [];
    this.emit();
  }
}

export const toastStore = new ToastStore();

export const toast = {
  success(title: string, description?: string, action?: ToastAction) {
    return toastStore.push("success", title, { description, action });
  },
  error(title: string, description?: string, action?: ToastAction) {
    return toastStore.push("error", title, {
      description,
      action,
      durationMs: 4500,
    });
  },
  info(title: string, description?: string, action?: ToastAction) {
    return toastStore.push("info", title, { description, action });
  },
};
