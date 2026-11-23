import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

const mockSetTheme = vi.fn();

vi.mock("../../hooks/useTheme", () => ({
  useTheme: () => ({
    theme: "light",
    setTheme: mockSetTheme,
    toggleTheme: vi.fn(),
  }),
}));

import { ThemeSettingsPage } from "./ThemeSettingsPage";

describe("ThemeSettingsPage", () => {
  it("renders Choose Theme heading", () => {
    render(<ThemeSettingsPage />);

    expect(screen.getByText("Choose Theme")).toBeInTheDocument();
  });

  it("renders Light and Dark buttons", () => {
    render(<ThemeSettingsPage />);

    expect(screen.getByText("Light")).toBeInTheDocument();
    expect(screen.getByText("Dark")).toBeInTheDocument();
  });

  it("clicking Dark calls setTheme with dark", async () => {
    const user = userEvent.setup();

    render(<ThemeSettingsPage />);

    await user.click(screen.getByText("Dark"));

    expect(mockSetTheme).toHaveBeenCalledWith("dark");
  });
});
