import { useCallback, useMemo, useState } from "react";
import SpecEditor from "./SpecEditor";
import ValidationPanel from "./ValidationPanel";
import type { ValidationResult } from "../workers/validation-worker";

interface SpecPanelProps {
  payload: any;
  readOnly?: boolean;
  onErrorPathClick?: (path: (string | number)[]) => void;
}

export default function SpecPanel({ payload, readOnly = true, onErrorPathClick }: SpecPanelProps) {
  const [errors, setErrors] = useState<ValidationResult["errors"]>();
  const value = useMemo(() => JSON.stringify(payload ?? {}, null, 2), [payload]);

  const handleValidationChange = useCallback((errs: ValidationResult["errors"]) => {
    setErrors(errs);
  }, []);

  return (
    <div className="spec-panel">
      <SpecEditor value={value} onChange={() => {}} onValidationChange={handleValidationChange} readOnly={readOnly} />
      <div style={{ marginTop: 12 }}>
        <ValidationPanel 
          errors={errors} 
          onErrorClick={(e) => onErrorPathClick?.(e.path)}
        />
      </div>
    </div>
  );
}
