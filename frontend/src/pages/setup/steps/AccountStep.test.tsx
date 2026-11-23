import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("axios", () => ({
  default: {
    post: vi.fn().mockResolvedValue({ data: {} }),
    isAxiosError: vi.fn().mockReturnValue(false),
  },
}));

vi.mock("../../../hooks/useToast", () => ({
  useToast: () => ({ showToast: vi.fn() }),
}));

import { AccountStep } from "./AccountStep";

describe("AccountStep", () => {
  it("renders Create Account heading", () => {
    render(<AccountStep onNext={vi.fn()} />);

    expect(screen.getByText("Create Account")).toBeInTheDocument();
  });

  it("renders username, password, and confirm password fields", () => {
    render(<AccountStep onNext={vi.fn()} />);

    expect(screen.getByText("Username")).toBeInTheDocument();
    expect(screen.getByText("Password")).toBeInTheDocument();
    expect(screen.getByText("Confirm Password")).toBeInTheDocument();
  });

  it("renders Next button", () => {
    render(<AccountStep onNext={vi.fn()} />);

    expect(screen.getByText("Next")).toBeInTheDocument();
  });
});
