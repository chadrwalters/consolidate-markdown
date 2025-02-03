---
description: "Git version control standards and workflow processes"
globs:
  - ".git/**/*"
  - ".gitignore"
  - ".gitattributes"
  - "!.git/objects/**"
  - "!.git/logs/**"
version: 1.0.0
status: Active
---

# Git Workflow Rules
Version: 1.0.0
Last Updated: 2024-02-02

## Abstract/Purpose
This rule defines the version control standards, workflow processes, and best practices for Git usage. It ensures consistent, traceable, and maintainable code management across the project.

## Table of Contents
- [Mandatory Constraints](#mandatory-constraints)
- [Advisory Guidelines](#advisory-guidelines)
- [Commit Standards](#commit-standards)
- [Branch Management](#branch-management)
- [Pull Request Process](#pull-request-process)
- [Release Management](#release-management)
- [Hotfix Protocols](#hotfix-protocols)
- [Exception Clauses](#exception-clauses)
- [Examples](#examples)
- [Migration Notes](#migration-notes)

## Commit Standards
### Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Commit Types
- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Formatting
- refactor: Code restructure
- test: Testing
- chore: Maintenance

### Message Rules
- Subject line ≤ 50 characters
- Capitalize subject line
- No period in subject
- Imperative mood
- Body wrapped at 72 characters
- Explain what and why

### Content Rules
- Atomic commits
- Related changes only
- Complete functionality
- Proper testing
- Documentation updates

## Branch Management
### Main Branches
- main: Production code
- develop: Development code
- release/*: Release preparation
- hotfix/*: Emergency fixes

### Feature Branches
**Naming**: `feature/<issue-id>-<description>`
**Rules**:
- Branch from develop
- Merge to develop
- Delete after merge
- Keep up to date
- Regular commits

### Release Branches
**Naming**: `release/v<major>.<minor>.<patch>`
**Rules**:
- Branch from develop
- Merge to main and develop
- Only bug fixes
- Version bumps
- Documentation updates

### Hotfix Branches
**Naming**: `hotfix/v<major>.<minor>.<patch>-<description>`
**Rules**:
- Branch from main
- Merge to main and develop
- Critical fixes only
- Immediate deployment
- Full testing required

## Pull Request Process
### Requirements
- Complete feature/fix
- Passing tests
- Updated documentation
- Code review approval
- CI/CD success

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Documentation
- [ ] Documentation updated
- [ ] Comments added/updated
- [ ] CHANGELOG.md updated
```

### Review Checklist
- Code quality
- Test coverage
- Documentation
- Performance impact
- Security implications

## Release Management
### Versioning
**Format**: Semantic Versioning (MAJOR.MINOR.PATCH)
**Rules**:
- MAJOR: Breaking changes
- MINOR: New features
- PATCH: Bug fixes
- Pre-release: alpha/beta/rc
- Build metadata allowed

### Release Process
1. Create release branch
2. Version bump
3. Update CHANGELOG
4. Update documentation
5. Final testing
6. Merge to main
7. Tag release
8. Deploy to production
9. Merge back to develop
10. Clean up branches

## Hotfix Protocols
### Criteria
- Production blocking issue
- Security vulnerability
- Data integrity risk
- Critical functionality
- Customer impact

### Process
1. Create hotfix branch
2. Implement fix
3. Emergency testing
4. Expedited review
5. Deploy to production

### Documentation
- Incident report
- Fix documentation
- Update CHANGELOG
- Customer communication
- Post-mortem analysis

## Mandatory Constraints
### MUST
- Use commit message template
- Follow branch naming conventions
- Create PR for all changes
- Get code review approval
- Update documentation
- Write clear commit messages
- Keep atomic commits
- Sign commits (GPG)
- Protect main branches
- Follow versioning rules
- Test before merge
- Update CHANGELOG
- Clean up branches

### MUST NOT
- Commit directly to main
- Skip code review
- Leave stale branches
- Mix unrelated changes
- Force push to shared branches
- Commit secrets
- Skip CI/CD
- Bypass security checks
- Leave PR template empty
- Merge failing tests
- Skip documentation
- Break version format

## Advisory Guidelines
### SHOULD
- Write descriptive messages
- Keep branches updated
- Review regularly
- Clean history
- Tag releases
- Monitor size
- Optimize performance
- Document changes
- Test thoroughly
- Follow patterns

### RECOMMENDED
- Regular cleanup
- Branch pruning
- Security scanning
- Access control
- Size management
- Performance monitoring
- History maintenance
- Documentation review
- Process automation
- Team training

## Exception Clauses
Workflow exceptions allowed when:
- Emergency hotfix needed
- Critical security issue
- System outage
- Data loss risk
- Customer blocking issue

## Examples
### Good Commit Message
```
feat(auth): Add OAuth2 authentication support

Implement OAuth2 authentication flow using Google provider.
This allows users to sign in with their Google accounts.

- Add OAuth2 client configuration
- Implement callback handler
- Add user profile mapping
- Update documentation

Closes #123
```

### Bad Commit Message
```
fixed stuff

updated some code and fixed the login bug
also added some new features and changed some configs
```

## Migration Notes
- Update commit templates
- Standardize branch naming
- Implement PR templates
- Configure branch protection
- Train team members

## Dependencies
- @rule(02-base.md:format_requirements)

## Changelog
### 1.0.0 (2024-02-02)
- Initial version
- Defined workflow standards
- Added branch management
- Set PR process
