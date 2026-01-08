import boto3
import os
import time
import signal
import sys

STREAM_NAME = os.environ["KINESIS_STREAM"]
REGION = os.environ.get("AWS_REGION", "us-east-1")
s3 = boto3.client("s3")
OUTPUT_BUCKET = os.environ["OUTPUT_BUCKET"]
kinesis = boto3.client("kinesis", region_name=REGION)
running = True


def shutdown_handler(signum, frame):
    global running
    print("Shutdown signal received", flush=True)
    running = False

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)


def main():
    print("Kinesis consumer started", flush=True)

    shard_id = kinesis.describe_stream(StreamName=STREAM_NAME)["StreamDescription"]["Shards"][0]["ShardId"]
    shard_iterator = kinesis.get_shard_iterator(StreamName=STREAM_NAME,ShardId=shard_id,ShardIteratorType="LATEST")["ShardIterator"]

    while running:
        response = kinesis.get_records( ShardIterator=shard_iterator,Limit=100 )
        shard_iterator = response["NextShardIterator"]

        if response["Records"]:
            print(f"Received {len(response['Records'])} records", flush=True)

        time.sleep(2)

    print("Consumer stopped", flush=True)

if __name__ == "__main__":
    main()

# def process_records(records):
#     for record in records:
#         data = record["data"].decode("utf-8")
#         key = f"events/{record['sequence_number']}.json"

#         s3.put_object(
#             Bucket=OUTPUT_BUCKET,
#             Key=key,
#             Body=data
#         )