import boto3
import json
import os
import time
import signal
from collections import deque
from datetime import datetime, timezone

# -------------------------
# CONFIG
# -------------------------
STREAM_NAME = os.environ["KINESIS_STREAM"]
OUTPUT_BUCKET = os.environ["OUTPUT_BUCKET"]
REGION = os.environ.get("AWS_REGION", "us-east-1")

WINDOW_SECONDS = 15
POLL_INTERVAL_SECONDS = 1

# -------------------------
# AWS CLIENTS
# -------------------------
kinesis = boto3.client("kinesis", region_name=REGION)
s3 = boto3.client("s3")

# -------------------------
# STATE
# -------------------------
# key = site:device_id
# value = deque[(timestamp, voltage, amperage)]
windows = {}

running = True

# -------------------------
# SIGNAL HANDLING (ECS SAFE)
# -------------------------
def shutdown_handler(signum, frame):
    global running
    print("Shutdown signal received", flush=True)
    running = False

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

# -------------------------
# WINDOW UTILITIES
# -------------------------
def prune_old_events(window, now_ts):
    cutoff = now_ts - WINDOW_SECONDS
    while window and window[0][0] < cutoff:
        window.popleft()

# -------------------------
# PROCESS ONE RECORD
# -------------------------
def process_record(record):
    payload = json.loads(record["Data"].decode("utf-8"))

    site = payload["site"]
    device_id = payload["device_id"]
    key = f"{site}:{device_id}"

    voltage = payload["metric"]["voltage"]
    amperage = payload["metric"]["amperage"]

    event_ts = datetime.fromisoformat(
        payload["timestamp"]
    ).timestamp()

    if key not in windows:
        windows[key] = deque()

    window = windows[key]

    # Add new event
    window.append((event_ts, voltage, amperage))

    # Remove events older than rolling window
    prune_old_events(window, event_ts)

    # Compute rolling averages
    count = len(window)

    avg_voltage = sum(v for _, v, _ in window) / count
    avg_amperage = sum(a for _, _, a in window) / count

    # Window boundaries
    window_start_ts = window[0][0]
    window_end_ts = event_ts

    result = {
        "site": site,
        "device_id": device_id,
        "window_seconds": WINDOW_SECONDS,
        "event_count": count,

        "window_start": datetime.fromtimestamp(
            window_start_ts, tz=timezone.utc
        ).isoformat(),

        "window_end": datetime.fromtimestamp(
            window_end_ts, tz=timezone.utc
        ).isoformat(),

        "avg_voltage": round(avg_voltage, 2),
        "avg_amperage": round(avg_amperage, 2),
        "voltage" : round(voltage,2),
        "amperage": round(amperage, 2)

    }

    return result

# -------------------------
# WRITE TO S3
# -------------------------
def write_to_s3(result):
    key = (
        f"aggregates/"
        f"site={result['site']}/"
        f"device={result['device_id']}/"
        f"{result['window_end']}.json"
    )

    s3.put_object(
        Bucket=OUTPUT_BUCKET,
        Key=key,
        Body=json.dumps(result),
        ContentType="application/json"
    )

# -------------------------
# MAIN LOOP
# -------------------------
def main():
    print("Kinesis consumer started", flush=True)

    shard_id = kinesis.describe_stream(
        StreamName=STREAM_NAME
    )["StreamDescription"]["Shards"][0]["ShardId"]

    shard_iterator = kinesis.get_shard_iterator(
        StreamName=STREAM_NAME,
        ShardId=shard_id,
        ShardIteratorType="LATEST",
    )["ShardIterator"]

    while running:
        response = kinesis.get_records(
            ShardIterator=shard_iterator,
            Limit=100
        )

        shard_iterator = response["NextShardIterator"]

        if response["Records"]:
            print(
                f"Shard {shard_id}: received {len(response['Records'])} record(s)",
                flush=True
            )

        for record in response["Records"]:
            result = process_record(record)
            write_to_s3(result)

        time.sleep(POLL_INTERVAL_SECONDS)

    print("Consumer stopped cleanly", flush=True)

if __name__ == "__main__":
    main()
