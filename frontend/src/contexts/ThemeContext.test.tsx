import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useContext } from "react";
import { describe, expect, it, vi } from "vitest";

import { ThemeContext, ThemeProvider } from "./ThemeContext";

vi.mock("../api/settings", () => ({
  updateTheme: vi.fn().mockResolvedValue({}),
}));

function ThemeConsumer() {
  const { theme, toggleTheme } = useContext(ThemeContext);

  return (
    <div>
      <span data-testid="theme">{theme}</span>
      <button onClick={toggleTheme}>Toggle</button>
    </div>
  );
}

describe("ThemeContext", () => {
  it("defaults to dark theme", () => {
    localStorage.removeItem("theme");

    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );

    expect(screen.getByTestId("theme").textContent).toBe("dark");
  });

  it("toggles theme from dark to light", async () => {
    localStorage.removeItem("theme");
    const user = userEvent.setup();

    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );

    expect(screen.getByTestId("theme").textContent).toBe("dark");

    await user.click(screen.getByText("Toggle"));

    expect(screen.getByTestId("theme").textContent).toBe("light");
  });
});
