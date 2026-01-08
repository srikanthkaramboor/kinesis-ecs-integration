import * as cdk from "aws-cdk-lib";
import { EcrStack } from "../lib/foundation/ecr-stack";
import { KinesisStack } from "../lib/foundation/kinesis-stack";
import { S3Stack } from "../lib/foundation/s3-stack";
import { IamStack } from "../lib/foundation/iam-stack";
import { EcsStack } from "../lib/runtime/ecs-stack";

const app = new cdk.App();

// -------- FOUNDATION --------
const ecr = new EcrStack(app, "Foundation-EcrStack");
const kinesis = new KinesisStack(app, "Foundation-KinesisStack");
const s3 = new S3Stack(app, "Foundation-S3Stack");
const iam = new IamStack(app, "Foundation-IamStack");

// -------- RUNTIME --------
new EcsStack(app, "Runtime-EcsStack", {
  repository: ecr.repository,
  streamName: kinesis.stream.streamName,
  bucketName: s3.bucket.bucketName,
  taskRole: iam.taskRole,
});
