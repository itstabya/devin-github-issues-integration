#!/usr/bin/env python3
"""
GitHub Issues CLI Tool
A command-line tool to list GitHub issues from a repository.
"""

import os
import sys
import requests
import click
from dotenv import load_dotenv

load_dotenv()

class GitHubIssuesClient:
    def __init__(self, token=None):
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.base_url = 'https://api.github.com'
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Issues-CLI'
        }
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
    
    def list_issues(self, repo_owner, repo_name, state='open', labels=None, assignee=None, limit=30):
        """
        List issues from a GitHub repository.
        
        Args:
            repo_owner (str): Repository owner/organization
            repo_name (str): Repository name
            state (str): Issue state ('open', 'closed', 'all')
            labels (str): Comma-separated list of labels
            assignee (str): Username of assignee
            limit (int): Maximum number of issues to return
        
        Returns:
            list: List of issue dictionaries
        """
        url = f'{self.base_url}/repos/{repo_owner}/{repo_name}/issues'
        
        params = {
            'state': state,
            'per_page': min(limit, 100),
            'sort': 'updated',
            'direction': 'desc'
        }
        
        if labels:
            params['labels'] = labels
        if assignee:
            params['assignee'] = assignee
            
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            click.echo(f"Error fetching issues: {e}", err=True)
            return []

def format_issue(issue):
    """Format an issue for display."""
    number = issue['number']
    title = issue['title']
    state = issue['state']
    author = issue['user']['login']
    created_at = issue['created_at'][:10]  # Just the date part
    
    labels = [label['name'] for label in issue.get('labels', [])]
    labels_str = f" [{', '.join(labels)}]" if labels else ""
    
    assignees = [assignee['login'] for assignee in issue.get('assignees', [])]
    assignees_str = f" (assigned to: {', '.join(assignees)})" if assignees else ""
    
    state_emoji = "🟢" if state == "open" else "🔴"
    
    return f"{state_emoji} #{number}: {title}{labels_str}{assignees_str}\n   Author: {author} | Created: {created_at}"

@click.command()
@click.argument('repo', required=True)
@click.option('--state', default='open', type=click.Choice(['open', 'closed', 'all']), 
              help='Filter issues by state (default: open)')
@click.option('--labels', help='Filter by labels (comma-separated)')
@click.option('--assignee', help='Filter by assignee username')
@click.option('--limit', default=30, type=int, help='Maximum number of issues to display (default: 30)')
@click.option('--token', help='GitHub personal access token (or set GITHUB_TOKEN env var)')
def list_issues(repo, state, labels, assignee, limit, token):
    """
    List GitHub issues from a repository.
    
    REPO should be in the format 'owner/repo-name' (e.g., 'microsoft/vscode')
    
    Examples:
        github_issues_cli.py microsoft/vscode
        github_issues_cli.py microsoft/vscode --state=all --limit=10
        github_issues_cli.py microsoft/vscode --labels=bug,enhancement
        github_issues_cli.py microsoft/vscode --assignee=username
    """
    
    try:
        repo_owner, repo_name = repo.split('/', 1)
    except ValueError:
        click.echo("Error: Repository must be in format 'owner/repo-name'", err=True)
        sys.exit(1)
    
    client = GitHubIssuesClient(token)
    
    if not client.token:
        click.echo("Warning: No GitHub token provided. API rate limits will be lower.", err=True)
        click.echo("Set GITHUB_TOKEN environment variable or use --token option for higher limits.", err=True)
        click.echo()
    
    click.echo(f"Fetching {state} issues from {repo}...")
    issues = client.list_issues(repo_owner, repo_name, state, labels, assignee, limit)
    
    if not issues:
        click.echo("No issues found or error occurred.")
        return
    
    click.echo(f"\nFound {len(issues)} issue(s):\n")
    for issue in issues:
        click.echo(format_issue(issue))
        click.echo()

if __name__ == '__main__':
    list_issues()
