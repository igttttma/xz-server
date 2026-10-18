import os
import base64
import asyncio
import functools
import threading
import traceback
from typing import Optional, Dict

import httpx

TAG = __name__

# Slice granularity for _retry_wait: wraps up within ~100ms of safe_close, so polling overhead is negligible
_RETRY_WAIT_SLICE = 0.1


class DeviceNotFoundException(Exception):
    pass


class DeviceBindException(Exception):
    def __init__(self, bind_code):
        self.bind_code = bind_code
        super().__init__(f"Device binding exception, bind code: {bind_code}")


class ManageApiShutdownError(Exception):
    """Cleanup exception raised after safe_close interrupts a retry wait; __cause__ keeps the last failure reason."""


class ManageApiClient:
    _instance = None
    _instance_lock = threading.Lock()  # Protects reads and writes of _instance and _closed
    _secret = None
    _closed = False  # Set to True after safe_close(); no new connections are created once closed

    def __new__(cls, config):
        """Singleton pattern ensures a globally unique instance and supports passing config"""
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._init_client(config)
            return cls._instance

    @classmethod
    def _init_client(cls, config):
        """Initialize the config (client creation is deferred)"""
        cls.config = config.get("manager-api")

        if not cls.config:
            raise Exception("manager-api config error")

        if not cls.config.get("url") or not cls.config.get("secret"):
            raise Exception("manager-api url or secret config error")

        if "your" in cls.config.get("secret"):
            raise Exception("Please configure the manager-api secret first")

        cls._secret = cls.config.get("secret")
        cls.max_retries = cls.config.get("max_retries", 6)  # Maximum number of retries
        cls.retry_delay = cls.config.get("retry_delay", 10)  # Initial retry delay (seconds)
        # Do not create the AsyncClient here; defer it until actual use
        cls._closed = False

    @classmethod
    def _build_client(cls) -> httpx.AsyncClient:
        """Build an AsyncClient dedicated to a single business request (including retries).

        Constraint: the caller closes it with ``async with`` in the same loop; never cache it across requests. It is constructed outside the lock to avoid blocking the event loop during concurrent requests.
        """
        with cls._instance_lock:
            if cls._closed:
                raise Exception("ManageApiClient is closed; no new HTTP clients will be created")
            base_url = cls.config.get("url")
            secret = cls._secret
            timeout = cls.config.get("timeout", 30)
        return httpx.AsyncClient(
            base_url=base_url,
            headers={
                "User-Agent": f"PythonClient/2.0 (PID:{os.getpid()})",
                "Accept": "application/json",
                "Authorization": "Bearer " + secret,
            },
            timeout=timeout,
            # Connection reuse is limited to this request; keepalive_expiry dynamically overrides retry_delay
            # to prevent pooled connections from expiring during retry waits.
            limits=httpx.Limits(
                max_keepalive_connections=1,
                keepalive_expiry=max(30, cls.retry_delay + 5),
            ),
            trust_env=False,
            # verify=True creates a context each time: httpcore rewrites the passed-in
            # context in place during connection setup (no lock), so concurrent handshakes on a shared singleton race.
            verify=True,
        )

    @classmethod
    async def _async_request(
        cls, client: httpx.AsyncClient, method: str, endpoint: str, **kwargs
    ) -> Dict:
        """Execute a single request on the given client; release it back to the pool immediately after reading the response."""
        endpoint = endpoint.lstrip("/")
        response = None
        try:
            response = await client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            result = response.json()
            if result.get("code") == 10041:
                raise DeviceNotFoundException(result.get("msg"))
            elif result.get("code") == 10042:
                raise DeviceBindException(result.get("msg"))
            elif result.get("code") != 0:
                raise Exception(f"API returned an error: {result.get('msg', 'unknown error')}")
            return result.get("data")
        finally:
            if response is not None:
                try:
                    await response.aclose()
                except Exception:
                    # Constraint: release exceptions must be swallowed to avoid masking business exceptions and breaking retry decisions
                    pass

    @classmethod
    def _should_retry(cls, exception: Exception) -> bool:
        """Determine whether the exception should be retried"""
        # Network connection related errors
        if isinstance(
            exception, (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)
        ):
            return True

        # Only retry the RPE variant "without sending a response" (response not started, safe);
        # the truncated variant may have processed the request and would duplicate the submission; fall back to no retry if the wording changes.
        if isinstance(exception, httpx.RemoteProtocolError):
            return "without sending a response" in str(exception)

        # HTTP status code errors
        if isinstance(exception, httpx.HTTPStatusError):
            status_code = exception.response.status_code
            return status_code in [408, 429, 500, 502, 503, 504]

        return False

    @classmethod
    async def _retry_wait(cls):
        """Retry wait that can be interrupted by safe_close() (polls _closed every 100ms).

        Constraint: do not sleep the full retry_delay at once, otherwise cleanup after close would drag on for the whole retry period.
        """
        remaining = cls.retry_delay
        while remaining > 0 and not cls._closed:
            step = min(_RETRY_WAIT_SLICE, remaining)
            await asyncio.sleep(step)
            remaining -= step

    @classmethod
    async def _execute_async_request(cls, method: str, endpoint: str, **kwargs) -> Dict:
        """Business request executor with a retry mechanism.

        Constraint: the client is constructed only once for the whole retry process and closed by ``async with`` afterwards; safe_close does not cancel an attempt already in progress, it only interrupts the retry wait (raising ManageApiShutdownError).
        """
        client = cls._build_client()
        async with client:
            retry_count = 0

            while retry_count <= cls.max_retries:
                try:
                    # Execute the async request
                    return await cls._async_request(client, method, endpoint, **kwargs)
                except Exception as e:
                    # Determine whether a retry is needed
                    if retry_count < cls.max_retries and cls._should_retry(e):
                        retry_count += 1
                        print(
                            f"{method} {endpoint} async request failed, retrying for the {retry_count} time in {cls.retry_delay:.1f} seconds"
                        )
                        await cls._retry_wait()
                        if cls._closed:
                            # Cleanup must be distinguishable: a bare raise would disguise an early shutdown
                            # as network jitter and hide the service shutdown signal
                            raise ManageApiShutdownError(
                                f"safe_close interrupted the retry wait: {e}") from e
                        continue
                    else:
                        # Do not retry; raise the exception directly
                        raise

    @classmethod
    def _get_instance(cls) -> Optional["ManageApiClient"]:
        """Thread-safely get a reference to the singleton instance.

        Constraint: the caller must keep the returned local reference; never re-read _instance after a None check (TOCTOU window).
        """
        with cls._instance_lock:
            return cls._instance

    @classmethod
    def safe_close(cls):
        """Close the request entry point; in-flight requests release their clients in their own event loops.

        Requests already started are not cancelled; retry waits are interrupted and the remaining retries skipped (see _retry_wait).
        """
        with cls._instance_lock:
            cls._closed = True
            cls._instance = None


