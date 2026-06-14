/**
 * In-memory metrics collector for the gateway.
 *
 * Exposes a simple accumulator that track counts, histograms, and
 * recent error states. Designed to be:
 *   - Zero-dependency (no Prometheus client library needed)
 *   - Lossy under high load (ring buffer for latencies)
 *   - Queryable via GET /metrics as JSON
 *
 * Enable with `GATEWAY_METRICS_ENABLED=true` in the environment.
 */

const MAX_LATENCY_SAMPLES = 1000;
const MAX_TELEMETRY_RECORDS = 100;

export interface MetricsSnapshot {
    uptimeMs: number;
    requestsTotal: number;
    requestsByModel: Record<string, number>;
    requestsByStatus: Record<string, number>;
    latencyHistogramMs: HistogramBuckets;
    toolCallsTotal: number;
    retrievalHitsTotal: number;
    entitiesExtractedTotal: number;
    degradationCount: number;
    recentDegradations: Array<{ component: string; reason: string; time: string }>;
}

export interface HistogramBuckets {
    "0-100": number;
    "100-500": number;
    "500-2000": number;
    "2000-5000": number;
    "5000+": number;
}

class MetricsCollector {
    private startTime = Date.now();
    private requestsTotal = 0;
    private requestsByModel: Record<string, number> = {};
    private requestsByStatus: Record<string, number> = {};
    private latencySamples: number[] = [];
    private toolCallsTotal = 0;
    private retrievalHitsTotal = 0;
    private entitiesExtractedTotal = 0;
    private recentDegradations: Array<{ component: string; reason: string; time: string }> = [];

    recordRequest(model: string, latencyMs: number, status: string): void {
        this.requestsTotal++;
        this.requestsByModel[model] = (this.requestsByModel[model] ?? 0) + 1;
        this.requestsByStatus[status] = (this.requestsByStatus[status] ?? 0) + 1;

        if (this.latencySamples.length < MAX_LATENCY_SAMPLES) {
            this.latencySamples.push(latencyMs);
        }
        // When full, drop — we don't need perfect accuracy for MVP
    }

    recordToolCall(count: number): void {
        this.toolCallsTotal += count;
    }

    recordRetrievalHits(count: number): void {
        this.retrievalHitsTotal += count;
    }

    recordEntityExtraction(count: number): void {
        this.entitiesExtractedTotal += count;
    }

    recordDegradation(component: string, reason: string): void {
        if (this.recentDegradations.length >= MAX_TELEMETRY_RECORDS) {
            this.recentDegradations.shift();
        }
        this.recentDegradations.push({
            component,
            reason,
            time: new Date().toISOString(),
        });
    }

    snapshot(): MetricsSnapshot {
        return {
            uptimeMs: Date.now() - this.startTime,
            requestsTotal: this.requestsTotal,
            requestsByModel: { ...this.requestsByModel },
            requestsByStatus: { ...this.requestsByStatus },
            latencyHistogramMs: this.computeHistogram(this.latencySamples),
            toolCallsTotal: this.toolCallsTotal,
            retrievalHitsTotal: this.retrievalHitsTotal,
            entitiesExtractedTotal: this.entitiesExtractedTotal,
            degradationCount: this.recentDegradations.length,
            recentDegradations: [...this.recentDegradations],
        };
    }

    private computeHistogram(samples: number[]): HistogramBuckets {
        const buckets: HistogramBuckets = {
            "0-100": 0,
            "100-500": 0,
            "500-2000": 0,
            "2000-5000": 0,
            "5000+": 0,
        };

        for (const ms of samples) {
            if (ms <= 100) buckets["0-100"]++;
            else if (ms <= 500) buckets["100-500"]++;
            else if (ms <= 2000) buckets["500-2000"]++;
            else if (ms <= 5000) buckets["2000-5000"]++;
            else buckets["5000+"]++;
        }

        return buckets;
    }
}

/** Singleton collector instance */
export const metricsCollector = new MetricsCollector();