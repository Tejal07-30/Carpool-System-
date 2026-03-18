from collections import deque
from .models import Edge


def findpath(startnode, endnode):
    queue = deque([[startnode]])
    visited = set()

    while queue:
        path = queue.popleft()
        node = path[-1]

        if node == endnode:
            return path

        if node not in visited:
            visited.add(node)

            edges = Edge.objects.filter(fromnode=node)
            for edge in edges:
                newpath = list(path)
                newpath.append(edge.tonode)
                queue.append(newpath)

    return None