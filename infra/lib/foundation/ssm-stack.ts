
import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as ssm from "aws-cdk-lib/aws-ssm";

export class SsmStack extends cdk.Stack {
  public readonly lastKnownGoodImageParam: ssm.StringParameter;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    this.lastKnownGoodImageParam = new ssm.StringParameter(
      this,
      "LastKnownGoodImage",
      {
        parameterName: "/kinesis-consumer/last-known-good-image",
        stringValue: "bootstrap", // initial placeholder
        description: "Last known good Docker image tag for ECS rollback",
      }
    );
  }
}