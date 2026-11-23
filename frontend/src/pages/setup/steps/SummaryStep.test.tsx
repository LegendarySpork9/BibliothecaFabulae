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

import { SummaryStep } from "./SummaryStep";

const defaultProps = {
  storagePath: "/app/storage",
  smtpConfigured: true,
  onComplete: vi.fn(),
  onBack: vi.fn(),
};

describe("SummaryStep", () => {
  it("renders Setup Summary heading", () => {
    render(<SummaryStep {...defaultProps} />);

    expect(screen.getByText("Setup Summary")).toBeInTheDocument();
  });

  it("shows Account created with 2FA enabled", () => {
    render(<SummaryStep {...defaultProps} />);

    expect(
      screen.getByText("Account created with 2FA enabled")
    ).toBeInTheDocument();
  });

  it("shows storage path", () => {
    render(<SummaryStep {...defaultProps} />);

    expect(screen.getByText("/app/storage")).toBeInTheDocument();
  });

  it("shows Configured when smtpConfigured is true", () => {
    render(<SummaryStep {...defaultProps} smtpConfigured={true} />);

    expect(
      screen.getByText(/Configured/)
    ).toBeInTheDocument();
  });

  it("shows Skipped when smtpConfigured is false", () => {
    render(<SummaryStep {...defaultProps} smtpConfigured={false} />);

    expect(
      screen.getByText(/Skipped/)
    ).toBeInTheDocument();
  });

  it("renders Complete Setup button", () => {
    render(<SummaryStep {...defaultProps} />);

    expect(screen.getByText("Complete Setup")).toBeInTheDocument();
  });
});
