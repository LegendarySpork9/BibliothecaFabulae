import { describe, expect, it } from "vitest";

import { getAccessToken, setAccessToken } from "./client";
import client from "./client";

describe("client", () => {
  it("setAccessToken and getAccessToken round-trip", () => {
    setAccessToken("my-token");

    expect(getAccessToken()).toBe("my-token");

    setAccessToken(null);

    expect(getAccessToken()).toBeNull();
  });

  it("request interceptor adds Authorization header when token is set", async () => {
    setAccessToken("test-token");

    const config = {
      headers: {} as Record<string, string>,
      url: "/test",
    };

    const interceptor = (client.interceptors.request as any).handlers[0];
    const result = interceptor.fulfilled(config);

    expect(result.headers.Authorization).toBe("Bearer test-token");

    setAccessToken(null);
  });
});
