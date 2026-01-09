import boto3
import os
import time
import signal
import base64

STREAM_NAME = os.environ["KINESIS_STREAM"]
REGION = os.environ.get("AWS_REGION", "us-east-1")
OUTPUT_BUCKET = os.environ["OUTPUT_BUCKET"]

kinesis = boto3.client("kinesis", region_name=REGION)
s3 = boto3.client("s3")

running = True


def shutdown_handler(signum, frame):
    global running
    print("Shutdown signal received", flush=True)
    running = False


signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)


def main():
    print("Kinesis consumer started", flush=True)

    shard_id = kinesis.describe_stream(
        StreamName=STREAM_NAME
    )["StreamDescription"]["Shards"][0]["ShardId"]

    print(f"Processing shard: {shard_id}", flush=True)

    shard_iterator = kinesis.get_shard_iterator(
        StreamName=STREAM_NAME,
        ShardId=shard_id,
        ShardIteratorType="LATEST"
    )["ShardIterator"]

    while running:
        response = kinesis.get_records(
            ShardIterator=shard_iterator,
            Limit=100
        )

        shard_iterator = response["NextShardIterator"]

        records = response["Records"]

        if records:
            print(f"Shard {shard_id}: received {len(records)} record(s)", flush=True)

        for record in records:
            payload = record["Data"].decode("utf-8")
            sequence = record["SequenceNumber"]

            key = f"events/{sequence}.txt"

            print(f"Writing record {sequence} to S3", flush=True)

            s3.put_object(
                Bucket=OUTPUT_BUCKET,
                Key=key,
                Body=payload
            )

        time.sleep(2)

    print("Consumer stopped", flush=True)


if __name__ == "__main__":
    main()