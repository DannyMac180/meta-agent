import { useEffect, useMemo, useState } from "react";
import type { InterviewScript, InterviewState } from "@metaagent/interview";
import { InterviewRunner } from "@metaagent/interview";
import { debounce } from "../utils/schema";

type Props = {
  script: InterviewScript;
  initialState: InterviewState;
  onStateChange?: (state: InterviewState) => void;
  onAutosave?: (state: InterviewState) => void;
};

export default function InterviewPanel({ script, initialState, onStateChange, onAutosave }: Props) {
  const runner = useMemo(() => new InterviewRunner(script), [script]);
  const [state, setState] = useState<InterviewState>(initialState);

  const [autosave] = useState(() => debounce((s: InterviewState) => onAutosave?.(s), 800));

  useEffect(() => {
    onStateChange?.(state);
    autosave(state);
  }, [state]);

  const currentNode = runner.getCurrentNode(state);

  const handleAnswer = (answer: any) => {
    const { updatedState } = runner.runNode(state, answer);
    setState(updatedState);
  };

  const renderQuestion = () => {
    switch (currentNode.inputType) {
      case "text":
        return (
          <input
            type="text"
            defaultValue={state.answers[currentNode.id] || ""}
            onBlur={(e) => handleAnswer(e.target.value)}
          />
        );
      case "textarea":
        return (
          <textarea
            defaultValue={state.answers[currentNode.id] || ""}
            onBlur={(e) => handleAnswer(e.target.value)}
          />
        );
      case "number":
        return (
          <input
            type="number"
            defaultValue={state.answers[currentNode.id] || ""}
            onBlur={(e) => handleAnswer(Number(e.target.value))}
          />
        );
      case "select":
        return (
          <select
            defaultValue={state.answers[currentNode.id] || ""}
            onChange={(e) => handleAnswer(e.target.value)}
          >
            <option value="" disabled>Select...</option>
            {currentNode.options?.map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        );
      default:
        return null;
    }
  };

  if (currentNode.type === "end") {
    return <div className="interview-complete">Interview complete.</div>;
  }

  return (
    <div className="interview-panel">
      <div className="question">
        <label>{currentNode.prompt}</label>
        <div className="control">{renderQuestion()}</div>
      </div>
    </div>
  );
}
