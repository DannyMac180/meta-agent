import { templates } from "@metaagent/templates";

export type TemplatePickerProps = {
  onSelect: (templateId: string) => void;
};

export function TemplatePicker({ onSelect }: TemplatePickerProps) {
  return (
    <div className="template-picker">
      <h3>Select a template</h3>
      <div className="template-grid">
        {templates.map((t) => (
          <button key={t.id} className="template-card" onClick={() => onSelect(t.id)}>
            <div className="template-name">{t.name}</div>
            <div className="template-desc">{t.description}</div>
            {t.tags && (
              <div className="template-tags">
                {t.tags.map((tag) => (
                  <span key={tag} className="tag">{tag}</span>
                ))}
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
export default TemplatePicker;
