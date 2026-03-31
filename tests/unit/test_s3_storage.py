"""Unit tests: S3 adapter with mocked boto3 client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from app.services.storage_service import S3ObjectStorage
from botocore.exceptions import ClientError


@pytest.mark.unit
@patch("app.services.storage_service.boto3.client")
def test_ensure_bucket_creates_when_missing(mock_boto):
    client = MagicMock()
    client.head_bucket.side_effect = ClientError({"Error": {"Code": "404"}}, "HeadBucket")
    mock_boto.return_value = client
    store = S3ObjectStorage(
        bucket="b",
        endpoint_url="http://localhost:9000",
        access_key_id="k",
        secret_access_key="s",
        region="us-east-1",
        use_path_style=True,
    )
    store.ensure_bucket()
    client.create_bucket.assert_called_once_with(Bucket="b")


@pytest.mark.unit
@patch("app.services.storage_service.boto3.client")
def test_upload_bytes_put_object(mock_boto):
    inner = MagicMock()
    mock_boto.return_value = inner
    store = S3ObjectStorage(
        bucket="verifiedsignal",
        endpoint_url=None,
        access_key_id="k",
        secret_access_key="s",
        region="us-east-1",
        use_path_style=False,
    )
    store.upload_bytes("raw/a/b.txt", b"hi", "text/plain")
    inner.put_object.assert_called_once()
    call_kw = inner.put_object.call_args.kwargs
    assert call_kw["Bucket"] == "verifiedsignal"
    assert call_kw["Key"] == "raw/a/b.txt"
    assert call_kw["Body"] == b"hi"
    assert call_kw["ContentType"] == "text/plain"


@pytest.mark.unit
@patch("app.services.storage_service.boto3.client")
def test_presigned_get_url_uses_generate_presigned_url(mock_boto):
    inner = MagicMock()
    inner.generate_presigned_url.return_value = "https://example.com/presigned"
    mock_boto.return_value = inner
    store = S3ObjectStorage(
        bucket="verifiedsignal",
        endpoint_url="http://localhost:9000",
        access_key_id="k",
        secret_access_key="s",
        region="us-east-1",
        use_path_style=True,
    )
    url = store.presigned_get_url("raw/a/b.txt", expires_seconds=120)
    assert url == "https://example.com/presigned"
    inner.generate_presigned_url.assert_called_once()
    call_kw = inner.generate_presigned_url.call_args.kwargs
    assert call_kw["ExpiresIn"] == 120
