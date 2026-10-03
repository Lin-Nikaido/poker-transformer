/// <reference path="rules.d.ts" />

export default {
  rules: {
    'redundant-comment-increment': {
      description: 'Forbid obvious comments like "# increment" or "# normalize"',
      severity: 'error',
      check: async (ctx) => {
        // Patterns for obvious comments
        const obviousPatterns = [
          /\s*#\s*increment\s*$/i,
          /\s*#\s*decrement\s*$/i,
          /\s*#\s*normalize\s*$/i,
          /\s*#\s*save\s+(log|file|data)\s*$/i,
          /\s*#\s*open\s+file\s*$/i,
          /\s*#\s*close\s+file\s*$/i,
        ]

        for (const file of ctx.scopedFiles) {
          for (const pattern of obviousPatterns) {
            const matches = await ctx.grep(file, pattern)
            for (const match of matches) {
              ctx.report.violation({
                message: `Redundant comment explaining what code obviously does: "${match.content.trim()}"`,
                file: match.file,
                line: match.line,
                fix: `Remove the comment — use a descriptive variable or function name instead`,
              })
            }
          }
        }
      },
    },

    'separator-comment-blocks': {
      description: 'Forbid separator comments that divide code blocks within a function',
      severity: 'error',
      check: async (ctx) => {
        // Patterns for separator comments (English only, as Japanese comments will be caught separately)
        const separatorPatterns = [
          /^\s*#\s*(verify|check|validate)\s+/i,
          /^\s*#\s*(load|fetch|get|retrieve)\s+/i,
          /^\s*#\s*(save|store|write)\s+/i,
          /^\s*#\s*(process|handle|execute)\s+/i,
          /^\s*#\s*(return|send|emit)\s+/i,
          /^\s*#\s*(calculate|compute)\s+/i,
        ]

        for (const file of ctx.scopedFiles) {
          for (const pattern of separatorPatterns) {
            const matches = await ctx.grep(file, pattern)
            for (const match of matches) {
              // Skip docstrings and module-level comments
              if (match.content.trim().startsWith('"""') || match.content.trim().startsWith("'''")) {
                continue
              }

              ctx.report.violation({
                message: `Separator comment found: "${match.content.trim()}" — extract this block into a function instead`,
                file: match.file,
                line: match.line,
                fix: `Extract the code block into a function with a descriptive name (e.g., verify_user, load_messages)`,
              })
            }
          }
        }
      },
    },

    'non-ascii-comment': {
      description: 'Detect non-ASCII characters in comments (Japanese, etc.)',
      severity: 'error',
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          // Match lines with comments containing non-ASCII characters
          const matches = await ctx.grep(file, /#.*[^\x00-\x7F]/)
          for (const match of matches) {
            // Skip lines that are entirely non-ASCII (likely docstrings in other encodings)
            const commentPart = match.content.split('#').slice(1).join('#')
            if (commentPart && /[^\x00-\x7F]/.test(commentPart)) {
              ctx.report.violation({
                message: `Non-ASCII characters detected in comment (prefer English for code comments)`,
                file: match.file,
                line: match.line,
                fix: `Rewrite the comment in English, or move context to documentation`,
              })
            }
          }
        }
      },
    },

    'inline-comment-duplication': {
      description: 'Detect inline comments that duplicate code logic',
      severity: 'error',
      check: async (ctx) => {
        // This is a heuristic check — look for patterns like "x = y  # set x to y"
        const duplicationPatterns = [
          /(\w+)\s*=\s*(\w+)\s*#\s*set\s+\1\s+to\s+\2/i,
          /(\w+)\s*=\s*.*\s*#\s*assign\s+/i,
          /return\s+.*\s*#\s*return\s+/i,
        ]

        for (const file of ctx.scopedFiles) {
          for (const pattern of duplicationPatterns) {
            const matches = await ctx.grep(file, pattern)
            for (const match of matches) {
              ctx.report.violation({
                message: `Inline comment appears to duplicate code logic: "${match.content.trim()}"`,
                file: match.file,
                line: match.line,
                fix: `Remove the comment if it restates what the code already expresses clearly`,
              })
            }
          }
        }
      },
    },
  },
} satisfies RuleSet
