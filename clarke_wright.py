from geopy.distance import geodesic
from functools import lru_cache

class ClarkeWrightOptimizer:
    def __init__(self, df):
        self.df = df.set_index('id')
        self.depot = self.df.loc[0]
    
    @lru_cache(maxsize=None)
    def _calculate_distance(self, id1, id2):
        coord1 = self.df.loc[id1, ['lat', 'lon']].values
        coord2 = self.df.loc[id2, ['lat', 'lon']].values
        return geodesic(coord1, coord2).km

    def _generate_savings(self):
        clients = self.df[self.df.index != 0].index
        return [
            (i, j, self._calculate_distance(0, i) + self._calculate_distance(0, j) - self._calculate_distance(i, j))
            for i in clients
            for j in clients
            if i < j
        ]

    def optimize_routes(self, vehicle_capacity):
        savings = sorted(self._generate_savings(), key=lambda x: -x[2])
        routes = [[i] for i in self.df.index if i != 0]
        
        for i, j, _ in savings:
            route_i = next((r for r in routes if i in r), None)
            route_j = next((r for r in routes if j in r), None)
            
            if route_i and route_j and route_i != route_j:
                total_load = sum(self.df.loc[x, 'positions'] for x in route_i + route_j)
                if total_load <= vehicle_capacity:
                    if route_i[-1] == i and route_j[0] == j:
                        routes.append(route_i + route_j)
                        routes.remove(route_i)
                        routes.remove(route_j)
        
        return [[0] + r + [0] for r in routes]

    def calculate_route_metrics(self, route, capacity):
        clients = route[1:-1]
        positions_used = sum(self.df.loc[x, 'positions'] for x in clients)
        return {
            'distance': sum(self._calculate_distance(route[i], route[i+1]) for i in range(len(route)-1)),
            'utilization': (positions_used / capacity) * 100,
            'clients_str': " → ".join(self.df.loc[x, 'nom'] for x in clients)
        }