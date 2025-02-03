---
description: "Pre-commit hook standards and validation requirements"
globs:
  - ".pre-commit-config.yaml"
  - ".git/hooks/pre-commit"
  - "!.git/hooks/pre-commit.sample"
version: 1.0.0
status: Active
---

# Pre-commit Handling Rules
Version: 1.0.0
Last Updated: 2024-02-02

## Abstract/Purpose
This rule defines the pre-commit check standards, validation processes, and automation requirements. It ensures consistent code quality and prevents problematic commits from entering the repository. This rule works in conjunction with the commit standards defined in `30-git-workflow.md` to ensure complete commit quality.

## Table of Contents
- [Mandatory Constraints](#mandatory-constraints)
- [Advisory Guidelines](#advisory-guidelines)
- [Check Sequence](#check-sequence)
- [Validation Rules](#validation-rules)
- [Error Handling](#error-handling)
- [Automation](#automation)
- [Exception Clauses](#exception-clauses)
- [Examples](#examples)
- [Migration Notes](#migration-notes)

## Check Sequence
### Initial Check
1. Run pre-commit run --all-files
2. Record any modifications made
3. Note failing checks

### Verification Process
1. If modifications made, rerun all checks
2. Continue until clean pass achieved
3. Maximum 3 iterations to prevent loops

### Additional Checks
- Run git status to check state
- Verify all files are staged
- Check for untracked files

### Completion Criteria
- All pre-commit hooks pass
- No unstaged changes
- Clean working directory
- Clear branch status

## Validation Rules
### Code Formatting
- Black formatting passes
- isort import sorting passes
- No trailing whitespace
- Proper line endings

### Code Linting
- Ruff linting passes
- MyPy type checking passes
- No large files added

### Git Checks
- No merge conflicts
- Clean branch status
- No untracked files in tracked directories

### Rule Validation
- Rule structure validation
- Frontmatter verification
- Cross-reference checking
- Glob pattern validation
- Constraint consistency

### Conflict Detection
- Rule overlap analysis
- Constraint conflict checks
- Pattern conflict detection
- Dependency validation
- Version compatibility

### Summary Generation
- Quick reference creation
- Constraint summaries
- Pattern documentation
- Dependency graphs
- Change tracking

## Error Handling
### Retry Policy
- Maximum 3 retry attempts
- Clear error messaging
- Specific fix suggestions

### Failure Actions
- Report all failing checks
- Suggest manual intervention steps
- Preserve original changes

## Automation
### Rule Validation Hooks
```yaml
# Rule validation hooks
- repo: local
  hooks:
    - id: rule-validation
      name: Validate Rules
      entry: python -m src.validation.rules
      language: python
      files: ^\.cursor/rules/.*\.md$

    - id: rule-conflict-check
      name: Check Rule Conflicts
      entry: python -m src.validation.conflicts
      language: python
      files: ^\.cursor/rules/.*\.md$

    - id: rule-summary
      name: Generate Rule Summaries
      entry: python -m src.validation.summary
      language: python
      files: ^\.cursor/rules/.*\.md$
```

### Prohibited Actions
- No automatic commits
- No force pushing
- No branch switching
- No stash operations
- No interactive commands

### Required Approvals
- User confirmation for fixes
- Manual review of changes
- Explicit push approval

## Mandatory Constraints
### MUST
- Run all pre-commit checks
- Follow retry policy
- Report all failures
- Preserve changes
- Get user approval
- Check formatting
- Verify linting
- Run type checks
- Check git state
- Follow sequence
- Handle errors
- Document failures

### MUST NOT
- Skip checks
- Auto-commit changes
- Force push
- Switch branches
- Use stash
- Run interactively
- Exceed retries
- Hide errors
- Bypass validation
- Mix check types
- Auto-fix without approval
- Leave checks incomplete

## Advisory Guidelines
### SHOULD
- Review changes
- Monitor performance
- Update hooks
- Document fixes
- Track patterns
- Optimize checks
- Report metrics
- Clean workspace
- Follow standards
- Keep logs

### RECOMMENDED
- Regular updates
- Hook maintenance
- Performance tuning
- Error analysis
- Pattern detection
- Process review
- Tool updates
- Config validation
- State monitoring
- Log rotation

## Exception Clauses
Pre-commit exceptions allowed when:
- Emergency fixes needed
- Tool failures occur
- Performance issues
- Integration conflicts
- System limitations

## Examples
### Good Pre-commit Setup
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.12

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.11
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

### Bad Pre-commit Setup
```yaml
# Missing essential checks
repos:
  - repo: local
    hooks:
      - id: custom-script
        entry: ./scripts/check.sh  # Unreliable local script
        language: system
```

## Migration Notes
- Install pre-commit
- Configure hooks
- Update settings
- Test workflow
- Train team

## Dependencies
- @rule(02-base.md:format_requirements)
- @rule(30-git-workflow.md:commit_standards)

## Changelog
### 1.0.0 (2024-02-02)
- Initial version
- Defined check standards
- Set validation rules
- Added automation requirements
