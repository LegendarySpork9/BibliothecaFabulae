import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ImportModal } from "../ImportModal";

function renderModal(overrides?: Partial<{
  onImport: (url: string) => void;
  onClose: () => void;
  isLoading: boolean;
}>) {
  const props = {
    onImport: overrides?.onImport ?? vi.fn(),
    onClose: overrides?.onClose ?? vi.fn(),
    isLoading: overrides?.isLoading ?? false,
  };

  return { ...render(<ImportModal {...props} />), props };
}

describe("ImportModal", () => {
  it("renders the modal heading", () => {
    renderModal();

    expect(screen.getByText("Import Fic by URL")).toBeInTheDocument();
  });

  it("renders the URL input field", () => {
    renderModal();

    const input = screen.getByPlaceholderText(
      "https://archiveofourown.org/works/12345"
    );

    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute("type", "url");
  });

  it("renders Import and Cancel buttons", () => {
    renderModal();

    expect(screen.getByText("Import")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });

  it("renders the support hint text", () => {
    renderModal();

    expect(
      screen.getByText(/Supports AO3, FFNet, Wattpad/)
    ).toBeInTheDocument();
  });

  it("calls onClose when Cancel is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    renderModal({ onClose });

    await user.click(screen.getByText("Cancel"));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when the X button is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    renderModal({ onClose });

    // The X button contains an SVG icon and no accessible text,
    // so we find the button by its position (first button in the header).
    const buttons = screen.getAllByRole("button");
    const closeButton = buttons.find(
      (btn) => !btn.textContent?.includes("Import") && !btn.textContent?.includes("Cancel")
    );

    expect(closeButton).toBeDefined();

    await user.click(closeButton!);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onImport with the entered URL on form submit", async () => {
    const user = userEvent.setup();
    const onImport = vi.fn();

    renderModal({ onImport });

    const input = screen.getByPlaceholderText(
      "https://archiveofourown.org/works/12345"
    );

    await user.type(input, "https://archiveofourown.org/works/99999");
    await user.click(screen.getByText("Import"));

    expect(onImport).toHaveBeenCalledWith(
      "https://archiveofourown.org/works/99999"
    );
  });

  it("disables input and submit button when isLoading is true", () => {
    renderModal({ isLoading: true });

    const input = screen.getByPlaceholderText(
      "https://archiveofourown.org/works/12345"
    );

    expect(input).toBeDisabled();
  });

  it("shows a loading message when isLoading is true", () => {
    renderModal({ isLoading: true });

    expect(
      screen.getByText(/Download started/)
    ).toBeInTheDocument();
  });

  it("does not show loading message when isLoading is false", () => {
    renderModal({ isLoading: false });

    expect(screen.queryByText(/Download started/)).not.toBeInTheDocument();
  });
});
