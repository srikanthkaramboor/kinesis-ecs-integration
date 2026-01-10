import boto3
import json
import random
import time
from datetime import datetime, timezone

# -----------------------
# CONFIGURATION
# -----------------------
STREAM_NAME = "kinesis-events"
REGION = "us-east-1"
SITE_NAME = "XYZA"

DEVICE_IDS = [f"VFD-{i:03d}" for i in range(1, 11)]

RUN_DURATION_SECONDS = 180     # 3 minutes
INTERVAL_SECONDS = 1           # every second

# Typical VFD ranges
VOLTAGE_RANGE = (380.0, 440.0)      # volts
AMPERAGE_RANGE = (5.0, 25.0)        # amps
FREQUENCY_RANGE = (48.0, 52.0)      # Hz

kinesis = boto3.client("kinesis", region_name=REGION)

# -----------------------
# DATA GENERATION
# -----------------------
def generate_vfd_metric(device_id):
    return {
        "site": SITE_NAME,
        "device_id": device_id,
        "metric": {
            "voltage": round(random.uniform(*VOLTAGE_RANGE), 2),
            "amperage": round(random.uniform(*AMPERAGE_RANGE), 2),
            "frequency_hz": round(random.uniform(*FREQUENCY_RANGE), 2),
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# -----------------------
# MAIN LOOP
# -----------------------
def main():
    print("Starting VFD telemetry simulator")
    print(f"Site={SITE_NAME}, Devices={len(DEVICE_IDS)}, Duration=3 min")

    start_time = time.time()

    while True:
        elapsed = time.time() - start_time
        if elapsed >= RUN_DURATION_SECONDS:
            break

        for device_id in DEVICE_IDS:
            payload = generate_vfd_metric(device_id)

            kinesis.put_record(
                StreamName=STREAM_NAME,
                PartitionKey=f"{SITE_NAME}-{device_id}",
                Data=json.dumps(payload).encode("utf-8"),
            )

            print(
                f"[{payload['timestamp']}] "
                f"{device_id} | "
                f"V={payload['metric']['voltage']}V "
                f"I={payload['metric']['amperage']}A"
            )

        time.sleep(INTERVAL_SECONDS)

    print("Simulation complete. Stopped after 3 minutes.")

if __name__ == "__main__":
    main()
