import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useContext } from "react";
import { describe, expect, it } from "vitest";

import { ToastContext, ToastProvider } from "./ToastContext";

function ToastTrigger() {
  const { showToast } = useContext(ToastContext);

  return (
    <button onClick={() => showToast("Test toast message", "success")}>
      Show Toast
    </button>
  );
}

describe("ToastContext", () => {
  it("showToast renders a toast message on screen", async () => {
    const user = userEvent.setup();

    render(
      <ToastProvider>
        <ToastTrigger />
      </ToastProvider>
    );

    await user.click(screen.getByText("Show Toast"));

    expect(
      screen.getByText("Test toast message")
    ).toBeInTheDocument();
  });

  it("toast contains the message text", async () => {
    const user = userEvent.setup();

    render(
      <ToastProvider>
        <ToastTrigger />
      </ToastProvider>
    );

    await user.click(screen.getByText("Show Toast"));

    const toast = screen.getByText("Test toast message");

    expect(toast).toBeInTheDocument();
    expect(toast.textContent).toBe("Test toast message");
  });
});
