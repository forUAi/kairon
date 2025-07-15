#!/usr/bin/env python3
"""
CLI tool for the modular reconciliation engine.
Allows users to trigger reconciliation with different sources.
"""

import argparse
import asyncio
import sys
from datetime import datetime, date
from typing import Optional

from recon_engine.recon.recon_engine import ReconEngine


def parse_date(date_str: str) -> date:
    """Parse date string in YYYY-MM-DD format"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def create_parser():
    """Create and configure the argument parser"""
    parser = argparse.ArgumentParser(
        description="Reconciliation Engine CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py run-recon --source bank_csv --date 2025-07-13 --file_path ./data/bank.csv
  python cli.py run-recon --source api --date 2025-07-13 --base_url https://api.example.com --auth_token abc123
  python cli.py run-recon --source csv --file_path ./data/transactions.csv
  python cli.py run-recon --source payment_processor --date 2025-07-13 --auth_token xyz789
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # run-recon subcommand
    recon_parser = subparsers.add_parser(
        "run-recon", 
        help="Run reconciliation with specified source and parameters"
    )
    
    recon_parser.add_argument(
        "--source",
        required=True,
        choices=["bank_csv", "csv", "api", "payment_processor"],
        help="Source type for reconciliation"
    )
    
    recon_parser.add_argument(
        "--date",
        type=parse_date,
        default=date.today(),
        help="Date for reconciliation (YYYY-MM-DD). Defaults to today"
    )
    
    recon_parser.add_argument(
        "--file_path",
        help="Path to CSV file (required for bank_csv and csv sources)"
    )
    
    recon_parser.add_argument(
        "--base_url",
        help="Base URL for API source"
    )
    
    recon_parser.add_argument(
        "--auth_token",
        help="Authentication token for API or payment processor sources"
    )
    
    return parser


def validate_args(args):
    """Validate argument combinations based on source type"""
    if args.source in ["bank_csv", "csv"]:
        if not args.file_path:
            raise ValueError(f"--file_path is required for source type '{args.source}'")
    
    if args.source == "api":
        if not args.base_url:
            raise ValueError("--base_url is required for source type 'api'")
        if not args.auth_token:
            raise ValueError("--auth_token is required for source type 'api'")
    
    if args.source == "payment_processor":
        if not args.auth_token:
            raise ValueError("--auth_token is required for source type 'payment_processor'")


def print_job_info(job_uuid: str, stats: dict):
    """Print job information and basic statistics"""
    print(f"\n✅ Reconciliation Job Started")
    print(f"Job UUID: {job_uuid}")
    print(f"Status: {stats.get('status', 'Unknown')}")
    
    if 'records_processed' in stats:
        print(f"Records Processed: {stats['records_processed']}")
    
    if 'matches_found' in stats:
        print(f"Matches Found: {stats['matches_found']}")
    
    if 'discrepancies' in stats:
        print(f"Discrepancies: {stats['discrepancies']}")
    
    if 'processing_time' in stats:
        print(f"Processing Time: {stats['processing_time']}")
    
    if 'errors' in stats and stats['errors']:
        print(f"Errors: {stats['errors']}")


async def run_reconciliation(args):
    """Execute the reconciliation process"""
    try:
        # Initialize the ReconEngine
        engine = ReconEngine()
        
        # Prepare arguments for the engine
        engine_args = {
            'date': args.date,
            'source': args.source
        }
        
        # Add optional parameters if provided
        if args.file_path:
            engine_args['file_path'] = args.file_path
        
        if args.base_url:
            engine_args['base_url'] = args.base_url
        
        if args.auth_token:
            engine_args['auth_token'] = args.auth_token
        
        print(f"🚀 Starting reconciliation for source: {args.source}")
        print(f"📅 Date: {args.date}")
        
        if args.file_path:
            print(f"📁 File: {args.file_path}")
        
        if args.base_url:
            print(f"🌐 Base URL: {args.base_url}")
        
        # Run the reconciliation
        result = await engine.run(**engine_args)
        
        # Extract job UUID and stats from result
        if isinstance(result, dict):
            job_uuid = result.get('job_uuid', 'N/A')
            stats = result.get('stats', {})
        else:
            # Handle case where result might be just a UUID or different format
            job_uuid = str(result) if result else 'N/A'
            stats = {'status': 'Completed'}
        
        print_job_info(job_uuid, stats)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error running reconciliation: {str(e)}", file=sys.stderr)
        return 1


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == "run-recon":
        try:
            # Validate arguments
            validate_args(args)
            
            # Run the reconciliation
            return asyncio.run(run_reconciliation(args))
            
        except ValueError as e:
            print(f"❌ Validation Error: {str(e)}", file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            print("\n⏹️  Operation cancelled by user", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}", file=sys.stderr)
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())