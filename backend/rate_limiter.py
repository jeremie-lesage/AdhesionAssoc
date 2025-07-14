from fastapi import Request, HTTPException, status
import time

RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 5  # max requests per window
request_counts = {}  # In-memory store for (ip, endpoint) -> (count, last_request_time)

def rate_limit(request: Request):
    client_ip = request.client.host
    endpoint = request.url.path
    key = (client_ip, endpoint)

    current_time = time.time()

    if key not in request_counts:
        request_counts[key] = [0, current_time]

    count, last_request_time = request_counts[key]

    if current_time - last_request_time > RATE_LIMIT_WINDOW:
        request_counts[key] = [1, current_time]
    else:
        if count >= RATE_LIMIT_MAX_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )
        request_counts[key][0] += 1
