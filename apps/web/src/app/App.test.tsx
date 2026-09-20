import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "./App";

describe("App", () => {
  it("renders the scaffold title", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise(() => undefined)),
    );

    render(<App />);

    expect(screen.getByRole("heading", { name: "Med Review Workbench" })).toBeInTheDocument();
    expect(screen.getByText("API health probe")).toBeInTheDocument();
  });
});
