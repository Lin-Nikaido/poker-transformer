/// <reference path="rules.d.ts" />

export default {
  rules: {
    "no-domain-model-in-application": {
      description:
        "Pydantic BaseModel subclasses representing domain concepts must be defined in core/types/, not in application/.",
      severity: "error",
      check: async (ctx) => {
        const matches = await ctx.grepFiles(
          /^class\s+\w+\s*\(\s*BaseModel\s*\)/,
          "src/trust/application/**/*.py",
        );
        for (const match of matches) {
          ctx.report.violation({
            message:
              "Pydantic BaseModel subclass found in application/ — domain types should be defined in core/types/ and imported here",
            file: match.file,
            line: match.line,
            fix: "Move this class to src/trust/core/types/ and import it in application/. For application-internal structures that need no external validation, use Python dataclass or TypedDict instead.",
          });
        }
      },
    },

    "no-domain-model-in-infrastructure": {
      description:
        "Pydantic BaseModel subclasses must not be defined in infrastructure/. Domain types belong in core/types/.",
      severity: "error",
      check: async (ctx) => {
        const matches = await ctx.grepFiles(
          /^class\s+\w+\s*\(\s*BaseModel\s*\)/,
          "src/trust/infrastructure/**/*.py",
        );
        for (const match of matches) {
          ctx.report.violation({
            message:
              "Pydantic BaseModel subclass found in infrastructure/ — domain types must be defined in core/types/",
            file: match.file,
            line: match.line,
            fix: "Move this class to src/trust/core/types/ and import it in infrastructure/.",
          });
        }
      },
    },
  },
} satisfies RuleSet;
