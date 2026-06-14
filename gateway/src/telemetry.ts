/**
 * Telemetry module — centralized factory, emission, and degradation tracking.
 *
 * Provides:
 *   - createTelemetry(): build a RequestTelemetry from request context
 *   - recordDegradation(): mark a component as degraded + set fallback reason
 *   - emitTelemetry(): write telemetry to the Fastify logger
 *
 * In later iterations, this will also push to an external metrics pipeline.
 */

import type { FastifyBaseLogger } from "fastify";
import type {
	RequestTelemetry,
	DegradedComponent,
} from "./types.js";

/**
 * Create a new RequestTelemetry object from request context.
 */
export function createTelemetry(opts: {
	requestId: string;
	tenantId?: string;
	client?: string;
	model: string;
	messageCount: number;
	toolCount: number;
	stream: boolean;
}): RequestTelemetry {
	return {
		requestId: opts.requestId,
		tenantId: opts.tenantId ?? "default",
		client: opts.client ?? "unknown",
		model: opts.model,
		messageCount: opts.messageCount,
		toolCount: opts.toolCount,
		injectedTools: 0,
		toolCallsExecuted: 0,
		retrievalHits: 0,
		stream: opts.stream,
		providerLatencyMs: 0,
		fallbackReason: undefined,
		skippedComponents: [],
		createdAt: new Date(),
	};
}

/**
 * Record that a component was degraded during this request.
 * Sets both the skippedComponents list and a human-readable fallbackReason.
 */
export function recordDegradation(
	telemetry: RequestTelemetry,
	component: DegradedComponent,
	reason: string,
): void {
	if (!telemetry.skippedComponents.includes(component)) {
		telemetry.skippedComponents.push(component);
	}
	telemetry.fallbackReason = telemetry.fallbackReason
		? `${telemetry.fallbackReason}; ${reason}`
		: reason;
}

/**
 * Emit telemetry — currently writes a structured JSON line via the Fastify logger.
 * In future: push to a metrics pipeline, write to a telemetry table, etc.
 */
export function emitTelemetry(
	telemetry: RequestTelemetry,
	log: FastifyBaseLogger,
): void {
	log.info({ telemetry }, "request completed");
}

/**
 * Build a human-readable summary string from the telemetry object
 * (useful for in-band response headers, e.g. x-gateway-telemetry).
 */
export function telemetrySummary(telemetry: RequestTelemetry): string {
	const parts: string[] = [
		`lat=${telemetry.providerLatencyMs}ms`,
		`retrieval=${telemetry.retrievalHits}`,
		`tools=${telemetry.toolCallsExecuted}`,
	];
	if (telemetry.skippedComponents.length > 0) {
		parts.push(`degraded=${telemetry.skippedComponents.join(",")}`);
	}
	return parts.join(" ");
}