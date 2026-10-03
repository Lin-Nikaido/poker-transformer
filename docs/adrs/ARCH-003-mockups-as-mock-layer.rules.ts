/// <reference path="rules.d.ts" />

export default {
  rules: {
    /**
     * Mock classes implementing core Base* ABCs must not be placed in test files.
     * Define them in tests/mockups/ and make them available to all tests via pytest_plugins.
     * Exception: private (_-prefixed) stubs that do not inherit any Base* ABC are allowed inline.
     */
    "no-base-mock-class-in-test-file": {
      description:
        "Classes implementing core Base* ABCs must be defined in tests/mockups/, not inline in test files.",
      severity: "error",
      check: async (ctx) => {
        const matches = await ctx.grepFiles(
          /^class\s+\w+\s*\(\s*Base\w+\s*\)/,
          "tests/**/*.py",
        );
        for (const match of matches) {
          if (match.file.includes("tests/mockups/")) continue;
          if (match.file.endsWith("conftest.py")) continue;

          ctx.report.violation({
            message:
              "Mock class implementing a Base* ABC found in test file — move to tests/mockups/ and register in tests/conftest.py pytest_plugins",
            file: match.file,
            line: match.line,
            fix: [
              "1. Create tests/mockups/mock_xxx.py with this class and a @pytest.fixture",
              "2. Add 'tests.mockups.mock_xxx' to pytest_plugins in tests/conftest.py",
              "3. Remove this class from the test file and use the fixture via function argument",
            ].join("\n"),
          });
        }
      },
    },
  },
} satisfies RuleSet;
