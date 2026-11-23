import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { SetupGuard } from "./SetupGuard";

const mockUseAuth = vi.fn();

vi.mock("../../hooks/useAuth", () => ({
  useAuth: () => mockUseAuth(),
}));

function renderGuard() {
  return render(
    <MemoryRouter>
      <SetupGuard>
        <p>Setup Content</p>
      </SetupGuard>
    </MemoryRouter>
  );
}

describe("SetupGuard", () => {
  it("shows spinner when loading", () => {
    mockUseAuth.mockReturnValue({
      isLoading: true,
      requiresSetup: false,
    });

    renderGuard();

    expect(screen.queryByText("Setup Content")).not.toBeInTheDocument();
    expect(document.querySelector(".animate-spin")).toBeInTheDocument();
  });

  it("redirects to dashboard when setup complete", () => {
    mockUseAuth.mockReturnValue({
      isLoading: false,
      requiresSetup: false,
    });

    renderGuard();

    expect(screen.queryByText("Setup Content")).not.toBeInTheDocument();
  });

  it("renders children when requiresSetup is true", () => {
    mockUseAuth.mockReturnValue({
      isLoading: false,
      requiresSetup: true,
    });

    renderGuard();

    expect(screen.getByText("Setup Content")).toBeInTheDocument();
  });
});
