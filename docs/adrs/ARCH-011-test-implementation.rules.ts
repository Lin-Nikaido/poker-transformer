/// <reference path="rules.d.ts" />

export default {
  rules: {
    /**
     * Every application use case must have a focused unit test. The test is
     * identified by its reference to the use-case function rather than by a
     * rigid filename convention, because existing modules use both
     * `test_<action>.py` and `test_<action>_<entity>.py` naming styles.
     */
    "every-application-usecase-has-unit-test": {
      description:
        "Every application use case must be referenced by a unit test under tests/unittests/application/.",
      severity: "error",
      check: async (ctx) => {
        const applicationFiles = await ctx.glob(
          "src/poker/application/**/*.py",
        );
        const testFiles = await ctx.glob(
          "tests/unittests/application/**/*.py",
        );
        const testContents = await Promise.all(
          testFiles.map(async (file) => ({
            file,
            content: await ctx.readFile(file),
          })),
        );

        for (const file of applicationFiles) {
          const content = await ctx.readFile(file);
          for (const match of content.matchAll(
            /async\s+def\s+(\w+_usecase)\s*\(/g,
          )) {
            const useCaseName = match[1];
            if (
              testContents.some(({ content: testContent }) =>
                testContent.includes(useCaseName),
              )
            ) {
              continue;
            }

            ctx.report.violation({
              message:
                `Application use case '${useCaseName}' has no corresponding unit test under tests/unittests/application/.`,
              file,
              line: content.slice(0, match.index ?? 0).split("\n").length,
              fix: `Add a unit test that references '${useCaseName}' under tests/unittests/application/.`,
            });
          }
        }
      },
    },

    /**
     * Application use-case tests must isolate the core collaborator at the
     * import binding used by the application module.
     */
    "application-usecase-must-patch-core-collaborator": {
      description:
        "Application use-case unit tests must patch the core collaborator at the application's import binding.",
      severity: "error",
      check: async (ctx) => {
        const applicationFiles = await ctx.glob(
          "src/poker/application/**/*.py",
        );
        const testFiles = await ctx.glob(
          "tests/unittests/application/**/*.py",
        );
        const testContents = await Promise.all(
          testFiles.map(async (file) => ({
            file,
            content: await ctx.readFile(file),
          })),
        );

        for (const file of applicationFiles) {
          const content = await ctx.readFile(file);
          const useCaseNames = [
            ...content.matchAll(/async\s+def\s+(\w+_usecase)\s*\(/g),
          ].map((match) => match[1]);
          if (useCaseNames.length === 0) continue;

          const coreCollaborators = [
            ...content.matchAll(
              /from\s+(poker\.core(?:\.[\w]+)+)\s+import\s+([a-z_]\w*)/g,
            ),
          ]
            .map((match) => match[2])
            .filter((name) =>
              new RegExp(`\\b${name}\\s*\\(`).test(content),
            );
          if (coreCollaborators.length === 0) continue;

          const modulePath = file
            .replace(/^src\\?\//, "")
            .replace(/\.py$/, "")
            .replace(/[\\/]/g, ".");

          for (const useCaseName of useCaseNames) {
            const matchingTests = testContents.filter(({ content: testContent }) =>
              testContent.includes(useCaseName),
            );
            if (matchingTests.length === 0) continue;
            for (const collaborator of coreCollaborators) {
              const patchPattern = new RegExp(
                `patch\\s*\\(\\s*["']${modulePath}\\.${collaborator}["']`,
              );
              if (
                matchingTests.some(({ content: testContent }) =>
                  patchPattern.test(testContent),
                )
              ) {
                continue;
              }

              const testFile = matchingTests[0].file;
              const testContent = matchingTests[0]?.content ?? "";
              const useCaseLine = testContent
                ? testContent
                    .split("\n")
                    .findIndex((line) => line.includes(useCaseName)) + 1
                : 1;
              ctx.report.violation({
                message:
                  `Application use-case test for '${useCaseName}' does not patch core collaborator '${collaborator}' at '${modulePath}.${collaborator}'.`,
                file: testFile,
                line: useCaseLine > 0 ? useCaseLine : 1,
                fix: `Patch '${modulePath}.${collaborator}' with AsyncMock in the application use-case test.`,
              });
            }
          }
        }
      },
    },

    /**
     * A patched core collaborator must have its returned value propagated by
     * the application use case without reconstructing or replacing it.
     */
    "application-usecase-must-propagate-mock-output": {
      description:
        "Application use-case tests must verify that a patched collaborator's output is returned unchanged.",
      severity: "error",
      check: async (ctx) => {
        const applicationFiles = await ctx.glob(
          "src/poker/application/**/*.py",
        );
        const testFiles = await ctx.glob(
          "tests/unittests/application/**/*.py",
        );
        const testContents = await Promise.all(
          testFiles.map(async (file) => ({
            file,
            content: await ctx.readFile(file),
          })),
        );

        for (const applicationFile of applicationFiles) {
          const applicationContent = await ctx.readFile(applicationFile);
          const useCaseNames = [
            ...applicationContent.matchAll(/async\s+def\s+(\w+_usecase)\s*\(/g),
          ].map((match) => match[1]);

          for (const useCaseName of useCaseNames) {
            for (const { file, content } of testContents) {
              if (!content.includes(useCaseName)) continue;

              const returnedValues = [
                ...content.matchAll(
                  /AsyncMock\s*\(\s*return_value\s*=\s*(\w+)/g,
                ),
              ].map((match) => match[1]);
              const hasPropagationAssertion = returnedValues.some((value) =>
                new RegExp(
                  `assert\\s+result\\s+(?:is|==)\\s+${value}\\b`,
                ).test(content),
              );
              if (hasPropagationAssertion) continue;

              const line = content
                .split("\n")
                .findIndex((currentLine) => currentLine.includes(useCaseName));
              ctx.report.violation({
                message:
                  `Application use-case test for '${useCaseName}' does not verify unchanged propagation of the core collaborator output.`,
                file,
                line: line >= 0 ? line + 1 : 1,
                fix: "Patch the core collaborator with AsyncMock(return_value=expected_output) and assert that the use-case result is or equals expected_output.",
              });
            }
          }
        }
      },
    },

    /**
     * Every FastAPI endpoint must be exercised by an integration test.
     * This source/test topology check catches a new route being added without
     * the corresponding HTTP-boundary test.
     */
    "every-api-endpoint-has-integration-test": {
      description:
        "Every FastAPI API endpoint must have a corresponding HTTP integration test under tests/integration/.",
      severity: "error",
      check: async (ctx) => {
        const apiFiles = await ctx.glob("src/poker/apis/**/*.py");
        const testFiles = await ctx.glob("tests/integration/**/*.py");
        const routePattern =
          /@[A-Za-z_][\w.]*\.(get|post|put|patch|delete|options|head|trace)\s*\(\s*["']([^"']+)["']/g;
        const methodCallPattern =
          /\b[A-Za-z_][\w]*\.(get|post|put|patch|delete|options|head|trace)\s*\(\s*["']([^"']+)["']/gi;
        const requestCallPattern =
          /\b[A-Za-z_][\w]*\.request\s*\(\s*["'](GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD|TRACE)["']\s*,\s*["']([^"']+)["']/g;

        const normalizePath = (path: string): string => {
          const withoutQuery = path.split("?", 1)[0];
          const withLeadingSlash = withoutQuery.startsWith("/")
            ? withoutQuery
            : `/${withoutQuery}`;
          return withLeadingSlash.length > 1
            ? withLeadingSlash.replace(/\/$/, "")
            : withLeadingSlash;
        };

        const testedEndpoints = new Set<string>();
        for (const file of testFiles) {
          const content = await ctx.readFile(file);
          for (const match of content.matchAll(methodCallPattern)) {
            testedEndpoints.add(
              `${match[1].toUpperCase()}:${normalizePath(match[2])}`,
            );
          }
          for (const match of content.matchAll(requestCallPattern)) {
            testedEndpoints.add(
              `${match[1].toUpperCase()}:${normalizePath(match[2])}`,
            );
          }
        }

        for (const file of apiFiles) {
          const content = await ctx.readFile(file);
          for (const match of content.matchAll(routePattern)) {
            const endpoint = `${match[1].toUpperCase()}:${normalizePath(match[2])}`;
            if (testedEndpoints.has(endpoint)) continue;

            const line = content.slice(0, match.index ?? 0).split("\n").length;
            ctx.report.violation({
              message:
                `API endpoint ${endpoint} has no corresponding integration test under tests/integration/`,
              file,
              line,
              fix: `Add a ${match[1].toUpperCase()} request test for ${normalizePath(match[2])} under tests/integration/.`,
            });
          }
        }
      },
    },

    /**
     * Integration tests must not use @patch or unittest.mock.patch.
     * Patching out real components turns the test into a unit test and removes
     * the ability to verify that actual component interactions work correctly.
     * (Moved from ARCH-004 — this is an implementation-level enforcement.)
     */
    "no-patch-in-integration-tests": {
      description:
        "Integration tests must not patch application collaborators. Deterministic boundary doubles are allowed for LLM model resolution, notification sending, ECS handoff setup, and startup registry isolation.",
      severity: "error",
      check: async (ctx) => {
        const matches = await ctx.grepFiles(
          /@patch\s*\(|with\s+patch\s*\(/,
          "tests/integration/**/*.py",
        );
        for (const match of matches) {
          if (match.file.endsWith("conftest.py")) continue;
          const allowedBoundaryPatch =
            match.content.includes("_resolve_model") ||
            match.content.includes("get_sentence_transformer_model") ||
            match.content.includes("send_notice") ||
            match.content.includes("run_task") ||
            match.content.includes("initialize_store_registry") ||
            match.content.includes("initialize_agent_registry");
          if (allowedBoundaryPatch) continue;

          ctx.report.violation({
            message:
              "unittest.mock.patch used in integration test — patching application collaborators turns this into a unit test",
            file: match.file,
            line: match.line,
            fix: [
              "Use real local services or framework-provided test doubles instead:",
              "  - AWS services: use the LocalStack-backed integration profile",
              "  - ADK sessions: use InMemorySessionService",
              "  - FastAPI dependencies: use app.dependency_overrides",
              "  - LLM determinism: patch only _resolve_model / MockModel boundary",
              "  - If unit-level isolation is truly needed, move to tests/unittests/",
            ].join("\n"),
          });
        }
      },
    },

    /**
     * monkeypatch.setattr() in integration tests must not replace components.
     * Using monkeypatch.setattr() on a service, agent, store, or I/O attribute
     * has the same effect as @patch — it removes a real collaborator from the
     * integration path.
     *
     * monkeypatch is permitted ONLY for environment configuration (setenv, setitem).
     */
    "no-monkeypatch-setattr-component-in-integration": {
      description:
        "monkeypatch.setattr() must not replace services, agents, stores, or I/O in integration tests. It is allowed only for environment configuration (setenv, setitem).",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/integration/**/*.py");
        for (const file of testFiles) {
          if (file.endsWith("conftest.py")) continue;
          const content = await ctx.readFile(file);
          if (!content.includes("monkeypatch.setattr")) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            if (lines[i].includes("monkeypatch.setattr")) {
              ctx.report.violation({
                message:
                  "monkeypatch.setattr() in integration test replaces a real component — this defeats the purpose of integration testing",
                file,
                line: i + 1,
                fix: [
                  "Replace with an environment-safe alternative:",
                  "  - For FastAPI dependencies: app.dependency_overrides[dep] = stub",
                  "  - For AWS services: use moto @mock_aws",
                  "  - For environment config: monkeypatch.setenv() or monkeypatch.setitem() are allowed",
                  "  - If component isolation is needed, move to tests/unittests/",
                ].join("\n"),
              });
              break;
            }
          }
        }
      },
    },











    /**
     * Async fixtures must use @pytest_asyncio.fixture, not @pytest.fixture.
     *
     * Using @pytest.fixture on an async def function is deprecated in
     * pytest-asyncio v0.21+ and causes a DeprecationWarning or error in v1.x.
     * It can also cause event-loop scope mismatches for session/module fixtures.
     */
    "async-fixture-must-use-pytest-asyncio-fixture": {
      description:
        "Async fixtures (async def) must use @pytest_asyncio.fixture, not @pytest.fixture. Using @pytest.fixture on async def is deprecated in pytest-asyncio v1.x and may cause event-loop scope mismatches.",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/**/*.py");
        for (const file of testFiles) {
          const content = await ctx.readFile(file);
          // Only check files that have async fixtures
          if (!content.includes("async def") || !content.includes("@pytest.fixture")) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            // Look for @pytest.fixture followed (within 3 lines) by async def
            if (/^\s*@pytest\.fixture/.test(lines[i])) {
              // Check next few lines for async def
              for (let j = i + 1; j <= i + 3 && j < lines.length; j++) {
                if (/^\s*async def /.test(lines[j])) {
                  // Check it's not a test function (those are decorated differently)
                  if (!/async def test_/.test(lines[j])) {
                    ctx.report.violation({
                      message:
                        "@pytest.fixture used on an async def function — use @pytest_asyncio.fixture to avoid event-loop scope mismatches in pytest-asyncio v1.x",
                      file,
                      line: i + 1,
                      fix: [
                        "Replace @pytest.fixture with @pytest_asyncio.fixture:",
                        "  import pytest_asyncio",
                        "",
                        "  @pytest_asyncio.fixture(scope='module')  # or 'function', 'session'",
                        "  async def my_fixture():",
                        "      ...",
                        "",
                        "For session-scoped async fixtures, add loop_scope:",
                        "  @pytest_asyncio.fixture(scope='session', loop_scope='session')",
                        "  async def my_session_fixture():",
                        "      ...",
                      ].join("\n"),
                    });
                    break;
                  }
                }
              }
            }
          }
        }
      },
    },

    /**
     * Mock classes implementing core ABCs (Base*) must be placed in tests/mockups/,
     * not defined inline inside test files.
     *
     * Inline mock class definitions cannot be reused, bloat test files, and lead
     * to the same mock being duplicated across modules. See ARCH-003 for the full policy.
     */
    "mock-abc-class-must-be-in-mockups-dir": {
      description:
        "Classes implementing Base* ABCs defined inline in test files must be moved to tests/mockups/. Inline mock classes cannot be shared and duplicate across modules.",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/**/*.py");
        for (const file of testFiles) {
          // Skip mockups/ themselves and conftest files
          if (file.includes("tests/mockups/")) continue;
          if (file.endsWith("conftest.py")) continue;

          const content = await ctx.readFile(file);
          // Look for class definitions that inherit from Base*
          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            const classMatch = lines[i].match(/^class\s+(\w+)\s*\(.*Base\w+.*\)\s*:/);
            if (classMatch) {
              const className = classMatch[1];
              // Exclude if it's a test class (TestFoo pattern)
              if (/^Test/.test(className)) continue;
              ctx.report.violation({
                message:
                  `Inline mock class '${className}' implements a Base* ABC — move it to tests/mockups/ so it can be shared and registered as a pytest plugin`,
                file,
                line: i + 1,
                fix: [
                  `Move the class to tests/mockups/mock_${className.toLowerCase().replace("mock", "")}.py`,
                  "Then register it in pytest_plugins in tests/conftest.py:",
                  '  pytest_plugins = [',
                  `      "tests.mockups.mock_${className.toLowerCase().replace("mock", "")}",`,
                  "  ]",
                  "See ARCH-003 for the full mock class policy.",
                ].join("\n"),
              });
            }
          }
        }
      },
    },

    /**
     * Expensive fixture setup (DB table creation, HTTP client creation, search index
     * initialization) must use module or session scope, not function scope.
     *
     * Creating a DynamoDB table or FastAPI TestClient for every test function
     * multiplies setup cost by the number of tests and slows the suite significantly.
     */
    "expensive-fixture-must-not-use-function-scope": {
      description:
        "Fixtures that create database tables, HTTP clients, or search indexes must use module or session scope. Function-scoped setup for expensive resources slows the test suite significantly.",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/**/*.py");
        for (const file of testFiles) {
          const content = await ctx.readFile(file);

          // Only check files with fixtures
          if (!content.includes("@pytest.fixture") && !content.includes("@pytest_asyncio.fixture")) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            // Look for function-scoped (default) fixtures — no scope= argument
            const isDefaultScopedFixture =
              (/^\s*@pytest\.fixture\s*$/.test(lines[i]) ||
                /^\s*@pytest_asyncio\.fixture\s*$/.test(lines[i]));

            if (!isDefaultScopedFixture) continue;

            // Check the body of the fixture (next ~10 lines) for expensive patterns
            const body = lines.slice(i + 1, Math.min(i + 15, lines.length)).join("\n");
            const isExpensive =
              body.includes("create_table") ||
              body.includes("TestClient") ||
              body.includes("create_async_engine") ||
              body.includes("create_index") ||
              body.includes("get_database_instance");

            if (isExpensive) {
              // Find the fixture function name for a better message
              const nextDef = lines.slice(i + 1, i + 4).find((l) => /def /.test(l));
              const nameMatch = nextDef?.match(/def (\w+)/);
              const fixtureName = nameMatch ? nameMatch[1] : "this fixture";

              ctx.report.violation({
                message:
                  `'${fixtureName}' creates an expensive resource (DB table, HTTP client, or index) in function scope — use scope='module' or scope='session' to avoid per-test recreation`,
                file,
                line: i + 1,
                fix: [
                  "Add scope='module' (shared within a test file) or scope='session' (shared across all tests):",
                  "  @pytest_asyncio.fixture(scope='module')",
                  "  async def my_table():",
                  "      with mock_aws():",
                  "          table = dynamodb.create_table(...)",
                  "          yield table",
                ].join("\n"),
              });
            }
          }
        }
      },
    },





    /**
     * Unit tests must not contain real outbound HTTP URLs without mocking.
     *
     * Tests in tests/unittests/ run in CI without external network access.
     * A real URL string (https://...) combined with no evidence of patching
     * the HTTP client or extractor class indicates the test will make a live
     * request that will either fail or produce non-deterministic results.
     *
     * Allowed safe patterns:
     *  - https://mock.  (explicit mock endpoint)
     *  - https://example.com  (RFC 2606 test domain, no real server)
     *  - https://localhost  / https://127.0.0.1  (local loopback)
     *  - any https:// URL inside a string that also appears in the same file
     *    alongside patch / AsyncMock / MagicMock (the URL is being mocked)
     */
    "unit-test-must-not-make-real-http-calls": {
      description:
        "Unit tests in tests/unittests/ must not contain real outbound HTTPS URLs without mocking the HTTP client or extractor class. CI has no external network access; real URLs cause non-deterministic failures.",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/unittests/**/*.py");
        // Matches https:// URLs that are NOT safe placeholder/loopback domains
        const realUrlPattern =
          /https:\/\/(?!mock\.|example\.com|localhost|127\.0\.0\.1)[a-zA-Z0-9][\w.-]+\.[a-zA-Z]{2,}/g;

        // Lines where a URL is clearly a data literal rather than a live call:
        //   - dict value:            "key": "https://..."  or  'key': 'https://...'
        //   - assert equality RHS:   assert expr == "https://..."
        //   - equality LHS check:    "https://..." ==
        const safeLinePattern =
          /(?:["']\w+["']\s*:\s*["']https?:|assert\b.*==\s*["']https?:|==\s*["']https?:)/;

        for (const file of testFiles) {
          const content = await ctx.readFile(file);
          realUrlPattern.lastIndex = 0;
          const matches = [...content.matchAll(realUrlPattern)];
          if (matches.length === 0) continue;

          // File-level guards — the author is already aware of the network
          // dependency and has handled it via mocking or a skipif guard.
          const hasMocking =
            content.includes("patch(") ||
            content.includes("AsyncMock") ||
            content.includes("MagicMock") ||
            content.includes("monkeypatch") ||
            content.includes("responses.") ||
            content.includes("httpretty") ||
            content.includes("respx");
          if (hasMocking) continue;

          // skipif guard: the real call is conditional on an env var, which is
          // the accepted integration-style pattern inside unittests/
          if (content.includes("skipif")) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            realUrlPattern.lastIndex = 0;
            if (!realUrlPattern.test(line)) continue;

            // Skip lines where the URL is a passive data value, not a call arg
            if (safeLinePattern.test(line)) continue;

            ctx.report.violation({
              message:
                "Real outbound HTTPS URL found in unit test without any mocking — CI has no external network access and the request will fail or return unexpected results",
              file,
              line: i + 1,
              fix: [
                "Option A — mock the HTTP client or extractor class (pure unit test):",
                "  from unittest.mock import AsyncMock, patch",
                "",
                "  with patch(",
                '      "poker.core.agents.website_reader_agent.tools.Html2MarkdownTextExtractor",',
                "      return_value=AsyncMock(return_value='mock content'),",
                "  ):",
                "      async for event in load_website('https://example.com/article'):",
                "          ...",
                "",
                "Option B — guard with skipif (integration-style, inside unittests/):",
                '  _NET_AVAILABLE = bool(os.environ.get("INTEGRATION_NET"))',
                "  @pytest.mark.skipif(not _NET_AVAILABLE,",
                '                      reason="Requires external network access")',
                "  async def test_load_real_website(): ...",
              ].join("\n"),
            });
            break;
          }
        }
      },
    },

    /**
     * monkeypatch.setattr() calls that pass a private attribute name (starting
     * with "_") are almost always wrong in unit tests targeting classes.
     *
     * The most common mistake is patching an instance attribute that doesn't
     * exist because the external client is created per-call via
     * `async with ClassName(...)`, not stored as `self._client`.
     *
     * The rule flags any monkeypatch.setattr() whose second argument is a
     * string starting with "_", prompting the author to verify the attribute
     * actually exists on the target object before merging.
     */
    "monkeypatch-setattr-underscore-attribute": {
      description:
        "monkeypatch.setattr(obj, '_attr', ...) with a private attribute name starting with '_' is likely wrong — the attribute may not exist on the target, masking the real failure with AttributeError. Verify existence first; for async-context-manager clients, patch the class at its import binding instead.",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/**/*.py");
        // Match: monkeypatch.setattr(<anything>, "_<name>", ...)
        // The second argument is a quoted string starting with underscore.
        const setAttrPrivatePattern =
          /monkeypatch\.setattr\s*\([^,]+,\s*["'](_[^"']+)["']/g;

        for (const file of testFiles) {
          const content = await ctx.readFile(file);
          if (!content.includes("monkeypatch.setattr")) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            const match = setAttrPrivatePattern.exec(lines[i]);
            if (match) {
              const attrName = match[1];
              ctx.report.violation({
                message: `monkeypatch.setattr with private attribute '${attrName}' — verify that this attribute exists on the target object. If the collaborator is created via 'async with ClassName(...)', patch the class at its import binding instead`,
                file,
                line: i + 1,
                fix: [
                  `Verify '${attrName}' is a real attribute of the target class.`,
                  "",
                  "If the collaborator is created per-call via `async with ClassName(...)`",
                  "there is no instance attribute to patch. Patch the class instead:",
                  "",
                  "  import module_under_test as _mod",
                  "  mock_client = AsyncMock()",
                  "  mock_client.__aenter__ = AsyncMock(return_value=mock_client)",
                  "  mock_client.__aexit__ = AsyncMock(return_value=False)",
                  "  monkeypatch.setattr(_mod, 'ClassName', MagicMock(return_value=mock_client))",
                ].join("\n"),
              });
            }
            setAttrPrivatePattern.lastIndex = 0;
          }
        }
      },
    },
  },
} satisfies RuleSet;
