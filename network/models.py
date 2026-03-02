from django.db import models
class Node(models.Model):
    name=models.CharField(max_length=100,unique=True)
    description=models.TextField(blank=True)
    def _str_(self):
        return self.name
class Edge(models.Model):
    from_node=models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        related_name="outgoing_edges"
    )
    to_node=models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        related_name="incoming_edges"
    )
    def __str__(self):
        return f"{self.from_node} -> {self.to_node}"
    class Meta:
        unique_together=("from_node","to_node")