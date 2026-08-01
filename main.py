import argparse
import os
import time

from dotenv import load_dotenv

from core.content import build_content_tree
from core.downloader import build_download_jobs, run_downloads, _safe_filename, zip_dir
from core.utils import verify_token

load_dotenv()

OUT_DIR = "downloads"
TOKEN_FILE = os.path.join("data", "token.txt")
ALL_TYPES = ["Notes", "DPP", "Quiz", "Announcements", "Lectures"]


def load_token():
    token = os.getenv("ACCESS_TOKEN", "").strip()
    if not token and os.path.exists(TOKEN_FILE):
        token = open(TOKEN_FILE).read().strip()
    if not token:
        raise SystemExit("No access token. Put it in ACCESS_TOKEN env or data/token.txt")
    if not verify_token(token).get("success"):
        raise SystemExit("Token is invalid or expired.")
    return token


def main():
    parser = argparse.ArgumentParser(description="PW batch downloader CLI")
    parser.add_argument("--out", default=OUT_DIR, help="Output directory")
    parser.add_argument("--batch", nargs="*", help="Batch name keywords (all if empty)")
    parser.add_argument("--subjects", nargs="*", help="Subject name keywords (all if empty)")
    parser.add_argument(
        "--types", nargs="*", choices=ALL_TYPES, default=ALL_TYPES,
        help="Content types to download (default: all)",
    )
    parser.add_argument("--workers", type=int, default=8, help="Parallel download workers")
    parser.add_argument("--zip", action="store_true", help="Zip each batch folder after download")
    parser.add_argument("--list", action="store_true", help="List batches/subjects/topics and exit")
    args = parser.parse_args()

    token = load_token()

    def _print_tree(tree):
        for bid, entry in tree.items():
            batch = entry["batch"]
            print(f"\nBatch: {batch.get('name')} ({bid})")
            for sid, subj_entry in entry["subjects"].items():
                subj = subj_entry["subject"]
                ntop = len(subj_entry["topics"])
                print(f"  Subject: {subj.get('subject')} ({sid}) — {ntop} topics")
                for tid, t in subj_entry["topics"].items():
                    print(f"    - {t.get('name')} ({tid})")

    print("Loading content tree...")
    tree = build_content_tree(token)
    if args.list:
        _print_tree(tree)
        return

    if not tree:
        raise SystemExit("No batches found for this account.")

    matched = []
    for bid, entry in tree.items():
        batch = entry["batch"]
        name = batch.get("name", "")
        if args.batch and not any(k.lower() in name.lower() for k in args.batch):
            continue
        matched.append(bid)

    if not matched:
        raise SystemExit("No batches matched your --batch keywords.")

    for bid in matched:
        batch = tree[bid]["batch"]
        name = batch.get("name", bid)
        print(f"\n[{name}]")

        subject_ids = []
        for sid, subj_entry in tree[bid]["subjects"].items():
            subj_name = subj_entry["subject"].get("subject", "")
            if not args.subjects or any(k.lower() in subj_name.lower() for k in args.subjects):
                subject_ids.append(sid)

        if not subject_ids:
            print("  No subjects matched --subjects; skipping.")
            continue

        jobs = build_download_jobs(token, tree[bid], subject_ids, args.types, args.out)
        if not jobs:
            print("  Nothing to download.")
            continue

        print(f"  Jobs: {len(jobs)} files")
        start = time.time()
        results = run_downloads(jobs, workers=args.workers)
        ok = sum(1 for _, s, _ in results if s)
        fail = len(results) - ok
        print(f"  Finished in {time.time() - start:.1f}s — {ok} OK, {fail} failed")
        for label, s, detail in results:
            if not s:
                print(f"    FAIL {label}: {detail}")

        base = os.path.join(args.out, _safe_filename(name))
        if args.zip and os.path.isdir(base):
            zip_path = base + ".zip"
            zip_dir(base, zip_path)
            print(f"  Zipped: {zip_path}")


if __name__ == "__main__":
    main()
