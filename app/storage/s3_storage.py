import boto3
import os

S3_BUCKET = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "ca-central-1")

s3 = boto3.client("s3", region_name=AWS_REGION)

def upload_file(file_path: str, key: str, content_type="text/plain"):
    """Upload any local file to S3."""
    s3.upload_file(
        Filename=file_path,
        Bucket=S3_BUCKET,
        Key=key,
        ExtraArgs={"ContentType": content_type}
    )
    return f"s3://{S3_BUCKET}/{key}"


def upload_text_content(content: str, key: str):
    """Upload string content directly (no local file needed)."""
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=content.encode("utf-8"),
        ContentType="text/plain"
    )
    return f"s3://{S3_BUCKET}/{key}"
