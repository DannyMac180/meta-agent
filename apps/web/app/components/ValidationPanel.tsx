import type { ValidationResult } from "../workers/validation-worker";

interface ValidationPanelProps {
  errors?: ValidationResult["errors"];
  onErrorClick?: (error: ValidationResult["errors"][0]) => void;
}

export default function ValidationPanel({ errors, onErrorClick }: ValidationPanelProps) {
  if (!errors || errors.length === 0) {
    return (
      <div className="validation-panel validation-panel--success">
        <div className="validation-header">
          <span className="validation-icon">✅</span>
          <h3>Validation Passed</h3>
        </div>
        <p>Your spec is valid and ready to save.</p>
      </div>
    );
  }

  return (
    <div className="validation-panel validation-panel--errors">
      <div className="validation-header">
        <span className="validation-icon">❌</span>
        <h3>Validation Errors ({errors.length})</h3>
      </div>
      
      <div className="validation-errors">
        {errors.map((error, index) => (
          <div 
            key={index}
            className="validation-error"
            onClick={() => onErrorClick?.(error)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                onErrorClick?.(error);
              }
            }}
          >
            <div className="error-path">
              {error.path.length > 0 ? error.path.join('.') : 'Root'}
            </div>
            <div className="error-message">{error.message}</div>
            <div className="error-code">{error.code}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
