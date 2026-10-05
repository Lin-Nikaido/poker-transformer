/// <reference path="rules.d.ts" />

export default {
  rules: {
    'recommend-keyword-only-params': {
      description: 'Require keyword-only parameters (*) for functions with 2+ parameters',
      severity: 'error',
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          // Match function definitions
          const matches = await ctx.grep(file, /^(\s*)def\s+(\w+)\s*\(([^)]*)\)\s*(->\s*[^:]+)?\s*:/)

          for (const match of matches) {
            const functionDef = match.content

            // Skip if function already has * separator
            if (functionDef.includes('*,') || functionDef.includes('*, ')) {
              continue
            }

            // Skip if function has *args or **kwargs (already using variadic)
            if (functionDef.includes('*args') || functionDef.includes('**kwargs')) {
              continue
            }

            // Count parameters (rough heuristic: count commas + 1, excluding return type)
            const paramsSection = functionDef.split('(')[1]?.split(')')[0] || ''
            const paramCount = paramsSection.trim() ? paramsSection.split(',').length : 0

            // Skip functions with 0-1 parameters
            if (paramCount <= 1) {
              continue
            }

            // Skip test functions (def test_*)
            if (functionDef.includes('def test_')) {
              continue
            }

            // Skip special methods (__init__, __str__, etc.)
            if (functionDef.includes('def __')) {
              continue
            }

            ctx.report.violation({
              message: `Function has ${paramCount} parameters but no keyword-only separator (*) — consider making parameters explicit`,
              file: match.file,
              line: match.line,
              fix: `Add '*,' before optional parameters to make them keyword-only, improving call-site readability`,
            })
          }
        }
      },
    },

    'detect-positional-function-calls': {
      description: 'Forbid function calls with multiple positional arguments',
      severity: 'error',
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          // Match function calls with 2+ positional arguments (very rough heuristic)
          // Example: some_func("arg1", "arg2", "arg3")
          const matches = await ctx.grep(
            file,
            /\b(?<!def )\w+\([^)]*,\s*[^)]*,\s*[^)]*\)/,
          )

          for (const match of matches) {
            const callContent = match.content.trim()

            // Skip if this looks like a keyword argument call (contains '=')
            if (callContent.includes('=')) {
              continue
            }

            // Skip common built-ins that are naturally positional
            if (
              /^(print|max|min|len|range|zip|map|filter|sum|sorted|list|dict|set|tuple)\(/.test(
                callContent,
              )
            ) {
              continue
            }

            // Skip test assertions
            if (/assert|assertEqual|assertEquals|assertTrue|assertFalse/.test(callContent)) {
              continue
            }

            ctx.report.violation({
              message: `Function call with multiple positional arguments — consider using keyword arguments for clarity`,
              file: match.file,
              line: match.line,
              fix: `Rewrite as func(param1=value1, param2=value2, ...) for better readability`,
            })
          }
        }
      },
    },

    'no-single-letter-params': {
      description: 'Forbid single-letter parameter names except for math operations',
      severity: 'error',
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          // Match function definitions with single-letter parameters (excluding x, y, z for math)
          const matches = await ctx.grep(file, /def\s+\w+\([^)]*\b([a-wA-W]|[yY][a-zA-Z])\s*:/)

          for (const match of matches) {
            const functionDef = match.content

            // Skip if function name suggests math operation
            if (/def\s+(add|sub|mul|div|pow|sqrt|abs|min|max|calculate|compute)/.test(functionDef)) {
              continue
            }

            // Extract single-letter parameter names
            const singleLetterParams = functionDef.match(/\b([a-wA-W])\s*:/g)
            if (singleLetterParams && singleLetterParams.length > 0) {
              ctx.report.violation({
                message: `Single-letter parameter name found — use descriptive names for clarity`,
                file: match.file,
                line: match.line,
                fix: `Rename parameter to a descriptive name (e.g., 'user_id' instead of 'u')`,
              })
            }
          }
        }
      },
    },

    'enforce-keyword-only-for-optional': {
      description: 'Require keyword-only for optional parameters with defaults',
      severity: 'error',
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          // Match function definitions with default parameters but no * separator
          const matches = await ctx.grep(file, /def\s+\w+\([^)]*=/)

          for (const match of matches) {
            const functionDef = match.content

            // Skip if function already has * separator
            if (functionDef.includes('*,') || functionDef.includes('*, ')) {
              continue
            }

            // Skip if function has **kwargs
            if (functionDef.includes('**kwargs')) {
              continue
            }

            // Skip special methods
            if (functionDef.includes('def __')) {
              continue
            }

            ctx.report.violation({
              message: `Function has optional parameters (with defaults) but no keyword-only separator — add '*,' for clarity`,
              file: match.file,
              line: match.line,
              fix: `Add '*,' before the first optional parameter to enforce keyword-only arguments`,
            })
          }
        }
      },
    },
  },
} satisfies RuleSet

