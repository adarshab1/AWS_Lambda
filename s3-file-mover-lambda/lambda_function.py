import boto3

s3 = boto3.client("s3")

DEST_PREFIX = "outbound/processed/"

def lambda_handler(event, context):
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        # Only process inbound/ prefix
        if not key.startswith("inbound/"):
            continue

        # Skip folder placeholder events
        if key.endswith("/"):
            continue

        # Destination key
        relative_path = key[len("inbound/"):]
        dest_key = DEST_PREFIX + relative_path

        # Copy object (NO DELETE!)
        s3.copy_object(
            Bucket=bucket,
            CopySource={"Bucket": bucket, "Key": key},
            Key=dest_key
        )

    return {"status": "success"}
