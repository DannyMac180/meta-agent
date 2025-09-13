import { json, type LoaderFunctionArgs } from "@remix-run/node";
import { useLoaderData, Link } from "@remix-run/react";

export async function loader({ request }: LoaderFunctionArgs) {
  // Fetch drafts via API
  const response = await fetch(`${request.url.replace(/\/catalog\/drafts.*/, "")}/api/specs/drafts`);
  
  if (!response.ok) {
    throw new Response("Failed to load drafts", { status: response.status });
  }

  const drafts = await response.json();
  return json({ drafts });
}

export default function DraftsCatalogRoute() {
  const { drafts } = useLoaderData<typeof loader>();

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="drafts-catalog">
      <header className="catalog-header">
        <h1>My Drafts</h1>
        <div className="catalog-actions">
          <Link to="/specs/new" className="new-draft-button">
            + New Draft
          </Link>
          <div className="template-buttons">
            <Link to="/specs/new?template=chatbot" className="template-button">
              Chatbot
            </Link>
            <Link to="/specs/new?template=web-automation" className="template-button">
              Web Automation
            </Link>
            <Link to="/specs/new?template=api-copilot" className="template-button">
              API Copilot
            </Link>
          </div>
        </div>
      </header>

      {drafts.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📝</div>
          <h2>No drafts yet</h2>
          <p>Create your first agent spec to get started.</p>
          <Link to="/specs/new" className="cta-button">
            Create First Draft
          </Link>
        </div>
      ) : (
        <div className="drafts-grid">
          {drafts.map((draft: any) => (
            <div key={draft.id} className="draft-card">
              <div className="draft-header">
                <h3 className="draft-name">
                  <Link to={`/specs/${draft.id}`}>
                    {draft.name}
                  </Link>
                </h3>
                <div className="draft-actions">
                  <Link to={`/specs/${draft.id}`} className="edit-link">
                    Edit
                  </Link>
                </div>
              </div>
              
              <div className="draft-meta">
                <div className="draft-dates">
                  <span className="created">Created: {formatDate(draft.createdAt)}</span>
                  <span className="updated">Updated: {formatDate(draft.updatedAt)}</span>
                </div>
                
                {draft.tags && draft.tags.length > 0 && (
                  <div className="draft-tags">
                    {draft.tags.map((tag: string) => (
                      <span key={tag} className="tag">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {draft.spec && (
                <div className="draft-preview">
                  {draft.spec.meta?.description && (
                    <p className="draft-description">
                      {draft.spec.meta.description}
                    </p>
                  )}
                  
                  <div className="spec-info">
                    {draft.spec.model && (
                      <span className="model-info">
                        {draft.spec.model.provider}/{draft.spec.model.model}
                      </span>
                    )}
                    {draft.spec.variables && (
                      <span className="variables-count">
                        {draft.spec.variables.length} variables
                      </span>
                    )}
                    {draft.spec.tools && draft.spec.tools.length > 0 && (
                      <span className="tools-count">
                        {draft.spec.tools.length} tools
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
