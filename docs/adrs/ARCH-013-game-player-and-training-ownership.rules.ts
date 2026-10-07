/// <reference path="rules.d.ts" />

export default {
  rules: {
    "application-functions-only": {
      description: "Application use cases must be functions rather than classes.",
      severity: "error",
      check: async (ctx) => {
        const matches = await ctx.grepFiles(
          /^\s*class\s+\w+/,
          "src/poker/application/**/*.py",
        );
        for (const match of matches) {
          ctx.report.violation({
            message: "Application classes are forbidden; keep state in Core and expose a use-case function.",
            file: match.file,
            line: match.line,
            fix: "Move the class to Core and invoke it through an application use-case function.",
          });
        }
      },
    },
  },
} satisfies RuleSet;
