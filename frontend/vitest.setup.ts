// Vitest setup — registers @testing-library/jest-dom matchers and clears
// DOM after each test so component tests stay isolated.
import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

afterEach(() => {
  cleanup();
});
