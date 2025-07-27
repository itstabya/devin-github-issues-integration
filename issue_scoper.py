#!/usr/bin/env python3
"""
GitHub Issue Scoping Module
Analyzes GitHub issues and provides confidence scores for resolution.
"""

import re
import json
import requests
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
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Issues-Scoper'
        }
        if self.github_token:
            self.headers['Authorization'] = f'token {self.github_token}'
    
    def analyze_issue(self, repo_owner: str, repo_name: str, issue_number: int) -> Optional[IssueAnalysis]:
        """
        Analyze a single GitHub issue and return confidence scoring.
        
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
        
        return self._perform_analysis(issue_data)
    
    def _fetch_issue_details(self, repo_owner: str, repo_name: str, issue_number: int) -> Optional[Dict]:
        """Fetch detailed issue information from GitHub API."""
        url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{issue_number}'
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            issue = response.json()
            
            comments_url = issue['comments_url']
            comments_response = requests.get(comments_url, headers=self.headers)
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
