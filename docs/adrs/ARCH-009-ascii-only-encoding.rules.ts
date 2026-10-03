/// <reference path="rules.d.ts" />

export default {
  rules: {
    'no-non-ascii-identifiers': {
      description: 'Forbid non-ASCII characters in variable/function/class names',
      severity: 'error',
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          // Skip ADR markdown files
          if (file.includes('docs/adrs/')) continue

          // Skip .claude/ (rulesync artifacts — the .rulesync/ sources are checked instead)
          if (file.startsWith('.claude/')) continue

          const content = await ctx.readFile(file)
          const lines = content.split('\n')

          for (let i = 0; i < lines.length; i++) {
            const line = lines[i]

            // Skip comments and string literals (rough heuristic)
            if (line.trim().startsWith('#')) continue
            const withoutStrings = line.replace(/["']{3}[\s\S]*?["']{3}|["'].*?["']/g, '""')

            // Match identifiers with non-ASCII characters
            // Look for patterns like: variable_name = ... or def function_name or class ClassName
            const identifierPatterns = [
              /\b([a-zA-Z_][a-zA-Z0-9_]*[^\x00-\x7F]+[a-zA-Z0-9_]*)\s*=/,  // variable assignment
              /def\s+([a-zA-Z_][a-zA-Z0-9_]*[^\x00-\x7F]+[a-zA-Z0-9_]*)\s*\(/,  // function def
              /class\s+([a-zA-Z_][a-zA-Z0-9_]*[^\x00-\x7F]+[a-zA-Z0-9_]*)\s*[\(:]/, // class def
              /([^\x00-\x7F]+[a-zA-Z0-9_]*)\s*[:=]/,  // identifier starting with non-ASCII
            ]

            for (const pattern of identifierPatterns) {
              const match = withoutStrings.match(pattern)
              if (match) {
                const identifier = match[1]
                ctx.report.violation({
                  message: `Non-ASCII identifier detected: "${identifier}" — use ASCII characters only for variable/function/class names`,
                  file,
                  line: i + 1,
                  fix: `Rename "${identifier}" to an English equivalent (e.g., user_name instead of ユーザー名)`,
                })
              }
            }
          }
        }
      },
    },

    'no-legacy-encoding-headers': {
      description: 'Forbid legacy encoding headers (Python 3 defaults to UTF-8)',
      severity: 'error',
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          // Skip ADR markdown files
          if (file.includes('docs/adrs/')) continue

          // Skip .claude/ (rulesync artifacts — the .rulesync/ sources are checked instead)
          if (file.startsWith('.claude/')) continue

          // Match encoding headers like # -*- coding: shift-jis -*- or # coding: iso-8859-1
          const matches = await ctx.grep(file, /#.*coding[:=]\s*(shift[-_]?jis|euc[-_]?jp|iso[-_]?8859|latin[-_]?1)/i)

          for (const match of matches) {
            ctx.report.violation({
              message: `Legacy encoding header detected — Python 3 defaults to UTF-8, remove this header`,
              file: match.file,
              line: match.line,
              fix: `Remove the encoding header line — Python 3 uses UTF-8 by default (PEP 3120)`,
            })
          }
        }
      },
    },

    'warn-non-ascii-content': {
      description: 'Forbid non-ASCII characters in files (prefer English for all content)',
      severity: 'error',
      check: async (ctx) => {
        // Process regular scopedFiles
        for (const file of ctx.scopedFiles) {
          // Skip ADR markdown files
          if (file.includes('docs/adrs/')) continue

          // Skip .claude/ (rulesync artifacts — the .rulesync/ sources are checked instead)
          if (file.startsWith('.claude/')) continue

          // Skip prompt files (they contain LLM prompt templates with user-facing messages)
          if (file.includes('prompts.py')) continue

          // Skip scenarios.json
          if (file.includes('src/poker/application/validation/')) continue

          const content = await ctx.readFile(file)
          const lines = content.split('\n')

          for (let i = 0; i < lines.length; i++) {
            const line = lines[i]

            // For Python files: skip string literals (user-facing messages allowed per ADR-009)
            if (file.endsWith('.py')) {
              // Remove string literals from the line
              const withoutStrings = line.replace(/"""[\s\S]*?"""|'''[\s\S]*?'''|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'/g, '""')

              if (/[^\x00-\x7F]/.test(withoutStrings)) {
                ctx.report.violation({
                  message: `Non-ASCII characters detected — use English for code comments and identifiers`,
                  file,
                  line: i + 1,
                  fix: `Rewrite in English to avoid encoding issues across environments`,
                })
              }
            }
            // For .rulesync and .devcontainer files: allow specific emoji (🔴🟢🤖⏸️❌✅⚠️)
            else if ((file.startsWith('.rulesync/') || file.startsWith('.devcontainer/')) &&
              (file.endsWith('.sh') || file.endsWith('.yaml') || file.endsWith('.yml') ||
                file.endsWith('.md') || file.endsWith('.json') || file.endsWith('.txt'))) {
              // Remove allowed emoji before checking
              const withoutAllowedEmoji = line.replace(/[🔴🟢🤖⏸️❌✅⚠️]/g, '')
              if (/[^\x00-\x7F]/.test(withoutAllowedEmoji)) {
                ctx.report.violation({
                  message: `Non-ASCII characters detected — prefer English to avoid encoding issues`,
                  file,
                  line: i + 1,
                  fix: `Rewrite in English to ensure compatibility across environments`,
                })
              }
            }
            // For Shell scripts, YAML, Markdown, JSON, txt: check everything
            else if (file.endsWith('.sh') || file.endsWith('.yaml') || file.endsWith('.yml') ||
              file.endsWith('.md') || file.endsWith('.json') || file.endsWith('.txt')) {
              if (/[^\x00-\x7F]/.test(line)) {
                ctx.report.violation({
                  message: `Non-ASCII characters detected — prefer English to avoid encoding issues`,
                  file,
                  line: i + 1,
                  fix: `Rewrite in English to ensure compatibility across environments`,
                })
              }
            }
          }
        }

        // Explicitly check .devcontainer and .github directories
        // NOTE: Archgate's glob doesn't match dot-prefixed directories, so we maintain a list here.
        // To update this list when new files are added, run:
        //   find .devcontainer .github .rulesync -type f \( -name "*.sh" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" -o -name "*.txt" -o -name "*.md" -o -name "*.py" -o -name "*.js" -o -name "*.ts" \) 2>/dev/null | sort
        const dotDirFiles = [
          '.devcontainer/devcontainer.json',
          '.devcontainer/local/cognito/config.json',
          '.devcontainer/local/cognito/init.sh',
          '.devcontainer/local/compose.yaml',
          '.devcontainer/local/devcontainer.json',
          '.devcontainer/local/localstack/init.sh',
          '.devcontainer/Readme.md',
          '.devcontainer/setup.sh',
          '.github/agents/update-llm-model.agent.md',
          '.github/copilot-instructions.md',
          '.github/ISSUE_TEMPLATE/bug_report.md',
          '.github/ISSUE_TEMPLATE/chore.md',
          '.github/ISSUE_TEMPLATE/feature_request.md',
          '.github/ISSUE_TEMPLATE/project.md',
          '.github/PULL_REQUEST_TEMPLATE.md',
          '.github/PULL_REQUEST_TEMPLATE/bugfix.md',
          '.github/PULL_REQUEST_TEMPLATE/feature.md',
          '.github/PULL_REQUEST_TEMPLATE/PULL_REQUEST_TEMPLATE.md',
          '.github/PULL_REQUEST_TEMPLATE/release.md',
          '.github/skills/update-llm-model-execution/SKILL.md',
          '.github/workflows/header_check.yaml',
          '.github/workflows/pr_into_main.yaml',
          '.github/workflows/ruff_formatter.yaml',
          '.github/workflows/toro_code_review.yaml',
          '.github/workflows/unittests.yaml',
          '.rulesync/commands/build.md',
          '.rulesync/commands/fix.md',
          '.rulesync/commands/hotfix.md',
          '.rulesync/commands/update-rules.md',
          '.rulesync/configs/.claude-settings.json',
          '.rulesync/configs/.claude-settings.local.json',
          '.rulesync/hooks.json',
          '.rulesync/mcp.json',
          '.rulesync/rules/architecture.md',
          '.rulesync/rules/overview.md',
          '.rulesync/rulesync.sh',
          '.rulesync/skills/designing-feature/SKILL.md',
          '.rulesync/skills/draft-pr/SKILL.md',
          '.rulesync/skills/exploring-codebase/SKILL.md',
          '.rulesync/skills/fetching-github-issue/SKILL.md',
          '.rulesync/skills/investigating-bugs/SKILL.md',
          '.rulesync/skills/quality-gate/SKILL.md',
          '.rulesync/skills/record-architectural-decision/SKILL.md',
          '.rulesync/skills/review-with-adrs/SKILL.md',
          '.rulesync/subagents/architect.md',
          '.rulesync/subagents/qa.md',
          '.rulesync/subagents/reviewer.md',
        ]

        const textFiles = dotDirFiles

        for (const filePath of textFiles) {
          try {
            // Skip ADR markdown files
            if (filePath.includes('docs/adrs/')) continue

            const content = await ctx.readFile(filePath)
            const lines = content.split('\n')

            for (let i = 0; i < lines.length; i++) {
              const line = lines[i]

              // For Python files in .devcontainer/.github: skip string literals
              if (filePath.endsWith('.py')) {
                const withoutStrings = line.replace(/"""[\s\S]*?"""|'''[\s\S]*?'''|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'/g, '""')
                if (/[^\x00-\x7F]/.test(withoutStrings)) {
                  ctx.report.violation({
                    message: `Non-ASCII characters detected — use English for code comments and identifiers`,
                    file: filePath,
                    line: i + 1,
                    fix: `Rewrite in English to avoid encoding issues across environments`,
                  })
                }
              }
              // For .rulesync and .devcontainer files: allow specific emoji (🔴🟢🤖⏸️❌✅⚠️)
              else if (filePath.startsWith('.rulesync/') || filePath.startsWith('.devcontainer/')) {
                // Remove allowed emoji before checking
                const withoutAllowedEmoji = line.replace(/[🔴🟢🤖⏸️❌✅⚠️]/g, '')
                if (/[^\x00-\x7F]/.test(withoutAllowedEmoji)) {
                  ctx.report.violation({
                    message: `Non-ASCII characters detected — prefer English to avoid encoding issues`,
                    file: filePath,
                    line: i + 1,
                    fix: `Rewrite in English to ensure compatibility across environments`,
                  })
                }
              }
              // For all other text files: check everything
              else if (/[^\x00-\x7F]/.test(line)) {
                ctx.report.violation({
                  message: `Non-ASCII characters detected — prefer English to avoid encoding issues`,
                  file: filePath,
                  line: i + 1,
                  fix: `Rewrite in English to ensure compatibility across environments`,
                })
              }
            }
          } catch (error) {
            // File might not be readable (binary, etc.), skip silently
          }
        }
      },
    },

    'detect-file-encoding': {
      description: 'Detect files that are not UTF-8 encoded',
      severity: 'error',
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          try {
            // Try to read file as UTF-8
            await ctx.readFile(file)
          } catch (error) {
            // If reading fails, file might not be UTF-8
            ctx.report.violation({
              message: `File encoding error — ensure file is saved with UTF-8 encoding`,
              file,
              fix: `Re-save the file with UTF-8 encoding in your editor`,
            })
          }
        }
      },
    },

    
  },
} satisfies RuleSet
