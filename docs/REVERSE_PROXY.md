# Serving the API behind nginx

A request can fit the model's context and still be rejected by the reverse proxy.
nginx defaults to a **1 MiB request body limit** unless a matching configuration
overrides it. An agent turn may contain tool results, prior messages and inline
base64 images, so a relatively short tokenized prompt can exceed that byte limit.

## Diagnose HTTP 413 at the correct layer

Check the proxy error log for "client intended to send too large body" and the
declared byte count. A rejected request may never reach Strata or dispatch to the
engine. Do not fix this by increasing the model context or completion budget.

Strata's context admission is separate: prompt tokens plus requested completion
tokens and its safety margin must fit the configured context. A body-size change
does not change this check, truncate history, or grant additional output tokens.

## Set a bounded limit for the inference location

For an API that needs multi-megabyte agent/image requests, **16 MiB** is a
reasonable starting bound, not a guarantee that every context-sized payload fits.
Choose a bound based on observed payload sizes, available memory and concurrency.
Do not disable limits with "client_max_body_size 0".

Add the directive to the **existing inference proxy location**, for example:

~~~nginx
location / {
    client_max_body_size 16m;
    proxy_pass http://127.0.0.1:8080;
    # Keep the deployment's existing headers, streaming and timeout settings.
}
~~~

The upstream address above is illustrative. Keep your actual upstream, TLS,
authentication, listener ports and access restrictions unchanged. Prefer
location scope to a global/server-wide change, especially when other applications
or control endpoints have their own smaller limits. A more-specific matching
location may have a different effective limit.

Back up the existing configuration, then validate and gracefully reload:

~~~sh
sudo nginx -t && sudo systemctl reload nginx
~~~

There is no need to restart the model server for this proxy-only change. If
validation fails, restore the backup and validate it before reloading.

## Verify both admission and rejection without inference

On an API requiring a key, a synthetic unauthenticated request larger than the
old limit but below the new limit should reach the backend and receive its JSON
authentication error (normally HTTP 401), rather than nginx's HTTP 413. This tests
proxy admission without sending a prompt to the model. Confirm the response is
the backend's expected authentication error, not an intermediary response.

For example, with STRATA_TEST_URL set to the HTTPS API origin (without /v1):

~~~sh
python3 - <<'PY'
import json
import os
import subprocess

url = os.environ["STRATA_TEST_URL"].rstrip("/") + "/v1/chat/completions"
tests = [
    (json.dumps({"messages": [], "max_tokens": 1,
                 "validation_padding": "x" * 3_200_000}).encode(), 401),
    (b" " * (16 * 1024 * 1024 + 1), 413),
]
for body, expected in tests:
    result = subprocess.run(
        ["curl", "--silent", "--show-error", "--max-time", "30",
         "-H", "Content-Type: application/json", "--data-binary", "@-",
         "-w", "\nHTTP_CODE=%{http_code}\n", url],
        input=body, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=True,
    )
    response = result.stdout.decode()
    status = int(response.rsplit("HTTP_CODE=", 1)[1].strip())
    print("bytes:", len(body), "status:", status, "expected:", expected)
    assert status == expected
PY
~~~

Run this check against the intended virtual host with normal TLS verification.
Do not add credentials: the under-limit probe relies on authentication rejection.
The larger probe intentionally produces one proxy error-log entry and must still
be rejected at 16 MiB plus one byte.

Finally check health, authentication and the effective model context/output
defaults. An oversized-body test does not establish token-context correctness,
model quality, or that an entire client workflow will complete. If a client still
receives 413, inspect every intervening proxy and its selected location.

## Rollback

Restore the saved proxy configuration, run nginx -t, then gracefully reload.
Do not restore unrelated service configuration or restart the engine for this
change. Keep private host configuration, authentication material and request
logs out of source-control commits.
