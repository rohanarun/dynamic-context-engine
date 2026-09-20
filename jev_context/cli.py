"""CLI usable from any agent with shell access."""
import argparse
import json
from pathlib import Path
import sys
from .engine import Engine, Store, ProviderError, DEFAULT_MAX_TOKENS

def main():
    parser = argparse.ArgumentParser(description="Store paragraphs and select relevant context with Jev.")
    parser.add_argument("--db", help="SQLite database (or JEV_CONTEXT_DB)")
    parser.add_argument("--collection", default="default")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest", help="Replace one document, split on blank lines")
    ingest.add_argument("file")
    ingest.add_argument("--source")
    query = commands.add_parser("query", help="Judge every paragraph in the collection")
    query.add_argument("request", nargs="?", help="Omit to read from stdin")
    query.add_argument("--threshold", type=float, default=0.5)
    query.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS, help="Context token budget, default/max 1,000,000 (o200k_base)")
    query.add_argument("--max-chars", type=int, help="Optional additional legacy character cap")
    query.add_argument("--json", action="store_true")
    query.add_argument("--no-cache", action="store_true")
    query.add_argument("--policy", help="Custom model judgment policy JSON")
    commands.add_parser("list")
    delete = commands.add_parser("delete")
    delete.add_argument("source")
    args = parser.parse_args()
    try:
        store = Store(args.db)
        if args.command == "ingest":
            result = store.ingest(Path(args.file).read_text(), args.source or str(Path(args.file).resolve()), args.collection)
            print(json.dumps({"paragraphs": len(result), "collection": args.collection}))
        elif args.command == "query":
            policy = json.loads(Path(args.policy).read_text()) if args.policy else None
            result = Engine(store, policy=policy, cache_ttl=0 if args.no_cache else 3600).query(args.request or sys.stdin.read(), args.collection, args.threshold, args.max_chars, max_tokens=args.max_tokens)
            print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["context"])
        elif args.command == "list":
            print(json.dumps(store.list(args.collection), ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"deleted": store.delete(args.source, args.collection)}))
    except (ProviderError, ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
