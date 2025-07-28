#!/usr/bin/env python3
"""
GitHub Issue Scoping Module
Analyzes GitHub issues and provides confidence scores for resolution using Devin API.
"""

import json
import requests
import time
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class IssueCategory(Enum):
    BUG = "bug"
    FEATURE = "feature"
    DOCUMENTATION = "documentation"
    ENHANCEMENT = "enhancement"
    QUESTION = "question"
    MAINTENANCE = "maintenance"
    SECURITY = "security"
    PERFORMANCE = "performance"
    UNKNOWN = "unknown"

class ComplexityLevel(Enum):
    TRIVIAL = 1
    SIMPLE = 2
    MODERATE = 3
    COMPLEX = 4
    VERY_COMPLEX = 5

@dataclass
class IssueAnalysis:
    issue_number: int
    title: str
    category: IssueCategory
    complexity: ComplexityLevel
    confidence_score: float  # 1-10 scale
    estimated_effort_hours: int
    key_factors: List[str]
    blockers: List[str]
    dependencies: List[str]
    reasoning: str

class IssueScoper:
    def __init__(self, github_token: Optional[str] = None, devin_token: Optional[str] = None):
        self.github_token = github_token
        self.devin_token = devin_token or os.getenv('DEVIN_API_TOKEN')
        self.github_headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Issues-Scoper'
        }
        if self.github_token:
            self.github_headers['Authorization'] = f'token {self.github_token}'
        
        self.devin_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.devin_token}' if self.devin_token else None
        }
        self.devin_base_url = 'https://api.devin.ai'
    
    def analyze_issue(self, repo_owner: str, repo_name: str, issue_number: int) -> Optional[IssueAnalysis]:
        """
        Analyze a single GitHub issue using Devin API and return confidence scoring.
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            issue_number: Issue number to analyze
            
        Returns:
            IssueAnalysis object with confidence score and metadata
        """
        issue_data = self._fetch_issue_details(repo_owner, repo_name, issue_number)
        if not issue_data:
            return None
        
        if self.devin_token:
            return self._analyze_with_devin_api(issue_data, repo_owner, repo_name)
        else:
            print("Error: Devin API token is required for issue analysis.")
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
    
    
    def _analyze_with_devin_api(self, issue_data: Dict, repo_owner: str, repo_name: str) -> Optional[IssueAnalysis]:
        """Analyze issue using Devin API session."""
        if not self.devin_token:
            print("Error: Devin API token is required for session-based analysis")
            return None
        
        title = issue_data['title']
        body = issue_data.get('body', '') or ''
        labels = [label['name'] for label in issue_data.get('labels', [])]
        comments = issue_data.get('comment_details', [])
        issue_number = issue_data['number']
        
        prompt = self._create_analysis_prompt(title, body, labels, comments, repo_owner, repo_name, issue_number)
        
        session_id = self._create_devin_session(prompt)
        if not session_id:
            print("Error: Failed to create Devin session")
            return None
        
        analysis_result = self._wait_for_session_completion(session_id)
        if not analysis_result:
            print("Error: Failed to get analysis from Devin session")
            return None
        
        return self._parse_devin_analysis(analysis_result, issue_data)
    
    def _create_analysis_prompt(self, title: str, body: str, labels: List[str], 
                              comments: List[Dict], repo_owner: str, repo_name: str, 
                              issue_number: int) -> str:
        """Create a detailed prompt for Devin to analyze the GitHub issue."""
        comments_text = ""
        if comments:
            comments_text = "\n\nComments:\n" + "\n".join([
                f"- {comment.get('user', {}).get('login', 'Unknown')}: {comment.get('body', '')[:200]}..."
                for comment in comments[:5]
            ])
        
        labels_text = f"Labels: {', '.join(labels)}" if labels else "Labels: None"
        
        prompt = f"""Please analyze this GitHub issue from {repo_owner}/{repo_name} and provide a structured assessment:

Issue #{issue_number}: {title}

{labels_text}

Description:
{body[:1000]}...{comments_text}

Please provide your analysis in the following JSON format:
{{
    "category": "bug|feature|documentation|enhancement|question|maintenance|security|performance|unknown",
    "complexity": "trivial|simple|moderate|complex|very_complex",
    "confidence_score": <float between 1.0 and 10.0>,
    "estimated_effort_hours": <integer>,
    "key_factors": ["factor1", "factor2", ...],
    "blockers": ["blocker1", "blocker2", ...],
    "dependencies": ["dep1", "dep2", ...],
    "reasoning": "Detailed explanation of your analysis and confidence score"
}}

Focus on:
1. Categorizing the issue type accurately
2. Assessing complexity based on technical requirements
3. Providing a realistic confidence score for successful resolution
4. Identifying key factors that affect implementation
5. Noting any blockers or dependencies
6. Explaining your reasoning clearly

Be thorough but concise in your analysis."""
        
        return prompt
    
    def _create_devin_session(self, prompt: str) -> Optional[str]:
        """Create a new Devin session with the analysis prompt."""
        url = f"{self.devin_base_url}/v1/sessions"
        payload = {
            "prompt": prompt,
            "unlisted": True  # Keep analysis sessions private
        }
        
        try:
            response = requests.post(url, headers=self.devin_headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get('session_id')
        except requests.exceptions.RequestException as e:
            print(f"Error creating Devin session: {e}")
            return None
    
    def _wait_for_session_completion(self, session_id: str, max_wait_time: int = 300) -> Optional[Dict]:
        """Wait for Devin session to complete and return the structured analysis result."""
        url = f"{self.devin_base_url}/v1/session/{session_id}"
        start_time = time.time()
        
        print(f"Waiting for session {session_id} to complete...")
        
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
                        print("Found structured_output with analysis data!")
                        return structured_output
                    else:
                        print("No structured_output found in session response")
                        return None
                elif status_enum in ['expired']:
                    print(f"Session {session_id} ended with status: {status_enum}")
                    return None
                
                time.sleep(10)
                
            except requests.exceptions.RequestException as e:
                print(f"Error checking session status: {e}")
                return None
        
        print(f"Session {session_id} timed out after {max_wait_time} seconds")
        return None
    
    def _parse_devin_analysis(self, analysis_data: Dict, issue_data: Dict) -> Optional[IssueAnalysis]:
        """Parse Devin's structured analysis response into IssueAnalysis object."""
        try:
            if not analysis_data:
                raise ValueError("No analysis data provided")
            
            category_map = {
                'bug': IssueCategory.BUG,
                'feature': IssueCategory.FEATURE,
                'documentation': IssueCategory.DOCUMENTATION,
                'enhancement': IssueCategory.ENHANCEMENT,
                'question': IssueCategory.QUESTION,
                'maintenance': IssueCategory.MAINTENANCE,
                'security': IssueCategory.SECURITY,
                'performance': IssueCategory.PERFORMANCE,
                'unknown': IssueCategory.UNKNOWN
            }
            
            complexity_map = {
                'trivial': ComplexityLevel.TRIVIAL,
                'simple': ComplexityLevel.SIMPLE,
                'moderate': ComplexityLevel.MODERATE,
                'complex': ComplexityLevel.COMPLEX,
                'very_complex': ComplexityLevel.VERY_COMPLEX
            }
            
            category = category_map.get(analysis_data.get('category', 'unknown'), IssueCategory.UNKNOWN)
            complexity = complexity_map.get(analysis_data.get('complexity', 'moderate'), ComplexityLevel.MODERATE)
            
            return IssueAnalysis(
                issue_number=issue_data['number'],
                title=issue_data['title'],
                category=category,
                complexity=complexity,
                confidence_score=float(analysis_data.get('confidence_score', 5.0)),
                estimated_effort_hours=int(analysis_data.get('estimated_effort_hours', 8)),
                key_factors=analysis_data.get('key_factors', []),
                blockers=analysis_data.get('blockers', []),
                dependencies=analysis_data.get('dependencies', []),
                reasoning=analysis_data.get('reasoning', 'Analysis completed via Devin API')
            )
            
        except (ValueError, KeyError) as e:
            print(f"Error parsing Devin analysis: {e}")
            print(f"Raw analysis data: {str(analysis_data)[:500]}...")
            return None

    def post_analysis_comment(self, repo_owner: str, repo_name: str, issue_number: int, analysis_text: str) -> bool:
        """
        Post analysis results as a comment on the GitHub issue.
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name  
            issue_number: Issue number to comment on
            analysis_text: Formatted analysis text to post
            
        Returns:
            True if comment was posted successfully, False otherwise
        """
        if not self.github_token:
            print("Error: GitHub token is required to post comments")
            return False
            
        url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{issue_number}/comments'
        
        markdown_text = f"""## 🤖 Devin Analysis Results

{analysis_text}

---
*This analysis was generated automatically by [Devin GitHub Issues Integration](https://github.com/itstabya/devin-github-issues-integration)*"""
        
        payload = {
            'body': markdown_text
        }
        
        try:
            response = requests.post(url, headers=self.github_headers, json=payload)
            response.raise_for_status()
            print(f"✅ Successfully posted analysis comment to issue #{issue_number}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Error posting comment to GitHub: {e}")
            return False

def format_analysis(analysis: IssueAnalysis) -> str:
    """Format analysis results for display."""
    confidence_emoji = "🟢" if analysis.confidence_score >= 7 else "🟡" if analysis.confidence_score >= 5 else "🔴"
    
    output = f"""
{confidence_emoji} Issue #{analysis.issue_number}: {analysis.title}

📊 Analysis Results:
   Category: {analysis.category.value.title()}
   Complexity: {analysis.complexity.name.title()} ({analysis.complexity.value}/5)
   Confidence Score: {analysis.confidence_score}/10
   Estimated Effort: {analysis.estimated_effort_hours} hours

🔍 Key Factors:
   {chr(10).join(f'   • {factor}' for factor in analysis.key_factors) if analysis.key_factors else '   • None identified'}

⚠️  Potential Blockers:
   {chr(10).join(f'   • {blocker}' for blocker in analysis.blockers) if analysis.blockers else '   • None identified'}

🔗 Dependencies:
   {chr(10).join(f'   • {dep}' for dep in analysis.dependencies) if analysis.dependencies else '   • None identified'}

💭 Reasoning:
   {analysis.reasoning}
"""
    return output
