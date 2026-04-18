import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallbackMessage?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * ErrorBoundary — Catches unhandled React rendering errors
 * and displays a recovery UI instead of a blank screen.
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary] Caught rendering error:', error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          position: 'fixed',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#0C0E14',
          zIndex: 9999,
        }}>
          <div style={{
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(248, 113, 113, 0.3)',
            borderRadius: '16px',
            padding: '32px 40px',
            maxWidth: '480px',
            textAlign: 'center',
            color: '#e2e8f0',
          }}>
            <div style={{ fontSize: '32px', marginBottom: '16px' }}>⚠️</div>
            <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '8px', color: '#F87171' }}>
              Rendering Error
            </h2>
            <p style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)', marginBottom: '16px', lineHeight: 1.5 }}>
              {this.props.fallbackMessage || 'A component crashed. This is usually caused by unexpected data from the backend.'}
            </p>
            <pre style={{
              fontSize: '10px',
              color: 'rgba(248, 113, 113, 0.8)',
              background: 'rgba(0,0,0,0.3)',
              padding: '12px',
              borderRadius: '8px',
              textAlign: 'left',
              overflow: 'auto',
              maxHeight: '120px',
              marginBottom: '16px',
            }}>
              {this.state.error?.message}
            </pre>
            <button
              onClick={this.handleReset}
              style={{
                padding: '10px 24px',
                background: 'rgba(103, 232, 249, 0.1)',
                border: '1px solid rgba(103, 232, 249, 0.3)',
                color: '#67e8f9',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '12px',
              }}
            >
              Retry
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
