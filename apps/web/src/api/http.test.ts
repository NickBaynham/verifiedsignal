import { describe, expect, it } from "vitest";
import { joinApiUrl } from "./http";

describe("joinApiUrl", () => {
  it("strips trailing slash on root and joins path", () => {
    expect(joinApiUrl("http://localhost:8000/", "/api/v1/health")).toBe("http://localhost:8000/api/v1/health");
  });

  it("adds leading slash when missing", () => {
    expect(joinApiUrl("http://localhost:8000", "auth/login")).toBe("http://localhost:8000/auth/login");
  });
});
