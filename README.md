# Kitty Skills

A collection of AI agent skills and coding rules for Claude and Cursor.

## Structure

```
kitty-skills/
├── claude-skills/          # Claude Code skills (40 skills)
│   ├── algorithmic-art/        # p5.js generative art
│   ├── artifacts-builder/      # Multi-component HTML artifacts (React + Tailwind + shadcn/ui)
│   ├── brand-guidelines/       # Anthropic brand colors & typography
│   ├── browser/                # Chrome DevTools Protocol automation
│   ├── clawhub/                # Search and install public agent skills
│   ├── codeagent/              # Multi-backend AI code tasks (Codex/Claude/Gemini)
│   ├── confluence-release-checklist-updater/ # Update release checklist pages in Confluence
│   ├── contract-interaction-finder/  # Multi-chain contract interaction search
│   ├── cron/                   # Scheduled reminders and recurring tasks
│   ├── debugging/              # Systematic debugging methodology
│   ├── github/                 # GitHub operations via gh CLI
│   ├── github-kb/              # GitHub repository investigation
│   ├── hotfix-branch-impact/   # Branch/commit impact and QA coverage analysis
│   ├── memory/                 # Two-layer memory system with grep recall
│   ├── memory-manager/         # Local memory compression, snapshot, semantic search
│   ├── nanobot-evolution/      # Self-improvement, indexing, local LLM maintenance
│   ├── notebooklm/             # Google NotebookLM integration
│   ├── omo/                    # Multi-agent orchestration
│   ├── onekey-knowledge-builder/   # OneKey: knowledge & UI mapping
│   ├── onekey-qa-director/     # OneKey: QA director & coordinator
│   ├── onekey-qa-manager/      # OneKey: failure analysis & diagnosis
│   ├── onekey-recorder/        # OneKey: flow exploration & recording
│   ├── onekey-reporter/        # OneKey: cross-feature reporting
│   ├── onekey-runner/          # OneKey: test execution
│   ├── onekey-test-designer/   # OneKey: BDD test case design
│   ├── planning-with-files/    # Manus-style file-based planning
│   ├── qa-add-case/            # Add new QA test cases and Jira Test issues
│   ├── qa-test-planner/        # Test plans & bug reports
│   ├── qa-update-case/         # Update existing QA test cases and Jira tables
│   ├── remotion/               # Remotion video programming
│   ├── self-improving-agent-cn/ # 中文自我改进与长期记忆沉淀
│   ├── skill-creator/          # Skill authoring guide
│   ├── skill-install/          # Install skills from GitHub
│   ├── slack-pr-qa-regression/ # Generate Slack QA regression items from PRs
│   ├── summarize/              # Summarize URLs, transcripts, and local files
│   ├── template/               # Skill template
│   ├── test-cases/             # PRD → test case generation
│   ├── theme-factory/          # 10 pre-set themes toolkit
│   ├── tmux/                   # Control tmux sessions and scrape output
│   └── weather/                # Weather and forecast lookup
├── cursor-rules/           # Cursor workspace rules (.mdc)
│   ├── debugging-methodology.mdc   # 5-phase bug fix workflow
│   └── feature-development.mdc     # Feature development workflow
└── user-rules/             # Global user rules
    └── global-clean-code.md        # Clean code standards for all projects
```

## Installation

### Claude Skills

Copy skills into your Claude skills directory:

```bash
cp -R claude-skills/* ~/.claude/skills/
```

### Cursor Rules

Copy rules into your Cursor rules directory:

```bash
cp cursor-rules/* ~/.cursor/rules/
```

### User Rules

The `user-rules/` directory contains global rules that apply across all projects. Configure them in your AI editor's user-level settings.

## Skill Categories

| Category | Skills | Description |
|---|---|---|
| **Creative** | algorithmic-art, artifacts-builder, theme-factory, remotion | Art, UI artifacts, theming, video |
| **Development** | browser, codeagent, omo, planning-with-files, tmux, github | Automation, multi-agent, planning, terminal and GitHub operations |
| **Blockchain** | contract-interaction-finder, hotfix-branch-impact | Multi-chain interaction analysis, release/hotfix impact analysis |
| **QA & Testing** | qa-test-planner, test-cases, qa-add-case, qa-update-case, slack-pr-qa-regression, confluence-release-checklist-updater | Test plans, case maintenance, PR regression items, release checklist workflows |
| **Memory & Evolution** | memory, memory-manager, nanobot-evolution, self-improving-agent-cn | Memory recall, compression management, self-improvement, long-term learning |
| **OneKey Suite** | onekey-qa-director, onekey-test-designer, onekey-qa-manager, onekey-runner, onekey-recorder, onekey-reporter, onekey-knowledge-builder | Full QA automation pipeline |
| **Utilities** | debugging, github-kb, notebooklm, brand-guidelines, skill-creator, skill-install, template, summarize, weather, cron, clawhub | Research, debugging, skill management, summaries, scheduling, weather, skill discovery |

## License

Personal use.
