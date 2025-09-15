import { S3, PutObjectCommand } from "@aws-sdk/client-s3";
import { Readable } from "node:stream";

export interface ObjectStorageConfig {
  endpoint?: string;
  region?: string;
  accessKeyId?: string;
  secretAccessKey?: string;
  forcePathStyle?: boolean;
}

export function createS3(config: ObjectStorageConfig = {}) {
  const s3 = new S3({
    endpoint: config.endpoint ?? process.env.S3_ENDPOINT,
    region: config.region ?? process.env.S3_REGION ?? "us-east-1",
    credentials: {
      accessKeyId: config.accessKeyId ?? process.env.S3_KEY ?? "",
      secretAccessKey: config.secretAccessKey ?? process.env.S3_SECRET ?? "",
    },
    forcePathStyle: config.forcePathStyle ?? true,
  });
  return s3;
}

export async function putObjectStream(params: {
  s3?: S3;
  bucket: string;
  key: string;
  body: Buffer | Uint8Array | Blob | string | Readable;
  contentType?: string;
}) {
  const s3 = params.s3 ?? createS3();
  const cmd = new PutObjectCommand({
    Bucket: params.bucket,
    Key: params.key,
    Body: params.body,
    ContentType: params.contentType ?? "application/zip",
  });
  const res = await s3.send(cmd);
  return {
    etag: res.ETag ?? undefined,
  };
}

export function artifactKey(opts: { userId: string; draftId: string; buildId: string; filename?: string }) {
  const file = opts.filename ?? "project.zip";
  return `scaffolds/${opts.userId}/${opts.draftId}/${opts.buildId}/${file}`;
}

// Test utilities
export * from "./test-utils.js";
