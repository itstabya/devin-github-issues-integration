# GitHub Issues Integration

A comprehensive automation system that integrates Devin with GitHub Issues to streamline issue management and resolution.

## 🎯 Project Goals

This project aims to build a complete GitHub Issues automation system with three main components:

1. **Issue Discovery** (✅ Complete) - CLI tool to list and filter GitHub issues
2. **Issue Scoping** (✅ Complete) - Trigger Devin sessions to analyze issues and assign confidence scores
3. **Issue Resolution** (✅ Complete) - Trigger Devin sessions to execute action plans and complete tickets

## 🚀 Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/itstabya/devin-github-issues-integration.git
cd devin-github-issues-integration
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up tokens:
```bash
cp .env.example .env
# Edit .env and add your tokens:
# - GitHub personal access token for higher API rate limits
# - Devin API token for AI-powered issue analysis
```

### Usage

#### Basic Usage
```bash
# List open issues from a repository
python github_issues_cli.py microsoft/vscode

# List issues with custom limit
python github_issues_cli.py microsoft/vscode --limit=10
```

#### Advanced Filtering
```bash
# Filter by issue state
python github_issues_cli.py microsoft/vscode --state=closed --limit=5
python github_issues_cli.py microsoft/vscode --state=all --limit=20

# Filter by labels
python github_issues_cli.py microsoft/vscode --labels=bug
python github_issues_cli.py microsoft/vscode --labels=bug,enhancement

# Filter by assignee
python github_issues_cli.py microsoft/vscode --assignee=username

# Combine filters
python github_issues_cli.py microsoft/vscode --state=open --labels=bug --limit=5
```

#### Authentication
```bash
# Use token from environment variable
export GITHUB_TOKEN=your_token_here
python github_issues_cli.py microsoft/vscode

# Or pass token directly
python github_issues_cli.py microsoft/vscode --token=your_token_here
```

## 🔧 Token Setup

### GitHub Token Setup
To avoid API rate limits, set up a GitHub personal access token:

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select scopes: `public_repo` (for public repositories) or `repo` (for private repositories)
4. Copy the generated token
5. Set it as an environment variable:
   ```bash
   export GITHUB_TOKEN=your_token_here
   ```
   Or add it to your `.env` file:
   ```
   GITHUB_TOKEN=your_token_here
   ```

### Devin API Token Setup
For AI-powered issue analysis, set up a Devin API token:

