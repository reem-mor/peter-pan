/**
 * "Draw me the problem" — the live incident graph (brief §6.7).
 *
 * A static synthetic service map (fixtures/topology.ts) overlaid with the
 * streamed story: the affected service is highlighted, its blast radius
 * (upstream consumers) tinted, and the likely root-cause path emphasized.
 * Click (or keyboard-select) a node for owner / deploys / related alerts.
 */
import { useMemo, useState } from "react";
import {
  Background,
  BackgroundVariant,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
  type OnSelectionChangeParams,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { IncidentStory } from "@peterpan/types";
import {
  INCIDENT_MAPPINGS,
  SERVICES,
  SERVICE_EDGES,
  blastRadius,
  type ServiceKind,
} from "../fixtures/topology";
import { ServiceDetailPanel } from "./ServiceDetailPanel";
import { SectionLabel } from "./ui";

type NodeRole = "affected" | "suspect" | "blast" | "steady";

interface ServiceNodeData extends Record<string, unknown> {
  label: string;
  kind: ServiceKind;
  role: NodeRole;
}

type ServiceFlowNode = Node<ServiceNodeData, "service">;

const ROLE_STYLES: Record<NodeRole, { border: string; dot: string; word: string }> = {
  affected: { border: "border-danger", dot: "bg-danger", word: "affected" },
  suspect: { border: "border-s3", dot: "bg-s3", word: "suspect" },
  blast: { border: "border-warn", dot: "bg-warn", word: "blast radius" },
  steady: { border: "border-edge", dot: "bg-muted", word: "steady" },
};

function ServiceNode({ data }: NodeProps<ServiceFlowNode>) {
  const style = ROLE_STYLES[data.role];
  return (
    <div
      aria-label={`${data.label} (${data.kind}) — ${style.word}`}
      className={`rounded-lg border bg-panel-2 px-3.5 py-2.5 transition-colors duration-200 ${style.border}`}
    >
      <Handle type="target" position={Position.Left} className="!bg-edge-hi" />
      <div className="font-mono text-[13px] font-semibold text-ink">{data.label}</div>
      <div className="mt-1 flex items-center gap-1.5">
        <span aria-hidden="true" className={`size-[7px] rounded-full ${style.dot}`} />
        <span className="font-mono text-[10px] tracking-wider text-muted uppercase">
          {data.kind} · {style.word}
        </span>
      </div>
      <Handle type="source" position={Position.Right} className="!bg-edge-hi" />
    </div>
  );
}

const NODE_TYPES = { service: ServiceNode };

export function IncidentGraph({ story }: { story: IncidentStory | null }) {
  const [selectedService, setSelectedService] = useState<string | null>(null);

  const mapping = story === null ? null : (INCIDENT_MAPPINGS[story.alert.id] ?? null);

  const { nodes, edges } = useMemo(() => {
    const impacted = mapping === null ? new Set<string>() : blastRadius(mapping.affectedService);
    const path = mapping?.rootCausePath ?? [];
    const pathEdges = new Set<string>();
    for (let i = 0; i + 1 < path.length; i++) {
      pathEdges.add(`${path[i]}->${path[i + 1]}`);
    }

    const roleOf = (id: string): NodeRole => {
      if (mapping === null) return "steady";
      if (id === mapping.affectedService) return "affected";
      if (path.includes(id)) return "suspect";
      if (impacted.has(id)) return "blast";
      return "steady";
    };

    const nodes: ServiceFlowNode[] = SERVICES.map((s) => ({
      id: s.id,
      type: "service",
      position: s.position,
      data: { label: s.label, kind: s.kind, role: roleOf(s.id) },
    }));

    const edges: Edge[] = SERVICE_EDGES.map((e) => {
      const onPath = pathEdges.has(`${e.source}->${e.target}`);
      const stroke = onPath ? "var(--color-accent)" : "var(--color-edge-hi)";
      return {
        id: `${e.source}->${e.target}`,
        source: e.source,
        target: e.target,
        label: e.kind,
        animated: onPath,
        style: { stroke, strokeWidth: onPath ? 2 : 1.4 },
        markerEnd: { type: MarkerType.ArrowClosed, color: stroke },
        labelStyle: {
          fill: "var(--color-faint)",
          fontFamily: "var(--font-mono)",
          fontSize: 10,
        },
        labelBgStyle: { fill: "var(--color-panel)", fillOpacity: 0.9 },
      };
    });

    return { nodes, edges };
  }, [mapping]);

  const onSelectionChange = ({ nodes }: OnSelectionChangeParams) => {
    setSelectedService(nodes[0]?.id ?? null);
  };

  return (
    <section className="flex min-h-0 flex-col rounded-xl border border-edge bg-panel transition-colors duration-200 hover:border-edge-hi">
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-edge px-4 py-3">
        <div>
          <h2>
            <SectionLabel>Draw me the problem</SectionLabel>
          </h2>
          <p className="mt-0.5 text-xs text-faint">
            Service map · affected, blast radius, and likely root-cause path
          </p>
        </div>
        {mapping !== null ? (
          <p className="max-w-md text-[11px] text-muted">{mapping.rationale}</p>
        ) : (
          <p className="font-mono text-[11px] text-faint">awaiting story — map is steady</p>
        )}
      </header>
      <div className="flex min-h-0 flex-1 flex-col md:flex-row">
        <div className="h-[320px] min-w-0 flex-1 md:h-auto">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={NODE_TYPES}
            onSelectionChange={onSelectionChange}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            minZoom={0.4}
            maxZoom={1.75}
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable
            colorMode="dark"
            aria-label="Incident service-dependency graph"
          >
            <Background
              variant={BackgroundVariant.Dots}
              gap={24}
              size={1}
              color="var(--color-edge)"
            />
          </ReactFlow>
        </div>
        <ServiceDetailPanel
          serviceId={selectedService}
          onClose={() => setSelectedService(null)}
        />
      </div>
    </section>
  );
}
