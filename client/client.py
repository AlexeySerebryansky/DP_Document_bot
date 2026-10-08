import json
import os
import shutil
import subprocess
from time import sleep

from dotenv import load_dotenv

load_dotenv()


class GoLoginClient:
    OPEN_TIMEOUT = 30
    COMMAND_TIMEOUT = 30
    CHECK_DELAY = 15

    E_QUEUE_URL = (
        "https://prague.pasport.org.ua/solutions/e-queue"
    )

    GOLOGIN_CLI = shutil.which("gologin-agent-browser")

    if not GOLOGIN_CLI:
        raise RuntimeError(
            "gologin-agent-browser not found"
        )

    def __init__(self):
        self.profile_id = self._get_profile_id()
        self.session_id = "dp-document"

    @staticmethod
    def _get_profile_id() -> str:
        profile_id = os.getenv("GOLOGIN_PROFILE_ID")

        if not profile_id:
            raise RuntimeError(
                "GOLOGIN_PROFILE_ID is not set"
            )

        return profile_id

    def _run(self, *args: str, timeout: int = COMMAND_TIMEOUT) -> str:

        command = [
            self.GOLOGIN_CLI,
            "local",
            *args,
        ]

        print(
            "[GOLOGIN CMD]",
            " ".join(command),
            flush=True,
        )

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=timeout,
            )

        except subprocess.TimeoutExpired:
            print(
                f"[GOLOGIN] TIMEOUT after {timeout}s: "
                f"{' '.join(command)}",
                flush=True,
            )
            raise

        if result.returncode != 0:
            raise RuntimeError(
                f"GoLogin CLI error:\n"
                f"{result.stderr}"
            )

        return result.stdout

    def _install_xhr_interceptor(self):
        self._run(
            "eval",
            "window.__dp_xhr=[]",
            "--session",
            self.session_id,
        )

        self._run(
            "eval",
            "window.__dp_old_open=XMLHttpRequest.prototype.open",
            "--session",
            self.session_id,
        )

        self._run(
            "eval",
            "window.__dp_old_send=XMLHttpRequest.prototype.send",
            "--session",
            self.session_id,
        )

        self._run(
            "eval",
            "XMLHttpRequest.prototype.open=function(m,u){this.__dp_method=m;this.__dp_url=u;return window.__dp_old_open.apply(this,arguments)}",
            "--session",
            self.session_id,
        )

        self._run(
            "eval",
            "XMLHttpRequest.prototype.send=function(b){this.addEventListener('load',function(){if(this.__dp_url&&this.__dp_url.includes('/solutions/e-queue'))window.__dp_xhr.push({method:this.__dp_method,url:this.__dp_url,status:this.status,response:this.responseText})});return window.__dp_old_send.apply(this,arguments)}",
            "--session",
            self.session_id,
        )

    def _clear_xhr_log(self):
        self._run(
            "eval",
            "window.__dp_xhr=[]",
            "--session",
            self.session_id,
        )

    def _get_xhr_log(self) -> list:
        result = self._run(
            "eval",
            "JSON.stringify(window.__dp_xhr)",
            "--session",
            self.session_id,
            "--json",
        )

        data = json.loads(result)

        if isinstance(data, str):
            data = json.loads(data)

        return data

    def open(self) -> None:
        print("[GOLOGIN] opening...", flush=True)

        self._run(
            "open",
            self.E_QUEUE_URL,
            "--profile",
            self.profile_id,
            "--session",
            self.session_id,
            "--background",
            timeout=self.OPEN_TIMEOUT,
        )

        print("[GOLOGIN] opened", flush=True)

        sleep(self.CHECK_DELAY)

        print("[GOLOGIN] installing interceptor...", flush=True)

        print(
            self._run(
                "eval",
                "JSON.stringify({"
                "url: location.href,"
                "title: document.title,"
                "readyState: document.readyState,"
                "serviceExists: !!document.querySelector('#service'),"
                "serviceValue: document.querySelector('#service')?.value ?? null"
                "})",
                "--session",
                self.session_id,
                "--json",
            ),
            flush=True,
        )

        self._install_xhr_interceptor()

        print("[GOLOGIN] interceptor installed", flush=True)

    def check_days(self) -> list:
        print("[GOLOGIN] clearing XHR log", flush=True)

        self._clear_xhr_log()

        print("[GOLOGIN] setting service=4", flush=True)

        self._run(
            "eval",
            'JSON.stringify(document.querySelector("#service").value="4")',
            "--session",
            self.session_id,
            "--json",
        )

        print("[GOLOGIN] dispatching change", flush=True)

        self._run(
            "eval",
            'JSON.stringify(document.querySelector("#service").dispatchEvent(new Event("change",{bubbles:true})))',
            "--session",
            self.session_id,
            "--json",
        )

        print("[GOLOGIN] waiting...", flush=True)

        sleep(self.CHECK_DELAY)

        requests = self._get_xhr_log()

        print(
            f"[GOLOGIN] captured requests: {requests}",
            flush=True,
        )

        days_requests = [
            request
            for request in requests
            if request.get("method") == "POST"
               and request.get("url") == self.E_QUEUE_URL
        ]

        if not days_requests:
            raise RuntimeError(
                "No availability request was captured"
            )

        request = days_requests[-1]

        status = request.get("status")

        if status != 200:
            raise RuntimeError(
                f"Availability request failed with HTTP {status}"
            )

        try:
            response = json.loads(request["response"])
        except (json.JSONDecodeError, TypeError) as exc:
            raise RuntimeError(
                "Availability response is not valid JSON"
            ) from exc

        if not isinstance(response, dict):
            raise RuntimeError(
                "Availability response has unexpected format"
            )

        days = response.get("days")

        if not isinstance(days, list):
            raise RuntimeError(
                "Availability response does not contain a valid 'days' list"
            )

        return [
            day
            for day in days
            if day.get("isAllowed") is True
        ]

    def close(self) -> None:
        command = [
            self.GOLOGIN_CLI,
            "local",
            "close",
            "--session",
            self.session_id,
        ]

        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        try:
            process.wait(timeout=10)

            print(
                "[GOLOGIN] Session closed normally",
                flush=True,
            )

        except subprocess.TimeoutExpired:
            print(
                "[GOLOGIN] Close command timeout. "
                "Killing Node.js process...",
                flush=True,
            )

            subprocess.run(
                [
                    "taskkill",
                    "/PID",
                    str(process.pid),
                    "/T",
                    "/F",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )

            print(
                "[GOLOGIN] Node.js CLI process terminated",
                flush=True,
            )
