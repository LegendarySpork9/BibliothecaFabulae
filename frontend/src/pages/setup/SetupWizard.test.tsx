import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("axios", () => ({
  default: {
    get: vi.fn().mockResolvedValue({
      data: { current_step: 1, storage_path: "", smtp_configured: false },
    }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    isAxiosError: vi.fn().mockReturnValue(false),
  },
}));

vi.mock("../../api/client", () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    patch: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
  },
  setAccessToken: vi.fn(),
}));

vi.mock("../../hooks/useToast", () => ({
  useToast: () => ({
    showToast: vi.fn(),
  }),
}));

import { SetupWizard } from "./SetupWizard";

describe("SetupWizard", () => {
  it("renders step indicator with 5 steps", async () => {
    render(<SetupWizard />);

    expect(await screen.findByText("Account")).toBeInTheDocument();
    expect(screen.getByText("2FA Setup")).toBeInTheDocument();
    expect(screen.getByText("Storage")).toBeInTheDocument();
    expect(screen.getByText("Email")).toBeInTheDocument();
    expect(screen.getByText("Summary")).toBeInTheDocument();
  });

  it("renders Create Account heading on step 1", async () => {
    render(<SetupWizard />);

    expect(
      await screen.findByText("Create Account")
    ).toBeInTheDocument();
  });
});
