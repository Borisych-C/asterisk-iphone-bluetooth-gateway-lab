#!/usr/bin/env python3
"""Minimal Secret Service client for the Asterisk gateway credentials."""

import argparse
import sys

import gi

gi.require_version("Secret", "1")
from gi.repository import Secret  # noqa: E402


SCHEMA = Secret.Schema.new(
    "org.openai.codex.asterisk.credentials",
    Secret.SchemaFlags.NONE,
    {
        "service": Secret.SchemaAttributeType.STRING,
        "host": Secret.SchemaAttributeType.STRING,
        "username": Secret.SchemaAttributeType.STRING,
        "kind": Secret.SchemaAttributeType.STRING,
    },
)


def attributes(args: argparse.Namespace) -> dict[str, str]:
    return {
        "service": "asterisk-gateway",
        "host": args.host,
        "username": args.username,
        "kind": args.kind,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("store", "lookup", "exists"))
    parser.add_argument("--host", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--kind", required=True)
    parser.add_argument("--label")
    args = parser.parse_args()
    attrs = attributes(args)

    if args.action == "store":
        secret = sys.stdin.readline().rstrip("\n")
        if not secret:
            print("Refusing to store an empty secret.", file=sys.stderr)
            return 2
        label = args.label or f"Asterisk gateway: {args.kind} for {args.username}@{args.host}"
        stored = Secret.password_store_sync(
            SCHEMA,
            attrs,
            Secret.COLLECTION_DEFAULT,
            label,
            secret,
            None,
        )
        secret = ""
        return 0 if stored else 3

    secret = Secret.password_lookup_sync(SCHEMA, attrs, None)
    if args.action == "exists":
        print("yes" if secret else "no")
        return 0 if secret else 1
    if not secret:
        return 1
    sys.stdout.write(secret)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

