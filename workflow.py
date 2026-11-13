"""Lesson-specific workflow. Read this file before the execution adapter."""
from __future__ import annotations
import asyncio
import json
from pathlib import Path
from runtime import atomic_json, contained_path, in_process_tool

async def run(agent, data):
    import random
    size, goal = data['size'], tuple(data['goal'])
    if not 2 <= size <= 8 or not 1 <= data['explorers'] <= 8 or not 1 <= data['rounds'] <= 6:
        raise ValueError('Use a bounded grid, explorer count and rounds')
    pheromone, best, attempts = {}, None, 0
    async def explore(seed):
        rng, path = random.Random(seed), [(0, 0)]
        for _ in range(size * size):
            if path[-1] == goal:
                return path
            x, y = path[-1]
            moves = [(a,b) for a,b in ((x+1,y),(x,y+1),(x-1,y),(x,y-1)) if 0 <= a < size and 0 <= b < size and (a,b) not in path]
            if not moves:
                return None
            path.append(rng.choices(moves, weights=[1 + pheromone.get(p, 0) for p in moves])[0])
            await asyncio.sleep(0)
        return path if path[-1] == goal else None
    for round_index in range(data['rounds']):
        paths = await asyncio.gather(*(explore(data['seed'] + round_index * 100 + i) for i in range(data['explorers'])))
        pheromone = {cell: weight * .8 for cell, weight in pheromone.items()}
        attempts += len(paths)
        for path in paths:
            if path:
                for cell in path:
                    pheromone[cell] = pheromone.get(cell, 0) + 1 / len(path)
                if best is None or len(path) < len(best):
                    best = path
    explanation = await agent.ask('explain_swarm', 'Explain the observed shared route search; do not claim convergence or optimality.', {'best': best, 'attempts': attempts}, 'Explorers reinforce successful route cells while weights evaporate; this bounded run supplies a candidate, not an optimality proof.')
    return {'best_path': best, 'attempts': attempts, 'reinforced_cells': len(pheromone), 'explanation': explanation}
