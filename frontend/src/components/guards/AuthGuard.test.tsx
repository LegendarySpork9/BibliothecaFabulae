import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { AuthContext } from "../../contexts/AuthContext";

import { AuthGuard } from "./AuthGuard";

function renderWithAuth(
  ui: React.ReactElement,
  authValue: {
    isAuthenticated: boolean;
    isLoading: boolean;
    requiresSetup: boolean;
  }
) {
  return render(
    <AuthContext.Provider
      value={{
        ...authValue,
        login: vi.fn(),
        verifyTotp: vi.fn(),
        logout: vi.fn(),
      }}
    >
      <MemoryRouter>{ui}</MemoryRouter>
    </AuthContext.Provider>
  );
}

describe("AuthGuard", () => {
  it("shows loading spinner when isLoading is true", () => {
    renderWithAuth(
      <AuthGuard>
        <p>Protected</p>
      </AuthGuard>,
      { isAuthenticated: false, isLoading: true, requiresSetup: false }
    );

    expect(screen.queryByText("Protected")).not.toBeInTheDocument();
    expect(document.querySelector(".animate-spin")).toBeInTheDocument();
  });

  it("redirects to /setup when requiresSetup is true", () => {
    renderWithAuth(
      <AuthGuard>
        <p>Protected</p>
      </AuthGuard>,
      { isAuthenticated: false, isLoading: false, requiresSetup: true }
    );

    expect(screen.queryByText("Protected")).not.toBeInTheDocument();
  });

  it("redirects to /login when not authenticated", () => {
    renderWithAuth(
      <AuthGuard>
        <p>Protected</p>
      </AuthGuard>,
      { isAuthenticated: false, isLoading: false, requiresSetup: false }
    );

    expect(screen.queryByText("Protected")).not.toBeInTheDocument();
  });

  it("renders children when authenticated", () => {
    renderWithAuth(
      <AuthGuard>
        <p>Protected</p>
      </AuthGuard>,
      { isAuthenticated: true, isLoading: false, requiresSetup: false }
    );

    expect(screen.getByText("Protected")).toBeInTheDocument();
  });
});
