import { S3 } from "@aws-sdk/client-s3";

export function createTestS3(endpoint: string) {
  return new S3({
    endpoint,
    region: "us-east-1",
    credentials: {
      accessKeyId: "minioadmin",
      secretAccessKey: "minioadmin",
    },
    forcePathStyle: true,
  });
}
