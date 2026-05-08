"use client";

import { useMemo } from "react";
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  MarkerType,
  Position,
  useNodesState,
  useEdgesState,
} from "reactflow";
import "reactflow/dist/style.css";

import type { GraphData } from "@/types";

interface DependencyGraphProps {
  data: GraphData;
}

const nodeStyles = {
  file: {
    background: "hsl(224 40% 12%)",
    border: "1px solid hsl(220 70% 60%)",
    color: "hsl(210 20% 90%)",
    borderRadius: "8px",
    padding: "8px 16px",
    fontSize: "11px",
    fontFamily: "monospace",
    minWidth: "120px",
    textAlign: "center" as const,
  },
  external: {
    background: "hsl(280 40% 12%)",
    border: "1px solid hsl(280 50% 50%)",
    color: "hsl(280 20% 80%)",
    borderRadius: "8px",
    padding: "8px 16px",
    fontSize: "11px",
    fontFamily: "monospace",
    minWidth: "100px",
    textAlign: "center" as const,
  },
  function: {
    background: "hsl(160 40% 12%)",
    border: "1px solid hsl(160 50% 45%)",
    color: "hsl(160 20% 80%)",
    borderRadius: "8px",
    padding: "8px 16px",
    fontSize: "11px",
    fontFamily: "monospace",
    textAlign: "center" as const,
  },
};

function layoutNodes(nodes: GraphData["nodes"], edges: GraphData["edges"]): Node[] {
  const nodeMap = new Map<string, { x: number; y: number; incoming: number }>();

  // Count incoming edges for each node
  for (const node of nodes) {
    nodeMap.set(node.id, { x: 0, y: 0, incoming: 0 });
  }
  for (const edge of edges) {
    const target = nodeMap.get(edge.target);
    if (target) target.incoming++;
  }

  // Simple layered layout: nodes with no incoming edges go left,
  // others are placed based on dependency depth
  const layers: Map<number, string[]> = new Map();
  const assigned = new Set<string>();

  // Assign layers
  let changed = true;
  let layer = 0;
  const remaining = new Set(nodes.map((n) => n.id));

  while (remaining.size > 0 && changed) {
    changed = false;
    const currentLayer: string[] = [];

    for (const nodeId of remaining) {
      const incomingEdges = edges.filter((e) => e.target === nodeId);
      const allAssigned = incomingEdges.every(
        (e) => assigned.has(e.source) || !remaining.has(e.source)
      );

      if (allAssigned || layer === 0) {
        currentLayer.push(nodeId);
      }
    }

    if (currentLayer.length > 0) {
      for (const nodeId of currentLayer) {
        remaining.delete(nodeId);
        assigned.add(nodeId);
      }
      layers.set(layer, currentLayer);
      changed = true;
    }
    layer++;

    if (layer > 20) break; // Safety limit
  }

  // Add any remaining nodes
  if (remaining.size > 0) {
    layers.set(layer, [...remaining]);
  }

  // Position nodes
  const X_GAP = 220;
  const Y_GAP = 60;
  const result: Node[] = [];

  for (const [layerIdx, nodeIds] of layers) {
    const totalHeight = nodeIds.length * Y_GAP;
    const startY = -totalHeight / 2;

    nodeIds.forEach((nodeId, idx) => {
      const originalNode = nodes.find((n) => n.id === nodeId);
      if (!originalNode) return;

      result.push({
        id: nodeId,
        position: {
          x: layerIdx * X_GAP,
          y: startY + idx * Y_GAP,
        },
        data: {
          label: (
            <div>
              <div className="font-semibold">{originalNode.label}</div>
              {originalNode.data.fullPath && (
                <div className="text-[10px] opacity-60 mt-0.5">
                  {originalNode.data.fullPath.length > 30
                    ? "..." + originalNode.data.fullPath.slice(-28)
                    : originalNode.data.fullPath}
                </div>
              )}
            </div>
          ),
        },
        style: nodeStyles[originalNode.type as keyof typeof nodeStyles] || nodeStyles.file,
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
    });
  });
  }

  return result;
}

export function DependencyGraph({ data }: DependencyGraphProps) {
  const initialNodes = useMemo(() => layoutNodes(data.nodes, data.edges), [data]);

  const initialEdges: Edge[] = useMemo(
    () =>
      data.edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.label,
        animated: edge.animated,
        style: { stroke: "hsl(220 70% 60%)", strokeWidth: 1.5 },
        labelStyle: {
          fill: "hsl(217 10% 64%)",
          fontSize: 10,
          fontFamily: "monospace",
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: "hsl(220 70% 60%)",
          width: 12,
          height: 12,
        },
      })),
    [data.edges]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      fitView
      attributionPosition="bottom-left"
      proOptions={{ hideAttribution: true }}
    >
      <Background color="hsl(224 20% 15%)" gap={20} />
      <Controls />
      <MiniMap
        nodeColor={(node) => {
          const type = node.style?.borderColor;
          return type || "hsl(220 70% 60%)";
        }}
        maskColor="hsl(224 50% 5% / 0.8)"
      />
    </ReactFlow>
  );
}
