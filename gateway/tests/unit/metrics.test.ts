import { describe, it, expect, beforeEach } from "vitest";
import { metricsCollector } from "../../../src/metrics.js";

describe("MetricsCollector", () => {
    beforeEach(() => {
        // Reset internal state through snapshot-and-ignore (no reset API)
        // We test discrete behaviors rather than cumulative totals
    });

    it("recordRequest should update counts", () => {
        metricsCollector.recordRequest("gpt-4o", 100, "200");
        const snap = metricsCollector.snapshot();
        expect(snap.requestsTotal).toBeGreaterThanOrEqual(1);
        expect(snap.requestsByModel["gpt-4o"]).toBeGreaterThanOrEqual(1);
        expect(snap.requestsByStatus["200"]).toBeGreaterThanOrEqual(1);
    });

    it("recordToolCall and retrieval/entity methods should increment", () => {
        metricsCollector.recordToolCall(3);
        metricsCollector.recordRetrievalHits(5);
        metricsCollector.recordEntityExtraction(2);
        const snap = metricsCollector.snapshot();
        expect(snap.toolCallsTotal).toBeGreaterThanOrEqual(3);
        expect(snap.retrievalHitsTotal).toBeGreaterThanOrEqual(5);
        expect(snap.entitiesExtractedTotal).toBeGreaterThanOrEqual(2);
    });

    it("snapshot should return MetricsSnapshot with histogram", () => {
        const snap = metricsCollector.snapshot();
        expect(snap).toHaveProperty("uptimeMs");
        expect(snap).toHaveProperty("latencyHistogramMs");
        expect(snap).toHaveProperty("recentDegradations");
        expect(snap.latencyHistogramMs["0-100"]).toBeTypeOf("number");
    });

    it("recordDegradation should add to recentDegradations", () => {
        metricsCollector.recordDegradation("test-component", "test reason");
        const snap = metricsCollector.snapshot();
        const found = snap.recentDegradations.find((d) => d.component === "test-component");
        expect(found).toBeDefined();
        expect(found!.reason).toBe("test reason");
    });
});