import argparse

from .checks import CheckResult, check_http
from .config import load_services


def format_result(result: CheckResult) -> str:
    if result.status == "up":
        return f"{result.name}  UP  {result.latency_ms}ms  {result.http_status}"

    if result.http_status is not None:
        bits = [result.name, "DOWN", f"{result.latency_ms}ms", str(result.http_status)]
        if result.error:
            bits.append(result.error)
        return "  ".join(bits)

    return f"{result.name}  DOWN  {result.error or 'unknown error'}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nodeview")
    parser.add_argument("config", help="yaml file with services to check")
    args = parser.parse_args(argv)

    results = [check_http(service) for service in load_services(args.config)]
    for result in results:
        print(format_result(result))

    return 1 if any(result.status == "down" for result in results) else 0


def entrypoint() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    entrypoint()
