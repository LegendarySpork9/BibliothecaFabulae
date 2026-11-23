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

import { SmtpStep } from "./SmtpStep";

describe("SmtpStep", () => {
  it("renders Email Notifications heading", () => {
    render(<SmtpStep onNext={vi.fn()} onBack={vi.fn()} />);

    expect(screen.getByText("Email Notifications")).toBeInTheDocument();
  });

  it("renders SMTP Host and Port fields", () => {
    render(<SmtpStep onNext={vi.fn()} onBack={vi.fn()} />);

    expect(screen.getByText("SMTP Host")).toBeInTheDocument();
    expect(screen.getByText("Port")).toBeInTheDocument();
  });

  it("renders Username and Password fields", () => {
    render(<SmtpStep onNext={vi.fn()} onBack={vi.fn()} />);

    expect(screen.getByText("Username")).toBeInTheDocument();
    expect(screen.getByText("Password")).toBeInTheDocument();
  });

  it("renders From and To Address fields", () => {
    render(<SmtpStep onNext={vi.fn()} onBack={vi.fn()} />);

    expect(screen.getByText("From Address")).toBeInTheDocument();
    expect(screen.getByText("To Address")).toBeInTheDocument();
  });

  it("renders Test Connection, Save & Next, and Skip buttons", () => {
    render(<SmtpStep onNext={vi.fn()} onBack={vi.fn()} />);

    expect(screen.getByText("Test Connection")).toBeInTheDocument();
    expect(screen.getByText("Save & Next")).toBeInTheDocument();
    expect(screen.getByText("Skip")).toBeInTheDocument();
  });

  it("renders Use TLS checkbox", () => {
    render(<SmtpStep onNext={vi.fn()} onBack={vi.fn()} />);

    expect(screen.getByText("Use TLS")).toBeInTheDocument();
    expect(screen.getByRole("checkbox")).toBeChecked();
  });
});
