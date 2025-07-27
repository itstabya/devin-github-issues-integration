#!/usr/bin/env python3
"""
GitHub Issue Scoping CLI Tool
Command-line interface for analyzing GitHub issues and providing confidence scores.
"""

import os
import sys
import click
from dotenv import load_dotenv
from issue_scoper import IssueScoper, format_analysis

load_dotenv()

@click.command()
@click.argument('repo', required=True)
@click.argument('issue_number', type=int, required=True)
@click.option('--token', help='GitHub personal access token (or set GITHUB_TOKEN env var)')
@click.option('--json', 'output_json', is_flag=True, help='Output results in JSON format')
def scope_issue(repo, issue_number, token, output_json):
    """
    Analyze a GitHub issue and provide confidence scoring for resolution.
    
    REPO should be in the format 'owner/repo-name' (e.g., 'microsoft/vscode')
    ISSUE_NUMBER is the GitHub issue number to analyze
    
    Examples:
        scope_issue_cli.py microsoft/vscode 12345
        scope_issue_cli.py microsoft/vscode 12345 --token=your_token
        scope_issue_cli.py microsoft/vscode 12345 --json
    """
    
    try:
        repo_owner, repo_name = repo.split('/', 1)
    except ValueError:
        click.echo("Error: Repository must be in format 'owner/repo-name'", err=True)
        sys.exit(1)
    
    github_token = token or os.getenv('GITHUB_TOKEN')
    scoper = IssueScoper(github_token)
    
    if not github_token:
        click.echo("Warning: No GitHub token provided. API rate limits will be lower.", err=True)
        click.echo("Set GITHUB_TOKEN environment variable or use --token option.", err=True)
        click.echo()
    
    click.echo(f"Analyzing issue #{issue_number} from {repo}...")
    
    analysis = scoper.analyze_issue(repo_owner, repo_name, issue_number)
    
    if not analysis:
        click.echo("Error: Could not analyze issue. Check repository and issue number.", err=True)
        sys.exit(1)
    
    if output_json:
        import json
        result = {
            'issue_number': analysis.issue_number,
            'title': analysis.title,
            'category': analysis.category.value,
            'complexity': {
                'level': analysis.complexity.name,
                'value': analysis.complexity.value
            },
            'confidence_score': analysis.confidence_score,
            'estimated_effort_hours': analysis.estimated_effort_hours,
            'key_factors': analysis.key_factors,
            'blockers': analysis.blockers,
            'dependencies': analysis.dependencies,
            'reasoning': analysis.reasoning
        }
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(format_analysis(analysis))

if __name__ == '__main__':
    scope_issue()
