/// <reference path="rules.d.ts" />

export default {
  rules: {
    'no-bare-any-in-signatures': {
      description: 'Forbid typing.Any in function signatures without justification',
      severity: 'error',
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          // Match function definitions with Any in type hints
          const matches = await ctx.grep(file, /def\s+\w+\([^)]*:\s*Any/)

          for (const match of matches) {
            // Check if there's a justifying comment on the same line or line above
            const lines = (await ctx.readFile(match.file)).split('\n')
            const lineIndex = match.line - 1
            const currentLine = lines[lineIndex] || ''
            const previousLine = lineIndex > 0 ? lines[lineIndex - 1] : ''

            // Look for justification patterns
            const hasJustification =
              /#.*(?:boto3|third-party|external|API|untyped|boundary|TODO|issue)/i.test(currentLine) ||
              /#.*(?:boto3|third-party|external|API|untyped|boundary|TODO|issue)/i.test(previousLine)

            if (!hasJustification) {
              ctx.report.violation({
                message: `Function signature uses 'Any' without justification — use Mapping, Sequence, or object instead`,
                file: match.file,
                line: match.line,
                fix: `Replace 'Any' with a more specific type (Mapping[K, V], Sequence[T], object) or add a comment explaining why Any is necessary at this external boundary`,
              })
            }
          }
        }
      },
    },

    'no-any-return-type': {
      description: 'Forbid Any as return type without justification',
      severity: 'error',
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          // Match function definitions with -> Any
          const matches = await ctx.grep(file, /def\s+\w+\([^)]*\)\s*->\s*Any\s*:/)

          for (const match of matches) {
            // Check if there's a justifying comment
            const lines = (await ctx.readFile(match.file)).split('\n')
            const lineIndex = match.line - 1
            const currentLine = lines[lineIndex] || ''
            const previousLine = lineIndex > 0 ? lines[lineIndex - 1] : ''

            const hasJustification =
              /#.*(?:boto3|third-party|external|API|untyped|boundary|TODO|issue)/i.test(currentLine) ||
              /#.*(?:boto3|third-party|external|API|untyped|boundary|TODO|issue)/i.test(previousLine)

            if (!hasJustification) {
              ctx.report.violation({
                message: `Return type 'Any' without justification — use a concrete type (list[T], dict[K, V], or Pydantic model)`,
                file: match.file,
                line: match.line,
                fix: `Replace 'Any' with a concrete return type or add a comment explaining why Any is necessary (e.g., external API with no type stub)`,
              })
            }
          }
        }
      },
    },

    'prefer-mapping-over-dict-args': {
      description: 'Require Mapping for function arguments instead of dict',
      severity: 'error',
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          // Match function arguments with dict[...] type hint
          const matches = await ctx.grep(file, /def\s+\w+\([^)]*:\s*dict\[/)

          for (const match of matches) {
            // Skip if this is a return type, not an argument
            if (match.content.includes('->')) {
              continue
            }

            ctx.report.violation({
              message: `Function argument uses 'dict' — consider 'Mapping' for better flexibility`,
              file: match.file,
              line: match.line,
              fix: `Change 'dict[K, V]' to 'Mapping[K, V]' for arguments (but keep 'dict' for return types)`,
            })
          }
        }
      },
    },

    'prefer-sequence-over-list-args': {
      description: 'Require Sequence for function arguments instead of list',
      severity: 'error',
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          // Match function arguments with list[...] type hint
          const matches = await ctx.grep(file, /def\s+\w+\([^)]*:\s*list\[/)

          for (const match of matches) {
            // Skip if this is a return type, not an argument
            if (match.content.includes('->')) {
              continue
            }

            ctx.report.violation({
              message: `Function argument uses 'list' — consider 'Sequence' for better flexibility`,
              file: match.file,
              line: match.line,
              fix: `Change 'list[T]' to 'Sequence[T]' for arguments (but keep 'list' for return types)`,
            })
          }
        }
      },
    },

    'use-object-not-any': {
      description: 'Require object instead of Any when truly accepting any value',
      severity: 'error',
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          // Match variable annotations or simple parameters with : Any
          const matches = await ctx.grep(file, /:\s*Any(?:\s|,|$)/)

          for (const match of matches) {
            // Skip if it's part of a generic like Mapping[str, Any]
            const before = match.content.substring(0, match.column - 1)
            if (/\[\s*str\s*,\s*$/.test(before) || /\[\s*\w+\s*,\s*$/.test(before)) {
              continue
            }

            // Skip if there's a justification comment
            const lines = (await ctx.readFile(match.file)).split('\n')
            const lineIndex = match.line - 1
            const currentLine = lines[lineIndex] || ''

            if (/#.*(?:boto3|third-party|external|API|untyped|boundary|TODO|issue)/i.test(currentLine)) {
              continue
            }

            ctx.report.violation({
              message: `Consider using 'object' instead of 'Any' if the value can truly be anything`,
              file: match.file,
              line: match.line,
              fix: `Replace 'Any' with 'object' for better type safety, or add a justification comment if this is an external boundary`,
            })
          }
        }
      },
    },
  },
} satisfies RuleSet
