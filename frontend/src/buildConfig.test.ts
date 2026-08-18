import { describe, expect, it } from "vitest";
import { normalizeBuildId } from "./buildConfig";

describe("deployment build id", () => {
  it("keeps safe Cloud Build identifiers intact", () => {
    expect(normalizeBuildId("869606d2-4d65-49b1-ab2c-2a2e8c613db7")).toBe(
      "869606d2-4d65-49b1-ab2c-2a2e8c613db7",
    );
  });

  it("sanitizes unsafe filename characters and supplies a local fallback", () => {
    expect(normalizeBuildId("release/one two")).toBe("release-one-two");
    expect(normalizeBuildId(undefined)).toBe("local");
  });
});
