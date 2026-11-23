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

import { StorageStep } from "./StorageStep";

describe("StorageStep", () => {
  it("renders Storage Path heading", () => {
    render(<StorageStep onNext={vi.fn()} onBack={vi.fn()} />);

    expect(screen.getByText("Storage Path")).toBeInTheDocument();
  });

  it("renders storage directory input", () => {
    render(<StorageStep onNext={vi.fn()} onBack={vi.fn()} />);

    expect(screen.getByText("Storage Directory")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("/path/to/storage")
    ).toBeInTheDocument();
  });

  it("renders Validate button", () => {
    render(<StorageStep onNext={vi.fn()} onBack={vi.fn()} />);

    expect(screen.getByText("Validate")).toBeInTheDocument();
  });

  it("renders Back and Next buttons", () => {
    render(<StorageStep onNext={vi.fn()} onBack={vi.fn()} />);

    expect(screen.getByText("Back")).toBeInTheDocument();
    expect(screen.getByText("Next")).toBeInTheDocument();
  });
});
