import React, { useRef, useLayoutEffect, useState, useMemo, useEffect } from "react";
import * as THREE from "three";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import ForceGraph3D from "3d-force-graph";
import { useResearchStore } from "../stores/useResearchStore";

// We use the 3d-force-graph library logic but render using React Three Fiber's InstancedMesh
// Actually, pure 3d-force-graph is easier to integrate as a black box if we want just the graph.
// BUT for "Premium Design" and deep integration (InstancedMesh), we should build a custom loop.
//
// STRATEGY: 
// Use `d3-force-3d` for physics.
// Use `InstancedMesh` for rendering.

import { forceSimulation, forceLink, forceManyBody, forceCenter } from "d3-force-3d";

function GraphNodes({ data, onNodeClick }) {
    const meshRef = useRef();
    const { nodes, links } = data;

    // Physics Simulation
    const simulation = useMemo(() => {
        if (!nodes.length) return null;

        return forceSimulation(nodes)
            .force("link", forceLink(links).id(d => d.id).distance(50))
            .force("charge", forceManyBody().strength(-50))
            .force("center", forceCenter());
    }, [nodes, links]);

    // Update loop
    useFrame(() => {
        if (!simulation) return;
        simulation.tick(); // Advance physics

        // Update InstancedMesh matrices
        const tempObject = new THREE.Object3D();

        nodes.forEach((node, i) => {
            const { x, y, z } = node;
            tempObject.position.set(x, y, z);
            tempObject.scale.set(1, 1, 1); // Could scale based on citation count
            tempObject.updateMatrix();
            meshRef.current.setMatrixAt(i, tempObject.matrix);
        });

        meshRef.current.instanceMatrix.needsUpdate = true;
    });

    return (
        <instancedMesh
            ref={meshRef}
            args={[null, null, nodes.length]}
            onClick={(e) => {
                const nodeId = e.instanceId;
                if (nodeId !== undefined && nodes[nodeId]) {
                    onNodeClick(nodes[nodeId]);
                }
            }}
        >
            <sphereGeometry args={[2, 16, 16]} />
            <meshStandardMaterial color="#3b82f6" />
        </instancedMesh>
    );
}

// Simple edge rendering (Lines are heavier, using simple lines for MVP)
function GraphEdges({ data }) {
    const linesRef = useRef();

    useFrame(() => {
        // Edges are tricky with React. For hi-perf, usually LineSegments with BufferGeometry 
        // updated every frame.
        // Skipping dynamic edge updates for this specific "Fastest Path" iteration 
        // unless we really need wires. 
        // Nodes are the priority for clustering visualization.
    });

    return null;
}

export function CitationGraph({ onNodeClick }) {
    const [data, setData] = useState({ nodes: [], links: [] });

    useEffect(() => {
        fetch('/api/graph')
            .then(r => r.json())
            .then(graphData => {
                // Transform data for D3 (it mutates objects, so clone)
                const nodes = graphData.nodes.map(n => ({ ...n }));
                const links = graphData.links.map(l => ({ ...l }));
                setData({ nodes, links });
            });
    }, []);

    if (!data.nodes.length) return <div className="text-white">Loading Graph...</div>;

    return (
        <div className="w-full h-full bg-black">
            <Canvas camera={{ position: [0, 0, 200], fov: 60 }}>
                <ambientLight intensity={0.5} />
                <pointLight position={[10, 10, 10]} intensity={1} />
                <OrbitControls enableDamping dampingFactor={0.1} rotateSpeed={0.5} />

                <GraphNodes data={data} onNodeClick={onNodeClick} />
                {/* <GraphEdges data={data} /> */}

                {/* Starfield Background */}
                <color attach="background" args={['#050505']} />
                <gridHelper args={[1000, 50, 0x222222, 0x111111]} />
            </Canvas>
        </div>
    );
}
