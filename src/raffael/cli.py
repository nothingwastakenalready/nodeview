import argparse

from .checks import CheckResult, check_service
from .config import load_services


def format_result(result: CheckResult) -> str:
    prefix = f"{result.name}  {result.kind.upper()}  {result.status.upper()}"

    if result.status == "up":
        bits = [prefix, f"{result.latency_ms}ms"]
        if result.http_status is not None:
            bits.append(str(result.http_status))
        return "  ".join(bits)

    if result.http_status is not None:
        bits = [prefix, f"{result.latency_ms}ms", str(result.http_status)]
        if result.error:
            bits.append(result.error)
        return "  ".join(bits)

    return f"{prefix}  {result.error or 'unknown error'}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="raffael")
    parser.add_argument("config", help="yaml file with services to check")
    args = parser.parse_args(argv)

    results = [check_service(service) for service in load_services(args.config)]
    for result in results:
        print(format_result(result))

    return 1 if any(result.status == "down" for result in results) else 0


def entrypoint() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    entrypoint()
