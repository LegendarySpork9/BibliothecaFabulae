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

import { TotpStep } from "./TotpStep";

const defaultProps = {
  qrCodeBase64: "dGVzdA==",
  totpSecret: "JBSWY3DPEHPK3PXP",
  onNext: vi.fn(),
  onBack: vi.fn(),
};

describe("TotpStep", () => {
  it("renders Two-Factor Authentication heading", () => {
    render(<TotpStep {...defaultProps} />);

    expect(
      screen.getByText("Two-Factor Authentication")
    ).toBeInTheDocument();
  });

  it("renders QR code image", () => {
    render(<TotpStep {...defaultProps} />);

    const img = screen.getByAltText("TOTP QR Code");

    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute(
      "src",
      "data:image/png;base64,dGVzdA=="
    );
  });

  it("renders verification code input", () => {
    render(<TotpStep {...defaultProps} />);

    expect(screen.getByText("Verification Code")).toBeInTheDocument();
  });

  it("renders Back and Verify buttons", () => {
    render(<TotpStep {...defaultProps} />);

    expect(screen.getByText("Back")).toBeInTheDocument();
    expect(screen.getByText("Verify")).toBeInTheDocument();
  });
});
