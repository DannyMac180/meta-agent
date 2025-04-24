from typing import Dict, Optional, Any
import threading

import json
import os

class StateManager:
    """
    Tracks the progress and state of agent generation, with thread safety.
    Extensible for persistence and checkpointing.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._state: Dict[str, Any] = {
            'status': 'initialized',  # e.g., running, failed, completed
            'progress': 0.0,         # 0.0 - 1.0
            'steps': [],             # List of steps/stages completed
            'current_step': None,    # Current step name/id
            'error': None,           # Error info if failed
            'retries': {}            # step -> retry count
        }

    def update_progress(self, progress: float, current_step: Optional[str] = None):
        with self._lock:
            self._state['progress'] = min(max(progress, 0.0), 1.0)
            if current_step:
                self._state['current_step'] = current_step
                if current_step not in self._state['steps']:
                    self._state['steps'].append(current_step)

    def set_status(self, status: str, error: Optional[str] = None):
        with self._lock:
            self._state['status'] = status
            if error:
                self._state['error'] = error

    def get_status(self) -> str:
        with self._lock:
            return self._state['status']

    def get_progress(self) -> float:
        with self._lock:
            return self._state['progress']

    def get_state(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._state)

    def get_report(self, as_dict: bool = False):
        """
        Returns a formatted string or dict summarizing status, progress, current step, completed steps, retries, and errors.
        """
        with self._lock:
            report = {
                'status': self._state['status'],
                'progress': self._state['progress'],
                'current_step': self._state['current_step'],
                'completed_steps': list(self._state['steps']),
                'retries': dict(self._state['retries']),
                'error': self._state['error']
            }
            if as_dict:
                return report
            # Human-friendly string
            lines = [
                f"Status: {report['status']}",
                f"Progress: {report['progress']*100:.1f}%",
                f"Current step: {report['current_step']}",
                f"Completed steps: {', '.join(report['completed_steps']) if report['completed_steps'] else 'None'}",
                f"Retries: {report['retries'] if report['retries'] else 'None'}",
                f"Error: {report['error'] if report['error'] else 'None'}"
            ]
            return "\n".join(lines)

    def reset(self):
        with self._lock:
            self._state = {
                'status': 'initialized',
                'progress': 0.0,
                'steps': [],
                'current_step': None,
                'error': None,
                'retries': {}
            }

    def register_failure(self, step: str):
        """Increment retry count for a step and update error info."""
        with self._lock:
            retries = self._state['retries'].get(step, 0)
            self._state['retries'][step] = retries + 1
            self._state['error'] = f"Failure in step '{step}', retry {retries + 1}"

    def should_retry(self, step: str, max_retries: int = 3) -> bool:
        """Return True if the step can be retried under max_retries."""
        with self._lock:
            retries = self._state['retries'].get(step, 0)
            return retries < max_retries

    def reset_retries(self, step: Optional[str] = None):
        """Reset retry count for a step or all steps if None."""
        with self._lock:
            if step is None:
                self._state['retries'] = {}
            else:
                self._state['retries'].pop(step, None)

    def save_state(self, filepath: str) -> bool:
        """Persist current state to a JSON file. Returns True if successful."""
        with self._lock:
            try:
                with open(filepath, 'w') as f:
                    json.dump(self._state, f, indent=2)
                return True
            except Exception as e:
                self._state['error'] = f"Save error: {e}"
                return False

    def load_state(self, filepath: str) -> bool:
        """Load state from a JSON file. Returns True if successful."""
        if not os.path.exists(filepath):
            return False
        with self._lock:
            try:
                with open(filepath, 'r') as f:
                    loaded = json.load(f)
                # Only update known keys
                for k in self._state:
                    if k in loaded:
                        self._state[k] = loaded[k]
                return True
            except Exception as e:
                self._state['error'] = f"Load error: {e}"
                return False

    def create_checkpoint(self, label: str, directory: str = "checkpoints") -> bool:
        """Save a checkpoint with the given label in the specified directory."""
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, f"{label}.json")
        return self.save_state(path)

    def restore_checkpoint(self, label: str, directory: str = "checkpoints") -> bool:
        """Restore state from a checkpoint with the given label in the specified directory."""
        path = os.path.join(directory, f"{label}.json")
        return self.load_state(path)
