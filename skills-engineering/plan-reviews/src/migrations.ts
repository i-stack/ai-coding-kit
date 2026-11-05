import type { EmbeddedChunk, KbIndexData } from "./types.js";

export const CURRENT_SCHEMA_VERSION = 2;

export function detectPromptInjection(text: string): string[] {
	const rules: Array<[string, RegExp]> = [
		["instruction-override", /(?:ignore|disregard).{0,30}(?:previous|system|instructions?)|忽略.{0,20}(?:规则|指令|系统)/iu],
		["destructive-command", /(?:delete|remove|erase).{0,30}(?:files?|repository|project)|删除.{0,20}(?:文件|项目|仓库)/iu],
		["secret-exfiltration", /(?:print|reveal|read).{0,30}(?:secret|token|password|key)|(?:读取|输出|泄露).{0,20}(?:密钥|令牌|密码)/iu],
		["role-impersonation", /(?:system message|developer message|you are now)|(?:系统消息|开发者消息|你现在是)/iu],
	];
	return rules.filter(([, pattern]) => pattern.test(text)).map(([name]) => name);
}

export function annotateChunk(chunk: EmbeddedChunk): EmbeddedChunk {
	const signals = detectPromptInjection(chunk.text);
	return {
		...chunk,
		trustLevel: chunk.trustLevel ?? "untrusted-history",
		promptInjectionSuspected: signals.length > 0,
		promptInjectionSignals: signals,
	};
}

export function migrateIndex(input: unknown): KbIndexData {
	if (!input || typeof input !== "object") throw new Error("Invalid knowledge-base index root");
	let data = { ...(input as Record<string, unknown>) };
	let version = typeof data.schemaVersion === "number" ? data.schemaVersion : 0;
	if (version > CURRENT_SCHEMA_VERSION) {
		throw new Error(`Unsupported knowledge-base schema version ${version}; current=${CURRENT_SCHEMA_VERSION}`);
	}
	if (version === 0) {
		data = { ...data, schemaVersion: 1 };
		version = 1;
	}
	if (version === 1) {
		const chunks = Array.isArray(data.chunks) ? data.chunks.map((chunk) => annotateChunk(chunk as EmbeddedChunk)) : [];
		data = { ...data, schemaVersion: 2, chunks };
		version = 2;
	}
	if (version !== CURRENT_SCHEMA_VERSION) throw new Error(`No migration path for schema version ${version}`);
	return data as unknown as KbIndexData;
}
