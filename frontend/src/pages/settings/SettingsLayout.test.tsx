import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { SettingsLayout } from "./SettingsLayout";

function renderSettings() {
  return render(
    <MemoryRouter>
      <SettingsLayout />
    </MemoryRouter>
  );
}

describe("SettingsLayout", () => {
  it("renders Settings heading", () => {
    renderSettings();

    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("renders all 6 tab links", () => {
    renderSettings();

    expect(screen.getByText("Storage")).toBeInTheDocument();
    expect(screen.getByText("Theme")).toBeInTheDocument();
    expect(screen.getByText("Account")).toBeInTheDocument();
    expect(screen.getByText("Backup")).toBeInTheDocument();
    expect(screen.getByText("SMTP")).toBeInTheDocument();
    expect(screen.getByText("Notifications")).toBeInTheDocument();
  });
});
