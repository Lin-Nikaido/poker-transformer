/// <reference path="rules.d.ts" />

export default {
  rules: {
    'no-bare-except': {
      description: 'Forbid bare except: clauses (catches KeyboardInterrupt and SystemExit)',
      severity: 'error',
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          // Match bare except: (with optional whitespace)
          const matches = await ctx.grep(file, /^\s*except\s*:\s*$/)

          for (const match of matches) {
            ctx.report.violation({
              message: `Bare 'except:' catches KeyboardInterrupt and SystemExit — use specific exception types`,
              file: match.file,
              line: match.line,
              fix: `Replace 'except:' with 'except SpecificException as e:' (e.g., ValueError, KeyError)`,
            })
          }
        }
      },
    },

    'no-exception-pass': {
      description: 'Forbid catching Exception and suppressing with pass',
      severity: 'error',
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          const content = await ctx.readFile(file)
          const lines = content.split('\n')

          for (let i = 0; i < lines.length - 1; i++) {
            const currentLine = lines[i]
            const nextLine = lines[i + 1]

            // Match "except Exception:" followed by "pass" (with whitespace)
            if (/except\s+Exception\s*:/.test(currentLine) && /^\s*pass\s*$/.test(nextLine)) {
              ctx.report.violation({
                message: `Catching 'Exception' and suppressing with 'pass' silently swallows all errors`,
                file,
                line: i + 1,
                fix: `Either catch a specific exception (ValueError, KeyError, etc.) or log + alert if this is an error boundary`,
              })
            }

            // Also check for bare except: followed by pass
            if (/except\s*:\s*$/.test(currentLine) && /^\s*pass\s*$/.test(nextLine)) {
              ctx.report.violation({
                message: `Bare 'except:' with 'pass' silently swallows all errors including KeyboardInterrupt`,
                file,
                line: i + 1,
                fix: `Catch specific exceptions only and handle them appropriately`,
              })
            }
          }
        }
      },
    },

    'no-broad-exception-in-library': {
      description: 'Forbid catching Exception in non-boundary functions (library code)',
      severity: 'error',
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          // Skip test files
          if (file.includes('/tests/')) {
            continue
          }

          // Match "except Exception" but allow it if followed by logging or send_error_alert
          const matches = await ctx.grep(file, /except\s+Exception\s+as\s+\w+\s*:/)

          for (const match of matches) {
            const content = await ctx.readFile(match.file)
            const lines = content.split('\n')
            const lineIndex = match.line - 1

            // Look ahead for logging.error or send_error_alert within the next 10 lines
            const blockLines = lines.slice(lineIndex, lineIndex + 10).join('\n')
            const hasLogging = /logging\.(error|exception|critical)/.test(blockLines)
            const hasAlert = /send_error_alert/.test(blockLines)

            // If this is an error boundary (has logging + alert), skip warning
            if (hasLogging && hasAlert) {
              continue
            }

            // Check if this is inside a top-level async function (likely a boundary)
            const functionContext = lines.slice(Math.max(0, lineIndex - 20), lineIndex).join('\n')
            const isTopLevelAsync = /async\s+def\s+\w+.*:\s*$/.test(functionContext)

            if (!isTopLevelAsync || (!hasLogging && !hasAlert)) {
              ctx.report.violation({
                message: `Catching broad 'Exception' — use specific exceptions or add logging + alerting if this is an error boundary`,
                file: match.file,
                line: match.line,
                fix: `Catch specific exceptions (ValueError, KeyError, etc.) or add logging.error() + send_error_alert() if this is a top-level error boundary`,
              })
            }
          }
        }
      },
    },

    'require-raise-from': {
      description: 'Require using "raise ... from e" to preserve exception context',
      severity: 'error',
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          const content = await ctx.readFile(file)
          const lines = content.split('\n')
          const exceptStack: { indent: number; varName: string }[] = []
          

          for (let i = 0; i < lines.length; i++) {
            const line = lines[i]

            const indent = line.match(/^(\s*)/)?.[1].length ?? 0

            // Exit blocks when indentation decreases
            while (
              exceptStack.length &&
              indent <= exceptStack[exceptStack.length - 1].indent &&
              line.trim() !== ''
            ) {
              exceptStack.pop()
            }

            const exceptMatch = line.match(
              /^\s*except\s+(?:[\w.]+)\s+as\s+(\w+)\s*:/
            )

            if (exceptMatch) {
              exceptStack.push({
                indent,
                varName: exceptMatch[1],
              })
              continue
            }

            const raiseMatch = line.match(/^\s*raise\s+\w+\(/)

            if (raiseMatch && exceptStack.length > 0) {
              let raiseStatement = line

              let parenDepth =
                (line.match(/\(/g)?.length ?? 0) -
                (line.match(/\)/g)?.length ?? 0)

              let j = i + 1

              while (parenDepth > 0 && j < lines.length) {
                raiseStatement += '\n' + lines[j]

                parenDepth +=
                  (lines[j].match(/\(/g)?.length ?? 0) -
                  (lines[j].match(/\)/g)?.length ?? 0)

                j++
              }

              const currentExceptionVar =
                exceptStack[exceptStack.length - 1].varName

              if (
                !new RegExp(`\\bfrom\\s+${currentExceptionVar}\\b`).test(
                  raiseStatement,
                )
              ) {
                ctx.report.violation({
                  message: `Raising new exception without 'from ${currentExceptionVar}'`,
                  file,
                  line: i + 1,
                  fix: `Use 'raise NewException(...) from ${currentExceptionVar}'`,
                })
              }
            }
          }
        }
      },
    },

    'no-exception-in-return-path': {
      description: 'Detect catching exceptions and returning default values (hides failures)',
      severity: 'error',
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          const content = await ctx.readFile(file)
          const lines = content.split('\n')

          for (let i = 0; i < lines.length - 3; i++) {
            const currentLine = lines[i]
            const nextLines = lines.slice(i + 1, i + 5).join('\n')

            // Match "except SomeException:" followed by "return" (within 5 lines)
            if (/except\s+\w+Error\s+as\s+\w+\s*:/.test(currentLine) && /^\s*return\s+/.test(nextLines)) {
              // Skip if there's logging
              if (/logging\.(error|warning|exception)/.test(nextLines)) {
                continue
              }

              ctx.report.violation({
                message: `Catching exception and returning default value without logging — caller assumes success`,
                file,
                line: i + 1,
                fix: `Either re-raise the exception or log the error before returning a default value`,
              })
            }
          }
        }
      },
    },
  },
} satisfies RuleSet
