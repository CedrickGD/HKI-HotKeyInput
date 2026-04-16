import * as React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

type ErrorBoundaryProps = {
  children: React.ReactNode;
};

type ErrorBoundaryState = {
  error: Error | null;
};

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("[HKI] Unhandled error:", error, info);
  }

  private handleReset = () => {
    this.setState({ error: null });
  };

  private handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.error) {
      return (
        <div className="flex h-full w-full items-center justify-center bg-background p-8 text-foreground">
          <div className="flex max-w-md flex-col items-center gap-4 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10 text-destructive">
              <AlertTriangle className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-xl font-semibold tracking-tight">
                Something went wrong
              </h1>
              <p className="mt-1.5 text-sm text-muted-foreground">
                The interface hit an unexpected error. Try again, or reload the
                window to recover.
              </p>
              <pre className="mt-3 max-h-40 overflow-auto rounded-md border border-border/60 bg-muted/40 px-3 py-2 text-left font-mono text-[11px] text-muted-foreground">
                {this.state.error.message}
              </pre>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={this.handleReset}
                className="inline-flex h-9 items-center gap-2 rounded-md border border-border bg-background px-4 text-sm font-medium transition-colors hover:bg-accent"
              >
                <RefreshCw className="h-4 w-4" />
                Try again
              </button>
              <button
                type="button"
                onClick={this.handleReload}
                className="inline-flex h-9 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-soft transition-colors hover:bg-primary/90"
              >
                Reload window
              </button>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
