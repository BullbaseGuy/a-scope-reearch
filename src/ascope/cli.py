from __future__ import annotations

import argparse
import json
from pathlib import Path

from ascope.adapters.cninfo import discover
from ascope.bundle import package_bundle
from ascope.config import load_settings
from ascope.dashboard import build as build_dashboard
from ascope.financial_merge import merge_exports
from ascope.financial_requests import build as build_financial_requests
from ascope.fixtures import generate
from ascope.io import read_frame, write_frame, write_json
from ascope.pipeline import run
from ascope.qa import validate_bundle, validate_output


def command_fixture(args: argparse.Namespace) -> int:
    generate(args.output_dir, args.as_of_date, args.count)
    manifest = run(args.output_dir, args.output_dir, args.as_of_date, mode='fixture')
    shortlist = read_frame(args.output_dir / 'shortlist.csv')
    build_dashboard(shortlist, args.output_dir / 'A_SCOPE_fixture_dashboard.html', 'A-SCOPE Fixture Regression')
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


def command_discover(args: argparse.Namespace) -> int:
    payloads = [Path(x) for x in args.payload] if args.payload else None
    frame, manifest = discover(args.output_dir, args.as_of_date, args.minimum_count, payloads)
    write_frame(frame, args.output_dir / 'security_master.csv')
    write_json(args.output_dir / 'discovery_manifest.json', manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if manifest['validation']['status'] == 'PASS' else 3


def command_merge_financials(args: argparse.Namespace) -> int:
    result = merge_exports(args.input_dir, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_package_bundle(args: argparse.Namespace) -> int:
    result = package_bundle(
        args.input_dir,
        args.output_zip,
        args.as_of_date,
        minimum_securities=args.minimum_securities,
        minimum_market_days=args.minimum_market_days,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog='ascope')
    sub = parser.add_subparsers(dest='command', required=True)

    p = sub.add_parser('validate-config')
    p.set_defaults(func=lambda _args: (load_settings(), print('{"status":"PASS"}'), 0)[2])

    p = sub.add_parser('fixture')
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--as-of-date', default='2026-07-29')
    p.add_argument('--count', type=int, default=120)
    p.set_defaults(func=command_fixture)

    p = sub.add_parser('discover')
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--as-of-date', required=True)
    p.add_argument('--minimum-count', type=int, default=5000)
    p.add_argument('--payload', action='append')
    p.set_defaults(func=command_discover)

    p = sub.add_parser('validate-bundle')
    p.add_argument('--input-dir', type=Path, required=True)
    p.add_argument('--as-of-date', required=True)
    p.add_argument('--minimum-securities', type=int, default=5000)
    p.add_argument('--minimum-market-days', type=int, default=120)
    p.set_defaults(func=lambda a: 0 if validate_bundle(a.input_dir, a.as_of_date, minimum_securities=a.minimum_securities, minimum_market_days=a.minimum_market_days)['status'] == 'PASS' else 2)

    p = sub.add_parser('screen')
    p.add_argument('--input-dir', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--as-of-date', required=True)
    p.add_argument('--mode', choices=['live','fixture'], required=True)
    p.set_defaults(func=lambda a: (print(json.dumps(run(a.input_dir, a.output_dir, a.as_of_date, mode=a.mode), ensure_ascii=False, indent=2)), 0)[1])

    p = sub.add_parser('validate-output')
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--mode', choices=['live','fixture'], required=True)
    p.set_defaults(func=lambda a: (lambda r: (print(json.dumps(r, ensure_ascii=False, indent=2)), 0 if r['status']=='PASS' else 2)[1])(validate_output(a.output_dir, a.mode)))

    p = sub.add_parser('financial-manifest')
    p.add_argument('--security-master', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--through', required=True)
    p.add_argument('--batch-size', type=int, default=200)
    p.set_defaults(func=lambda a: (print(json.dumps(build_financial_requests(a.security_master, a.output_dir, a.through, a.batch_size), ensure_ascii=False, indent=2)), 0)[1])

    p = sub.add_parser('merge-financials')
    p.add_argument('--input-dir', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.set_defaults(func=command_merge_financials)

    p = sub.add_parser('package-bundle')
    p.add_argument('--input-dir', type=Path, required=True)
    p.add_argument('--output-zip', type=Path, required=True)
    p.add_argument('--as-of-date', required=True)
    p.add_argument('--minimum-securities', type=int, default=5000)
    p.add_argument('--minimum-market-days', type=int, default=120)
    p.set_defaults(func=command_package_bundle)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == '__main__':
    raise SystemExit(main())