1. Go to [Devin Settings](https://app.devin.ai/settings) → API section
2. Generate a new API token
3. Copy the generated token
4. Set it as an environment variable:
   ```bash
   export DEVIN_API_TOKEN=your_devin_token_here
   ```
   Or add it to your `.env` file:
   ```
   DEVIN_API_TOKEN=your_devin_token_here
   ```

**Note**: A Devin API token is required for issue scoping. The automation relies exclusively on the Devin API for analysis.

## 📋 CLI Tool Features

### GitHub Issues CLI (`github_issues_cli.py`)
- **Repository Support**: Works with any public GitHub repository
- **Flexible Filtering**: Filter by state (open/closed/all), labels, assignees
- **Rate Limit Handling**: Optional GitHub token support for higher limits
- **Rich Output**: Formatted display with emojis, metadata, and color coding
- **Error Handling**: Graceful handling of API errors and invalid inputs

### Issue Scoping CLI (`scope_issue_cli.py`)
- **AI-Powered Analysis**: Uses Devin API sessions for intelligent issue analysis
- **Confidence Scoring**: Provides 1-10 confidence scores for issue resolution
- **Issue Categorization**: Automatically categorizes issues (bug, feature, etc.)
- **Complexity Assessment**: Evaluates technical complexity (trivial to very complex)
- **Effort Estimation**: Estimates development time in hours
- **Dependency Detection**: Identifies blockers and dependencies
- **Automatic Comment Posting**: Posts analysis results directly to GitHub issues as comments
- **Duplicate Analysis Detection**: Checks for existing analysis and skips re-analysis
- **JSON Output**: Supports structured JSON output for automation

#### Usage Examples:
```bash
# Basic issue analysis (requires DEVIN_API_TOKEN environment variable)
python scope_issue_cli.py microsoft/vscode 12345

# With GitHub token for higher API limits and comment posting
python scope_issue_cli.py microsoft/vscode 12345 --token=github_token

# JSON output for automation
python scope_issue_cli.py microsoft/vscode 12345 --json
```

### Issue Resolution CLI (`resolve_issue_cli.py`)
- **Automatic Analysis Fetching**: Retrieves existing Devin analysis from GitHub issue comments
- **User Prompting**: Prompts users when no analysis exists with options to scope first or continue
- **AI-Powered Resolution**: Uses Devin API sessions to execute action plans and resolve issues
- **PR Creation**: Automatically creates pull requests with implemented solutions
- **Progress Tracking**: Monitors resolution progress and reports results
- **Fallback Support**: Can proceed without prior analysis when needed

#### Usage Examples:
```bash
# Basic issue resolution (automatically fetches existing analysis)
python resolve_issue_cli.py microsoft/vscode 12345

# JSON output for automation
python resolve_issue_cli.py microsoft/vscode 12345 --json
```

### Output Format

Each issue is displayed with:
- 🟢 Status indicator (🟢 for open, 🔴 for closed)
- Issue number and title
- Labels (if any)
- Assignees (if any)
- Author and creation date

Example output:
```
🟢 #258031: Cannot read properties of undefined (reading 'column'): TypeError [triage-needed] (assigned to: justschen)
   Author: RedCMD | Created: 2025-07-27
```

## 🗺️ Roadmap

### Phase 1: Issue Discovery ✅
- [x] GitHub API integration
- [x] CLI tool for listing issues
- [x] Filtering and search capabilities
- [x] Authentication support

### Phase 2: Issue Scoping ✅
**Goal**: Automatically analyze GitHub issues and provide confidence scores for resolution

**Features**:
- ✅ Devin API session integration for issue analysis
- ✅ AI-powered issue complexity assessment via Devin sessions
- ✅ Confidence scoring system (1-10 scale)
- ✅ Issue categorization (bug, feature, documentation, etc.)
- ✅ Estimated effort calculation
- ✅ Dependencies and blocker detection
- ✅ Lightweight automation relying exclusively on Devin API

**Technical Implementation**:
- Integration with Devin API for session-based analysis
- Structured prompts for consistent issue evaluation
- Session polling and result parsing
- Streamlined codebase with single analysis pathway

### Phase 3: Issue Resolution ✅
**Goal**: Automatically execute action plans to resolve GitHub issues

**Implemented Features**:
- ✅ Automated Devin session triggering for issue resolution
- ✅ Automatic analysis fetching from GitHub issue comments
- ✅ User prompting when no prior analysis exists
- ✅ Action plan generation and execution via Devin API
- ✅ Progress tracking and status updates
- ✅ Pull request creation and management
- ✅ Success/failure reporting with detailed results
- ✅ Fallback support for resolution without prior analysis

**Technical Implementation**:
- GitHub API integration for comment parsing and analysis retrieval
- Structured prompts for consistent issue resolution
- Session polling and result parsing with comprehensive error handling
- Automatic PR creation with detailed resolution summaries
- User-friendly CLI with interactive prompting for missing analysis

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Phase 1       │    │   Phase 2       │    │   Phase 3       │
│ Issue Discovery │───▶│ Issue Scoping   │───▶│ Issue Resolution│
│                 │    │                 │    │                 │
│ • CLI Tool      │    │ • Devin Sessions│    │ • Auto Execution│
│ • GitHub API    │    │ • AI Analysis   │    │ • PR Creation   │
│ • Filtering     │    │ • Confidence    │    │ • Testing       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🤝 Contributing

This project is part of a larger automation initiative. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
