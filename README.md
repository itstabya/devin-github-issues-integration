# GitHub Issues Integration

A comprehensive automation system that integrates Devin with GitHub Issues to streamline issue management and resolution.

## 🎯 Project Goals

This project aims to build a complete GitHub Issues automation system with three main components:

1. **Issue Discovery** (✅ Complete) - CLI tool to list and filter GitHub issues
2. **Issue Scoping** (🚧 Planned) - Trigger Devin sessions to analyze issues and assign confidence scores
3. **Issue Resolution** (🚧 Planned) - Trigger Devin sessions to execute action plans and complete tickets

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

3. (Optional) Set up GitHub token for higher API rate limits:
```bash
cp .env.example .env
# Edit .env and add your GitHub personal access token
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

## 🔧 GitHub Token Setup

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

## 📋 CLI Tool Features

The GitHub Issues CLI tool (`github_issues_cli.py`) provides:

- **Repository Support**: Works with any public GitHub repository
- **Flexible Filtering**: Filter by state (open/closed/all), labels, assignees
- **Rate Limit Handling**: Optional GitHub token support for higher limits
- **Rich Output**: Formatted display with emojis, metadata, and color coding
- **Error Handling**: Graceful handling of API errors and invalid inputs

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

### Phase 2: Issue Scoping 🚧
**Goal**: Automatically analyze GitHub issues and provide confidence scores for resolution

**Planned Features**:
- Devin session integration for issue analysis
- AI-powered issue complexity assessment
- Confidence scoring system (1-10 scale)
- Issue categorization (bug, feature, documentation, etc.)
- Estimated effort calculation
- Dependencies and blocker detection

**Technical Approach**:
- Integration with Devin API/SDK
- Natural language processing for issue content analysis
- Machine learning models for complexity prediction
- Database for storing analysis results and confidence scores

### Phase 3: Issue Resolution 🚧
**Goal**: Automatically execute action plans to resolve GitHub issues

**Planned Features**:
- Automated Devin session triggering for issue resolution
- Action plan generation and execution
- Progress tracking and status updates
- Pull request creation and management
- Testing and validation automation
- Success/failure reporting

**Technical Approach**:
- Workflow orchestration system
- Integration with CI/CD pipelines
- Automated testing frameworks
- Code review automation
- Rollback mechanisms for failed attempts

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
