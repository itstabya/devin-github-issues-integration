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
@click.option('--json', 'output_json', is_flag=True, help='Output results in JSON format')
def resolve_issue(repo, issue_number, token, devin_token, output_json):
    """
    Trigger a Devin session to resolve a GitHub issue using the most recent Devin analysis comment.
    If no analysis exists, prompts user to run Step 2 (scoping) or continue without analysis.
    
    REPO should be in the format 'owner/repo-name' (e.g., 'microsoft/vscode')
    ISSUE_NUMBER is the GitHub issue number to resolve
    
    Examples:
        resolve_issue_cli.py microsoft/vscode 12345
        resolve_issue_cli.py microsoft/vscode 12345 --json
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
    
    click.echo(f"Looking for existing Devin analysis on issue #{issue_number}...")
    analysis_data = resolver._fetch_devin_analysis_from_comments(repo_owner, repo_name, issue_number)
    
    if not analysis_data:
        click.echo("⚠️  No existing Devin analysis found on this issue.")
        click.echo()
        click.echo("Options:")
        click.echo("1. Run Step 2 (Issue Scoping) first to analyze the issue")
        click.echo("2. Continue with resolution without prior analysis (not recommended)")
        click.echo("3. Cancel and exit")
        
        choice = click.prompt("Choose an option", type=click.Choice(['1', '2', '3']))
        
        if choice == '1':
            click.echo("Please run the scoping tool first:")
            click.echo(f"python scope_issue_cli.py {repo} {issue_number}")
            sys.exit(0)
        elif choice == '3':
            click.echo("Operation cancelled.")
            sys.exit(0)
        else:
            click.echo("⚠️  Proceeding without prior analysis. Results may be less reliable.")
            analysis_data = {
                'category': 'unknown',
                'complexity': {
                    'level': 'moderate',
                    'value': 3
                },
                'confidence_score': 5.0,
                'estimated_effort_hours': 8,
                'key_factors': [],
                'blockers': [],
                'dependencies': [],
                'reasoning': 'No prior analysis available'
            }
    else:
        click.echo("✅ Found existing Devin analysis. Using it for resolution guidance.")
    
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
