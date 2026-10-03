/// <reference path="rules.d.ts" />

export default {
  rules: {
    /**
     * async def test_* functions (or their enclosing class) must have @pytest.mark.asyncio.
     * Without the decorator, pytest treats the coroutine as a return value and the test body
     * is never executed — it silently passes. Report when a file contains async def test_
     * but no @pytest.mark.asyncio anywhere.
     * NOTE: This rule is a compensating control for the absence of asyncio_mode = "auto".
     * See DEV-006 in known-deviations.md for the migration path.
     */
    "async-test-needs-asyncio-mark": {
      description:
        "Test files containing 'async def test_' must include @pytest.mark.asyncio. Without it, async tests silently pass without executing.",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/**/*.py");
        for (const file of testFiles) {
          if (file.endsWith("conftest.py")) continue;

          const content = await ctx.readFile(file);
          if (!content.includes("async def test_")) continue;
          if (content.includes("pytest.mark.asyncio")) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            if (/async def test_/.test(lines[i])) {
              ctx.report.violation({
                message:
                  "async test function found but @pytest.mark.asyncio is absent from this file — the test body will not execute and will silently PASS",
                file,
                line: i + 1,
                fix: [
                  "Add @pytest.mark.asyncio to the function or its class:",
                  "  @pytest.mark.asyncio",
                  "  async def test_foo(): ...",
                  "",
                  "  # or at class level (applies to all async methods):",
                  "  @pytest.mark.asyncio",
                  "  class TestFoo:",
                  "      async def test_foo(self): ...",
                ].join("\n"),
              });
              break;
            }
          }
        }
      },
    },


















  },
} satisfies RuleSet;
