#!/usr/bin/env python3
"""
GitHub Issue Resolution CLI Tool
Command-line interface for triggering Devin sessions to resolve GitHub issues.
"""

import os
import sys
import json
import click
from dotenv import load_dotenv
from issue_resolver import IssueResolver, format_resolution

load_dotenv()

@click.command()
@click.argument('repo', required=True)
@click.argument('issue_number', type=int, required=True)
@click.option('--token', help='GitHub personal access token (or set GITHUB_TOKEN env var)')
@click.option('--devin-token', help='Devin API token for session-based resolution (or set DEVIN_API_TOKEN env var)')
@click.option('--analysis-file', help='Path to JSON file containing issue analysis from scope_issue_cli.py')
@click.option('--analysis-json', help='JSON string containing issue analysis from scope_issue_cli.py')
@click.option('--json', 'output_json', is_flag=True, help='Output results in JSON format')
def resolve_issue(repo, issue_number, token, devin_token, analysis_file, analysis_json, output_json):
    """
    Trigger a Devin session to resolve a GitHub issue using a provided action plan from issue scoping.
    
    REPO should be in the format 'owner/repo-name' (e.g., 'microsoft/vscode')
    ISSUE_NUMBER is the GitHub issue number to resolve
    
    Examples:
        resolve_issue_cli.py microsoft/vscode 12345 --analysis-file=analysis.json
        resolve_issue_cli.py microsoft/vscode 12345 --analysis-json='{"category":"bug",...}'
        resolve_issue_cli.py microsoft/vscode 12345 --analysis-file=analysis.json --json
    """
    
    try:
        repo_owner, repo_name = repo.split('/', 1)
    except ValueError:
        click.echo("Error: Repository must be in format 'owner/repo-name'", err=True)
        sys.exit(1)
    
    github_token = token or os.getenv('GITHUB_TOKEN')
    devin_api_token = devin_token or os.getenv('DEVIN_API_TOKEN')
    resolver = IssueResolver(github_token, devin_api_token)
    
    if not github_token:
        click.echo("Warning: No GitHub token provided. API rate limits will be lower.", err=True)
        click.echo("Set GITHUB_TOKEN environment variable or use --token option.", err=True)
        click.echo()
    
    if not devin_api_token:
        click.echo("Error: Devin API token is required for issue resolution.", err=True)
        click.echo("Set DEVIN_API_TOKEN environment variable or use --devin-token option.", err=True)
        sys.exit(1)
    
    analysis_data = None
    if analysis_file:
        try:
            with open(analysis_file, 'r') as f:
                analysis_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            click.echo(f"Error reading analysis file: {e}", err=True)
            sys.exit(1)
    elif analysis_json:
        try:
            analysis_data = json.loads(analysis_json)
        except json.JSONDecodeError as e:
            click.echo(f"Error parsing analysis JSON: {e}", err=True)
            sys.exit(1)
    else:
        click.echo("Error: Either --analysis-file or --analysis-json must be provided.", err=True)
        click.echo("Run scope_issue_cli.py first to generate the analysis data.", err=True)
        sys.exit(1)
    
    click.echo(f"Triggering Devin session to resolve issue #{issue_number} from {repo}...")
    
    resolution = resolver.resolve_issue(repo_owner, repo_name, issue_number, analysis_data)
    
    if not resolution:
        click.echo("Error: Could not resolve issue. Check repository and issue number.", err=True)
        sys.exit(1)
    
    if output_json:
        import json
        result = {
            'issue_number': resolution.issue_number,
            'title': resolution.title,
            'execution_status': resolution.execution_status.value,
            'success_score': resolution.success_score,
            'action_plan': resolution.action_plan,
            'changes_made': resolution.changes_made,
            'pr_created': resolution.pr_created,
            'pr_url': resolution.pr_url,
            'blockers_encountered': resolution.blockers_encountered,
            'session_url': resolution.session_url,
            'summary': resolution.summary
        }
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(format_resolution(resolution))

if __name__ == '__main__':
    resolve_issue()
