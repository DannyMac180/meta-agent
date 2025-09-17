export interface AgentExecData {
  runId: string;
  prompt: string;
  context?: unknown;
}

export interface AgentExecResult {
  runId: string;
  output: string;
  logs?: string[];
}

export interface DraftAutosaveData {
  userId: string;
  draft: {
    id?: string;
    templateId?: string;
    title: string;
    payload: any;
    isDraft?: boolean;
    status?: 'DRAFT' | 'PUBLISHED';
  };
}

export interface DraftAutosaveResult {
  id: string;
  updatedAt: string;
}

export interface BuilderPackageDockerOptions {
  enabled: boolean;
  imageTag?: string;
}

export interface BuilderPackageOptions {
  includeZip?: boolean;
  docker?: BuilderPackageDockerOptions;
}

export interface BuilderScaffoldJob {
  userId: string;
  draftId: string;
  buildId?: string;
  package?: BuilderPackageOptions;
}

export interface BuilderPackagedArtifact {
  artifactId: string;
  bucket: string;
  key: string;
  sizeBytes?: number;
  etag?: string;
  step: "package:zip" | "package:docker" | (string & {});
}

export interface BuilderScaffoldResult {
  zip?: BuilderPackagedArtifact;
  docker?: BuilderPackagedArtifact;
  artifacts: BuilderPackagedArtifact[];
}