def api_guard(error_msg: str = None, raise_when_closed: bool = False):
    """Decorator: uniformly acquire the singleton instance, check for None and handle exceptions

    - Obtain a local instance reference once via _get_instance() and inject it as the
      first argument of the decorated function, eliminating the TOCTOU race window with safe_close();
    - When the instance is not initialized or already closed: raise_when_closed=True raises an explicit
      exception (for startup path functions), otherwise returns None silently (for daemon thread paths);
    - When error_msg is not None, catch request exceptions, log them and return None;
      when None, exceptions propagate as-is for the caller to handle.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            instance = ManageApiClient._get_instance()
            if instance is None:
                if raise_when_closed:
                    raise Exception("ManageApiClient is not initialized or has been closed")
                return None
            if error_msg is None:
                return await func(instance, *args, **kwargs)
            try:
                return await func(instance, *args, **kwargs)
            except Exception as e:
                # Constraint: print full stacks for httpx / parsing exceptions; for business semantic exceptions
                # print only the message (messages carry their own context, stacks are high-frequency noise)
                if isinstance(e, (httpx.HTTPError, ValueError)):
                    print(f"{error_msg}: {e}\n{traceback.format_exc()}")
                else:
                    print(f"{error_msg}: {e}")
                return None

        return wrapper

    return decorator


@api_guard(raise_when_closed=True)
async def get_server_config(instance) -> Optional[Dict]:
    """Get the basic server config"""
    return await instance._execute_async_request("POST", "/config/server-base")


@api_guard(raise_when_closed=True)
async def get_agent_models(
    instance, mac_address: str, client_id: str, selected_module: Dict
) -> Optional[Dict]:
    """Get the agent model config"""
    return await instance._execute_async_request(
        "POST",
        "/config/agent-models",
        json={
            "macAddress": mac_address,
            "clientId": client_id,
            "selectedModule": selected_module,
        },
    )


@api_guard("Failed to get replacement words")
async def get_correct_words(instance, mac_address: str) -> Optional[Dict]:
    """Get the agent replacement words"""
    return await instance._execute_async_request(
        "POST", "/config/correct-words",
        json={"macAddress": mac_address}
    )


@api_guard("Failed to generate and save chat history summary")
async def generate_and_save_chat_summary(instance, session_id: str) -> Optional[Dict]:
    """Generate and save the chat history summary (called from a daemon thread; returns None silently if the service is closed)"""
    return await instance._execute_async_request(
        "POST",
        f"/agent/chat-summary/{session_id}/save",
    )


@api_guard("Failed to generate and save chat title")
async def generate_and_save_chat_title(instance, session_id: str) -> Optional[Dict]:
    """Generate and save the chat title (called from a daemon thread; returns None silently if the service is closed)"""
    return await instance._execute_async_request(
        "POST",
        f"/agent/chat-title/{session_id}/generate",
    )


@api_guard("Failed to report TTS")
async def report(
    instance, mac_address: str, session_id: str, chat_type: int, content: str, audio, report_time
) -> Optional[Dict]:
    """Asynchronously report chat history"""
    if not content:
        return None
    return await instance._execute_async_request(
        "POST",
        f"/agent/chat-history/report",
        json={
            "macAddress": mac_address,
            "sessionId": session_id,
            "chatType": chat_type,
            "content": content,
            "reportTime": report_time,
            "audioBase64": (
                base64.b64encode(audio).decode("utf-8") if audio else None
            ),
        },
    )


@api_guard("Address book lookup failed")
async def lookup_address_book(instance, caller_mac: str, nickname: str) -> Optional[Dict]:
    """Look up the target device by nickname"""
    return await instance._execute_async_request(
        "GET",
        f"/device/address-book/lookup?callerMac={caller_mac}&nickname={nickname}",
    )


def init_service(config):
    ManageApiClient(config)


def manage_api_http_safe_close():
    ManageApiClient.safe_close()
