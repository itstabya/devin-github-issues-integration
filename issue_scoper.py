#!/usr/bin/env python3
"""
GitHub Issue Scoping Module
Analyzes GitHub issues and provides confidence scores for resolution using Devin API.
"""

import re
import json
import requests
import time
import os
from typing import Dict, List, Optional, Tuple
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
        self.devin_base_url = 'https://api.devin.ai/v1'
    
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
            print("Warning: No Devin API token provided. Falling back to keyword analysis.")
            return self._perform_analysis(issue_data)
    
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
    
    def _perform_analysis(self, issue_data: Dict) -> IssueAnalysis:
        """Perform comprehensive analysis of the issue."""
        title = issue_data['title']
        body = issue_data.get('body', '') or ''
        labels = [label['name'] for label in issue_data.get('labels', [])]
        comments = issue_data.get('comment_details', [])
        
        full_text = f"{title}\n{body}"
        for comment in comments[:5]:  # Analyze first 5 comments
            full_text += f"\n{comment.get('body', '')}"
        
        category = self._categorize_issue(title, body, labels)
        
        complexity = self._assess_complexity(title, body, labels, comments)
        
        confidence_score = self._calculate_confidence_score(
            title, body, labels, comments, category, complexity
        )
        
        effort_hours = self._estimate_effort(complexity, category, len(comments))
        
        key_factors = self._identify_key_factors(title, body, labels)
        
        blockers = self._identify_blockers(body, comments)
        dependencies = self._identify_dependencies(body, comments)
        
        reasoning = self._generate_reasoning(
            category, complexity, confidence_score, key_factors, blockers
        )
        
        return IssueAnalysis(
            issue_number=issue_data['number'],
            title=title,
            category=category,
            complexity=complexity,
            confidence_score=confidence_score,
            estimated_effort_hours=effort_hours,
            key_factors=key_factors,
            blockers=blockers,
            dependencies=dependencies,
            reasoning=reasoning
        )
    
    def _categorize_issue(self, title: str, body: str, labels: List[str]) -> IssueCategory:
        """Categorize the issue based on title, body, and labels."""
        text = f"{title} {body}".lower()
        
        label_categories = {
            'bug': IssueCategory.BUG,
            'feature': IssueCategory.FEATURE,
            'enhancement': IssueCategory.ENHANCEMENT,
            'documentation': IssueCategory.DOCUMENTATION,
            'question': IssueCategory.QUESTION,
            'security': IssueCategory.SECURITY,
            'performance': IssueCategory.PERFORMANCE,
        }
        
        for label in labels:
            label_lower = label.lower()
            for keyword, category in label_categories.items():
                if keyword in label_lower:
                    return category
        
        if any(word in text for word in ['bug', 'error', 'crash', 'broken', 'fail', 'issue']):
            return IssueCategory.BUG
        elif any(word in text for word in ['feature', 'add', 'implement', 'new']):
            return IssueCategory.FEATURE
        elif any(word in text for word in ['improve', 'enhance', 'better', 'optimize']):
            return IssueCategory.ENHANCEMENT
        elif any(word in text for word in ['document', 'readme', 'docs', 'guide']):
            return IssueCategory.DOCUMENTATION
        elif any(word in text for word in ['question', 'how', 'why', 'what', '?']):
            return IssueCategory.QUESTION
        elif any(word in text for word in ['security', 'vulnerability', 'exploit']):
            return IssueCategory.SECURITY
        elif any(word in text for word in ['performance', 'slow', 'speed', 'optimize']):
            return IssueCategory.PERFORMANCE
        
        return IssueCategory.UNKNOWN
    
    def _assess_complexity(self, title: str, body: str, labels: List[str], comments: List[Dict]) -> ComplexityLevel:
        """Assess the complexity level of the issue."""
        complexity_score = 0
        
        if len(body) > 1000:
            complexity_score += 1
        if len(comments) > 10:
            complexity_score += 1
        
        text = f"{title} {body}".lower()
        complex_keywords = [
            'architecture', 'refactor', 'breaking change', 'api change',
            'database', 'migration', 'performance', 'security',
            'integration', 'compatibility', 'cross-platform'
        ]
        
        for keyword in complex_keywords:
            if keyword in text:
                complexity_score += 1
        
        complex_labels = ['breaking-change', 'architecture', 'refactor', 'major']
        for label in labels:
            if any(complex_label in label.lower() for complex_label in complex_labels):
                complexity_score += 2
        
        if complexity_score <= 1:
            return ComplexityLevel.TRIVIAL
        elif complexity_score <= 2:
            return ComplexityLevel.SIMPLE
        elif complexity_score <= 4:
            return ComplexityLevel.MODERATE
        elif complexity_score <= 6:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.VERY_COMPLEX
    
    def _calculate_confidence_score(self, title: str, body: str, labels: List[str], 
                                  comments: List[Dict], category: IssueCategory, 
                                  complexity: ComplexityLevel) -> float:
        """Calculate confidence score (1-10) for successful resolution."""
        base_score = 7.0  # Start with moderate confidence
        
        category_adjustments = {
            IssueCategory.BUG: 0.5,  # Bugs are often well-defined
            IssueCategory.DOCUMENTATION: 1.0,  # Documentation is usually straightforward
            IssueCategory.FEATURE: -0.5,  # Features can be complex
            IssueCategory.ENHANCEMENT: -0.3,
            IssueCategory.QUESTION: 1.5,  # Questions are easy to answer
            IssueCategory.SECURITY: -1.0,  # Security issues are complex
            IssueCategory.UNKNOWN: -1.5,  # Unknown category is risky
        }
        
        base_score += category_adjustments.get(category, 0)
        
        complexity_adjustments = {
            ComplexityLevel.TRIVIAL: 2.0,
            ComplexityLevel.SIMPLE: 1.0,
            ComplexityLevel.MODERATE: 0,
            ComplexityLevel.COMPLEX: -1.5,
            ComplexityLevel.VERY_COMPLEX: -3.0,
        }
        
        base_score += complexity_adjustments.get(complexity, 0)
        
        if len(body) > 200:  # Well-described issues
            base_score += 0.5
        if len(body) < 50:  # Poorly described issues
            base_score -= 1.0
        
        if len(comments) > 5:  # Active discussion might indicate complexity
            base_score -= 0.3
        
        if 'steps to reproduce' in body.lower() or 'reproduce' in body.lower():
            base_score += 0.8
        
        if any(keyword in body.lower() for keyword in ['error', 'exception', 'stack trace']):
            base_score += 0.5
        
        return max(1.0, min(10.0, round(base_score, 1)))
    
    def _estimate_effort(self, complexity: ComplexityLevel, category: IssueCategory, comment_count: int) -> int:
        """Estimate effort in hours."""
        base_hours = {
            ComplexityLevel.TRIVIAL: 1,
            ComplexityLevel.SIMPLE: 3,
            ComplexityLevel.MODERATE: 8,
            ComplexityLevel.COMPLEX: 20,
            ComplexityLevel.VERY_COMPLEX: 40,
        }
        
        hours = base_hours.get(complexity, 8)
        
        if category == IssueCategory.DOCUMENTATION:
            hours = max(1, hours // 2)
        elif category == IssueCategory.SECURITY:
            hours = int(hours * 1.5)
        elif category == IssueCategory.FEATURE:
            hours = int(hours * 1.2)
        
        if comment_count > 10:
            hours = int(hours * 1.3)
        
        return hours
    
    def _identify_key_factors(self, title: str, body: str, labels: List[str]) -> List[str]:
        """Identify key factors that affect the issue."""
        factors = []
        text = f"{title} {body}".lower()
        
        if any(word in text for word in ['api', 'breaking', 'compatibility']):
            factors.append("API/Compatibility concerns")
        if any(word in text for word in ['performance', 'slow', 'memory']):
            factors.append("Performance implications")
        if any(word in text for word in ['security', 'vulnerability']):
            factors.append("Security considerations")
        if any(word in text for word in ['test', 'testing', 'coverage']):
            factors.append("Testing requirements")
        
        if 'breaking' in text:
            factors.append("Breaking change")
        if any(label.lower() in ['good first issue', 'help wanted'] for label in labels):
            factors.append("Community-friendly")
        
        return factors
    
    def _identify_blockers(self, body: str, comments: List[Dict]) -> List[str]:
        """Identify potential blockers."""
        blockers = []
        text = f"{body} {' '.join(comment.get('body', '') for comment in comments[:3])}".lower()
        
        if 'blocked' in text or 'blocker' in text:
            blockers.append("Explicitly marked as blocked")
        if 'depends on' in text or 'dependency' in text:
            blockers.append("Has dependencies")
        if 'breaking change' in text:
            blockers.append("Breaking change requires careful planning")
        if 'need more info' in text or 'more information' in text:
            blockers.append("Insufficient information")
        
        return blockers
    
    def _identify_dependencies(self, body: str, comments: List[Dict]) -> List[str]:
        """Identify dependencies mentioned in the issue."""
        dependencies = []
        text = f"{body} {' '.join(comment.get('body', '') for comment in comments[:3])}"
        
        issue_refs = re.findall(r'#(\d+)', text)
        if issue_refs:
            dependencies.extend([f"Issue #{ref}" for ref in issue_refs[:3]])
        
        if 'depends on' in text.lower():
            dependencies.append("Has explicit dependencies")
        
        return dependencies
    
    def _generate_reasoning(self, category: IssueCategory, complexity: ComplexityLevel, 
                          confidence_score: float, key_factors: List[str], 
                          blockers: List[str]) -> str:
        """Generate human-readable reasoning for the analysis."""
        reasoning_parts = []
        
        reasoning_parts.append(f"Categorized as {category.value} with {complexity.name.lower()} complexity.")
        
        if confidence_score >= 8:
            reasoning_parts.append("High confidence due to clear description and straightforward resolution path.")
        elif confidence_score >= 6:
            reasoning_parts.append("Moderate confidence with some uncertainty factors.")
        else:
            reasoning_parts.append("Lower confidence due to complexity or unclear requirements.")
        
        if key_factors:
            reasoning_parts.append(f"Key considerations: {', '.join(key_factors)}.")
        
        if blockers:
            reasoning_parts.append(f"Potential blockers: {', '.join(blockers)}.")
        
        return " ".join(reasoning_parts)
    
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
            return self._perform_analysis(issue_data)  # Fallback to keyword analysis
        
        analysis_result = self._wait_for_session_completion(session_id)
        if not analysis_result:
            print("Error: Failed to get analysis from Devin session")
            return self._perform_analysis(issue_data)  # Fallback to keyword analysis
        
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
        url = f"{self.devin_base_url}/sessions"
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
    
    def _wait_for_session_completion(self, session_id: str, max_wait_time: int = 300) -> Optional[str]:
        """Wait for Devin session to complete and return the analysis result."""
        url = f"{self.devin_base_url}/session/{session_id}"
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = requests.get(url, headers=self.devin_headers)
                response.raise_for_status()
                session_data = response.json()
                
                latest_status = session_data.get('latest_status_contents', {})
                agent_status = latest_status.get('agent_status', '')
                
                if agent_status == 'finished':
                    latest_message = session_data.get('latest_message_contents', {})
                    if latest_message.get('type') == 'devin_message':
                        content = latest_message.get('message', '')
                        if '{' in content and '}' in content:  # Look for JSON response
                            return content
                    return None
                elif latest_status.get('enum') in ['expired']:
                    print(f"Session {session_id} ended with status: {latest_status.get('enum')}")
                    return None
                
                time.sleep(10)
                
            except requests.exceptions.RequestException as e:
                print(f"Error checking session status: {e}")
                return None
        
        print(f"Session {session_id} timed out after {max_wait_time} seconds")
        return None
    
    def _parse_devin_analysis(self, analysis_text: str, issue_data: Dict) -> Optional[IssueAnalysis]:
        """Parse Devin's analysis response into IssueAnalysis object."""
        try:
            start_idx = analysis_text.find('{')
            end_idx = analysis_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in analysis response")
            
            json_str = analysis_text[start_idx:end_idx]
            analysis_data = json.loads(json_str)
            
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
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Error parsing Devin analysis: {e}")
            print(f"Raw analysis text: {analysis_text[:500]}...")
            return self._perform_analysis(issue_data)

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
