import { describe, it, expect, vi } from "vitest";
import { createTelemetry, recordDegradation, telemetrySummary, emitTelemetry } from "../../src/telemetry.js";

describe("Telemetry", () => {
    it("createTelemetry should produce correct shape with defaults", () => {
        const t = createTelemetry({
            requestId: "req-1",
            model: "gpt-4o",
            messageCount: 2,
            toolCount: 0,
            stream: false,
        });
        expect(t.requestId).toBe("req-1");
        expect(t.tenantId).toBe("default");
        expect(t.retrievalHits).toBe(0);
        expect(t.createdAt).toBeInstanceOf(Date);
    });

    it("recordDegradation should add to skippedComponents (deduplicated)", () => {
        const t = createTelemetry({ requestId: "r1", model: "gpt-4o", messageCount: 1, toolCount: 0, stream: false });
        recordDegradation(t, "qdrant", "Qdrant unavailable");
        recordDegradation(t, "qdrant", "Qdrant unavailable");
        expect(t.skippedComponents).toHaveLength(1);
    });

    it("recordDegradation should append to fallbackReason", () => {
        const t = createTelemetry({ requestId: "r2", model: "gpt-4o", messageCount: 1, toolCount: 0, stream: false });
        recordDegradation(t, "qdrant", "Qdrant down");
        recordDegradation(t, "postgres", "DB down");
        expect(t.fallbackReason).toContain("Qdrant down");
        expect(t.fallbackReason).toContain("DB down");
    });

    it("telemetrySummary should format correctly", () => {
        const t = createTelemetry({ requestId: "r3", model: "gpt-4o", messageCount: 2, toolCount: 1, stream: false });
        t.providerLatencyMs = 200;
        t.retrievalHits = 3;
        t.toolCallsExecuted = 1;
        const summary = telemetrySummary(t);
        expect(summary).toContain("lat=200ms");
        expect(summary).toContain("retrieval=3");
        expect(summary).toContain("tools=1");
    });

    it("telemetrySummary should include degraded components", () => {
        const t = createTelemetry({ requestId: "r4", model: "gpt-4o", messageCount: 1, toolCount: 0, stream: false });
        recordDegradation(t, "qdrant", "Qdrant down");
        const summary = telemetrySummary(t);
        expect(summary).toContain("degraded=qdrant");
    });

    it("emitTelemetry should log via Fastify logger", () => {
        const t = createTelemetry({ requestId: "r5", model: "gpt-4o", messageCount: 1, toolCount: 0, stream: false });
        const mockLog = { info: vi.fn() };
        emitTelemetry(t, mockLog as any);
        expect(mockLog.info).toHaveBeenCalledWith({ telemetry: t }, "request completed");
    });
});