# Kitty Skills

A collection of AI agent skills and coding rules for Claude and Cursor.

## Structure

```
kitty-skills/
├── claude-skills/          # Claude Code skills (25 skills)
│   ├── algorithmic-art/        # p5.js generative art
│   ├── artifacts-builder/      # Multi-component HTML artifacts (React + Tailwind + shadcn/ui)
│   ├── brand-guidelines/       # Anthropic brand colors & typography
│   ├── browser/                # Chrome DevTools Protocol automation
│   ├── codeagent/              # Multi-backend AI code tasks (Codex/Claude/Gemini)
│   ├── contract-interaction-finder/  # Multi-chain contract interaction search
│   ├── debugging/              # Systematic debugging methodology
│   ├── github-kb/              # GitHub repository investigation
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
│   ├── qa-test-planner/        # QA test plans & bug reports
│   ├── remotion/               # Remotion video programming
│   ├── skill-creator/          # Skill authoring guide
│   ├── skill-install/          # Install skills from GitHub
│   ├── template/               # Skill template
│   ├── test-cases/             # PRD → test case generation
│   └── theme-factory/          # 10 pre-set themes toolkit
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
| **Development** | browser, codeagent, omo, planning-with-files | Automation, multi-agent, planning |
| **Blockchain** | contract-interaction-finder | Multi-chain contract interaction analysis |
| **QA & Testing** | qa-test-planner, test-cases | Test plans, case generation |
| **OneKey Suite** | onekey-qa-director, onekey-test-designer, onekey-qa-manager, onekey-runner, onekey-recorder, onekey-reporter, onekey-knowledge-builder | Full QA automation pipeline |
| **Utilities** | debugging, github-kb, notebooklm, brand-guidelines, skill-creator, skill-install, template | Research, debugging, skill management |

## License

Personal use.
