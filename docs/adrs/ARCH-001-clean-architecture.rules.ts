/// <reference path="rules.d.ts" />

export default {
  rules: {
    "no-infrastructure-imports-application": {
      description:
        "infrastructure/ must not import from application/ or apis/ — prevents upward coupling.",
      severity: "error",
      check: async (ctx) => {
        const matches = await ctx.grepFiles(
          /from poker\.(application|apis)\b/,
          "src/poker/infrastructure/**/*.py",
        );
        for (const match of matches) {
          const target = match.content.includes("poker.application")
            ? "application"
            : "apis";
          ctx.report.violation({
            message: `infrastructure/ imports from ${target}/ — this creates upward coupling that breaks the dependency rule`,
            file: match.file,
            line: match.line,
            fix: "Move shared logic to core/, or invert the dependency via an abstract interface in core/",
          });
        }
      },
    },

    "no-application-imports-apis": {
      description:
        "application/ must not import from apis/ — use cases must stay decoupled from HTTP schemas.",
      severity: "error",
      check: async (ctx) => {
        const matches = await ctx.grepFiles(
          /from poker\.apis\b/,
          "src/poker/application/**/*.py",
        );
        for (const match of matches) {
          ctx.report.violation({
            message:
              "application/ imports from apis/ — use cases must not depend on FastAPI/Pydantic request models",
            file: match.file,
            line: match.line,
            fix: "Accept plain Python types or core/types/ models as parameters instead of apis/ schemas",
          });
        }
      },
    },

    "no-core-imports-infrastructure": {
      description:
        "core/ should not import concrete implementations from infrastructure/. Use injected abstract contracts.",
      severity: "error",
      check: async (ctx) => {
        const matches = await ctx.grepFiles(
          /from poker\.infrastructure\b/,
          "src/poker/core/**/*.py",
        );
        for (const match of matches) {
          ctx.report.violation({
            message:
              "core/ imports from infrastructure/ — receive the concrete implementation through the abstract contract",
            file: match.file,
            line: match.line,
            fix: "Import the abstract contract from core/ and inject its implementation at startup",
          });
        }
      },
    },
  },
} satisfies RuleSet;
