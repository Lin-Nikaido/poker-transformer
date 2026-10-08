/// <reference path="rules.d.ts" />

type Position = { line: number; column: number };
type ParameterSpan = { start: Position; end: Position };

function astPosition(node: PythonAstNode, end = false): Position {
  return {
    line: Number(end ? node.end_lineno : node.lineno),
    column: Number(end ? node.end_col_offset : node.col_offset),
  };
}

function sourceOffset(lines: string[], position: Position): number {
  const prefix = lines.slice(0, position.line - 1).join('\n');
  const line = lines[position.line - 1];
  const column = new TextDecoder().decode(
    new TextEncoder().encode(line).slice(0, position.column),
  ).length;
  return prefix.length + (position.line > 1 ? 1 : 0) + column;
}

function parameterSpans(node: PythonAstNode): ParameterSpan[] {
  const args = node.args as PythonAstNode;
  const positional = [
    ...(args.posonlyargs as PythonAstNode[]),
    ...(args.args as PythonAstNode[]),
  ];
  const defaults = args.defaults as PythonAstNode[];
  const keyword = args.kwonlyargs as PythonAstNode[];
  const keywordDefaults = args.kw_defaults as (PythonAstNode | null)[];
  const span = (arg: PythonAstNode, value?: PythonAstNode | null, stars = 0): ParameterSpan => {
    const start = astPosition(arg);
    start.column -= stars;
    return { start, end: astPosition(value ?? arg, true) };
  };
  return [
    ...positional.map((arg, index) => span(arg, defaults[index - positional.length + defaults.length])),
    ...(args.vararg ? [span(args.vararg as PythonAstNode, null, 1)] : []),
    ...keyword.map((arg, index) => span(arg, keywordDefaults[index])),
    ...(args.kwarg ? [span(args.kwarg as PythonAstNode, null, 2)] : []),
  ];
}

function isVerticalSignature(source: string, node: PythonAstNode): boolean {
  const spans = parameterSpans(node);
  if (spans.length < 2) {
    return true;
  }
  const lines = source.split('\n');
  const start = sourceOffset(lines, spans[0].start);
  const prefix = source.slice(sourceOffset(lines, astPosition(node)), start).replace(/#[^\n]*/g, '');
  const opening = prefix.lastIndexOf('(');
  const beforeFirst = prefix.slice(opening + 1);
  if (opening < 0 || !/^\s*(?:\*\s*,\s*)?$/.test(beforeFirst) || !beforeFirst.includes('\n')) {
    return false;
  }
  const openingLine = Number(node.lineno) + prefix.slice(0, opening).split('\n').length - 1;
  const separator = beforeFirst.indexOf('*');
  if (separator >= 0) {
    const separatorLine = openingLine + beforeFirst.slice(0, separator).split('\n').length - 1;
    if (separatorLine <= openingLine || separatorLine >= spans[0].start.line) {
      return false;
    }
  }
  for (let index = 0; index < spans.length; index++) {
    const current = spans[index];
    const next = spans[index + 1];
    const end = sourceOffset(lines, current.end);
    const limit = next ? sourceOffset(lines, next.start) : source.length;
    const gap = source.slice(end, limit).replace(/#[^\n]*/g, '');
    const punctuation = next ? gap : gap.slice(0, gap.indexOf(')') + 1);
    if (!/^\s*,\s*(?:[*/]\s*,\s*)*\)?\s*$/.test(punctuation)) {
      return false;
    }
    let previousLine = current.end.line;
    for (const match of punctuation.matchAll(/[*/)]/g)) {
      const line = current.end.line + punctuation.slice(0, match.index).split('\n').length - 1;
      if (line <= previousLine) {
        return false;
      }
      previousLine = line;
    }
    if (next && next.start.line <= previousLine) {
      return false;
    }
    if (!next && !punctuation.includes(')')) {
      return false;
    }
  }
  return true;
}

export default {
  rules: {
    'multiline-function-signatures': {
      description: 'Require one parameter or separator per line and a trailing comma for signatures with 2+ parameters',
      severity: 'error',
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          const source = await ctx.readFile(file);
          const tree = await ctx.ast(file, 'python');
          for (const node of ctx.findAstNodes(tree, 'FunctionDef', 'AsyncFunctionDef')) {
            if (isVerticalSignature(source, node)) {
              continue;
            }
            ctx.report.violation({
              message: `Function '${node.name}' has multiple parameters; put each parameter and separator on its own line with a trailing comma`,
              file,
              line: node.lineno,
              fix: 'Move parameters (including self/cls), * and / to separate lines, add a trailing comma, and put the closing parenthesis on a separate line.',
            });
          }
        }
      },
    },

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

