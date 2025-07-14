from fastapi import Request, HTTPException, status
import time

RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 5  # max requests per window
request_counts = {}  # In-memory store for (ip, endpoint) -> (count, last_request_time)


def rate_limit(request: Request):
    """
    Apply a rate-limiting mechanism to incoming requests based on client IP and endpoint.

    This function keeps track of the number of requests made by a specific client
    to a specific endpoint within a specified time window. If the number of requests
    exceeds the allowed limit, it raises an exception to deny further access temporarily.

    :param request: The incoming HTTP request object containing details such as
        client IP and the requested endpoint.
    :return: None
    """
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
