"""Tasks extension (``io.modelcontextprotocol/tasks``, 2026-07-28 schema).

The server decides per request whether to return a ``CreateTaskResult``
(``resultType: "task"``) and only does so when the request's client
capabilities declare the extension. Tool errors finish as ``completed`` with an
``isError`` result; ``failed`` is reserved for JSON-RPC errors.
"""

from __future__ import annotations

import datetime as dt
import secrets
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from verityngn.agent.mcp_v2.errors import INVALID_PARAMS, RpcError

EXTENSION = "io.modelcontextprotocol/tasks"
TERMINAL = ("completed", "failed", "cancelled")


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


class Cancelled(Exception):
    pass


@dataclass
class _Task:
    task_id: str
    tenant: str
    ttl_ms: int
    poll_ms: int
    status: str = "working"
    status_message: str = ""
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    result: Optional[dict[str, Any]] = None
    error: Optional[dict[str, Any]] = None
    input_requests: dict[str, Any] = field(default_factory=dict)
    input_responses: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)
    cancel_event: threading.Event = field(default_factory=threading.Event)
    input_event: threading.Event = field(default_factory=threading.Event)
    lock: threading.Lock = field(default_factory=threading.Lock)


class TaskContext:
    """Handed to a running job: progress, cancellation and mid-flight input."""

    def __init__(self, task: Optional[_Task]) -> None:
        self._task = task
        self._standalone_cancel = threading.Event()

    @property
    def cancelled(self) -> bool:
        return (self._task.cancel_event if self._task else self._standalone_cancel).is_set()

    def check(self) -> None:
        if self.cancelled:
            raise Cancelled()

    def progress(self, message: str, **meta: Any) -> None:
        if not self._task:
            return
        with self._task.lock:
            if self._task.status in TERMINAL:
                return
            self._task.status_message = message
            self._task.meta.update(meta)
            self._task.updated_at = _now()

    def request_input(self, key: str, request: dict[str, Any], *, message: str, timeout: float = 3600) -> Any:
        """Move to ``input_required`` and block until ``tasks/update`` answers ``key``."""
        task = self._task
        if task is None:
            raise RuntimeError("request_input needs a task")
        with task.lock:
            task.input_requests[key] = request
            task.status = "input_required"
            task.status_message = message
            task.updated_at = _now()
            task.input_event.clear()
        while True:
            if task.input_event.wait(timeout=0.5):
                with task.lock:
                    if key in task.input_responses:
                        task.input_requests.pop(key, None)
                        task.status = "working"
                        task.updated_at = _now()
                        return task.input_responses[key]
                    task.input_event.clear()
            if task.cancel_event.is_set():
                raise Cancelled()
            timeout -= 0.5
            if timeout <= 0:
                raise Cancelled()


class TaskManager:
    def __init__(self, *, max_workers: int = 4) -> None:
        self._tasks: dict[str, _Task] = {}
        self._lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="mcp-task")

    def start(
        self,
        tenant: str,
        job: Callable[[TaskContext], dict[str, Any]],
        *,
        poll_ms: int,
        ttl_ms: int = 24 * 3600 * 1000,
        on_cancel: Optional[Callable[[], None]] = None,
    ) -> dict[str, Any]:
        """Create the task durably, then schedule the job. Returns the CreateTaskResult body."""
        task = _Task(task_id=secrets.token_urlsafe(24), tenant=tenant, ttl_ms=ttl_ms, poll_ms=poll_ms)
        with self._lock:
            self._purge()
            self._tasks[task.task_id] = task
        self._pool.submit(self._run, task, job, on_cancel)
        return {"resultType": "task", **self._view(task)}

    def run_detached(self, job: Callable[[TaskContext], dict[str, Any]]) -> None:
        """Run a job with no task handle (hosts without the Tasks extension)."""
        self._pool.submit(self._safe_detached, job)

    @staticmethod
    def _safe_detached(job: Callable[[TaskContext], dict[str, Any]]) -> None:
        try:
            job(TaskContext(None))
        except Exception:  # noqa: BLE001 - the job records its own failure on the report
            pass

    def _run(self, task: _Task, job: Callable[[TaskContext], dict[str, Any]], on_cancel: Optional[Callable[[], None]]) -> None:
        ctx = TaskContext(task)
        try:
            result = job(ctx)
            with task.lock:
                if task.status != "cancelled":
                    task.status = "completed"
                    task.result = result
                    task.input_requests.clear()
                    task.status_message = "finished with a tool error" if result.get("isError") else "done"
        except Cancelled:
            with task.lock:
                task.status = "cancelled"
                task.status_message = task.status_message or "cancelled"
            if on_cancel:
                on_cancel()
        except RpcError as exc:
            with task.lock:
                task.status = "failed"
                task.error = exc.to_dict()
                task.status_message = exc.message
        except Exception as exc:  # noqa: BLE001
            with task.lock:
                task.status = "failed"
                task.error = {"code": -32603, "message": f"Internal error: {type(exc).__name__}"}
                task.status_message = "internal error"
        finally:
            with task.lock:
                task.updated_at = _now()

    def _purge(self) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        dead = []
        for tid, t in self._tasks.items():
            created = dt.datetime.fromisoformat(t.created_at.replace("Z", "+00:00"))
            if (now - created).total_seconds() * 1000 > t.ttl_ms:
                dead.append(tid)
        for tid in dead:
            self._tasks.pop(tid, None)

    def _find(self, task_id: str, tenant: str) -> _Task:
        with self._lock:
            self._purge()
            task = self._tasks.get(task_id)
        if task is None or task.tenant != tenant:
            raise RpcError(INVALID_PARAMS, "Failed to retrieve task: Task not found")
        return task

    @staticmethod
    def _view(task: _Task) -> dict[str, Any]:
        with task.lock:
            out: dict[str, Any] = {
                "taskId": task.task_id,
                "status": task.status,
                "createdAt": task.created_at,
                "lastUpdatedAt": task.updated_at,
                "ttlMs": task.ttl_ms,
                "pollIntervalMs": task.poll_ms,
            }
            if task.status_message:
                out["statusMessage"] = task.status_message
            if task.status == "input_required":
                out["inputRequests"] = dict(task.input_requests)
            if task.status == "completed" and task.result is not None:
                out["result"] = task.result
            if task.status == "failed" and task.error is not None:
                out["error"] = task.error
            if task.meta:
                out["_meta"] = {f"com.verityindex.splitrisk/{k}": v for k, v in task.meta.items()}
        return out

    def get(self, task_id: str, tenant: str) -> dict[str, Any]:
        return self._view(self._find(task_id, tenant))

    def update(self, task_id: str, tenant: str, responses: dict[str, Any]) -> None:
        task = self._find(task_id, tenant)
        with task.lock:
            for key, value in (responses or {}).items():
                if key in task.input_requests and key not in task.input_responses:
                    task.input_responses[key] = value
            task.input_event.set()

    def cancel(self, task_id: str, tenant: str) -> None:
        task = self._find(task_id, tenant)
        with task.lock:
            if task.status in TERMINAL:
                return
            task.cancel_event.set()
            if task.status == "input_required":
                task.status = "cancelled"
                task.status_message = "cancelled while waiting for input"
                task.updated_at = _now()
