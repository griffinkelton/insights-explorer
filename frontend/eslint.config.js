// Phase 4 Task 8 — lint boundaries (enforced in CI):
// 1. no-restricted-imports: production paths may not import src/test, src/prototype, or mock-*.
// 2. no raw fetch() outside src/lib/api.ts (the sanctioned module that calls fetch).
import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";

// Production paths — src/lib/api.ts and colocated test files are re-enabled by
// explicit override objects below (guaranteed override semantics).
const PRODUCTION_PATHS = [
  "src/components/**",
  "src/routes/**",
  "src/lib/**",
  "src/hooks/**",
  "src/router.tsx",
];

export default tseslint.config(
  { ignores: ["dist", "node_modules", "src/routeTree.gen.ts"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    plugins: { "react-hooks": reactHooks },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "@typescript-eslint/no-explicit-any": "off",
    },
  },
  {
    // Prototype quarantine (master-plan §12) + mock isolation (drift row 12).
    files: PRODUCTION_PATHS,
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            { group: ["@/test/*"], message: "Production code must never import from src/test/ (prototype quarantine)." },
            { group: ["@/prototype/*"], message: "Production code must never import from src/prototype/ (prototype quarantine)." },
            { group: ["*/mock-ga4", "*/mock-braintree", "*/mock-evidence"], message: "Mock fixtures are TEST-ONLY (drift row 12)." },
          ],
        },
      ],
    },
  },
  {
    // No raw fetch outside the single API-base module (Task 3 acceptance).
    files: PRODUCTION_PATHS,
    rules: {
      "no-restricted-syntax": [
        "error",
        {
          selector: "CallExpression[callee.name='fetch']",
          message: "Use apiFetch() from src/lib/api.ts — all calls must go through the typed client (Task 3).",
        },
      ],
    },
  },
  {
    // api.ts is the ONE sanctioned fetch module (Task 3).
    files: ["src/lib/api.ts"],
    rules: { "no-restricted-syntax": "off" },
  },
  {
    // Colocated tests live under src/lib but are not production code.
    files: ["src/**/*.test.{ts,tsx}"],
    rules: { "no-restricted-imports": "off", "no-restricted-syntax": "off" },
  },
);
