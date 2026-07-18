/**
 * SSE consumption for `GET /agent/stream?alert_id=…` (docs/CONTRACTS.md §5).
 *
 * Event types: `step` (reasoning step), `evidence` (Evidence JSON), `story`
 * (final IncidentStory JSON), `done`. Fixture-first: if the backend is
 * unreachable the hook replays the identical event sequence from
 * `fixtures/replay.ts`, so the demo renders meaningfully with every backend
 * down (design-system invariant).
 */
import { useCallback, useEffect, useRef, useState } from "react";
import type { Evidence, IncidentStory } from "@peterpan/types";
import { REPLAY_STREAMS } from "../fixtures/replay";

/** Base URL for the agent service. Empty string = same origin; the vite dev
 * server proxies `/agent` to :8004 (see vite.config.ts). */
export const API_BASE: string =
  (import.meta.env.VITE_API_BASE as string | undefined) ?? "";

/** Mirror of the `step` event payload (CONTRACTS.md §5). */
export interface StepEvent {
  name: string;
  detail: string;
  ts: string;
}

/** One SSE frame, decoded. Discriminated on `event`. */
export type StreamFrame =
  | { event: "step"; data: StepEvent }
  | { event: "evidence"; data: Evidence }
  | { event: "story"; data: IncidentStory }
  | { event: "done"; data: { status: string } };

export type StreamPhase = "idle" | "connecting" | "streaming" | "done";
export type StreamMode = "live" | "replay";

export interface StreamState {
  phase: StreamPhase;
  /** Where frames are coming from. Meaningful once phase !== "idle". */
  mode: StreamMode;
  alertId: string | null;
  steps: StepEvent[];
  evidence: Evidence[];
  story: IncidentStory | null;
}

const INITIAL_STATE: StreamState = {
  phase: "idle",
  mode: "live",
  alertId: null,
  steps: [],
  evidence: [],
  story: null,
};

/** Pacing between canned frames so the replay reads like the live stream. */
const REPLAY_FRAME_DELAY_MS = 350;

export function useAgentStream(): {
  state: StreamState;
  start: (alertId: string) => void;
} {
  const [state, setState] = useState<StreamState>(INITIAL_STATE);
  // Sequence token: every start() takes ++seq and handlers render only if
  // their token is still current — live frames and replay timers can never
  // interleave across runs (design system §3, polled-UI rule).
  const seqRef = useRef(0);
  const sourceRef = useRef<EventSource | null>(null);
  const timersRef = useRef<number[]>([]);

  const teardown = useCallback(() => {
    sourceRef.current?.close();
    sourceRef.current = null;
    for (const t of timersRef.current) window.clearTimeout(t);
    timersRef.current = [];
  }, []);

  useEffect(() => teardown, [teardown]); // unmount cleanup

  const applyFrame = useCallback((seq: number, frame: StreamFrame) => {
    if (seq !== seqRef.current) return; // stale run — drop
    setState((s) => {
      switch (frame.event) {
        case "step":
          return { ...s, phase: "streaming", steps: [...s.steps, frame.data] };
        case "evidence":
          return {
            ...s,
            phase: "streaming",
            evidence: [...s.evidence, frame.data],
          };
        case "story":
          return { ...s, phase: "streaming", story: frame.data };
        case "done":
          return { ...s, phase: "done" };
      }
    });
  }, []);

  /** Canned replay of the captured event sequence — same frames, same order. */
  const startReplay = useCallback(
    (alertId: string, seq: number) => {
      const frames = REPLAY_STREAMS[alertId] ?? [];
      setState({
        phase: frames.length > 0 ? "connecting" : "done",
        mode: "replay",
        alertId,
        steps: [],
        evidence: [],
        story: null,
      });
      frames.forEach((frame, i) => {
        timersRef.current.push(
          window.setTimeout(
            () => applyFrame(seq, frame),
            REPLAY_FRAME_DELAY_MS * (i + 1),
          ),
        );
      });
    },
    [applyFrame],
  );

  const start = useCallback(
    (alertId: string) => {
      teardown();
      const seq = ++seqRef.current;
      setState({
        phase: "connecting",
        mode: "live",
        alertId,
        steps: [],
        evidence: [],
        story: null,
      });

      const source = new EventSource(
        `${API_BASE}/agent/stream?alert_id=${encodeURIComponent(alertId)}`,
      );
      sourceRef.current = source;

      const listen = <E extends StreamFrame["event"]>(event: E) => {
        source.addEventListener(event, (e: MessageEvent<string>) => {
          // Payloads come from our own typed service (SseEvent envelopes);
          // the cast mirrors CONTRACTS.md §5, not a validation step. A
          // malformed frame degrades to the fixture replay instead of
          // throwing mid-presentation.
          let data: unknown;
          try {
            data = JSON.parse(e.data);
          } catch {
            source.close();
            if (sourceRef.current === source) sourceRef.current = null;
            if (seq === seqRef.current) startReplay(alertId, seq);
            return;
          }
          applyFrame(seq, { event, data } as StreamFrame);
          if (event === "done") {
            source.close();
            if (sourceRef.current === source) sourceRef.current = null;
          }
        });
      };
      listen("step");
      listen("evidence");
      listen("story");
      listen("done");

      source.onerror = () => {
        // Connection refused, 404, or a mid-stream drop. EventSource would
        // retry forever; instead close and fall back to the canned fixture
        // replay of the same sequence (fixture-first — never a blank page).
        source.close();
        if (sourceRef.current === source) sourceRef.current = null;
        if (seq !== seqRef.current) return;
        startReplay(alertId, seq);
      };
    },
    [applyFrame, startReplay, teardown],
  );

  return { state, start };
}
