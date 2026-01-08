import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as logs from "aws-cdk-lib/aws-logs";
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as iam from "aws-cdk-lib/aws-iam";

interface EcsStackProps extends cdk.StackProps {
  repository: ecr.Repository;
  streamName: string;
  bucketName: string;
  taskRole: iam.Role;
}

export class EcsStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: EcsStackProps) {
    super(scope, id, props);

    const vpc = new ec2.Vpc(this, "Vpc", { maxAzs: 2 });

    const cluster = new ecs.Cluster(this, "Cluster", { vpc });

    const logGroup = new logs.LogGroup(this, "ConsumerLogs");

    const taskDef = new ecs.FargateTaskDefinition(this, "TaskDef", {
      cpu: 256,
      memoryLimitMiB: 512,
      taskRole: props.taskRole,
    });

    taskDef.addContainer("ConsumerContainer", {
      image: ecs.ContainerImage.fromEcrRepository(props.repository),
      logging: ecs.LogDrivers.awsLogs({
        logGroup,
        streamPrefix: "kinesis-consumer",
      }),
      environment: {
        KINESIS_STREAM: props.streamName,
        OUTPUT_BUCKET: props.bucketName,
        AWS_REGION: this.region,
      },
    });

    new ecs.FargateService(this, "Service", {
      cluster,
      taskDefinition: taskDef,
      desiredCount: 1,
    });
  }
}