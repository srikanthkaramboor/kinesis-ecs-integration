import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as kinesis from "aws-cdk-lib/aws-kinesis";

export class KinesisStack extends cdk.Stack {
  public readonly stream: kinesis.Stream;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    this.stream = new kinesis.Stream(this, "EventStream", {
      streamName: "kinesis-events",
      shardCount: 1,
    });
  }
}