from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import StreamingResponse
import os
import aiofiles
import aioboto3
from botocore.exceptions import ClientError
from src.storage.client import s3_storage

router = APIRouter()

@router.get("/stream/{object_name}")
async def stream_from_minio(request: Request, object_name: str) -> StreamingResponse:
    range_header = request.headers.get("range")

    s3_client = await s3_storage.get_client().__aenter__()

    try:
        kwargs = {"Bucket": s3_storage.bucket_name, "Key": object_name}
        if range_header:
            kwargs["Range"] = range_header

        s3_response = await s3_client.get_object(**kwargs)
        
        res_headers = {
            "Content-Type": s3_response.get("ContentType", "audio/mpeg"),
            "Accept-Ranges": "bytes",
            "Content-Length": str(s3_response["ContentLength"]),
        }
        
        if "ContentRange" in s3_response:
            res_headers["Content-Range"] = s3_response["ContentRange"]
        
        status_code = status.HTTP_206_PARTIAL_CONTENT if range_header else status.HTTP_200_OK

        async def body_iterator():
            try:
                async for chunk in s3_response["Body"]:
                    yield chunk
            finally:
                s3_response["Body"].close()
                await s3_client.__aexit__(None, None, None)

        return StreamingResponse(
            body_iterator(),
            status_code=status_code,
            headers=res_headers
        )

    except Exception as e:
        await s3_client.__aexit__(None, None, None)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)