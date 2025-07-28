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
@click.option('--devin-token', help='Devin API token for session-based analysis (or set DEVIN_API_TOKEN env var)')
@click.option('--json', 'output_json', is_flag=True, help='Output results in JSON format')
def scope_issue(repo, issue_number, token, devin_token, output_json):
    """
    Analyze a GitHub issue and provide confidence scoring for resolution.
    Automatically posts analysis results as a comment to the GitHub issue when a token is provided.
    
    REPO should be in the format 'owner/repo-name' (e.g., 'microsoft/vscode')
    ISSUE_NUMBER is the GitHub issue number to analyze
    
    Examples:
        scope_issue_cli.py microsoft/vscode 12345
        scope_issue_cli.py microsoft/vscode 12345 --token=your_github_token
        scope_issue_cli.py microsoft/vscode 12345 --devin-token=your_devin_token
        scope_issue_cli.py microsoft/vscode 12345 --json
    """
    
    try:
        repo_owner, repo_name = repo.split('/', 1)
    except ValueError:
        click.echo("Error: Repository must be in format 'owner/repo-name'", err=True)
        sys.exit(1)
    
    github_token = token or os.getenv('GITHUB_TOKEN')
    devin_api_token = devin_token or os.getenv('DEVIN_API_TOKEN')
    scoper = IssueScoper(github_token, devin_api_token)
    
    if not github_token:
        click.echo("Warning: No GitHub token provided. API rate limits will be lower.", err=True)
        click.echo("Set GITHUB_TOKEN environment variable or use --token option.", err=True)
        click.echo()
    
    if not devin_api_token:
        click.echo("Warning: No Devin API token provided. Using fallback keyword analysis.", err=True)
        click.echo("Set DEVIN_API_TOKEN environment variable or use --devin-token option for AI-powered analysis.", err=True)
        click.echo()
    
    click.echo(f"Analyzing issue #{issue_number} from {repo}...")
    
    analysis = scoper.analyze_issue(repo_owner, repo_name, issue_number)
    
    if not analysis:
        click.echo("Warning: Could not parse structured analysis from Devin session.", err=True)
        click.echo("This may happen when the session completes but doesn't return expected format.", err=True)
        
        if github_token:
            click.echo("Attempting to extract and post available analysis data as comment...")
            
            raw_analysis = scoper.get_raw_session_analysis(repo_owner, repo_name, issue_number)
            if raw_analysis:
                success = scoper.post_raw_analysis_comment(repo_owner, repo_name, issue_number, raw_analysis)
                if success:
                    click.echo("✅ Successfully posted available analysis as comment to GitHub issue!")
                    click.echo("📝 Analysis has been documented directly on the GitHub issue.")
                    sys.exit(0)
                else:
                    click.echo("❌ Failed to post comment to GitHub issue.", err=True)
            else:
                click.echo("❌ No analysis data could be extracted from the session.", err=True)
        
        click.echo("Error: Could not analyze issue. Check repository and issue number.", err=True)
        sys.exit(1)
    
    formatted_analysis = format_analysis(analysis)
    
    if github_token:
        click.echo("Posting analysis as comment to GitHub issue...")
        success = scoper.post_analysis_comment(repo_owner, repo_name, issue_number, formatted_analysis)
        if success:
            click.echo("✅ Analysis successfully posted as comment to GitHub issue!")
            click.echo("📝 Full analysis has been documented directly on the GitHub issue.")
        else:
            click.echo("Warning: Failed to post comment to GitHub issue, but analysis completed successfully.", err=True)
    
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
        click.echo(formatted_analysis)

if __name__ == '__main__':
    scope_issue()
