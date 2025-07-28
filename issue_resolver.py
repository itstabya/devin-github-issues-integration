#!/usr/bin/env python3
"""
GitHub Issue Resolution Module
Triggers Devin sessions to resolve GitHub issues by creating and executing action plans.
"""

import json
import requests
import time
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class ExecutionStatus(Enum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    BLOCKED = "blocked"
    IN_PROGRESS = "in_progress"

@dataclass
class ResolutionResult:
    issue_number: int
    title: str
    execution_status: ExecutionStatus
    success_score: float  # 1-10 scale
    action_plan: List[str]
    changes_made: List[str]
    pr_created: bool
    pr_url: Optional[str]
    blockers_encountered: List[str]
    session_url: str
    summary: str

class IssueResolver:
    def __init__(self, github_token: Optional[str] = None, devin_token: Optional[str] = None):
        self.github_token = github_token
        self.devin_token = devin_token or os.getenv('DEVIN_API_TOKEN')
        self.github_headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Issues-Resolver'
        }
        if self.github_token:
            self.github_headers['Authorization'] = f'token {self.github_token}'
        
        self.devin_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.devin_token}' if self.devin_token else None
        }
        self.devin_base_url = 'https://api.devin.ai'
    
    def resolve_issue(self, repo_owner: str, repo_name: str, issue_number: int, analysis_data: Dict) -> Optional[ResolutionResult]:
        """
        Trigger a Devin session to resolve a GitHub issue using a provided action plan from issue scoping.
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            issue_number: Issue number to resolve
            analysis_data: Dictionary containing issue analysis from scope_issue_cli.py
            
        Returns:
            ResolutionResult object with execution status and details
        """
        issue_data = self._fetch_issue_details(repo_owner, repo_name, issue_number)
        if not issue_data:
            return None
        
        if self.devin_token:
            return self._resolve_with_devin_api(issue_data, repo_owner, repo_name, analysis_data)
        else:
            print("Error: Devin API token is required for issue resolution.")
            return None
    
    def _fetch_issue_details(self, repo_owner: str, repo_name: str, issue_number: int) -> Optional[Dict]:
        """Fetch detailed issue information from GitHub API."""
        url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{issue_number}'
        
        try:
            response = requests.get(url, headers=self.github_headers)
            response.raise_for_status()
            issue = response.json()
            
            comments_url = issue['comments_url']
            comments_response = requests.get(comments_url, headers=self.github_headers)
            comments = comments_response.json() if comments_response.status_code == 200 else []
            
            issue['comment_details'] = comments
            return issue
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching issue details: {e}")
            return None
    
    def _fetch_devin_analysis_from_comments(self, repo_owner: str, repo_name: str, issue_number: int) -> Optional[Dict]:
        """
        Fetch the most recent Devin analysis comment from GitHub issue comments.
        
        Returns:
            Dictionary containing parsed analysis data or None if no analysis found
        """
        issue_data = self._fetch_issue_details(repo_owner, repo_name, issue_number)
        if not issue_data:
            return None
            
        comments = issue_data.get('comment_details', [])
        
        for comment in reversed(comments):
            body = comment.get('body', '')
            if '🤖 Devin Analysis Results' in body:
                return self._parse_analysis_comment(body)
        
        return None
    
    def _parse_analysis_comment(self, comment_body: str) -> Optional[Dict]:
        """Parse Devin analysis comment markdown into analysis data dictionary."""
        import re
        
        try:
            category_match = re.search(r'Category:\s*([^\n]+)', comment_body)
            complexity_match = re.search(r'Complexity:\s*(\w+)\s*\((\d+)/5\)', comment_body)
            confidence_match = re.search(r'Confidence Score:\s*([\d.]+)/10', comment_body)
            effort_match = re.search(r'Estimated Effort:\s*(\d+)\s*hours?', comment_body)
            
            key_factors = []
            factors_section = re.search(r'🔍 Key Factors:(.*?)(?=⚠️|🔗|💭|$)', comment_body, re.DOTALL)
            if factors_section:
                factors_text = factors_section.group(1)
                key_factors = [line.strip().lstrip('• ').strip() for line in factors_text.split('\n') 
                             if line.strip() and '•' in line and 'None identified' not in line]
            
            blockers = []
            blockers_section = re.search(r'⚠️.*?Potential Blockers:(.*?)(?=🔗|💭|$)', comment_body, re.DOTALL)
            if blockers_section:
                blockers_text = blockers_section.group(1)
                blockers = [line.strip().lstrip('• ').strip() for line in blockers_text.split('\n') 
                          if line.strip() and '•' in line and 'None identified' not in line]
            
            dependencies = []
            deps_section = re.search(r'🔗 Dependencies:(.*?)(?=💭|$)', comment_body, re.DOTALL)
            if deps_section:
                deps_text = deps_section.group(1)
                dependencies = [line.strip().lstrip('• ').strip() for line in deps_text.split('\n') 
                              if line.strip() and '•' in line and 'None identified' not in line]
            
            reasoning_match = re.search(r'💭 Reasoning:\s*(.*?)(?=---|$)', comment_body, re.DOTALL)
            reasoning = reasoning_match.group(1).strip() if reasoning_match else ''
            
            complexity_level = 'moderate'
            complexity_value = 3
            if complexity_match:
                complexity_level = complexity_match.group(1).strip().lower()
                complexity_value = int(complexity_match.group(2)) if complexity_match.group(2) else 3
            
            return {
                'category': category_match.group(1).strip().lower() if category_match else 'unknown',
                'complexity': {
                    'level': complexity_level,
                    'value': complexity_value
                },
                'confidence_score': float(confidence_match.group(1)) if confidence_match else 5.0,
                'estimated_effort_hours': int(effort_match.group(1)) if effort_match else 8,
                'key_factors': key_factors,
                'blockers': blockers,
                'dependencies': dependencies,
                'reasoning': reasoning
            }
            
        except Exception as e:
            print(f"Error parsing analysis comment: {e}")
            return None
    
    def _resolve_with_devin_api(self, issue_data: Dict, repo_owner: str, repo_name: str, analysis_data: Dict) -> Optional[ResolutionResult]:
        """Resolve issue using Devin API session."""
        if not self.devin_token:
            print("Error: Devin API token is required for session-based resolution")
            return None
        
        title = issue_data['title']
        body = issue_data.get('body', '') or ''
        labels = [label['name'] for label in issue_data.get('labels', [])]
        comments = issue_data.get('comment_details', [])
        issue_number = issue_data['number']
        
        prompt = self._create_resolution_prompt(title, body, labels, comments, repo_owner, repo_name, issue_number, analysis_data)
        
        session_id = self._create_devin_session(prompt)
        if not session_id:
            print("Error: Failed to create Devin session")
            return None
        
        resolution_result = self._wait_for_session_completion(session_id)
        if not resolution_result:
            print("Error: Failed to get resolution from Devin session")
            return None
        
        return self._parse_devin_resolution(resolution_result, issue_data, session_id)
    
    def _create_resolution_prompt(self, title: str, body: str, labels: List[str], 
                                comments: List[Dict], repo_owner: str, repo_name: str, 
                                issue_number: int, analysis_data: Dict) -> str:
        """Create a detailed prompt for Devin to resolve the GitHub issue using provided analysis."""
        comments_text = ""
        if comments:
            comments_text = "\n\nComments:\n" + "\n".join([
                f"- {comment.get('user', {}).get('login', 'Unknown')}: {comment.get('body', '')[:200]}..."
                for comment in comments[:5]
            ])
        
        labels_text = f"Labels: {', '.join(labels)}" if labels else "Labels: None"
        
        category = analysis_data.get('category', 'unknown')
        complexity = analysis_data.get('complexity', {})
        confidence_score = analysis_data.get('confidence_score', 5.0)
        estimated_effort = analysis_data.get('estimated_effort_hours', 8)
        key_factors = analysis_data.get('key_factors', [])
        blockers = analysis_data.get('blockers', [])
        dependencies = analysis_data.get('dependencies', [])
        reasoning = analysis_data.get('reasoning', '')
        
        analysis_summary = f"""
Previous Analysis Results:
- Category: {category}
- Complexity: {complexity.get('level', 'moderate')} ({complexity.get('value', 3)}/5)
- Confidence Score: {confidence_score}/10
- Estimated Effort: {estimated_effort} hours
- Key Factors: {', '.join(key_factors) if key_factors else 'None'}
- Potential Blockers: {', '.join(blockers) if blockers else 'None'}
- Dependencies: {', '.join(dependencies) if dependencies else 'None'}
- Analysis Reasoning: {reasoning}
"""

        prompt = f"""You are tasked with resolving this GitHub issue from {repo_owner}/{repo_name}. A previous analysis has been completed and you should use this information to guide your resolution approach.

Issue #{issue_number}: {title}

{labels_text}

Description:
{body[:1000]}...{comments_text}

{analysis_summary}

Please follow these steps to execute the resolution:

1. **REVIEW THE ANALYSIS**: Use the provided analysis to understand the issue scope and approach
2. **EXECUTE THE RESOLUTION**: Implement the necessary changes based on the analysis insights
3. **ADDRESS KEY FACTORS**: Pay special attention to the identified key factors
4. **HANDLE BLOCKERS**: Work around or resolve any identified blockers
5. **MANAGE DEPENDENCIES**: Ensure dependencies are properly handled
6. **CREATE PULL REQUEST**: If code changes were made, create a PR with your changes
7. **REPORT RESULTS**: Provide a summary of what was accomplished

At the end of your session, please provide a structured summary in this JSON format:
{{
    "execution_status": "success|partial_success|failed|blocked",
    "success_score": <float between 1.0 and 10.0>,
    "action_plan": ["step1", "step2", "step3", ...],
    "changes_made": ["change1", "change2", ...],
    "pr_created": true|false,
    "pr_url": "https://github.com/owner/repo/pull/123" or null,
    "blockers_encountered": ["blocker1", "blocker2", ...],
    "summary": "Detailed summary of what was accomplished and any remaining work"
}}

Focus on:
- Using the provided analysis to guide your approach and avoid re-analyzing
- Implementing working solutions that address the core problem identified in the analysis
- Paying special attention to the key factors, blockers, and dependencies from the analysis
- Testing your changes to ensure they work correctly
- Creating a well-documented pull request if changes were made
- Providing clear feedback on success/failure and any remaining blockers

Be thorough in your implementation and testing. The analysis has already identified the scope and approach, so focus on execution rather than re-analysis."""
        
        return prompt
    
    def _create_devin_session(self, prompt: str) -> Optional[str]:
        """Create a new Devin session with the resolution prompt."""
        url = f"{self.devin_base_url}/v1/sessions"
        payload = {
            "prompt": prompt,
            "unlisted": True
        }
        
        try:
            response = requests.post(url, headers=self.devin_headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get('session_id')
        except requests.exceptions.RequestException as e:
            print(f"Error creating Devin session: {e}")
            return None
    
    def _wait_for_session_completion(self, session_id: str, max_wait_time: int = 1800) -> Optional[Dict]:
        """Wait for Devin session to complete and return the structured resolution result."""
        url = f"{self.devin_base_url}/v1/session/{session_id}"
        start_time = time.time()
        
        print(f"Waiting for session {session_id} to complete...")
        print("This may take several minutes as Devin works to resolve the issue...")
        
        while time.time() - start_time < max_wait_time:
            try:
                response = requests.get(url, headers=self.devin_headers)
                response.raise_for_status()
                session_data = response.json()
                
                status_enum = session_data.get('status_enum', '')
                
                print(f"Session status: status_enum={status_enum}")
                
                if status_enum in ['blocked', 'finished']:
                    structured_output = session_data.get('structured_output', {})
                    if structured_output:
                        print("Found structured_output with resolution data!")
                        return structured_output
                    else:
                        print("No structured_output found in session response")
                        if status_enum == 'finished':
                            return None
                elif status_enum in ['expired']:
                    print(f"Session {session_id} ended with status: {status_enum}")
                    return None
                
                time.sleep(30)
                
            except requests.exceptions.RequestException as e:
                print(f"Error checking session status: {e}")
                return None
        
        print(f"Session {session_id} timed out after {max_wait_time} seconds")
        return None
    
    def _parse_devin_resolution(self, resolution_data: Dict, issue_data: Dict, session_id: str) -> Optional[ResolutionResult]:
        """Parse Devin's structured resolution response into ResolutionResult object."""
        try:
            if not resolution_data:
                raise ValueError("No resolution data provided")
            
            status_map = {
                'success': ExecutionStatus.SUCCESS,
                'partial_success': ExecutionStatus.PARTIAL_SUCCESS,
                'failed': ExecutionStatus.FAILED,
                'blocked': ExecutionStatus.BLOCKED,
                'in_progress': ExecutionStatus.IN_PROGRESS
            }
            
            execution_status = status_map.get(
                resolution_data.get('execution_status', 'failed'), 
                ExecutionStatus.FAILED
            )
            
            session_url = f"https://app.devin.ai/sessions/{session_id}"
            
            return ResolutionResult(
                issue_number=issue_data['number'],
                title=issue_data['title'],
                execution_status=execution_status,
                success_score=float(resolution_data.get('success_score', 5.0)),
                action_plan=resolution_data.get('action_plan', []),
                changes_made=resolution_data.get('changes_made', []),
                pr_created=bool(resolution_data.get('pr_created', False)),
                pr_url=resolution_data.get('pr_url'),
                blockers_encountered=resolution_data.get('blockers_encountered', []),
                session_url=session_url,
                summary=resolution_data.get('summary', 'Resolution completed via Devin API')
            )
            
        except (ValueError, KeyError) as e:
            print(f"Error parsing Devin resolution: {e}")
            print(f"Raw resolution data: {str(resolution_data)[:500]}...")
            return None

def format_resolution(resolution: ResolutionResult) -> str:
    """Format resolution results for display."""
    status_emoji = {
        ExecutionStatus.SUCCESS: "🟢",
        ExecutionStatus.PARTIAL_SUCCESS: "🟡", 
        ExecutionStatus.FAILED: "🔴",
        ExecutionStatus.BLOCKED: "⚠️",
        ExecutionStatus.IN_PROGRESS: "🔄"
    }
    
    emoji = status_emoji.get(resolution.execution_status, "❓")
    
    output = f"""
{emoji} Issue #{resolution.issue_number}: {resolution.title}

🎯 Resolution Results:
   Status: {resolution.execution_status.value.replace('_', ' ').title()}
   Success Score: {resolution.success_score}/10
   PR Created: {'Yes' if resolution.pr_created else 'No'}
   {f'PR URL: {resolution.pr_url}' if resolution.pr_url else ''}

📋 Action Plan:
   {chr(10).join(f'   {i+1}. {step}' for i, step in enumerate(resolution.action_plan)) if resolution.action_plan else '   • No action plan provided'}

✅ Changes Made:
   {chr(10).join(f'   • {change}' for change in resolution.changes_made) if resolution.changes_made else '   • No changes documented'}

⚠️  Blockers Encountered:
   {chr(10).join(f'   • {blocker}' for blocker in resolution.blockers_encountered) if resolution.blockers_encountered else '   • None'}

🔗 Session URL: {resolution.session_url}

📝 Summary:
   {resolution.summary}
"""
    return output
